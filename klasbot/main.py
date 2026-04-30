from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

app = FastAPI(title="Klasbot", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/static/{path:path}")
async def static_files(path: str) -> FileResponse:
    return FileResponse(STATIC_DIR / path)


async def _sse_tokens(prompt: str):
    # Placeholder token streaming until Ollama client integration is added.
    chunks = [
        "# Draft Lesson Plan\n\n",
        f"Topic: {prompt or 'Untitled'}\n\n",
        "## Objectives\n- Identify learning goals.\n\n",
        "## Materials\n- Paper\n- Pencil\n\n",
        "## Procedure\n1. Introduction\n2. Guided activity\n3. Wrap-up\n\n",
        "## Assessment\n- Quick check questions\n",
    ]

    for chunk in chunks:
        await asyncio.sleep(0.25)
        yield f"data: {chunk}\n\n"

    yield "event: done\ndata: [DONE]\n\n"


@app.get("/generate")
async def generate(prompt: str = Query(default="", description="Lesson prompt/topic")):
    return StreamingResponse(_sse_tokens(prompt), media_type="text/event-stream")
