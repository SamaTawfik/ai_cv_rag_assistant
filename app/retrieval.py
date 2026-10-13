
from langchain_core.documents import Document

from app.config import settings
from app.ingestion import get_vector_store


def retrieve_documents(question: str) -> list[Document]:
    """Retrieve the most relevant document chunks for a question."""
    vector_store = get_vector_store()

    # Avoid searching an empty collection.
    existing = vector_store.get(limit=1)

    if not existing["ids"]:
        return []

    results = vector_store.similarity_search_with_relevance_scores(
        question,
        k=settings.retrieval_k,
    )

    documents = []

    for document, score in results:
        document.metadata["relevance_score"] = float(score)
        documents.append(document)

    return documents
