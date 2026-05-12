from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CURRICULUM_UPLOAD_DIR = DATA_DIR / "curriculum_uploads"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
SESSION_COOKIE_NAME = os.getenv("KLASBOT_SESSION_COOKIE", "klasbot_session")
SESSION_HOURS = int(os.getenv("KLASBOT_SESSION_HOURS", "12"))
SCHOOL_NAME = os.getenv("KLASBOT_SCHOOL_NAME", "Klasbot School")
PRINT_COMMAND = os.getenv("KLASBOT_PRINT_COMMAND", "lp")
SHARE_TOKEN_MINUTES = int(os.getenv("KLASBOT_SHARE_TOKEN_MINUTES", "15"))
PUBLIC_BASE_URL = os.getenv("KLASBOT_PUBLIC_BASE_URL", "").rstrip("/")
PROMPT_PREVIEW_ENABLED = os.getenv("KLASBOT_PROMPT_PREVIEW", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def get_db_path() -> Path:
    configured = os.getenv("KLASBOT_DB_PATH")
    if configured:
        return Path(configured).expanduser()
    return DATA_DIR / "klasbot.db"


def get_share_dir() -> Path:
    configured = os.getenv("KLASBOT_SHARE_DIR")
    if configured:
        return Path(configured).expanduser()
    return DATA_DIR / "shared_exports"
