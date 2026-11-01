"""Google OAuth 2.0 credential management.

Handles the OAuth flow for Gmail + Calendar access.
Requires a ``credentials.json`` downloaded from the Google Cloud Console
placed in the backend root (or the path set by GOOGLE_CREDENTIALS_FILE env var).
"""

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = _BASE_DIR / "credentials.json"
TOKEN_FILE = _BASE_DIR / "token.json"


def get_flow(redirect_uri: str) -> Flow:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {CREDENTIALS_FILE}. "
            "Download it from Google Cloud Console → APIs & Services → Credentials."
        )
    return Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )


def get_credentials() -> Credentials | None:
    if not TOKEN_FILE.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
        except Exception:
            return None
    return creds if (creds and creds.valid) else None


def _save_credentials(creds: Credentials) -> None:
    TOKEN_FILE.write_text(creds.to_json())


def save_credentials_with_email(creds: Credentials, email: str) -> None:
    data = json.loads(creds.to_json())
    data["user_email"] = email
    TOKEN_FILE.write_text(json.dumps(data, indent=2))


def is_connected() -> bool:
    return get_credentials() is not None


def get_user_email() -> str | None:
    if not TOKEN_FILE.exists():
        return None
    try:
        data = json.loads(TOKEN_FILE.read_text())
        return data.get("user_email")
    except Exception:
        return None
