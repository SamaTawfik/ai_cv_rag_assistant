
from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_empty_question_is_rejected():
    response = client.post(
        "/ask",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_ask_returns_answer_and_sources(monkeypatch):
    def fake_answer_question(question: str) -> dict:
        return {
            "question": question,
            "answer": "A CNN learns spatial features.",
            "sources": [
                {
                    "file_name": "deep_learning.pdf",
                    "page_number": 3,
                    "excerpt": "CNNs learn spatial features.",
                }
            ],
        }

    monkeypatch.setattr(
        main,
        "answer_question",
        fake_answer_question,
    )

    response = client.post(
        "/ask",
        json={"question": "What does a CNN learn?"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["answer"] == "A CNN learns spatial features."
    assert body["sources"][0]["file_name"] == "deep_learning.pdf"
    assert body["sources"][0]["page_number"] == 3


def test_upload_rejects_non_pdf():
    response = client.post(
        "/upload",
        files={
            "file": (
                "notes.txt",
                b"Not a PDF",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_upload_calls_ingestion(monkeypatch, tmp_path):
    monkeypatch.setattr(
        main.settings,
        "upload_dir",
        tmp_path,
    )

    def fake_ingest_pdf(path):
        assert path.exists()
        assert path.name == "sample.pdf"

        return {
            "file_name": "sample.pdf",
            "pages_loaded": 2,
            "chunks_stored": 4,
            "status": "success",
        }

    monkeypatch.setattr(main, "ingest_pdf", fake_ingest_pdf)

    response = client.post(
        "/upload",
        files={
            "file": (
                "sample.pdf",
                b"%PDF-1.4 test content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["chunks_stored"] == 4
