"""
Configuration settings for the Prompt Manager backend.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Prompt Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database settings
    DATABASE_URL: str = "sqlite:///./prompt_manager.db"

    # Multi-tenancy (optional future configs)
    DEFAULT_TENANT: str = "public"

    class Config:
        env_file = ".env"  # Load environment variables from .env file
        from_attributes = True


# Singleton instance
settings = Settings()
