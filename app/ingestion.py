
import hashlib
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def get_embeddings() -> OllamaEmbeddings:
    """Create the embedding model used by the vector store."""
    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )


def get_vector_store() -> Chroma:
    """Open the persistent Chroma database."""
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name="ai_cv_knowledge",
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def ingest_pdf(pdf_path: str | Path) -> dict:
    """Load a PDF, split its text, and save its chunks in Chroma."""
    path = Path(pdf_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    loader = PyPDFLoader(str(path))
    documents = loader.load()

    if not documents:
        raise ValueError(f"No pages were extracted from {path.name}.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    if not chunks or not any(chunk.page_content.strip() for chunk in chunks):
        raise ValueError(
            f"No extractable text found in {path.name}. "
            "The PDF may be scanned or image-based."
        )

    # Preserve source information and convert page numbers to 1-based numbering.
    for chunk in chunks:
        raw_page = chunk.metadata.get("page")
        chunk.metadata["file_name"] = path.name
        chunk.metadata["source"] = str(path)
        if raw_page is not None:
            chunk.metadata["page_number"] = int(raw_page) + 1

    vector_store = get_vector_store()

    # Re-index this exact file instead of leaving stale chunks behind.
    vector_store.delete(where={"source": str(path)})

    # Stable IDs prevent duplicate chunks when the same file is re-indexed.
    chunk_ids = []
    for chunk in chunks:
        identity = (
            f"{path}|"
            f"{chunk.metadata.get('page_number', '')}|"
            f"{chunk.page_content}"
        )
        chunk_ids.append(hashlib.sha256(identity.encode("utf-8")).hexdigest())

    vector_store.add_documents(
        documents=chunks,
        ids=chunk_ids,
    )

    return {
        "file_name": path.name,
        "pages_loaded": len(documents),
        "chunks_stored": len(chunks),
        "status": "success",
    }


def ingest_directory(directory: str | Path | None = None) -> list[dict]:
    """Index all PDFs in a directory, skipping the uploads subdirectory."""
    root = Path(directory) if directory else settings.data_dir
    upload_root = settings.upload_dir.resolve()

    results = []

    for pdf_path in sorted(root.glob("*.pdf")):
        if pdf_path.resolve().is_relative_to(upload_root):
            continue

        results.append(ingest_pdf(pdf_path))

    return results
