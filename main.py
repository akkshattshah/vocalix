import sys
import os
import threading
import webbrowser
import logging
import queue as _queue

from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon

from ui.widget import FloatingPill, StateIndicator
from ui.main_window import MainWindow
from ui.setup_dialog import ApiKeyDialog
from core.hotkey import HotkeyListener
from core.recorder import AudioRecorder
from core.transcriber import Transcriber
from core.formatter import Formatter, detect_command
from core.commander import Commander
from core.injector import inject_text
from core.config import get_api_key, set_api_key, get_hotkey
from auth.session import is_authenticated, clear_session
from auth.server import run_server


load_dotenv()

logging.getLogger("werkzeug").setLevel(logging.ERROR)

_dispatch: _queue.Queue = _queue.Queue()


def _resource_path(relative: str) -> str:
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


def _ensure_authenticated():
    """Block until the user has signed in via the browser."""
    if is_authenticated():
        return

    auth_event = threading.Event()
    server_thread = threading.Thread(
        target=run_server, args=(auth_event,), daemon=True,
    )
    server_thread.start()

    webbrowser.open("http://localhost:5111/login")
    print("[vocalix] Waiting for sign-in…")
    auth_event.wait()
    print("[vocalix] Authenticated.")


def _ensure_api_key(app: QApplication) -> str:
    """Return the OpenAI API key, prompting the user if not yet stored."""
    key = get_api_key()
    if key:
        return key

    dlg = ApiKeyDialog()
    if dlg.exec_() == ApiKeyDialog.Accepted:
        key = dlg.get_key()
        set_api_key(key)
        return key

    sys.exit(0)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    api_key = _ensure_api_key(app)
    os.environ["OPENAI_API_KEY"] = api_key

    _ensure_authenticated()

    # --- System tray icon ---

    logo_path = _resource_path("logo.png")
    tray_icon = QSystemTrayIcon(QIcon(logo_path), app)

    tray_menu = QMenu()
    open_action = QAction("Open Vocalix")
    quit_action = QAction("Quit")
    tray_menu.addAction(open_action)
    tray_menu.addSeparator()
    tray_menu.addAction(quit_action)
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Vocalix")
    tray_icon.show()

    # --- Main window + floating pill ---

    window = MainWindow()
    pill = FloatingPill()

    def show_app():
        window.show()
        window.raise_()
        window.activateWindow()
        pill.show()

    def quit_app():
        hotkey.stop()
        pill.hide()
        window.hide()
        tray_icon.hide()
        app.quit()

    open_action.triggered.connect(show_app)
    quit_action.triggered.connect(quit_app)
    tray_icon.activated.connect(
        lambda reason: show_app() if reason == QSystemTrayIcon.Trigger else None
    )

    # Override window close to fully quit
    def on_window_close(event):
        hotkey.stop()
        pill.hide()
        tray_icon.hide()
        event.accept()
        app.quit()

    window.closeEvent = on_window_close

    # --- Hotkey and audio pipeline ---

    hotkey = HotkeyListener(hotkey=get_hotkey())
    recorder = AudioRecorder()
    transcriber = Transcriber()
    formatter = Formatter()
    commander = Commander()

    def _poll():
        while not _dispatch.empty():
            try:
                fn, args = _dispatch.get_nowait()
                fn(*args)
            except Exception as e:
                print(f"[vocalix] dispatch error: {e}", flush=True)

    poll_timer = QTimer()
    poll_timer.setInterval(50)
    poll_timer.timeout.connect(_poll)
    poll_timer.start()

    # --- Callbacks ---

    def on_start_recording():
        print("[vocalix] Recording started", flush=True)
        pill.set_state(StateIndicator.RECORDING)
        recorder.start()

    def on_stop_recording():
        print("[vocalix] Recording stopped", flush=True)
        pill.set_state(StateIndicator.TRANSCRIBING)
        recorder.stop()

    def on_discarded():
        print("[vocalix] Recording discarded (too short)", flush=True)
        pill.set_state(StateIndicator.IDLE)

    def on_wav_ready(wav_path: str):
        print(f"[vocalix] WAV ready, sending to Whisper …", flush=True)

        def _work():
            try:
                text = transcriber.transcribe_sync(wav_path)
                print(f"[vocalix] Whisper returned: {text!r}", flush=True)
                if text:
                    _dispatch.put((on_raw_transcription, (text,)))
                else:
                    _dispatch.put((on_error, ("Whisper returned empty text.",)))
            except Exception as exc:
                print(f"[vocalix] Whisper error: {exc}", flush=True)
                _dispatch.put((on_error, (str(exc),)))

        threading.Thread(target=_work, daemon=True).start()

    def on_raw_transcription(raw_text: str):
        print(f"[vocalix] Transcription: {raw_text!r}", flush=True)
        is_cmd, payload = detect_command(raw_text)

        if is_cmd:
            pill.set_state(StateIndicator.COMMANDING)

            def _work():
                try:
                    result = commander.execute_sync(payload)
                    print(f"[vocalix] Command result: {result!r}", flush=True)
                    _dispatch.put((on_formatted, (result,)))
                except Exception as exc:
                    print(f"[vocalix] Command error: {exc}", flush=True)
                    _dispatch.put((on_error, (str(exc),)))

            threading.Thread(target=_work, daemon=True).start()
        else:
            def _work():
                try:
                    result = formatter.format_sync(raw_text)
                    print(f"[vocalix] Formatted result: {result!r}", flush=True)
                    _dispatch.put((on_formatted, (result,)))
                except Exception as exc:
                    print(f"[vocalix] Format error: {exc}", flush=True)
                    _dispatch.put((on_error, (str(exc),)))

            threading.Thread(target=_work, daemon=True).start()

    def on_formatted(text: str):
        if not text or not text.strip():
            print("[vocalix] Empty result, skipping injection", flush=True)
            pill.set_state(StateIndicator.IDLE)
            return

        print(f"[vocalix] Injecting: {text!r}", flush=True)
        hotkey.suppress(True)
        try:
            inject_text(text)
        except Exception as exc:
            print(f"[vocalix] Inject error: {exc}", flush=True)
        finally:
            hotkey.suppress(False)
        pill.set_state(StateIndicator.IDLE)

    def on_error(msg: str):
        print(f"[vocalix] error: {msg}", flush=True)
        pill.set_state(StateIndicator.IDLE)

    # --- Signal wiring ---

    hotkey.start_recording.connect(on_start_recording)
    hotkey.stop_recording.connect(on_stop_recording)
    recorder.finished.connect(on_wav_ready)
    recorder.discarded.connect(on_discarded)

    window.hotkey_updated.connect(lambda key: hotkey.restart(key))

    def on_signed_out():
        clear_session()
        hotkey.stop()
        pill.hide()
        window.hide()
        tray_icon.hide()
        app.quit()

    window.signed_out.connect(on_signed_out)

    # --- Launch ---

    show_app()
    hotkey.start()

    exit_code = app.exec_()
    hotkey.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
