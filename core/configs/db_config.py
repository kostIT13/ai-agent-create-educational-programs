from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    LOG_LEVEL: str = "INFO"
    DEBUG: str = "release"

    POSTGRES_URL: str = "postgresql+asyncpg://User:Pass@localhost:5432/postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PASSWORD: str = "Pass"
    POSTGRES_USER: str = "User"
    POSTGRES_PORT: int = 5432


db_settings = Settings()