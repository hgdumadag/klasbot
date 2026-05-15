from __future__ import annotations

import asyncio
import html
import re
import secrets
import socket
import time
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, Literal, Optional
from urllib.parse import quote, urlsplit

import httpx
import qrcode
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from qrcode.image.svg import SvgPathImage
from pydantic import BaseModel, Field

from klasbot import curriculum
from klasbot import db
from klasbot.auth import (
    clear_login_session,
    create_login_session,
    find_teacher_by_pin,
    get_current_teacher,
    hash_pin,
    pin_is_in_use,
    require_admin,
)
from klasbot.config import (
    OLLAMA_BASE_URL,
    OLLAMA_GRADING_TIMEOUT_SECONDS,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    PROMPT_PREVIEW_ENABLED,
    PUBLIC_BASE_URL,
    SESSION_COOKIE_NAME,
    SHARE_TOKEN_MINUTES,
    get_share_dir,
)
from klasbot.grading import detection as grading_detection
from klasbot.grading import extraction as grading_extraction
from klasbot.grading import images as grading_images
from klasbot.grading import reports as grading_reports
from klasbot.grading import scoring as grading_scoring
from klasbot.ollama_client import OllamaClient, OllamaStreamError
from klasbot.print_utils import export_pdf, print_html, render_print_html
from klasbot.prompts import build_prompt
from klasbot.prompts.teaching_aid import (
    teaching_aid_label,
    valid_teaching_aid_types,
    build_teaching_aid_prompt,
)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    db.prune_expired_sessions()
    db.prune_mobile_pairing_tokens()
    yield


