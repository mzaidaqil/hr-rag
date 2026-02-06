from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

from .config import Settings
from .embeddings import PineconeInferenceEmbeddings
from .gemini_llm import GeminiChat
from .pinecone_client import build_pinecone, get_index


@dataclass(frozen=True)
class Citation:
    title: str
    source_path: str
    effective_date: str


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    citations: List[Citation]


def _doc_to_citation(d: Document) -> Citation:
    md = d.metadata or {}
    return Citation(
        title=str(md.get("title") or md.get("doc_title") or md.get("source") or "Document"),
        source_path=str(md.get("source_path") or md.get("source") or "unknown"),
        effective_date=str(md.get("effectiveDate") or md.get("effective_date") or "unknown"),
    )


class RagService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._pc = build_pinecone(settings)
        self._index = get_index(self._pc, settings)
        self._embeddings = PineconeInferenceEmbeddings(self._pc, settings)
        self._vs = PineconeVectorStore(index=self._index, embedding=self._embeddings)
        self._llm = GeminiChat(settings)

    def answer_policy_question(
        self,
        *,
        question: str,
        user_context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> RagAnswer:
        user_context = user_context or {}

        # Metadata filters can be expanded later (region, employeeType, etc.)
        region = user_context.get("region")
        filters: Optional[Dict[str, Any]] = None
        if region:
            filters = {"region": {"$in": [region, "GLOBAL"]}}

        retriever = self._vs.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": top_k,
                "score_threshold": score_threshold,
                "filter": filters,
                "namespace": self._settings.pinecone_namespace,
            },
        )

        docs = retriever.invoke(question)
        citations = [_doc_to_citation(d) for d in docs]

        context_blocks = []
        for i, d in enumerate(docs, start=1):
            md = d.metadata or {}
            title = md.get("title") or md.get("doc_title") or md.get("source_path") or md.get("source") or "Document"
            eff = md.get("effectiveDate") or md.get("effective_date") or "unknown"
            context_blocks.append(f"[{i}] {title} (effective {eff})\n{d.page_content}")

        system = (
            "You are an HR policy assistant.\n"
            "- Answer ONLY using the provided context.\n"
            "- If the context is insufficient, say you don't know and ask a clarifying question.\n"
            "- Keep the answer concise.\n"
            "- Include citations like [1], [2] that reference the context blocks."
        )
        user = f"Question: {question}\n\nContext:\n\n" + ("\n\n".join(context_blocks) or "(no context)")

        answer = self._llm.answer(system=system, user=user, temperature=0.2)
        return RagAnswer(answer=answer, citations=citations)

