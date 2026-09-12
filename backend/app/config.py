from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./electronics_store.db"
    admin_api_key: str = "change-this-admin-key"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
