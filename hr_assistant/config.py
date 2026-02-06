from __future__ import annotations

from dataclasses import dataclass
import os


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    # Pinecone
    pinecone_api_key: str
    pinecone_index_host: str
    pinecone_namespace: str

    # Embeddings (Pinecone Inference)
    pinecone_embed_model: str
    pinecone_embed_input_type_passage: str
    pinecone_embed_input_type_query: str

    # Gemini
    gemini_api_key: str
    gemini_model: str

    # MongoDB
    mongodb_uri: str
    mongodb_db: str
    mongodb_employees_collection: str
    mongodb_promotion_rules_collection: str
    mongodb_promotion_progress_collection: str


def load_settings() -> Settings:
    return Settings(
        pinecone_api_key=_require("PINECONE_API_KEY"),
        pinecone_index_host=_require("PINECONE_INDEX_HOST"),
        pinecone_namespace=os.environ.get("PINECONE_NAMESPACE", "dev"),
        pinecone_embed_model=os.environ.get("PINECONE_EMBED_MODEL", "multilingual-e5-large"),
        pinecone_embed_input_type_passage=os.environ.get(
            "PINECONE_EMBED_INPUT_TYPE_PASSAGE", "passage"
        ),
        pinecone_embed_input_type_query=os.environ.get(
            "PINECONE_EMBED_INPUT_TYPE_QUERY", "query"
        ),
        gemini_api_key=_require("GEMINI_API_KEY"),
        # Prefer a widely-available "models/*-latest" alias.
        gemini_model=os.environ.get("GEMINI_MODEL", "models/gemini-flash-latest"),

        mongodb_uri=_require("MONGODB_URI"),
        mongodb_db=os.environ.get("MONGODB_DB", "hr_assistant"),
        mongodb_employees_collection=os.environ.get(
            "MONGODB_EMPLOYEES_COLLECTION", "employees"
        ),
        mongodb_promotion_rules_collection=os.environ.get(
            "MONGODB_PROMOTION_RULES_COLLECTION", "promotion_rules"
        ),
        mongodb_promotion_progress_collection=os.environ.get(
            "MONGODB_PROMOTION_PROGRESS_COLLECTION", "promotion_progress"
        ),
    )

