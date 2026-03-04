import tempfile
import threading
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from PyQt5.QtCore import QObject, pyqtSignal


SAMPLE_RATE = 16_000  # Whisper-optimal
CHANNELS = 1


class AudioRecorder(QObject):
    """Records microphone audio into a temporary WAV file."""

    finished = pyqtSignal(str)   # emits path to the recorded WAV
    discarded = pyqtSignal()      # emitted when recording was too short

    def __init__(self):
        super().__init__()
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    def start(self):
        self._frames.clear()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=self._audio_callback,
        )
        self._stream.start()

    MIN_DURATION_S = 0.6

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._frames:
                self.discarded.emit()
                return
            audio = np.concatenate(self._frames, axis=0)

        duration = len(audio) / SAMPLE_RATE
        if duration < self.MIN_DURATION_S:
            self.discarded.emit()
            return

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wavfile.write(tmp.name, SAMPLE_RATE, audio)
        tmp.close()
        self.finished.emit(tmp.name)

    def _audio_callback(self, indata, _frames, _time, _status):
        with self._lock:
            self._frames.append(indata.copy())
