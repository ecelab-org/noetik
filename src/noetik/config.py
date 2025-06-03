"""Configuration settings for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pydantic settings class for the application."""

    # Define the settings with default values and types
    # These will be loaded from environment variables or a .env file if not provided
    API_PORT: int = 8000
    WEBUI_PORT: int = 8080
    DEBUG: bool = True
    DATA_DIR: str = "/data"
    LOG_LEVEL: str = "info"  # Options: debug, info, warning, error, critical

    # LLM Configuration
    PLANNER: str = "anthropic"  # Options: tgi, openai, anthropic
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    LOCAL_MODEL_PATH: str | None = None

    # Memory Configuration
    VECTOR_DB: str = "chroma"  # Options: chroma, weaviate, json
    VECTOR_DB_HOST: str = "chroma"  # Service name in docker-compose
    VECTOR_DB_PORT: int = 8000
    PERSISTENCE_PATH: str = "./data"

    # Other API Keys
    SERPER_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    class Config:
        """Configuration for Pydantic settings."""

        # Load environment variables from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
