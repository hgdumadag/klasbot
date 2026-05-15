from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CURRICULUM_UPLOAD_DIR = DATA_DIR / "curriculum_uploads"
GRADING_UPLOAD_DIR = DATA_DIR / "grading_uploads"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
OLLAMA_GRADING_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_GRADING_TIMEOUT_SECONDS", "60"))
KLASBOT_AI_PROVIDER = os.getenv("KLASBOT_AI_PROVIDER", "ollama").strip().lower() or "ollama"
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "").strip()
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "global").strip() or "global"
VERTEX_GEMMA_MODEL = os.getenv("VERTEX_GEMMA_MODEL", "gemma-4-26b-a4b-it-maas").strip()
SESSION_COOKIE_NAME = os.getenv("KLASBOT_SESSION_COOKIE", "klasbot_session")
SESSION_HOURS = int(os.getenv("KLASBOT_SESSION_HOURS", "12"))
SCHOOL_NAME = os.getenv("KLASBOT_SCHOOL_NAME", "Klasbot School")
PRINT_COMMAND = os.getenv("KLASBOT_PRINT_COMMAND", "lp")
SHARE_TOKEN_MINUTES = int(os.getenv("KLASBOT_SHARE_TOKEN_MINUTES", "15"))
PUBLIC_BASE_URL = os.getenv("KLASBOT_PUBLIC_BASE_URL", "").rstrip("/")
KLASBOT_DEPLOYMENT_MODE = os.getenv("KLASBOT_DEPLOYMENT_MODE", "offline").strip().lower()
HOSTED_DEMO_ENABLED = KLASBOT_DEPLOYMENT_MODE == "hosted_demo"
KLASBOT_DEMO_ADMIN_NAME = os.getenv("KLASBOT_DEMO_ADMIN_NAME", "Judge Demo").strip() or "Judge Demo"
KLASBOT_DEMO_ADMIN_PIN = os.getenv("KLASBOT_DEMO_ADMIN_PIN", "1111").strip() or "1111"
KLASBOT_PREFILL_DEMO_PIN = os.getenv("KLASBOT_PREFILL_DEMO_PIN", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
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
    if HOSTED_DEMO_ENABLED:
        return Path("/tmp/klasbot-demo.db")
    return DATA_DIR / "klasbot.db"


def get_share_dir() -> Path:
    configured = os.getenv("KLASBOT_SHARE_DIR")
    if configured:
        return Path(configured).expanduser()
    if HOSTED_DEMO_ENABLED:
        return Path("/tmp/klasbot-shared-exports")
    return DATA_DIR / "shared_exports"


def get_grading_upload_dir() -> Path:
    configured = os.getenv("KLASBOT_GRADING_UPLOAD_DIR")
    if configured:
        return Path(configured).expanduser()
    if HOSTED_DEMO_ENABLED:
        return Path("/tmp/klasbot-grading-uploads")
    return GRADING_UPLOAD_DIR
