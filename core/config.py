import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".vocalix"
CONFIG_FILE = CONFIG_DIR / "config.json"

_SUPABASE_URL_DEFAULT = "https://jwvclhvauhahftkuogdh.supabase.co"
_SUPABASE_ANON_KEY_DEFAULT = "sb_publishable_iABVO6g3FH22coQIkpN1UQ_Q672I3q2"


def _load() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_api_key() -> str | None:
    """Resolve API key: embedded build key > env var > user config."""
    try:
        from core._embedded_key import OPENAI_API_KEY
        if OPENAI_API_KEY:
            return OPENAI_API_KEY
    except ImportError:
        pass
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    return _load().get("openai_api_key")


def set_api_key(key: str):
    data = _load()
    data["openai_api_key"] = key
    _save(data)


def get_hotkey() -> str:
    return _load().get("hotkey", "ctrl")


def set_hotkey(key: str):
    data = _load()
    data["hotkey"] = key
    _save(data)


def get_onboarded() -> bool:
    return _load().get("onboarded", False)


def set_onboarded(value: bool = True):
    data = _load()
    data["onboarded"] = value
    _save(data)


def get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", _SUPABASE_URL_DEFAULT)


def get_supabase_anon_key() -> str:
    return os.getenv("SUPABASE_ANON_KEY", _SUPABASE_ANON_KEY_DEFAULT)
