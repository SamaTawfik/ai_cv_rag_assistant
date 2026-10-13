
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


def calculate_file_hash(path: Path) -> str:
    """Return a SHA-256 fingerprint of the file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest_pdf(pdf_path: str | Path) -> dict:
    """Load, split, embed, and persist a PDF unless unchanged."""
    path = Path(pdf_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    file_hash = calculate_file_hash(path)
    vector_store = get_vector_store()

    existing = vector_store.get(
        where={"source": str(path)},
        include=["metadatas"],
    )

    existing_ids = existing["ids"]
    existing_metadata = existing.get("metadatas") or []

    # Skip embedding work if this exact file was already indexed.
    if (
        existing_ids
        and existing_metadata
        and all(
            metadata and metadata.get("file_hash") == file_hash
            for metadata in existing_metadata
        )
    ):
        return {
            "file_name": path.name,
            "pages_loaded": 0,
            "chunks_stored": len(existing_ids),
            "status": "skipped_unchanged",
        }

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

    if not chunks or not any(
        chunk.page_content.strip() for chunk in chunks
    ):
        raise ValueError(
            f"No extractable text found in {path.name}. "
            "The PDF may be scanned or image-based."
        )

    for chunk in chunks:
        raw_page = chunk.metadata.get("page")

        chunk.metadata["file_name"] = path.name
        chunk.metadata["source"] = str(path)
        chunk.metadata["file_hash"] = file_hash

        if raw_page is not None:
            chunk.metadata["page_number"] = int(raw_page) + 1

    # Remove stale chunks only after the replacement chunks are prepared.
    vector_store.delete(where={"source": str(path)})

    chunk_ids = []

    for index, chunk in enumerate(chunks):
        identity = (
            f"{path}|{file_hash}|{index}|{chunk.page_content}"
        )
        chunk_ids.append(
            hashlib.sha256(identity.encode("utf-8")).hexdigest()
        )

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


def ingest_directory(
    directory: str | Path | None = None,
) -> list[dict]:
    """Index top-level PDF files in the configured data directory."""
    root = Path(directory) if directory else settings.data_dir

    if not root.is_dir():
        raise FileNotFoundError(
            f"Data directory not found: {root}"
        )

    results = []

    for pdf_path in sorted(root.glob("*.pdf")):
        results.append(ingest_pdf(pdf_path))

    return results
