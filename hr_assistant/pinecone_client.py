from __future__ import annotations

from pinecone import Pinecone

from .config import Settings


def build_pinecone(settings: Settings) -> Pinecone:
    return Pinecone(api_key=settings.pinecone_api_key)


def get_index(pc: Pinecone, settings: Settings):
    # Use host targeting for faster data ops and to avoid control-plane lookups.
    return pc.Index(host=settings.pinecone_index_host)

