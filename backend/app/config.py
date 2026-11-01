"""Application settings loaded from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 4000
    cors_origins: str = "http://localhost:3000,http://10.50.14.252:3000"
    database_url: str = "postgresql+asyncpg://hirepilot_user:hirepilot_pass@localhost:5432/hirepilot_db"

    # Supabase configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # LLM provider selection: "openai" | "gemini" | "cerebras"
    llm_provider: str = "openai"

    openai_api_key: str | None = None
    openai_chat_model: str = "llama3.1-8b"
    openai_base_url: str = "https://api.cerebras.ai/v1"

    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-2.0-flash"

    cerebras_api_key: str | None = None
    cerebras_chat_model: str = "llama3.1-8b"

    # Embedding provider: "openai" | "gemini" | "local"
    # Independent of llm_provider — e.g. Cerebras for chat, OpenAI for embeddings.
    embedding_provider: str = "local"

    openai_embedding_model: str = "text-embedding-3-small"
    gemini_embedding_model: str = "models/text-embedding-004"
    # "local" uses chromadb's bundled all-MiniLM-L6-v2 — no API key needed.

    # ChromaDB HTTP server (Docker service)
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # Frontend URL (for building scheduling links in emails)
    frontend_url: str = "http://localhost:3000"

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
