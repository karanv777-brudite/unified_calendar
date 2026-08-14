from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # It automatically searches for .env and fetches the sensitive data from the file., And if not found then replaces them with the default placeholder.
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET: str = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    MICROSOFT_CLIENT_ID: str = "YOUR_MICROSOFT_CLIENT_ID"
    MICROSOFT_CLIENT_SECRET: str = "YOUR_MICROSOFT_CLIENT_SECRET"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/auth/microsoft/callback"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/calendar_db"

    ENCRYPTION_KEY: str = "Random_Key=1234"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
        
settings = Settings()