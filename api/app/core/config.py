"""
app/core/config.py
──────────────────
Central configuration — edit this file to change app-wide settings.
"""
from pathlib import Path

class Settings:
    APP_NAME: str = "LogAnalyzer"
    APP_VERSION: str = "0.1.0"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    ANALYSES_DIR: Path = BASE_DIR / "analyses"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/loganalyzer.db"

    # Security
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    PASSWORD_MIN_LENGTH: int = 6

    # AI — set ANTHROPIC_API_KEY in env or replace the empty string
    ANTHROPIC_API_KEY: str = ""          # os.getenv("ANTHROPIC_API_KEY", "")
    AI_MODEL: str = "claude-sonnet-4-20250514"
    AI_MAX_LOG_CHARS: int = 40_000       # truncate huge log files before sending

    # Upload limits
    MAX_UPLOAD_MB: int = 50
    ALLOWED_EXTENSIONS: set = {".log", ".txt", ".csv", ".json", ".gz"}

settings = Settings()

# Ensure storage dirs exist
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.ANALYSES_DIR.mkdir(parents=True, exist_ok=True)