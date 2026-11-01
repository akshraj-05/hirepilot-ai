"""Health / readiness endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, object]:
    return {"ok": True, "service": "hirepilot-backend"}
