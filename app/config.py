from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b"
    embedding_model: str = "nomic-embed-text"

    data_dir: Path = PROJECT_ROOT / "data"
    upload_dir: Path = PROJECT_ROOT / "data" / "uploads"
    chroma_dir: Path = PROJECT_ROOT / "chroma_db"

    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_k: int = 4


settings = Settings()
