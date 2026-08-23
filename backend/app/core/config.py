from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Last Mile Delivery Tracker"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")

    # Database
    DATABASE_URL: str = Field(alias="DATABASE_URL")
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security
    SECRET_KEY: str = Field(alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")

    # Email (Resend)
    RESEND_API_KEY: str | None = Field(default=None, alias="RESEND_API_KEY")
    EMAIL_FROM: str = Field(default="noreply@localhost", alias="EMAIL_FROM")

    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: str | None = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str | None = Field(default=None, alias="TWILIO_PHONE_NUMBER")

    # Frontend URL (for links in emails)
    FRONTEND_URL: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
