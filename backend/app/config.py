from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    APP_ENV: str = "development"
    APP_NAME: str = "FinTrack API"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    PORT: int = 8000
    DATABASE_URL: str

    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Authentication & JWT Configuration
    JWT_SECRET: str = "fintrack_jwt_super_secret_dev_key_change_in_production_min32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES: int = 10

    # Google OAuth 2.0 / OpenID Connect
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Email Service Configuration (Google SMTP locally, Resend in production)
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@fintrack.app"
    EMAILS_FROM_NAME: str = "FinTrack"
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate Limiting
    AUTH_RATE_LIMIT: str = "10/minute"
    LOGIN_RATE_LIMIT: str = "5/minute"
    PASSWORD_RESET_RATE_LIMIT: str = "10/15minutes"
    EMAIL_VERIFY_RATE_LIMIT: str = "5/10minutes"
    AI_RATE_LIMIT: str = "5/10minutes"

    # AI Recommendation Engine (Google Gemini / Extensible)
    GEMINI_API_KEY: str = ""
    AI_PROVIDER: str = "gemini"  # Supported: "gemini" (future: "openai", "claude")
    AI_MODEL_NAME: str = "gemini-1.5-flash"
    AI_INSIGHTS_CACHE_MINUTES: int = 360

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()
