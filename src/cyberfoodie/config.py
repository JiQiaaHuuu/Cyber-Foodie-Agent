from __future__ import annotations

import os
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent

STATIC_DIR = PACKAGE_ROOT / "static"
DATA_DIR = PACKAGE_ROOT / "data"

DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
PORT = int(os.getenv("PORT", "8000"))


def load_api_key() -> str:
    env_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if env_key:
        return env_key

    key_file = WORKSPACE_ROOT / "api key.txt"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    return ""
