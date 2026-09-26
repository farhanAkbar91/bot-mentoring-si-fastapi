import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    ADMIN_ID: str  # Can be a comma-separated list of Telegram user IDs
    DATABASE_URL: str
    WEBHOOK_HOST: str
    PORT: int = 8080
    API_SYNC_KEY: str = "default_sync_key"
    GOOGLE_CREDS_JSON: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> List[str]:
        return [admin.strip() for admin in self.ADMIN_ID.split(",") if admin.strip()]

    @property
    def clean_webhook_host(self) -> str:
        return self.WEBHOOK_HOST.rstrip("/")

settings = Settings()
