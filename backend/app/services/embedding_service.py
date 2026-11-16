"""
Embedding generation service.
Supports SentenceTransformers, API providers, and deterministic offline hash-embeddings.
"""
import math
import hashlib
from typing import List
import numpy as np
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("embedding_service")

_MODEL_INSTANCE = None
_MODEL_FAILED = False


def _get_sentence_transformer():
    global _MODEL_INSTANCE, _MODEL_FAILED
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE
    if _MODEL_FAILED:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
        _MODEL_INSTANCE = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return _MODEL_INSTANCE
    except Exception as e:
        logger.warning(f"SentenceTransformer not loaded ({str(e)}). Using deterministic semantic fallback.")
        _MODEL_FAILED = True
        return None


class EmbeddingService:
    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """Generates a normalized embedding vector for a single text."""
        return cls.get_embeddings_batch([text])[0]

    @classmethod
    def get_embeddings_batch(cls, texts: List[str]) -> List[List[float]]:
        """Generates normalized embedding vectors for a batch of texts."""
        if not texts:
            return []

        model = _get_sentence_transformer()
        if model is not None:
            try:
                embeddings = model.encode(texts, batch_size=settings.EMBEDDING_BATCH_SIZE, normalize_embeddings=True)
                return [e.tolist() for e in embeddings]
            except Exception as e:
                logger.warning(f"Inference error with SentenceTransformer: {str(e)}. Falling back to deterministic embedding.")

        # Deterministic semantic hash embedding fallback (dimension = settings.VECTOR_DIMENSION)
        return [cls._compute_deterministic_embedding(t, settings.VECTOR_DIMENSION) for t in texts]

    @staticmethod
    def _compute_deterministic_embedding(text: str, dim: int = 384) -> List[float]:
        """
        Generates a unit-normalized vector deterministically from text tokens.
        Preserves cosine similarity properties for identical or overlapping vocabulary.
        """
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            vec[0] = 1.0
            return vec.tolist()

        for word in words:
            # Hash word into bucket indices and signs
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            vec[idx] += sign

            # Bigram token interaction
            h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx2 = h2 % dim
            vec[idx2] += 0.5 * (1.0 if (h2 // dim) % 2 == 0 else -1.0)

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculates cosine similarity between two unit vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
