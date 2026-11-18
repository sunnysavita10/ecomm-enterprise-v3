from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    app_name: str = "E-Commerce AI Assistant"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    auth_mode: str = "dev"  # dev (local only), jwks (production)
    jwt_issuer: str = ""
    jwt_audience: str = ""
    jwks_url: str = ""
    dev_user_id: str = "local-user"
    database_url: str = "postgresql+asyncpg://ecomm:ecomm@localhost:5432/ecomm"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    llm_provider_order: str = "openai,groq"
    provider_retries: int = Field(default=1, ge=0, le=4)
    circuit_breaker_threshold: int = Field(default=3, ge=1)
    circuit_breaker_cooldown_seconds: int = 60
    hybrid_enabled: bool = True
    langfuse_host: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    ingestion_batch_size: int = Field(default=50, ge=1, le=1000)
    openai_embedding_model: str = "text-embedding-3-small"
    astra_db_api_endpoint: str = ""
    astra_db_application_token: str = ""
    astra_db_keyspace: str = ""
    astra_collection: str = "ecommercedata"
    retrieval_mode: str = "demo"  # demo / astra
    demo_catalog_path: str = "data/products.csv"
    max_input_chars: int = 3000
    max_history_messages: int = 8
    llm_timeout_seconds: float = 25.0
    request_timeout_seconds: float = 40.0
    retrieval_k: int = Field(default=4, ge=1, le=20)
    per_user_rate_limit: int = Field(default=30, ge=1)
    cache_ttl_seconds: int = 90
    otlp_endpoint: str = ""
    log_level: str = "INFO"

    @model_validator(mode="after")
    def check_production(self):
        if self.environment == "production":
            if self.auth_mode != "jwks" or not all([self.jwt_issuer,self.jwt_audience,self.jwks_url]):
                raise ValueError("Production requires configured JWKS authentication")
            if not (self.openai_api_key or self.groq_api_key):
                raise ValueError("Production requires at least one model provider API key")
            if not self.openai_api_key:
                raise ValueError("Production Astra embeddings require OPENAI_API_KEY")
            if self.retrieval_mode != "astra":
                raise ValueError("Production requires AstraDB retrieval mode")
            if not all([self.astra_db_api_endpoint,self.astra_db_application_token]):
                raise ValueError("Production requires AstraDB credentials")
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()
