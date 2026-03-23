from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/meetwise"
    mistral_api_key: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    upload_dir: str = "/data/uploads"
    brave_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
