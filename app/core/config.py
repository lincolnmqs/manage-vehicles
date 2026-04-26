from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    test_database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    exchange_api_primary: str = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
    exchange_api_fallback: str = "https://api.frankfurter.app/latest?from=USD&to=BRL"
    exchange_cache_ttl: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
