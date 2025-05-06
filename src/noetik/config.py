"""Configuration settings for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pydantic settings class for the application."""

    # Define the settings with default values and types
    # These will be loaded from environment variables or a .env file if not provided
    SOME_API_KEY: str | None = None
    DATA_DIR: str = "/data"
    LOG_LEVEL: str = "INFO"

    class Config:
        """Configuration for Pydantic settings."""

        # Load environment variables from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
