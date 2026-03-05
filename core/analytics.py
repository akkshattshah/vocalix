"""Fire-and-forget usage tracking — one row per successful activation."""

import sys
import json
import threading
import urllib.request
from auth.session import load_session
from core.config import get_supabase_url, get_supabase_anon_key

_PLATFORM = "mac" if sys.platform == "darwin" else "win"


def log_activation():
    """Log a single usage event to Supabase. Runs in a background thread,
    silently swallows all errors so it never disrupts the app."""
    threading.Thread(target=_send, daemon=True).start()


def _send():
    try:
        session = load_session()
        if not session:
            return

        user = session.get("user", {})
        user_id = user.get("id", "")
        email = user.get("email", "")
        if not user_id:
            return

        anon_key = get_supabase_anon_key()
        url = f"{get_supabase_url()}/rest/v1/usage_events"
        body = json.dumps({
            "user_id": user_id,
            "email": email,
            "platform": _PLATFORM,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Prefer": "return=minimal",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
