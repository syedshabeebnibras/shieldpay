from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: str = "development"  # development | staging | production

    # Database
    database_url: str = "postgresql+asyncpg://shieldpay:shieldpay_dev@localhost:5432/shieldpay"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # Auth
    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Email
    sendgrid_api_key: str = ""

    # Monitoring
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("database_url")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        # Railway provides postgresql://, we need postgresql+asyncpg://
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("frontend_url")
    @classmethod
    def fix_frontend_url(cls, v: str) -> str:
        # Ensure URL has scheme
        if v and not v.startswith("http"):
            v = f"https://{v}"
        return v.rstrip("/")

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_secure(cls, v: str) -> str:
        import os

        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and v == "change-me-to-a-random-secret":
            raise ValueError("JWT_SECRET must be changed in production")
        return v


settings = Settings()
