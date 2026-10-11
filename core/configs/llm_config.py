from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LLM_",
        extra="ignore",
    )
    API_KEY: str = ""
    BASE_URL: str = "https://api.openai.com/v1"
    MODEL: str = "gpt-4o-mini"
    FALLBACK_MODEL: str = ""
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 4096
    TIMEOUT_SECONDS: float = 60.0
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_SECONDS: float = 2.0


llm_settings = LLMSettings()
