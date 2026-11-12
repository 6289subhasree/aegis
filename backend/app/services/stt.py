"""Speech-to-text. STT_BACKEND=whisper uses faster-whisper locally (free, offline).

For speech that is not English, Whisper runs twice: once to transcribe in the original language
(shown to responders) and once with task="translate" to get English (used by the pipeline).
"""

import io
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from ..config import get_settings


@dataclass(frozen=True)
class Transcript:
    text: str  # in the spoken language
    english: str  # English version (same as text when the speech was English)
    language: str  # detected or hinted language code, e.g. "hi", "en"


class SpeechToText(Protocol):
    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript: ...


class NoSTT:
    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        raise RuntimeError(
            "Voice reports need STT_BACKEND=whisper. Install with: pip install -r requirements-voice.txt"
        )


class WhisperSTT:  # pragma: no cover - needs a model download
    def __init__(self, size: str | None = None, device: str | None = None):
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise RuntimeError("STT_BACKEND=whisper needs: pip install -r requirements-voice.txt") from e
        s = get_settings()
        self._model = WhisperModel(
            size or s.whisper_model,
            device=device or s.whisper_device,
            compute_type="int8" if (device or s.whisper_device) == "cpu" else "float16",
        )

    def _run(self, audio: bytes, task: str, language: str | None):
        segments, info = self._model.transcribe(
            io.BytesIO(audio),
            task=task,
            language=language,
            vad_filter=True,  # skip silence; also avoids hallucinated text on empty audio
            beam_size=5,
        )
        return " ".join(seg.text.strip() for seg in segments).strip(), info.language

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        text, lang = self._run(audio, "transcribe", language)
        if not text or lang == "en":
            return Transcript(text=text, english=text, language=lang or "en")
        english, _ = self._run(audio, "translate", lang)
        return Transcript(text=text, english=english, language=lang)


@lru_cache
def get_stt() -> SpeechToText:
    return WhisperSTT() if get_settings().stt_backend == "whisper" else NoSTT()