app = FastAPI(title="Klasbot", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ollama_client = OllamaClient(OLLAMA_BASE_URL, OLLAMA_TIMEOUT_SECONDS)


class LoginRequest(BaseModel):
    pin: str = Field(min_length=1, max_length=32)


class TeacherCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    pin: str = Field(min_length=1, max_length=32)
    is_admin: bool = False


class PinResetRequest(BaseModel):
    pin: str = Field(min_length=1, max_length=32)


class OutputSaveRequest(BaseModel):
    kind: Literal["lesson_plan", "assessment"]
    format: str = Field(default="", max_length=32)
    subject: str = Field(default="", max_length=120)
    topic: str = Field(default="", max_length=200)
    quarter: Optional[int] = None
    week_number: Optional[int] = Field(default=None, ge=1, le=10)
    grade_levels: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    inputs: dict[str, Any]
    content_md: str = Field(min_length=1)


class OutputUpdateRequest(BaseModel):
    content_md: str = Field(min_length=1)
    expected_updated_at: Optional[str] = None
    force: bool = False


class TeachingAidGenerateRequest(BaseModel):
    aid_type: str = Field(min_length=1, max_length=40)
    source_section: str = Field(default="", max_length=6000)
    custom_request: str = Field(default="", max_length=1000)


class TeachingAidSaveRequest(TeachingAidGenerateRequest):
    title: str = Field(default="", max_length=160)
    content_md: str = Field(min_length=1)


class TeachingAidUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content_md: str = Field(min_length=1)


class PrintRequest(BaseModel):
    output_id: Optional[int] = None
    teaching_aid_id: Optional[int] = None
    content_md: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShareCreateRequest(BaseModel):
    expires_minutes: int = Field(default=SHARE_TOKEN_MINUTES, ge=1, le=240)


class PromptPreviewRequest(BaseModel):
    kind: Literal["lesson_plan", "assessment"]
    format: str = Field(default="DLP", max_length=32)
    subject: str = Field(default="", max_length=120)
    topic: str = Field(default="", max_length=200)
    grade_level: str = Field(default="", max_length=32)
    quarter: Optional[int] = None
    week_number: Optional[int] = Field(default=None, ge=1, le=10)
    grade_levels: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class LessonPlanFormatUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    requirements: str = Field(min_length=1, max_length=20000)


class PacingWeekUpdate(BaseModel):
    week_number: int = Field(ge=1, le=10)
    focus: str = Field(min_length=1, max_length=500)
    notes: str = Field(default="", max_length=1000)
    competency_ids: list[int] = Field(default_factory=list)


class PacingUpdateRequest(BaseModel):
    weeks: list[PacingWeekUpdate] = Field(min_length=10, max_length=10)


class GradingBatchCreateRequest(BaseModel):
    subject: str = Field(default="", max_length=120)
    grade_level: str = Field(default="", max_length=32)
    topic: str = Field(default="", max_length=200)
    quarter: Optional[int] = Field(default=None, ge=1, le=4)
    week_number: Optional[int] = Field(default=None, ge=1, le=10)
    week_topic: str = Field(default="", max_length=500)
    total_points: float = Field(gt=0, le=1000)
    grading_style: Literal["exact", "partial", "rubric", "review_only"] = "exact"
    questions: str = Field(default="", max_length=20000)
    answer_key: Any = Field(default_factory=dict)
    rubric: Any = Field(default_factory=dict)


class GradingSubmissionUpdateRequest(BaseModel):
    student_name: str = Field(default="", max_length=160)
    student_identifier: str = Field(default="", max_length=80)
    extracted_answers: dict[str, Any] = Field(default_factory=dict)
    grading_result: dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None
    max_score: Optional[float] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    teacher_reviewed: bool = False


class ClassRecordRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    grade_level: str = Field(min_length=1, max_length=32)
    section: str = Field(default="", max_length=80)
    subject: str = Field(min_length=1, max_length=120)
    school_year: str = Field(default="", max_length=32)


class StudentCreateRequest(BaseModel):
    student_id: Optional[int] = None
    learner_reference_number: str = Field(default="", max_length=80)
    first_name: str = Field(default="", max_length=80)
    middle_name: str = Field(default="", max_length=80)
    last_name: str = Field(default="", max_length=80)
    display_name: str = Field(default="", max_length=180)
    status: Literal["active", "inactive", "transferred"] = "active"


class StudentUpdateRequest(BaseModel):
    learner_reference_number: str = Field(default="", max_length=80)
    first_name: str = Field(min_length=1, max_length=80)
    middle_name: str = Field(default="", max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    display_name: str = Field(default="", max_length=180)
    status: Literal["active", "inactive", "transferred"] = "active"


class AssessmentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    assessment_type: Literal["exam", "quiz", "project", "performance_task", "assignment", "other"]
    assessment_date: str = Field(min_length=1, max_length=32)
    max_score: float = Field(gt=0, le=10000)
    weight: Optional[float] = Field(default=None, ge=0, le=100)
    notes: str = Field(default="", max_length=1000)


class ScoreEntryRequest(BaseModel):
    student_id: int
    score: Optional[float] = Field(default=None, ge=0)
    is_absent: bool = False
    notes: str = Field(default="", max_length=500)


class ScoreGridRequest(BaseModel):
    scores: list[ScoreEntryRequest] = Field(default_factory=list)


LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}
REMOTE_PUBLIC_PREFIXES = ("/share/", "/mobile/pair/")
REMOTE_STATIC_PREFIXES = ("/static/mobile",)
REMOTE_SESSION_PATHS = {"/mobile", "/api/me", "/api/ollama/status", "/api/auth/logout"}
REMOTE_SESSION_PREFIXES = (
    "/api/generate/stream",
    "/api/curriculum/",
    "/api/library",
    "/api/grading/",
    "/api/class-records/",
    "/api/print/preview",
)
REMOTE_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
MOBILE_PAIRING_MINUTES = 5
GENERATION_RATE_LIMIT_SECONDS = 60
GENERATION_RATE_LIMIT_COUNT = 6
PHILIPPINE_TZ = timezone(timedelta(hours=8), name="PHT")
generation_attempts: dict[int, list[float]] = {}


def _is_local_request(request: Request) -> bool:
    client_host = request.client.host if request.client else ""
    return client_host in LOCAL_CLIENT_HOSTS


def _remote_path_allowed_with_session(path: str) -> bool:
    return path in REMOTE_SESSION_PATHS or any(path.startswith(prefix) for prefix in REMOTE_SESSION_PREFIXES)


def _session_from_request(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    session = db.get_session(token)
    if not session or session["expires_at"] <= db.utc_now():
        if session:
            db.delete_session(token)
        return None
    return session


def _csrf_valid(request: Request, session: dict[str, Any]) -> bool:
    expected = session.get("csrf_token") or ""
    supplied = request.headers.get("X-Klasbot-CSRF", "")
    return bool(expected) and secrets.compare_digest(expected, supplied)


def _check_generation_rate_limit(teacher_id: int) -> None:
    now = time.monotonic()
    window_start = now - GENERATION_RATE_LIMIT_SECONDS
    attempts = [stamp for stamp in generation_attempts.get(teacher_id, []) if stamp >= window_start]
    if len(attempts) >= GENERATION_RATE_LIMIT_COUNT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many generation requests. Try again in a minute.",
        )
    attempts.append(now)
    generation_attempts[teacher_id] = attempts


def _format_philippine_time(value: datetime) -> str:
    local_value = value.astimezone(PHILIPPINE_TZ)
    return local_value.strftime("%Y-%m-%d %I:%M %p PHT")


def _limited_remote_response() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>KlasBot sharing</title>
    <style>
      body { margin: 0; font-family: Arial, sans-serif; background: #f7f4ed; color: #17211d; }
      main { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
      section { width: min(440px, 100%); display: grid; gap: 12px; }
      h1 { margin: 0; font-size: 24px; }
      p { margin: 0; color: #52605a; line-height: 1.45; }
    </style>
  </head>
  <body>
    <main>
      <section>
        <h1>KlasBot PDF sharing only</h1>
        <p>This device can only open temporary PDF share links from the kiosk. Use the kiosk screen to create a Share QR code, then scan that code here.</p>
      </section>
    </main>
  </body>
</html>""",
        status_code=status.HTTP_403_FORBIDDEN,
    )


@app.middleware("http")
async def limit_remote_clients_to_share_routes(request: Request, call_next):
    path = request.url.path
    if _is_local_request(request):
        return await call_next(request)
    if path.startswith(REMOTE_PUBLIC_PREFIXES) or path.startswith(REMOTE_STATIC_PREFIXES):
        return await call_next(request)
    if _remote_path_allowed_with_session(path):
        session = _session_from_request(request)
        if session:
            if request.method in REMOTE_MUTATING_METHODS and not _csrf_valid(request, session):
                return JSONResponse(
                    {"detail": "CSRF token missing or invalid"},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            return await call_next(request)
    return _limited_remote_response()


def _local_lan_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.2)
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def _public_base_url(request: Request) -> str:
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    hostname = request.url.hostname or ""
    if hostname in LOCAL_CLIENT_HOSTS:
        port = f":{request.url.port}" if request.url.port else ""
        return f"{request.url.scheme}://{_local_lan_ip()}{port}"
    return f"{request.url.scheme}://{request.url.netloc}"


def _public_url_for(request: Request, route_name: str, **path_params: Any) -> str:
    path = request.url_for(route_name, **path_params).path
    return f"{_public_base_url(request)}{path}"


def _public_qr_url_for(
    request: Request,
    qr_route_name: str,
    target_route_name: str,
    **path_params: Any,
) -> str:
    target = _public_url_for(request, target_route_name, **path_params)
    qr_url = _public_url_for(request, qr_route_name, **path_params)
    return f"{qr_url}?target={quote(target, safe='')}"


def _qr_target_url(
    request: Request,
    target: str | None,
    target_route_name: str,
    **path_params: Any,
) -> str:
    fallback = _public_url_for(request, target_route_name, **path_params)
    if not target:
        return fallback

    parsed = urlsplit(target)
    expected_path = request.url_for(target_route_name, **path_params).path
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path != expected_path:
        return fallback
    return target


def _qr_svg_response(target_url: str) -> Response:
    qr = qrcode.make(target_url, image_factory=SvgPathImage)
    buffer = BytesIO()
    qr.save(buffer)
    return Response(content=buffer.getvalue(), media_type="image/svg+xml")


@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/mobile", response_class=FileResponse)
async def mobile_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "mobile.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/me")
async def me(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    return {
        "teacher": {
            "id": teacher["id"],
            "name": teacher["name"],
            "is_admin": bool(teacher["is_admin"]),
        },
        "csrf_token": teacher.get("csrf_token", ""),
    }


@app.get("/api/ollama/status")
async def ollama_status(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    try:
        return await ollama_client.status(OLLAMA_MODEL)
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "model_available": False,
            "models": [],
            "error": str(exc),
        }


@app.post("/api/auth/login")
async def login(payload: LoginRequest, response: Response) -> dict:
    teacher = find_teacher_by_pin(payload.pin)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
    create_login_session(response, teacher["id"])
    return {"teacher": {"id": teacher["id"], "name": teacher["name"], "is_admin": bool(teacher["is_admin"])}}


@app.post("/api/mobile/pairing-token", status_code=status.HTTP_201_CREATED)
async def create_mobile_pairing_token(
    request: Request,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MOBILE_PAIRING_MINUTES)
    expires_iso = expires_at.replace(microsecond=0).isoformat()
    db.create_mobile_pairing_token(token, teacher["id"], expires_iso)
    url = f"{_public_base_url(request)}/mobile/pair/{token}"
    return {
        "token": token,
        "url": url,
        "qr_url": _public_qr_url_for(request, "mobile_pair_qr", "mobile_pair", token=token),
        "expires_at": _format_philippine_time(expires_at),
        "expires_at_utc": expires_iso,
        "timezone": "Asia/Manila",
    }


@app.get("/mobile/pair/{token}", response_class=HTMLResponse)
async def mobile_pair(token: str) -> Response:
    pairing = db.get_mobile_pairing_token(token)
    if not pairing or pairing["consumed_at"] or pairing["expires_at"] <= db.utc_now():
        return HTMLResponse(
            """<!doctype html><html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>KlasBot mobile pairing</title><link rel="stylesheet" href="/static/mobile.css" /></head>
<body><main class="mb-pair-state"><section><h1>Pairing link expired</h1>
<p>Use the kiosk to create a new mobile QR code.</p></section></main></body></html>""",
            status_code=status.HTTP_410_GONE,
        )
    expires_label = _format_philippine_time(datetime.fromisoformat(pairing["expires_at"]))
    return HTMLResponse(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>KlasBot mobile pairing</title><link rel="stylesheet" href="/static/mobile.css" /></head>
<body><main class="mb-pair-state"><section>
<div class="mb-brand"><div class="mb-brand-mark">K</div><div><h1>Pair this phone</h1>
<p>Connect this browser to {html.escape(pairing["name"])}'s KlasBot workspace.</p></div></div>
<form method="post" action="/mobile/pair/{html.escape(token)}" class="mb-form">
<p>This pairing link expires at {html.escape(expires_label)}.</p>
<button class="mb-primary" type="submit">Pair this phone</button>
</form></section></main></body></html>""",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/mobile/pair/{token}", response_class=HTMLResponse)
async def mobile_pair_confirm(token: str) -> Response:
    pairing = db.consume_mobile_pairing_token(token)
    if not pairing:
        return HTMLResponse(
            """<!doctype html><html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>KlasBot mobile pairing</title><link rel="stylesheet" href="/static/mobile.css" /></head>
<body><main class="mb-pair-state"><section><h1>Pairing link expired</h1>
<p>Use the kiosk to create a new mobile QR code.</p></section></main></body></html>""",
            status_code=status.HTTP_410_GONE,
        )
    redirect = RedirectResponse("/mobile", status_code=status.HTTP_303_SEE_OTHER)
    create_login_session(redirect, int(pairing["teacher_id"]))
    return redirect


@app.get("/mobile/pair/{token}/qr.svg", name="mobile_pair_qr")
async def mobile_pair_qr(token: str, request: Request, target: Optional[str] = None) -> Response:
    pairing = db.get_mobile_pairing_token(token)
    if not pairing or pairing["consumed_at"] or pairing["expires_at"] <= db.utc_now():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pairing link not found")
    return _qr_svg_response(_qr_target_url(request, target, "mobile_pair", token=token))


@app.post("/api/auth/logout")
async def logout(
    response: Response,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> dict:
    clear_login_session(response, session_token)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@app.get("/api/admin/teachers")
async def admin_teachers(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    require_admin(teacher)
    return {"teachers": db.list_teachers()}


@app.post("/api/admin/teachers", status_code=status.HTTP_201_CREATED)
async def admin_create_teacher(
    payload: TeacherCreateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    if pin_is_in_use(payload.pin):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PIN is already in use")
    created = db.create_teacher(payload.name, hash_pin(payload.pin), payload.is_admin)
    created["is_admin"] = bool(created["is_admin"])
    return {"teacher": created}


@app.post("/api/admin/teachers/{teacher_id}/reset-pin")
async def admin_reset_pin(
    teacher_id: int,
    payload: PinResetRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    if pin_is_in_use(payload.pin, exclude_teacher_id=teacher_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PIN is already in use")
    updated = db.update_teacher_pin(teacher_id, hash_pin(payload.pin))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    updated["is_admin"] = bool(updated["is_admin"])
    return {"teacher": updated}


@app.get("/api/admin/lesson-plan-formats")
async def admin_lesson_plan_formats(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    require_admin(teacher)
    return {"formats": db.list_lesson_plan_formats()}


@app.put("/api/admin/lesson-plan-formats/{format_name}")
async def admin_update_lesson_plan_format(
    format_name: str,
    payload: LessonPlanFormatUpdateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    updated = db.update_lesson_plan_format(format_name, payload.title, payload.requirements, teacher["id"])
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson plan format not found")
    return {"format": updated}


@app.post("/api/admin/lesson-plan-formats/{format_name}/reset")
async def admin_reset_lesson_plan_format(
    format_name: str,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    updated = db.reset_lesson_plan_format(format_name, teacher["id"])
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson plan format not found")
    return {"format": updated}


def _clean_list(values: list[str] | None) -> list[str]:
    return [value.strip() for value in values or [] if value.strip()]


def _generation_inputs(
    kind: str,
    format_name: str,
    subject: str,
    topic: str,
    grade_level: str | None,
    quarter: int | None,
    week_number: int | None,
    grade_levels: list[str] | None,
    resources: list[str] | None,
) -> dict[str, Any]:
    clean_grades = _clean_list(grade_levels)
    if grade_level and grade_level.strip() and grade_level.strip() not in clean_grades:
        clean_grades.insert(0, grade_level.strip())
    return {
        "kind": kind,
        "format": format_name.strip(),
        "subject": subject.strip(),
        "topic": topic.strip(),
        "grade_level": grade_level.strip() if grade_level else "",
        "quarter": quarter,
        "week_number": week_number,
        "grade_levels": clean_grades,
        "resources": _clean_list(resources),
    }


def _matching_curriculum_context(inputs: dict[str, Any]) -> dict[str, Any] | None:
    return db.get_curriculum_context(
        grade_level=inputs.get("grade_level") or (inputs.get("grade_levels") or [""])[0],
        subject=inputs.get("subject") or "",
        quarter=inputs.get("quarter"),
        topic=inputs.get("topic") or "",
    )


def _ensure_week_scoped_generation(inputs: dict[str, Any]) -> None:
    context = _matching_curriculum_context(inputs)
    if not context:
        return
    if not inputs.get("week_number"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select a pacing week before generating from the active curriculum.",
        )
    weekly_context = db.get_curriculum_week_context(
        grade_level=inputs.get("grade_level") or (inputs.get("grade_levels") or [""])[0],
        subject=inputs.get("subject") or "",
        quarter=inputs.get("quarter"),
        topic=inputs.get("topic") or "",
        week_number=inputs.get("week_number"),
    )
    if not weekly_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected pacing week was not found for this curriculum topic.",
        )


def _sse(data: str, event: str | None = None) -> str:
    lines = data.split("\n")
    prefix = f"event: {event}\n" if event else ""
    body = "".join(f"data: {line}\n" for line in lines)
    return f"{prefix}{body}\n"


async def _placeholder_sse(inputs: dict[str, Any]):
    heading = "Assessment" if inputs["kind"] == "assessment" else "Lesson Plan"
    chunks = [
        f"# Draft {heading}\n\n",
        f"Subject: {inputs.get('subject') or 'Untitled'}\n\nTopic: {inputs.get('topic') or 'Untitled'}\n\n",
        "## Objectives\n- Identify learning goals for the selected grade level.\n\n",
        "## Materials\n- Paper\n- Pencil\n- Locally available resources\n\n",
        "## Procedure\n1. Introduce the topic using a local example.\n2. Guide learners through a short activity.\n3. Ask learners to explain their answer.\n\n",
        "## Assessment\n- Give quick check questions and review answers together.\n",
    ]
    for chunk in chunks:
        await asyncio.sleep(0.15)
        yield _sse(chunk)


async def _sse_tokens(inputs: dict[str, Any]):
    if not inputs["topic"] or not inputs["subject"]:
        yield _sse("Please enter both subject and topic before generating.")
        yield _sse("[DONE]", event="done")
        return

    prompt = _build_grounded_prompt(inputs)
    generated_content = False
    try:
        async for token in ollama_client.stream_generate(OLLAMA_MODEL, prompt):
            if token.strip():
                generated_content = True
            yield _sse(token)
        if not generated_content:
            yield _sse("[Ollama generation returned no content - showing fallback draft]\n\n")
            async for chunk in _placeholder_sse(inputs):
                yield chunk
    except (OllamaStreamError, httpx.HTTPError, ValueError, KeyError) as exc:
        reason = _ollama_error_message(exc)
        yield _sse(f"[Ollama generation failed - showing fallback draft]\nReason: {reason}\n\n")
        async for chunk in _placeholder_sse(inputs):
            yield chunk

    yield _sse("[DONE]", event="done")


def _ollama_error_message(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            data = exc.response.json()
            if isinstance(data, dict) and data.get("error"):
                return str(data["error"])
        except (ValueError, httpx.ResponseNotRead):
            pass
        return f"Ollama returned HTTP {exc.response.status_code}"
    return str(exc) or exc.__class__.__name__


def _build_grounded_prompt(inputs: dict[str, Any]) -> str:
    inputs["curriculum_context"] = curriculum.build_curriculum_context(inputs)
    return build_prompt(inputs)


def _validate_teaching_aid_parent(output: dict[str, Any]) -> None:
    if output.get("kind") != "lesson_plan":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teaching Aids are available for lesson plans only.",
        )


def _teaching_aid_inputs(output: dict[str, Any], payload: TeachingAidGenerateRequest) -> dict[str, Any]:
    aid_type = payload.aid_type.strip()
    if aid_type not in valid_teaching_aid_types():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported teaching aid type")
    parent_inputs = dict(output.get("inputs") or {})
    try:
        curriculum_context = curriculum.build_curriculum_context(parent_inputs)
    except ValueError:
        curriculum_context = ""
    return {
        "aid_type": aid_type,
        "source_section": payload.source_section.strip(),
        "custom_request": payload.custom_request.strip(),
        "curriculum_context": curriculum_context,
    }


async def _teaching_aid_sse(output: dict[str, Any], inputs: dict[str, Any]):
    prompt = build_teaching_aid_prompt(output, inputs)
    generated_content = False
    try:
        async for token in ollama_client.stream_generate(OLLAMA_MODEL, prompt):
            if token.strip():
                generated_content = True
            yield _sse(token)
        if not generated_content:
            label = teaching_aid_label(inputs.get("aid_type") or "")
            yield _sse(f"[Ollama generation returned no content - showing fallback {label}]\n\n")
            yield _sse(_fallback_teaching_aid(output, inputs))
    except (OllamaStreamError, httpx.HTTPError, ValueError, KeyError) as exc:
        reason = _ollama_error_message(exc)
        label = teaching_aid_label(inputs.get("aid_type") or "")
        yield _sse(f"[Ollama generation failed - showing fallback {label}]\nReason: {reason}\n\n")
        yield _sse(_fallback_teaching_aid(output, inputs))
    yield _sse("[DONE]", event="done")


def _fallback_teaching_aid(output: dict[str, Any], inputs: dict[str, Any]) -> str:
    label = teaching_aid_label(inputs.get("aid_type") or "")
    topic = output.get("topic") or "the lesson topic"
    if inputs.get("aid_type") == "worked_example":
        return f"""# Worked Example

## Problem
Create a simple example about {topic} using the available classroom materials.

## Given
- Lesson topic: {topic}
- Resources: {", ".join(output.get("resources") or ["locally available materials"])}

## Concept or Theorem Used
Use the selected weekly competency from the lesson plan.

## Step-by-Step Solution
1. Identify what the problem is asking.
2. List the known information.
3. Apply the lesson concept one step at a time.
4. Check whether the answer is reasonable.

## Final Answer
Teacher completes the final answer based on the class example.

## Teacher Talk Track
Ask learners to explain each step before revealing the next step.

## Common Learner Mistake
Learners may jump to an answer without matching it to the given information.

## Similar Practice Item
Give one similar item with smaller numbers or a simpler situation, then ask learners to solve it independently.
"""
    return f"""# {label}

Use this Teaching Aid with the saved lesson on {topic}.

## Teacher Actions
- Review the selected weekly focus.
- Model one short example.
- Ask learners to explain their thinking.

## Learner Actions
- Answer the guide questions.
- Try one practice item.
- Correct mistakes using teacher feedback.

## Check for Understanding
- Ask one oral question.
- Review one written response.
"""


def _slugify_filename(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug[:80] or "klasbot-output"


def _share_metadata(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": output.get("subject"),
        "topic": output.get("topic"),
        "format": output.get("format"),
        "week_number": output.get("week_number") or (output.get("inputs") or {}).get("week_number"),
        "title": output.get("topic") or output.get("format") or "Klasbot Output",
    }


def _teaching_aid_metadata(output: dict[str, Any], aid: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": output.get("subject"),
        "topic": output.get("topic"),
        "format": "Teaching Aid",
        "week_number": output.get("week_number") or (output.get("inputs") or {}).get("week_number"),
        "title": aid.get("title") or teaching_aid_label(aid.get("aid_type") or ""),
    }


def _cleanup_expired_shared_exports() -> None:
    expired = db.list_expired_shared_exports()
    for export in expired:
        Path(export["file_path"]).unlink(missing_ok=True)
    db.delete_shared_exports(export["token"] for export in expired)


def _get_active_shared_export(token: str) -> dict[str, Any]:
    export = db.get_shared_export(token)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")
    if export["expires_at"] <= db.utc_now():
        Path(export["file_path"]).unlink(missing_ok=True)
        db.delete_shared_exports([token])
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link expired")
    if not Path(export["file_path"]).exists():
        db.delete_shared_exports([token])
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared file is unavailable")
    return export


@app.get("/api/generate/stream")
async def generate_stream(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    kind: Literal["lesson_plan", "assessment"] = Query(default="lesson_plan"),
    format: str = Query(default="DLP", max_length=32),
    subject: str = Query(default="", max_length=120),
    topic: str = Query(default="", max_length=200),
    grade_level: str = Query(default="", max_length=32),
    quarter: Optional[int] = Query(default=None),
    week_number: Optional[int] = Query(default=None, ge=1, le=10),
    grade_levels: list[str] | None = Query(default=None),
    resources: list[str] | None = Query(default=None),
):
    _check_generation_rate_limit(int(teacher["id"]))
    inputs = _generation_inputs(kind, format, subject, topic, grade_level, quarter, week_number, grade_levels, resources)
    _ensure_week_scoped_generation(inputs)
    return StreamingResponse(_sse_tokens(inputs), media_type="text/event-stream")


@app.get("/api/dev/prompt-preview/enabled")
async def prompt_preview_enabled(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    return {"enabled": PROMPT_PREVIEW_ENABLED and bool(teacher.get("is_admin"))}


@app.post("/api/dev/prompt-preview")
async def prompt_preview(
    payload: PromptPreviewRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    if not PROMPT_PREVIEW_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt preview is disabled")
    inputs = _generation_inputs(
        payload.kind,
        payload.format,
        payload.subject,
        payload.topic,
        payload.grade_level,
        payload.quarter,
        payload.week_number,
        payload.grade_levels,
        payload.resources,
    )
    if not inputs["topic"] or not inputs["subject"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject and topic are required")
    _ensure_week_scoped_generation(inputs)
    prompt = _build_grounded_prompt(inputs)
    return {
        "prompt": prompt,
        "inputs": inputs,
        "prompt_chars": len(prompt),
        "curriculum_context_chars": len(inputs.get("curriculum_context") or ""),
    }


@app.get("/api/curriculum/grades")
async def curriculum_grades(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    return {"grades": db.curriculum_grades()}


@app.get("/api/curriculum/subjects")
async def curriculum_subjects(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    grade: str = Query(..., max_length=32),
) -> dict:
    return {"subjects": db.curriculum_subjects(grade)}


@app.get("/api/curriculum/quarters")
async def curriculum_quarters(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    grade: str = Query(..., max_length=32),
    subject: str = Query(..., max_length=120),
) -> dict:
    return {"quarters": db.curriculum_quarters(grade, subject)}


@app.get("/api/curriculum/topics")
async def curriculum_topics(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    grade: str = Query(..., max_length=32),
    subject: str = Query(..., max_length=120),
    quarter: int = Query(..., ge=1, le=4),
) -> dict:
    return {"topics": db.curriculum_topics(grade, subject, quarter)}


@app.get("/api/curriculum/context")
async def curriculum_context(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    grade: str = Query(..., max_length=32),
    subject: str = Query(..., max_length=120),
    quarter: int = Query(..., ge=1, le=4),
    topic: str = Query(..., max_length=200),
) -> dict:
    return {"context": db.get_curriculum_context(grade_level=grade, subject=subject, quarter=quarter, topic=topic)}


@app.get("/api/curriculum/pacing")
async def curriculum_pacing(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    grade: str = Query(..., max_length=32),
    subject: str = Query(..., max_length=120),
    quarter: int = Query(..., ge=1, le=4),
    topic: str = Query(..., max_length=200),
) -> dict:
    pacing = db.get_curriculum_pacing(grade_level=grade, subject=subject, quarter=quarter, topic=topic)
    if not pacing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum pacing not found")
    return {"pacing": pacing}


@app.put("/api/admin/curriculum/pacing/{unit_id}")
async def admin_update_curriculum_pacing(
    unit_id: int,
    payload: PacingUpdateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    try:
        pacing = db.update_curriculum_pacing(
            unit_id,
            [week.model_dump() if hasattr(week, "model_dump") else week.dict() for week in payload.weeks],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not pacing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum unit not found")
    return {"pacing": pacing}


@app.post("/api/admin/curriculum/pacing/{unit_id}/reset")
async def admin_reset_curriculum_pacing(
    unit_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    pacing = db.reset_curriculum_pacing(unit_id)
    if not pacing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum unit not found")
    return {"pacing": pacing}


@app.get("/api/admin/curriculum")
async def admin_curriculum_list(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    require_admin(teacher)
    return {"documents": db.list_curriculum_documents()}


@app.post("/api/admin/curriculum/upload", status_code=status.HTTP_201_CREATED)
async def admin_curriculum_upload(
    teacher: Annotated[dict, Depends(get_current_teacher)],
    file: UploadFile = File(...),
    subject: str = Form(default=""),
    version_label: str = Form(default=""),
) -> dict:
    require_admin(teacher)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a PDF curriculum file")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(await file.read())
    try:
        document = curriculum.ingest_pdf(
            source_path=tmp_path,
            original_filename=file.filename,
            subject=subject or None,
            version_label=version_label or None,
            uploaded_by=teacher["id"],
        )
    finally:
        tmp_path.unlink(missing_ok=True)
    return {"document": document}


@app.post("/api/admin/curriculum/{document_id}/activate")
async def admin_curriculum_activate(
    document_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    document = db.activate_curriculum_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum document not found")
    return {"document": document}


@app.post("/api/admin/curriculum/{document_id}/deactivate")
async def admin_curriculum_deactivate(
    document_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    document = db.deactivate_curriculum_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum document not found")
    return {"document": document}


@app.delete("/api/admin/curriculum/{document_id}")
async def admin_curriculum_delete(
    document_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    require_admin(teacher)
    stored_path = db.get_curriculum_document_path(document_id)
    deleted = db.delete_inactive_curriculum_document(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only inactive curriculum documents can be deleted",
        )
    if stored_path:
        Path(stored_path).unlink(missing_ok=True)
    return {"ok": True}


@app.get("/api/library")
async def library_list(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    return {"outputs": db.list_outputs(teacher["id"])}


@app.post("/api/library", status_code=status.HTTP_201_CREATED)
async def library_create(
    payload: OutputSaveRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    inputs = dict(payload_dict.get("inputs") or {})
    if payload_dict.get("week_number") and not inputs.get("week_number"):
        inputs["week_number"] = payload_dict["week_number"]
    payload_dict["inputs"] = inputs
    _ensure_week_scoped_generation(inputs)
    output = db.create_output(teacher["id"], payload_dict)
    return {"output": output}


@app.get("/api/library/{output_id}")
async def library_get(
    output_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    output = db.get_output(teacher["id"], output_id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    return {"output": output}


@app.put("/api/library/{output_id}")
async def library_update(
    output_id: int,
    payload: OutputUpdateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    current = db.get_output(teacher["id"], output_id)
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    if (
        payload.expected_updated_at
        and payload.expected_updated_at != current["updated_at"]
        and not payload.force
    ):
        return JSONResponse(
            {"detail": "Output changed on another device", "output": current},
            status_code=status.HTTP_409_CONFLICT,
        )
    output = db.update_output(teacher["id"], output_id, payload.content_md)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    return {"output": output}


@app.get("/api/library/{output_id}/teaching-aids")
async def teaching_aids_list(
    output_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    output = db.get_output(teacher["id"], output_id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    _validate_teaching_aid_parent(output)
    return {"teaching_aids": db.list_teaching_aids(teacher["id"], output_id)}


@app.post("/api/library/{output_id}/teaching-aids/stream")
async def teaching_aids_stream(
    output_id: int,
    payload: TeachingAidGenerateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
):
    _check_generation_rate_limit(int(teacher["id"]))
    output = db.get_output(teacher["id"], output_id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    _validate_teaching_aid_parent(output)
    inputs = _teaching_aid_inputs(output, payload)
    return StreamingResponse(_teaching_aid_sse(output, inputs), media_type="text/event-stream")


@app.post("/api/library/{output_id}/teaching-aids", status_code=status.HTTP_201_CREATED)
async def teaching_aids_create(
    output_id: int,
    payload: TeachingAidSaveRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    output = db.get_output(teacher["id"], output_id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    _validate_teaching_aid_parent(output)
    inputs = _teaching_aid_inputs(output, payload)
    title = payload.title.strip() or teaching_aid_label(inputs["aid_type"])
    aid = db.create_teaching_aid(
        teacher["id"],
        output_id,
        {
            "aid_type": inputs["aid_type"],
            "title": title,
            "source_section": inputs["source_section"],
            "inputs": inputs,
            "content_md": payload.content_md,
        },
    )
    if not aid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    return {"teaching_aid": aid}


@app.put("/api/library/{output_id}/teaching-aids/{aid_id}")
async def teaching_aids_update(
    output_id: int,
    aid_id: int,
    payload: TeachingAidUpdateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    aid = db.update_teaching_aid(
        teacher["id"],
        output_id,
        aid_id,
        payload.title.strip(),
        payload.content_md,
    )
    if not aid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching Aid not found")
    return {"teaching_aid": aid}


@app.delete("/api/library/{output_id}/teaching-aids/{aid_id}")
async def teaching_aids_delete(
    output_id: int,
    aid_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    deleted = db.delete_teaching_aid(teacher["id"], output_id, aid_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching Aid not found")
    return {"ok": True}


@app.delete("/api/library/{output_id}")
async def library_delete(
    output_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    deleted = db.delete_output(teacher["id"], output_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    return {"ok": True}


@app.get("/api/class-records/classes")
async def class_records_list(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    return {"classes": db.list_class_records(teacher["id"])}


@app.post("/api/class-records/classes", status_code=status.HTTP_201_CREATED)
async def class_records_create(
    payload: ClassRecordRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    return {"class": db.create_class_record(teacher["id"], payload.model_dump() if hasattr(payload, "model_dump") else payload.dict())}


@app.get("/api/class-records/classes/{class_id}")
async def class_records_get(
    class_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    class_record = db.get_class_record(teacher["id"], class_id)
    if not class_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"class": class_record, "dashboard": db.get_class_dashboard(teacher["id"], class_id)}


@app.patch("/api/class-records/classes/{class_id}")
async def class_records_update(
    class_id: int,
    payload: ClassRecordRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    class_record = db.update_class_record(
        teacher["id"],
        class_id,
        payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
    )
    if not class_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"class": class_record}


@app.get("/api/class-records/classes/{class_id}/students")
async def class_records_students_list(
    class_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    students = db.list_class_students(teacher["id"], class_id)
    if students is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"students": students}


@app.post("/api/class-records/classes/{class_id}/students", status_code=status.HTTP_201_CREATED)
async def class_records_students_create(
    class_id: int,
    payload: StudentCreateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    payload_dict = (
        payload.model_dump(exclude_unset=True)
        if hasattr(payload, "model_dump")
        else payload.dict(exclude_unset=True)
    )
    if not payload_dict.get("student_id") and (not payload.first_name.strip() or not payload.last_name.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student first and last name are required")
    student = db.create_or_enroll_student(teacher["id"], class_id, payload_dict)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class or student not found")
    return {"student": student}


@app.patch("/api/class-records/students/{student_id}")
async def class_records_students_update(
    student_id: int,
    payload: StudentUpdateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    student = db.update_student(
        teacher["id"],
        student_id,
        payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
    )
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"student": student}


@app.get("/api/class-records/classes/{class_id}/assessments")
async def class_records_assessments_list(
    class_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    assessments = db.list_class_assessments(teacher["id"], class_id)
    if assessments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"assessments": assessments}


@app.post("/api/class-records/classes/{class_id}/assessments", status_code=status.HTTP_201_CREATED)
async def class_records_assessments_create(
    class_id: int,
    payload: AssessmentRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    assessment = db.create_assessment(
        teacher["id"],
        class_id,
        payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
    )
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"assessment": assessment}


@app.patch("/api/class-records/assessments/{assessment_id}")
async def class_records_assessments_update(
    assessment_id: int,
    payload: AssessmentRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    try:
        assessment = db.update_assessment(
            teacher["id"],
            assessment_id,
            payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return {"assessment": assessment}


@app.get("/api/class-records/assessments/{assessment_id}/scores")
async def class_records_scores_get(
    assessment_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    grid = db.get_score_grid(teacher["id"], assessment_id)
    if not grid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return grid


@app.put("/api/class-records/assessments/{assessment_id}/scores")
async def class_records_scores_save(
    assessment_id: int,
    payload: ScoreGridRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    try:
        grid = db.save_score_grid(
            teacher["id"],
            assessment_id,
            [item.model_dump() if hasattr(item, "model_dump") else item.dict() for item in payload.scores],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not grid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return grid


@app.get("/api/class-records/classes/{class_id}/dashboard")
async def class_records_dashboard(
    class_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    dashboard = db.get_class_dashboard(teacher["id"], class_id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"dashboard": dashboard}


@app.get("/api/class-records/assessments/{assessment_id}/dashboard")
async def class_records_assessment_dashboard(
    assessment_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    dashboard = db.get_assessment_dashboard(teacher["id"], assessment_id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return {"dashboard": dashboard}


@app.get("/api/grading/batches")
async def grading_batches_list(teacher: Annotated[dict, Depends(get_current_teacher)]) -> dict:
    return {"batches": db.list_grading_batches(teacher["id"])}


@app.post("/api/grading/batches", status_code=status.HTTP_201_CREATED)
async def grading_batches_create(
    payload: GradingBatchCreateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    if payload.grading_style == "exact" and not grading_scoring.parse_answer_key(payload.answer_key, payload.total_points):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exact-answer grading needs an answer key")
    batch = db.create_grading_batch(teacher["id"], payload_dict)
    return {"batch": batch}


@app.get("/api/grading/batches/{batch_id}")
async def grading_batches_get(
    batch_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    batch = db.get_grading_batch(teacher["id"], batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    return {"batch": batch}


@app.post("/api/grading/batches/{batch_id}/images", status_code=status.HTTP_201_CREATED)
async def grading_batch_upload_image(
    batch_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
    file: UploadFile = File(...),
) -> dict:
    if not db.get_grading_batch(teacher["id"], batch_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    data = await file.read()
    try:
        payload = grading_images.save_uploaded_image(
            teacher_id=teacher["id"],
            batch_id=batch_id,
            filename=file.filename or "worksheet",
            mime_type=file.content_type or "",
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    image = db.create_grading_image(teacher["id"], batch_id, payload)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    return {"image": image}


@app.get("/api/grading/images/{image_id}/thumbnail")
async def grading_image_thumbnail(
    image_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> FileResponse:
    image = db.get_grading_image(teacher["id"], image_id)
    if not image or not image.get("thumbnail_path"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    path = Path(image["thumbnail_path"])
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")
    return FileResponse(path, media_type="image/jpeg")


@app.post("/api/grading/batches/{batch_id}/detect-submissions")
async def grading_batch_detect_submissions(
    batch_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    batch = db.get_grading_batch(teacher["id"], batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    images = batch.get("images") or []
    if not images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload at least one image first")
    submissions = []
    for image in images:
        submissions.extend(grading_detection.detect_submission_regions(image))
    saved = db.replace_grading_submissions(teacher["id"], batch_id, submissions)
    return {"submissions": saved or []}


@app.post("/api/grading/batches/{batch_id}/grade")
async def grading_batch_grade(
    batch_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    batch = db.get_grading_batch(teacher["id"], batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    submissions = batch.get("submissions") or []
    if not submissions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Detect submissions before grading")
    images_by_id = {image["id"]: image for image in (batch.get("images") or [])}
    graded = []
    for submission in submissions:
        try:
            result = await asyncio.wait_for(
                grading_extraction.extract_and_grade_submission(
                    ollama_client=ollama_client,
                    model=OLLAMA_MODEL,
                    batch=batch,
                    submission=submission,
                    image=images_by_id.get(submission.get("image_id")),
                ),
                timeout=OLLAMA_GRADING_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            result = grading_scoring.build_review_grading_result(submission=submission, batch=batch)
            result["grading_result"]["warnings"].append(
                f"Ollama grading timed out after {int(OLLAMA_GRADING_TIMEOUT_SECONDS)} seconds. "
                "Review the worksheet manually or try a smaller crop/file."
            )
            result["grading_result"]["overall_feedback"] = (
                "Ollama did not return a grading result in time. Review the worksheet manually."
            )
        graded.append({**submission, **result})
    saved = db.save_grading_results(teacher["id"], batch_id, graded)
    return {"submissions": saved or []}


@app.patch("/api/grading/submissions/{submission_id}")
async def grading_submission_update(
    submission_id: int,
    payload: GradingSubmissionUpdateRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    submission = db.update_grading_submission(teacher["id"], submission_id, payload_dict)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading submission not found")
    return {"submission": submission}


@app.delete("/api/grading/batches/{batch_id}")
async def grading_batch_delete(
    batch_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    file_paths = db.list_grading_batch_file_paths(teacher["id"], batch_id)
    deleted = db.delete_grading_batch(teacher["id"], batch_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    for file_path in file_paths:
        Path(file_path).unlink(missing_ok=True)
    return {"ok": True}


@app.post("/api/grading/batches/{batch_id}/print", response_class=HTMLResponse)
async def grading_batch_print_preview(
    batch_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> HTMLResponse:
    batch = db.get_grading_batch(teacher["id"], batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading batch not found")
    content_md = grading_reports.batch_report_markdown(batch)
    return HTMLResponse(render_print_html(content_md, {"format": "Quiz Photo Grading"}))


@app.post("/api/library/{output_id}/regenerate")
async def library_regenerate(
    output_id: int,
    teacher: Annotated[dict, Depends(get_current_teacher)],
):
    output = db.get_output(teacher["id"], output_id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
    _ensure_week_scoped_generation(output["inputs"])
    return StreamingResponse(_sse_tokens(output["inputs"]), media_type="text/event-stream")


@app.post("/api/library/{output_id}/teaching-aids/{aid_id}/share", status_code=status.HTTP_201_CREATED)
async def teaching_aid_share(
    output_id: int,
    aid_id: int,
    payload: ShareCreateRequest,
    request: Request,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    output = db.get_output(teacher["id"], output_id)
    aid = db.get_teaching_aid(teacher["id"], output_id, aid_id)
    if not output or not aid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching Aid not found")

    _cleanup_expired_shared_exports()
    token = secrets.token_urlsafe(16)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=payload.expires_minutes)
    ).replace(microsecond=0).isoformat()
    filename_base = _slugify_filename(f"{output.get('topic') or 'lesson'}-{aid.get('title') or 'teaching-aid'}")
    filename = f"{filename_base}.pdf"
    share_dir = get_share_dir()
    file_path = share_dir / f"{token}.pdf"
    metadata = _teaching_aid_metadata(output, aid)
    export_pdf(aid["content_md"], metadata, file_path)
    export = db.create_shared_export(
        token=token,
        teacher_id=teacher["id"],
        output_id=output["id"],
        filename=filename,
        file_path=str(file_path),
        expires_at=expires_at,
    )
    return {
        "token": token,
        "url": _public_url_for(request, "share_page", token=token),
        "download_url": _public_url_for(request, "share_download", token=token),
        "qr_url": _public_qr_url_for(request, "share_qr", "share_page", token=token),
        "filename": filename,
        "expires_at": export["expires_at"],
    }


@app.post("/api/library/{output_id}/share", status_code=status.HTTP_201_CREATED)
async def library_share(
    output_id: int,
    payload: ShareCreateRequest,
    request: Request,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    output = db.get_output(teacher["id"], output_id)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")

    _cleanup_expired_shared_exports()
    token = secrets.token_urlsafe(16)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=payload.expires_minutes)
    ).replace(microsecond=0).isoformat()
    filename_base = _slugify_filename(
        f"{output.get('topic') or output.get('kind')}-{output.get('format') or 'output'}"
    )
    filename = f"{filename_base}.pdf"
    share_dir = get_share_dir()
    file_path = share_dir / f"{token}.pdf"
    export_pdf(output["content_md"], _share_metadata(output), file_path)
    export = db.create_shared_export(
        token=token,
        teacher_id=teacher["id"],
        output_id=output["id"],
        filename=filename,
        file_path=str(file_path),
        expires_at=expires_at,
    )
    return {
        "token": token,
        "url": _public_url_for(request, "share_page", token=token),
        "download_url": _public_url_for(request, "share_download", token=token),
        "qr_url": _public_qr_url_for(request, "share_qr", "share_page", token=token),
        "filename": filename,
        "expires_at": export["expires_at"],
    }


@app.get("/share/{token}", response_class=HTMLResponse)
async def share_page(token: str, request: Request) -> HTMLResponse:
    export = _get_active_shared_export(token)
    download_url = _public_url_for(request, "share_download", token=token)
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>KlasBot shared file</title>
    <style>
      body {{ margin: 0; font-family: Arial, sans-serif; background: #f7f4ed; color: #17211d; }}
      main {{ min-height: 100vh; display: grid; place-items: center; padding: 24px; }}
      section {{ width: min(420px, 100%); display: grid; gap: 14px; }}
      h1 {{ margin: 0; font-size: 24px; }}
      p {{ margin: 0; color: #52605a; line-height: 1.4; }}
      a {{ display: inline-flex; justify-content: center; padding: 12px 16px; border-radius: 6px; background: #167251; color: white; text-decoration: none; font-weight: 700; }}
      .meta {{ font-size: 13px; }}
    </style>
  </head>
  <body>
    <main>
      <section>
        <h1>KlasBot PDF</h1>
        <p>{html.escape(export["filename"])} is ready to download.</p>
        <a href="{html.escape(download_url)}">Download PDF</a>
        <p class="meta">This link expires at {html.escape(export["expires_at"])}.</p>
      </section>
    </main>
  </body>
</html>"""
    )


@app.get("/share/{token}/download", name="share_download")
async def share_download(token: str) -> FileResponse:
    export = _get_active_shared_export(token)
    db.increment_shared_export_download(token)
    return FileResponse(
        export["file_path"],
        media_type="application/pdf",
        filename=export["filename"],
    )


@app.get("/share/{token}/qr.svg", name="share_qr")
async def share_qr(token: str, request: Request, target: Optional[str] = None) -> Response:
    _get_active_shared_export(token)
    return _qr_svg_response(_qr_target_url(request, target, "share_page", token=token))


@app.post("/api/print")
async def print_output(
    payload: PrintRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> dict:
    metadata = payload.metadata
    content_md = payload.content_md
    if payload.output_id is not None:
        output = db.get_output(teacher["id"], payload.output_id)
        if not output:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
        if payload.teaching_aid_id is not None:
            aid = db.get_teaching_aid(teacher["id"], payload.output_id, payload.teaching_aid_id)
            if not aid:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching Aid not found")
            content_md = aid["content_md"]
            metadata = _teaching_aid_metadata(output, aid)
        else:
            content_md = output["content_md"]
            metadata = {
                "subject": output.get("subject"),
                "topic": output.get("topic"),
                "format": output.get("format"),
                "week_number": output.get("week_number") or (output.get("inputs") or {}).get("week_number"),
            }
    if not content_md:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to print")

    html = render_print_html(content_md, metadata)
    result = print_html(html)
    result["html"] = html
    return result


@app.post("/api/print/preview", response_class=HTMLResponse)
async def print_preview(
    payload: PrintRequest,
    teacher: Annotated[dict, Depends(get_current_teacher)],
) -> HTMLResponse:
    content_md = payload.content_md
    metadata = payload.metadata
    if payload.output_id is not None:
        output = db.get_output(teacher["id"], payload.output_id)
        if not output:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
        if payload.teaching_aid_id is not None:
            aid = db.get_teaching_aid(teacher["id"], payload.output_id, payload.teaching_aid_id)
            if not aid:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching Aid not found")
            content_md = aid["content_md"]
            metadata = _teaching_aid_metadata(output, aid)
        else:
            content_md = output["content_md"]
            metadata = {
                "subject": output.get("subject"),
                "topic": output.get("topic"),
                "week_number": output.get("week_number") or (output.get("inputs") or {}).get("week_number"),
            }
    if not content_md:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to print")
    return HTMLResponse(render_print_html(content_md, metadata))
