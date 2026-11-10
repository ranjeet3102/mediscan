import os
import math
import hashlib
import logging
from typing import List, Optional

logger = logging.getLogger("medical_ocr.embedding")

class VectorEmbeddingService:
    """
    High-performance 384-dimensional vector embedding engine for clinical knowledge grounding.
    Supports SentenceTransformers (all-MiniLM-L6-v2) with a deterministic fallback vectorizer.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._model = None
        self._initialized = False

    def _lazy_init_model(self):
        if self._initialized:
            return
        if os.getenv("ENABLE_ST_EMBEDDINGS", "false").lower() == "true":
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded SentenceTransformer ('all-MiniLM-L6-v2') successfully.")
            except Exception as e:
                logger.info(f"SentenceTransformer fallback: {e}")
                self._model = None
        else:
            self._model = None
        self._initialized = True

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized 384-dimensional vector for a text string.
        """
        self._lazy_init_model()

        clean_text = text.strip() if text else ""
        if not clean_text:
            return [0.0] * self.dimension

        if self._model is not None:
            try:
                emb = self._model.encode(clean_text, convert_to_numpy=True)
                return emb.tolist()
            except Exception as e:
                logger.warning(f"Embedding model execution failed: {e}; falling back to dense hash vectorizer.")

        # Deterministic semantic n-gram dense projection generator (384-d unit vector)
        return self._generate_dense_vector(clean_text)

    def _generate_dense_vector(self, text: str) -> List[float]:
        """
        Generates a consistent, normalized 384-dimensional semantic dense representation.
        Uses character n-grams and token hashes projected onto a unit sphere.
        """
        vector = [0.0] * self.dimension
        tokens = text.lower().split()

        # Token and sub-token n-grams
        ngrams = []
        for t in tokens:
            ngrams.append(t)
            if len(t) >= 4:
                for i in range(len(t) - 2):
                    ngrams.append(t[i:i+3])

        if not ngrams:
            ngrams = [text.lower()]

        for term in ngrams:
            # Hash term to dimension coordinates
            h = hashlib.sha256(term.encode("utf-8")).digest()
            for i in range(0, len(h) - 1, 2):
                idx = (h[i] * 256 + h[i+1]) % self.dimension
                val = ((h[i] % 31) - 15) / 15.0
                vector[idx] += val

        # Normalize to unit length (L2 norm)
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        else:
            vector[0] = 1.0

        return vector

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Computes cosine similarity between two dense vectors.
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        sim = dot_product / (norm_a * norm_b)
        return round(max(-1.0, min(1.0, sim)), 4)

# Global singleton embedding service
embedding_service = VectorEmbeddingService()
