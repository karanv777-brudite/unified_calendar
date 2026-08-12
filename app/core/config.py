from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET: str = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    MICROSOFT_CLIENT_ID: str = "YOUR_MICROSOFT_CLIENT_ID"
    MICROSOFT_CLIENT_SECRET: str = "YOUR_MICROSOFT_CLIENT_SECRET"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/auth/microsoft/callback"

    class Config:
        env_file = ".env"

settings = Settings()