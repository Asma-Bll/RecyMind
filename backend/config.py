from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    TOKEN_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5500"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
