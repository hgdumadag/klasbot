from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Cookie, HTTPException, Response, status
from passlib.context import CryptContext

from klasbot import db
from klasbot.config import HOSTED_DEMO_ENABLED, KLASBOT_DEMO_ADMIN_NAME, SESSION_COOKIE_NAME, SESSION_HOURS

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(pin: str, pin_hash: str) -> bool:
    return pwd_context.verify(pin, pin_hash)


def find_teacher_by_pin(pin: str) -> dict | None:
    for teacher in db.list_teachers(include_hash=True):
        if verify_pin(pin, teacher["pin_hash"]):
            teacher.pop("pin_hash", None)
            return teacher
    return None


def pin_is_in_use(pin: str, exclude_teacher_id: int | None = None) -> bool:
    for teacher in db.list_teachers(include_hash=True):
        if exclude_teacher_id is not None and teacher["id"] == exclude_teacher_id:
            continue
        if verify_pin(pin, teacher["pin_hash"]):
            return True
    return False


def create_login_session(response: Response, teacher_id: int) -> str:
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    db.create_session(token, teacher_id, expires_at.replace(microsecond=0).isoformat(), csrf_token)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_HOURS * 60 * 60,
    )
    return token


def clear_login_session(response: Response, token: str | None) -> None:
    if token:
        db.delete_session(token)
    response.delete_cookie(SESSION_COOKIE_NAME)


def get_current_teacher(
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> dict:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    session = db.get_session(session_token)
    if not session:
        demo_teacher = _hosted_demo_teacher_for_cookie(session_token)
        if demo_teacher:
            return demo_teacher
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    if session["expires_at"] <= db.utc_now():
        db.delete_session(session_token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return {
        "id": session["teacher_id"],
        "name": session["name"],
        "is_admin": bool(session["is_admin"]),
        "csrf_token": session["csrf_token"],
    }


def _hosted_demo_teacher_for_cookie(session_token: str | None) -> dict | None:
    if not HOSTED_DEMO_ENABLED or not session_token:
        return None
    for teacher in db.list_teachers():
        if teacher["name"].casefold() == KLASBOT_DEMO_ADMIN_NAME.casefold():
            return {
                "id": teacher["id"],
                "name": teacher["name"],
                "is_admin": bool(teacher["is_admin"]),
                "csrf_token": "",
            }
    return None


def require_admin(teacher: dict) -> dict:
    if not teacher.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return teacher
