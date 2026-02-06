import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pypdf import PdfReader

from hr_assistant.config import load_settings
from hr_assistant.embeddings import PineconeInferenceEmbeddings
from hr_assistant.pinecone_client import build_pinecone, get_index


def _parse_front_matter(text: str) -> tuple[dict, str]:
    """Parse minimal YAML-ish front matter between --- lines."""
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, text

    meta: dict = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        ln = lines[i].strip()
        if ln and ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
        i += 1
    # Skip closing ---
    body = "\n".join(lines[i + 1 :]) if i < len(lines) else text
    return meta, body


def load_mock_kb_docs(root: Path) -> list[Document]:
    docs: list[Document] = []
    for p in sorted(root.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(text)
        meta["source_path"] = str(p.as_posix())
        docs.append(Document(page_content=body.strip(), metadata=meta))
    return docs


def _infer_pdf_metadata(pdf_path: Path) -> dict:
    """Heuristic metadata for PDFs (since PDFs have no front-matter)."""
    name = pdf_path.stem
    lowered = name.lower()

    # Prefer region derived from folder structure (documents/kb/<REGION>/...).
    region = "GLOBAL"
    for part in pdf_path.parts[::-1]:
        up = str(part).upper()
        if up in {"US", "MY", "GLOBAL"}:
            region = up
            break
    if region == "GLOBAL" and ("malaysia" in lowered or lowered.endswith("-my") or lowered.endswith("_my")):
        region = "MY"

    doc_type = "pdf_document"
    if "handbook" in lowered:
        doc_type = "employee_handbook"

    title = name.replace("_", " ").replace("-", " ").strip()

    return {
        "docType": doc_type,
        "title": title,
        "region": region,
        "employeeType": "all",
        # Set this to a real date if you know it (YYYY-MM-DD)
        "effectiveDate": "unknown",
        "source": "pdf",
        "source_path": str(pdf_path.as_posix()),
    }


def load_pdf_docs(root: Path) -> list[Document]:
    docs: list[Document] = []
    for pdf_path in sorted(root.rglob("*.pdf")):
        meta = _infer_pdf_metadata(pdf_path)
        reader = PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                # Skip empty pages (common for scanned PDFs without OCR).
                continue
            page_meta = dict(meta)
            page_meta["page_number"] = i
            docs.append(Document(page_content=text, metadata=page_meta))
    return docs


def main():
    load_dotenv()
    settings = load_settings()

    pc = build_pinecone(settings)
    index = get_index(pc, settings)
    embeddings = PineconeInferenceEmbeddings(pc, settings)
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)

    kb_root = Path("documents/kb")
    raw_docs = load_mock_kb_docs(kb_root) + load_pdf_docs(kb_root)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = splitter.split_documents(raw_docs)

    # Add stable IDs
    ids = []
    for i, c in enumerate(chunks):
        source_path = str((c.metadata or {}).get("source_path", "unknown"))
        source_name = Path(source_path).name if source_path else "unknown"
        doc_type = str((c.metadata or {}).get("docType", "doc"))
        ids.append(f"{doc_type}::{source_name}::{i}")
    vector_store.add_documents(documents=chunks, ids=ids, namespace=settings.pinecone_namespace)

    print(f"Upserted {len(chunks)} chunks into Pinecone namespace '{settings.pinecone_namespace}'.")


if __name__ == "__main__":
    main()