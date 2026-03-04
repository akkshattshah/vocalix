import os
import sys
import threading
import json
from urllib.parse import urlencode

from flask import Flask, redirect, request, render_template, jsonify
from auth.session import save_session, is_authenticated
from core.config import get_supabase_url

REDIRECT_URI = "http://localhost:5111/auth/callback"


def _resource_path(relative: str) -> str:
    """Return the absolute path to a bundled resource, works both in dev and
    when frozen with PyInstaller (where files live under sys._MEIPASS)."""
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, "auth", relative)
    return os.path.join(os.path.dirname(__file__), relative)


app = Flask(
    __name__,
    template_folder=_resource_path("templates"),
)
app.secret_key = os.urandom(24)

auth_complete_event = threading.Event()


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/auth/google")
def auth_google():
    supabase_url = get_supabase_url()
    params = urlencode({
        "provider": "google",
        "redirect_to": REDIRECT_URI,
    })
    url = f"{supabase_url}/auth/v1/authorize?{params}"
    return redirect(url)


@app.route("/auth/callback")
def auth_callback():
    return render_template("login.html")


@app.route("/auth/save-token", methods=["POST"])
def save_token():
    """Called by JS on the callback page after extracting the hash fragment."""
    data = request.get_json(silent=True) or {}
    access_token = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")
    user = data.get("user", {})

    if not access_token:
        return jsonify({"ok": False, "error": "No access token"}), 400

    save_session(access_token, refresh_token, user)
    auth_complete_event.set()
    return jsonify({"ok": True})


@app.route("/auth/status")
def auth_status():
    return jsonify({"authenticated": is_authenticated()})


def run_server(event: threading.Event):
    """Start Flask; *event* is shared so main.py can wait on auth_complete."""
    global auth_complete_event
    auth_complete_event = event
    app.run(host="127.0.0.1", port=5111, use_reloader=False, threaded=True)
