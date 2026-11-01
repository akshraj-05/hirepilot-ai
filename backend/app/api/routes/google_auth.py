"""Google OAuth 2.0 endpoints — connect Gmail + Calendar to HirePilot."""

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.services.google_auth import (
    CREDENTIALS_FILE,
    get_flow,
    get_user_email,
    is_connected,
    save_credentials_with_email,
)

router = APIRouter(prefix="/google", tags=["google-auth"])

_pending_auth: dict[str, str] = {}


@router.get("/auth-url")
async def auth_url(request: Request) -> dict[str, str]:
    if not CREDENTIALS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="credentials.json not found. Download from Google Cloud Console.",
        )
    redirect_uri = f"{str(request.base_url).rstrip('/')}/api/google/callback"
    flow = get_flow(redirect_uri)
    url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    if hasattr(flow, "code_verifier") and flow.code_verifier:
        _pending_auth[state] = flow.code_verifier
    return {"auth_url": url}


@router.get("/callback")
async def callback(code: str, state: str = "", request: Request = None) -> RedirectResponse:
    redirect_uri = f"{str(request.base_url).rstrip('/')}/api/google/callback"
    flow = get_flow(redirect_uri)

    code_verifier = _pending_auth.pop(state, None)
    if code_verifier:
        flow.code_verifier = code_verifier

    flow.fetch_token(code=code, code_verifier=code_verifier)
    creds = flow.credentials

    email = ""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"},
            )
            if resp.status_code == 200:
                email = resp.json().get("email", "")
    except Exception:
        pass

    save_credentials_with_email(creds, email)
    return RedirectResponse(url=f"{settings.frontend_url}/meetings?google=connected")


@router.get("/status")
async def status() -> dict:
    return {
        "connected": is_connected(),
        "email": get_user_email() if is_connected() else None,
    }
