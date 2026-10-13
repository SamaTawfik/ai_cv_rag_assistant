
# AI & Computer Vision RAG Assistant

A local Retrieval-Augmented Generation (RAG) application that answers
questions using a collection of AI and Computer Vision PDF documents.

## Architecture

- Python
- LangChain for document loading, splitting, embeddings, and retrieval
- Chroma for persistent vector storage
- Ollama with `nomic-embed-text` for embeddings
- Ollama with `qwen2.5:3b` for answer generation
- LangGraph for workflow orchestration
- FastAPI and Pydantic for the API

## Workflow

1. Load PDF documents with PyPDFLoader.
2. Split documents into chunks.
3. Embed chunks and store them in persistent Chroma storage.
4. Retrieve the top-k relevant chunks for a question.
5. Check whether the retrieved relevance scores meet the configured threshold.
6. Generate an answer grounded in the retrieved context, or abstain.
7. Return the answer and source information.

## Chunking Configuration

- Chunk size: 800 characters
- Chunk overlap: 120 characters
- Retrieval top-k: 4
- Initial relevance threshold: 0.25

These are initial settings and should be evaluated on the selected documents.

## Requirements

- Python 3.10 or newer
- Ollama installed and running
- Required Ollama models:
  - `qwen2.5:3b`
  - `nomic-embed-text`

## Setup

Create and activate a Python virtual environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local `.env` file using `.env.example` and adjust settings if needed.

## Add Documents

Place PDF documents in the `data/` directory.

Index them using:

```bash
python -m app.index_documents
```

Unchanged files are skipped; changed files are re-indexed.

## Run the API

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

## API Endpoints

### GET /health

Checks whether the API is running.

### POST /ask

Example JSON body:

```json
{
  "question": "What is object detection?"
}
```

The response contains an answer and a list of sources.

### POST /upload

Upload a PDF using multipart form data with the field name `file`.

The maximum upload size is 20 MB.

## Run Tests

```bash
python -m pytest -q
```

## Evaluation

Evaluate the application using questions that cover:

- Direct factual questions
- Questions requiring multiple document passages
- Questions outside the document collection
- Citation and page-number accuracy
- Unsupported-answer abstention
- Invalid API requests and uploads

Record actual outcomes before drawing conclusions about performance.

## Limitations

- Scanned PDFs may require OCR, which is not implemented.
- Relevance scores are not proof of factual correctness.
- Local model answers can still contain errors.
- The current upload and error-handling implementation is a prototype
  and should be hardened before public deployment.
