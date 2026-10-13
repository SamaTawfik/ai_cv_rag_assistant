
from app.graph import rag_graph


def answer_question(question: str) -> dict:
    """Run the RAG graph and return a normalized answer."""
    result = rag_graph.invoke({"question": question})

    return {
        "question": question,
        "answer": result["answer"],
        "sources": result.get("sources", []),
    }
