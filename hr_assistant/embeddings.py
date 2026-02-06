from __future__ import annotations

from typing import List

from langchain_core.embeddings import Embeddings
from pinecone import Pinecone

from .config import Settings


class PineconeInferenceEmbeddings(Embeddings):
    """LangChain-compatible embeddings using Pinecone Inference API.

    This is the simplest way to keep embeddings dimension aligned with your Pinecone index.
    """

    def __init__(self, pc: Pinecone, settings: Settings):
        self._pc = pc
        self._model = settings.pinecone_embed_model
        self._passage_type = settings.pinecone_embed_input_type_passage
        self._query_type = settings.pinecone_embed_input_type_query
        # Pinecone Inference API has a max inputs-per-request limit (commonly 96).
        self._max_batch_size = 96

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        if not texts:
            return vectors

        for start in range(0, len(texts), self._max_batch_size):
            batch = texts[start : start + self._max_batch_size]
            out = self._pc.inference.embed(
                model=self._model,
                inputs=batch,
                parameters={"input_type": self._passage_type, "truncate": "END"},
            )
            vectors.extend([item["values"] for item in out.data])
        return vectors

    def embed_query(self, text: str) -> List[float]:
        out = self._pc.inference.embed(
            model=self._model,
            inputs=[text],
            parameters={"input_type": self._query_type, "truncate": "END"},
        )
        return out.data[0]["values"]

