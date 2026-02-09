from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class SentenceTransformerEmbedder:
    """
    I wrap SentenceTransformer so the rest of the system doesn't care
    which embedding model is being used.
    """

    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        vec = self.model.encode(
            text or '',
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vec.tolist()
