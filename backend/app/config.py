from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./aegis.db"

    # Pipeline backends. "builtin"/"none"/"passthrough" run fully offline.
    embedder: str = "builtin"
    stt_backend: str = "none"
    translator: str = "passthrough"

    # Duplicate detection. 0.45 suits the built-in hashing embedder (paraphrases score ~0.5-0.7,
    # unrelated reports < 0.15). Sentence-BERT scores run higher: use ~0.75 with EMBEDDER=sbert.
    dedup_similarity: float = 0.45
    dedup_radius_km: float = 2.0
    dedup_window_hours: float = 6.0

    # Severity tier cut-offs
    tier_critical: float = 80.0
    tier_high: float = 60.0
    tier_medium: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
