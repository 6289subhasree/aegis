"""Language ID and translation to English.

The default `passthrough` translator assumes text is already English. TRANSLATOR=indictrans2
is reserved for the AI4Bharat IndicTrans2 model (free, local); see docs/ROADMAP.md.
"""

from functools import lru_cache
from typing import Protocol

from ..config import get_settings


class Translator(Protocol):
    def to_english(self, text: str, source_lang: str | None = None) -> tuple[str, str]:
        """Return (english_text, detected_language_code)."""


class PassthroughTranslator:
    def to_english(self, text: str, source_lang: str | None = None) -> tuple[str, str]:
        return text, source_lang or "en"


class IndicTrans2Translator:  # pragma: no cover - to be implemented
    def to_english(self, text: str, source_lang: str | None = None) -> tuple[str, str]:
        raise NotImplementedError("IndicTrans2 adapter is on the roadmap (docs/ROADMAP.md)")


@lru_cache
def get_translator() -> Translator:
    return IndicTrans2Translator() if get_settings().translator == "indictrans2" else PassthroughTranslator()
