from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    tavily_api_key: str = ""

    redis_url: str = "redis://localhost:6379"

    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = False
    app_version: str = "0.1.0"

    chroma_persist_dir: str = "./data/chroma"
    documents_dir: str = "./docs/data"
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 4


settings = Settings()
