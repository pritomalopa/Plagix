from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    database_url: str = "postgresql+psycopg://plagix_user:plagix_dev_password@db:5432/plagix_db"
    redis_url: str = "redis://redis:6379/0"
    
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    postgres_user: str = "plagix_user"
    postgres_password: str = "plagix_dev_password"
    postgres_db: str = "plagix_db"
    postgres_host: str = "db"
    postgres_port: int = 5432


settings = Settings()
