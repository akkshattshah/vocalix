import json
import os
from pathlib import Path

SESSION_DIR = Path.home() / ".vocalix"
SESSION_FILE = SESSION_DIR / "session.json"


def save_session(access_token: str, refresh_token: str, user: dict):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user,
    }
    SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        if data.get("access_token"):
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def clear_session():
    try:
        SESSION_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def is_authenticated() -> bool:
    return load_session() is not None
