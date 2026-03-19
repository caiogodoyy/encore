from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Spotify OAuth
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:3000/api/auth/spotify/callback"

    # Google/YouTube OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:3000/api/auth/youtube/callback"

    # Redis
    redis_url: str = "redis://127.0.0.1:6379/0"

    # Frontend
    frontend_url: str = "http://127.0.0.1:3000"

    # Session
    session_ttl_seconds: int = 3600

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


settings = Settings()
