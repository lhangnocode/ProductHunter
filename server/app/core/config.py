from pathlib import Path
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings import NoDecode
from pydantic import field_validator
from typing import Annotated, Any, List
from urllib.parse import quote_plus


class Settings(BaseSettings):
    IMAGE_TAG: str = "latest"
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "ProductHunter API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    HOST: str = "0.0.0.0"
    PORT: int = 3000

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "producthunter"
    DEV_API_KEY: str = ""
    
    TYPESENSE_HOST: str = "localhost"
    TYPESENSE_PORT: int = 8108
    TYPESENSE_API_KEY: str = ""
    TYPESENSE_PROTOCOL: str = "http"
    DASHSCOPE_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen3.6-flash"
    QWEN_TIMEOUT_SECONDS: int = 30
    ADVISOR_MAX_CONTEXT_PRODUCTS: int = 5
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    MAIL_USERNAME: str = "default@email.com"
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@producthunt.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = ""
    BACKEND_URL: str = ""

    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    ALLOWED_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://product-hunter-xi.vercel.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> List[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                parsed = json.loads(raw_value)
                if not isinstance(parsed, list):
                    raise ValueError("ALLOWED_ORIGINS JSON value must be a list")
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return [
                origin.strip()
                for origin in raw_value.split(",")
                if origin.strip()
            ]
        raise ValueError("ALLOWED_ORIGINS must be a list or comma-separated string")

settings = Settings()
