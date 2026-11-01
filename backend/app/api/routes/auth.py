import asyncio
import uuid
from functools import partial

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.crud import users as users_crud
from app.utils.security import hash_password, verify_password

router = APIRouter(tags=["auth"])

_DEFAULT_ORG_ID = uuid.UUID("2a72a509-16e0-44a8-a7fd-1e07b9e2e5dc")


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    role: str | None
    organization_id: str


@router.post("/auth/login", response_model=UserResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await users_crud.get_by_email(db, body.email)
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    loop = asyncio.get_event_loop()
    password_ok = await loop.run_in_executor(None, partial(verify_password, body.password, user.password_hash))
    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        organization_id=str(user.org_id),
    )


@router.post("/auth/signup", response_model=UserResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    existing = await users_crud.get_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    loop = asyncio.get_event_loop()
    password_hash = await loop.run_in_executor(None, partial(hash_password, body.password))

    user = await users_crud.create(
        db,
        org_id=_DEFAULT_ORG_ID,
        email=body.email,
        password_hash=password_hash,
        name=body.name,
        role="admin",
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        organization_id=str(user.org_id),
    )
