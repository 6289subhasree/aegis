"""Speech-to-text. STT_BACKEND=whisper uses faster-whisper locally (free, offline)."""

from functools import lru_cache
from typing import Protocol

from ..config import get_settings


class SpeechToText(Protocol):
    def transcribe(self, audio: bytes) -> tuple[str, str]:
        """Return (text, language_code)."""


class NoSTT:
    def transcribe(self, audio: bytes) -> tuple[str, str]:
        raise RuntimeError("Voice reports need STT_BACKEND=whisper (see requirements-ml.txt)")


class WhisperSTT:  # pragma: no cover - needs model download
    def __init__(self, size: str = "small"):
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise RuntimeError("STT_BACKEND=whisper needs: pip install -r requirements-ml.txt") from e
        self._model = WhisperModel(size, compute_type="int8")

    def transcribe(self, audio: bytes) -> tuple[str, str]:
        import io

        segments, info = self._model.transcribe(io.BytesIO(audio))
        return " ".join(s.text.strip() for s in segments), info.language


@lru_cache
def get_stt() -> SpeechToText:
    return WhisperSTT() if get_settings().stt_backend == "whisper" else NoSTT()
