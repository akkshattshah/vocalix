import os
from openai import OpenAI
from PyQt5.QtCore import QObject, pyqtSignal


class Transcriber(QObject):
    """Sends a WAV file to OpenAI Whisper and emits the transcribed text."""

    transcription_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def transcribe(self, wav_path: str):
        try:
            with open(wav_path, "rb") as f:
                result = self._client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    prompt="Hey Vocalix",
                )
            text = result.text.strip()
            if text:
                self.transcription_ready.emit(text)
            else:
                self.error.emit("Whisper returned empty text.")
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass

    def transcribe_sync(self, wav_path: str) -> str:
        """Synchronous variant -- returns transcribed text, raises on error."""
        try:
            with open(wav_path, "rb") as f:
                result = self._client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    prompt="Hey Vocalix",
                )
            return result.text.strip()
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass
