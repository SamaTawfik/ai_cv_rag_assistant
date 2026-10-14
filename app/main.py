import hashlib

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.ingestion import ingest_pdf
from app.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    UploadResponse,
)
from app.services import answer_question
from app.ingestion import get_embeddings
from app.schemas import EmbeddingRequest, EmbeddingResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI and Computer Vision RAG Assistant",
    description=(
        "A document-grounded assistant for AI and Computer Vision PDFs."
    ),
    version="1.0.0",
)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    try:
        return answer_question(request.question)
    except Exception:
        # Log the actual error on the server in a production version.
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the question.",
        )


@app.post("/upload", response_model=UploadResponse)
def upload_pdf(file: UploadFile = File(...)):
    original_name = file.filename or ""
    safe_name = Path(
        original_name.replace("\\", "/")
    ).name

    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="A valid filename is required.",
        )

    if Path(safe_name).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    content = file.file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="The uploaded file exceeds the 20 MB limit.",
        )

    if b"%PDF-" not in content[:1024]:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not appear to be a PDF.",
        )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    print("UPLOAD DIR:", settings.upload_dir.resolve())
    print("FILES:", list(settings.upload_dir.rglob("*.pdf")))
    print("NEW HASH:", hashlib.sha256(content).hexdigest())

    # Detect duplicate files by content, not filename.
    file_hash = hashlib.sha256(content).hexdigest()

    for existing_file in settings.upload_dir.rglob("*.pdf"):
        try:
            existing_hash = hashlib.sha256(
                existing_file.read_bytes()
            ).hexdigest()

            if existing_hash == file_hash:
                raise HTTPException(
                    status_code=409,
                    detail="This PDF has already been uploaded.",
                )
        except OSError:
            continue

    destination = settings.upload_dir / safe_name

    # Avoid overwriting a different PDF with the same filename.
    if destination.exists():
        destination = (
            settings.upload_dir
            / f"{Path(safe_name).stem}_{file_hash[:12]}.pdf"
        )

    destination.write_bytes(content)

    try:
        result = ingest_pdf(destination)
    except (ValueError, FileNotFoundError) as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return result

@app.post("/embed", response_model=EmbeddingResponse)
def create_embedding(request: EmbeddingRequest):
    try:
        vector = get_embeddings().embed_query(request.text)
        return {
            "dimensions": len(vector),
            "embedding": vector,
        }
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the embedding.",
        )
