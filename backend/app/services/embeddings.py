"""Text embeddings.

`builtin` is a deterministic hashing embedder (word + character n-grams). It needs no model
download, so the framework runs offline. Set EMBEDDER=sbert to use Sentence-BERT instead.
"""

import hashlib
import re
from functools import lru_cache
from typing import Protocol

import numpy as np

from ..config import get_settings

DIM = 256
_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "of", "to", "and", "we", "our", "it"}


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder:
    def embed(self, text: str) -> list[float]:
        vec = np.zeros(DIM, dtype=float)
        words = [w for w in _WORD.findall(text.lower()) if w not in _STOP]
        grams = list(words)
        for w in words:
            padded = f"#{w}#"
            grams.extend(padded[i : i + 3] for i in range(len(padded) - 2))
        for g in grams:
            h = int(hashlib.md5(g.encode()).hexdigest(), 16)
            vec[h % DIM] += 1.0 if (h >> 8) & 1 else -1.0
        n = np.linalg.norm(vec)
        return (vec / n).tolist() if n else vec.tolist()


class SBertEmbedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("EMBEDDER=sbert needs: pip install -r requirements-ml.txt") from e
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:  # pragma: no cover
        return self._model.encode(text, normalize_embeddings=True).tolist()


@lru_cache
def get_embedder() -> Embedder:
    kind = get_settings().embedder
    if kind == "sbert":
        return SBertEmbedder()
    return HashingEmbedder()
