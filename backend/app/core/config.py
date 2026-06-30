from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Database
    database_url: str
    redis_url: str

    # Auth
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Storage
    storage_path: str = "./storage"

    # Ollama / AI
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"


settings = Settings()