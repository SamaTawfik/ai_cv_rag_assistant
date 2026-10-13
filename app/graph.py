
from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from app.config import settings
from app.retrieval import retrieve_documents


MIN_RELEVANCE_SCORE = 0.25


class RAGState(TypedDict, total=False):
    question: str
    documents: list[Document]
    answer: str
    sources: list[dict]
    context_sufficient: bool


llm = ChatOllama(
    model=settings.llm_model,
    base_url=settings.ollama_base_url,
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an AI and Computer Vision knowledge assistant.

Answer the question using only the supplied context.
Do not use outside knowledge to fill missing information.
If the context does not contain enough evidence, say:
"I don't know based on the provided documents."

Cite supporting sources in the answer using the exact source
labels provided in the context, including page numbers when available.
Do not invent citations or claim that a source supports something
that it does not actually say.

Context:
{context}
""",
        ),
        ("human", "{question}"),
    ]
)


def retrieve_node(state: RAGState) -> dict:
    documents = retrieve_documents(state["question"])

    sufficient = any(
        document.metadata.get("relevance_score", 0.0)
        >= MIN_RELEVANCE_SCORE
        for document in documents
    )

    return {
        "documents": documents,
        "context_sufficient": sufficient,
    }


def route_after_retrieval(state: RAGState) -> str:
    if state.get("context_sufficient", False):
        return "generate"

    return "abstain"


def build_context(documents: list[Document]) -> str:
    context_parts = []

    for document in documents:
        file_name = document.metadata.get(
            "file_name", "Unknown file"
        )
        page_number = document.metadata.get("page_number")

        if page_number is not None:
            source_label = f"{file_name}, page {page_number}"
        else:
            source_label = file_name

        context_parts.append(
            f"[Source: {source_label}]\n{document.page_content}"
        )

    return "\n\n".join(context_parts)


def build_sources(documents: list[Document]) -> list[dict]:
    sources = []
    seen = set()

    for document in documents:
        file_name = document.metadata.get(
            "file_name", "Unknown file"
        )
        page_number = document.metadata.get("page_number")

        identity = (file_name, page_number)

        if identity in seen:
            continue

        seen.add(identity)

        sources.append(
            {
                "file_name": file_name,
                "page_number": page_number,
                "excerpt": document.page_content[:350],
            }
        )

    return sources


def generate_node(state: RAGState) -> dict:
    documents = state.get("documents", [])
    context = build_context(documents)

    messages = prompt.invoke(
        {
            "context": context,
            "question": state["question"],
        }
    )

    response = llm.invoke(messages)

    return {
        "answer": str(response.content),
        "sources": build_sources(documents),
    }


def abstain_node(state: RAGState) -> dict:
    return {
        "answer": (
            "I don't know based on the provided documents. "
            "The retrieved context did not meet the relevance threshold."
        ),
        "sources": [],
    }


builder = StateGraph(RAGState)

builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)
builder.add_node("abstain", abstain_node)

builder.set_entry_point("retrieve")

builder.add_conditional_edges(
    "retrieve",
    route_after_retrieval,
    {
        "generate": "generate",
        "abstain": "abstain",
    },
)

builder.add_edge("generate", END)
builder.add_edge("abstain", END)

rag_graph = builder.compile()
