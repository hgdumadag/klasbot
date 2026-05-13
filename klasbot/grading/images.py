from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, ImageStat
from pypdf import PdfReader

from klasbot.config import get_grading_upload_dir

ALLOWED_MIME_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "application/pdf": ".pdf"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def teacher_batch_dir(teacher_id: int, batch_id: int) -> Path:
    path = get_grading_upload_dir() / f"teacher_{teacher_id}" / f"batch_{batch_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploaded_image(
    *,
    teacher_id: int,
    batch_id: int,
    filename: str,
    mime_type: str,
    data: bytes,
) -> dict[str, Any]:
    mime_type = _normalize_mime_type(mime_type, filename, data)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Upload a PNG, JPEG, or PDF file")
    if not data:
        raise ValueError("Uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File is larger than 20 MB")

    suffix = ALLOWED_MIME_TYPES[mime_type]
    safe_stem = _slugify(Path(filename or "worksheet").stem) or "worksheet"
    token = secrets.token_hex(8)
    output_dir = teacher_batch_dir(teacher_id, batch_id)
    original_path = output_dir / f"{safe_stem}-{token}{suffix}"
    thumbnail_path = output_dir / f"{safe_stem}-{token}-thumb.jpg"

    if mime_type == "application/pdf":
        return _save_uploaded_pdf(
            original_path=original_path,
            thumbnail_path=thumbnail_path,
            mime_type=mime_type,
            data=data,
        )

    try:
        with Image.open(_bytes_path(data)) as source_image:
            image = ImageOps.exif_transpose(source_image).convert("RGB")
            image.save(original_path, quality=88, optimize=True)
            thumbnail = image.copy()
            thumbnail.thumbnail((720, 720))
            thumbnail.save(thumbnail_path, "JPEG", quality=82, optimize=True)
            warnings = quality_warnings(image)
            width, height = image.size
    except Exception as exc:  # Pillow raises several format-specific exceptions.
        original_path.unlink(missing_ok=True)
        thumbnail_path.unlink(missing_ok=True)
        raise ValueError("Uploaded file is not a readable PNG or JPEG image") from exc

    return {
        "original_path": str(original_path),
        "thumbnail_path": str(thumbnail_path),
        "mime_type": mime_type,
        "width": width,
        "height": height,
        "quality_warnings": warnings,
    }


def _save_uploaded_pdf(
    *,
    original_path: Path,
    thumbnail_path: Path,
    mime_type: str,
    data: bytes,
) -> dict[str, Any]:
    original_path.write_bytes(data)
    try:
        reader = PdfReader(_bytes_path(data))
        if not reader.pages:
            raise ValueError("PDF has no pages")
        first_page = reader.pages[0]
        width = int(float(first_page.mediabox.width or 612))
        height = int(float(first_page.mediabox.height or 792))
        page_count = len(reader.pages)
    except Exception as exc:
        original_path.unlink(missing_ok=True)
        thumbnail_path.unlink(missing_ok=True)
        raise ValueError("Uploaded file is not a readable PDF") from exc

    warnings = [
        "PDF uploaded. Confirm each worksheet page or region before grading.",
    ]
    if page_count > 1:
        warnings.append(f"PDF has {page_count} pages; this foundation workflow previews the first page only.")
    _write_pdf_thumbnail(thumbnail_path, page_count)
    return {
        "original_path": str(original_path),
        "thumbnail_path": str(thumbnail_path),
        "mime_type": mime_type,
        "width": width,
        "height": height,
        "quality_warnings": warnings,
    }


def _write_pdf_thumbnail(thumbnail_path: Path, page_count: int) -> None:
    image = Image.new("RGB", (720, 720), "#f7f4ed")
    # Keep the preview dependency-light; actual page rendering can be swapped in later.
    from PIL import ImageDraw

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((155, 95, 565, 625), radius=14, fill="#ffffff", outline="#d9d1c1", width=3)
    draw.rectangle((205, 170, 515, 190), fill="#d9d1c1")
    draw.rectangle((205, 225, 515, 245), fill="#d9d1c1")
    draw.rectangle((205, 280, 430, 300), fill="#d9d1c1")
    draw.text((275, 360), "PDF", fill="#17211d")
    draw.text((255, 410), f"{page_count} page{'s' if page_count != 1 else ''}", fill="#52605a")
    image.save(thumbnail_path, "JPEG", quality=88, optimize=True)


def quality_warnings(image: Image.Image) -> list[str]:
    warnings: list[str] = []
    width, height = image.size
    if width < 900 or height < 700:
        warnings.append("Low resolution may make handwriting difficult to read.")

    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    brightness = stat.mean[0]
    contrast = stat.stddev[0]
    if brightness < 70:
        warnings.append("Image appears dark; retake near brighter light if needed.")
    if brightness > 235:
        warnings.append("Image appears overexposed; check for glare.")
    if contrast < 24:
        warnings.append("Low contrast may reduce OCR accuracy.")

    aspect_ratio = max(width, height) / max(1, min(width, height))
    if aspect_ratio > 2.4:
        warnings.append("Unusual image shape; confirm worksheet crop boundaries.")
    return warnings


def _bytes_path(data: bytes):
    from io import BytesIO

    return BytesIO(data)


def _normalize_mime_type(mime_type: str, filename: str, data: bytes) -> str:
    clean_type = (mime_type or "").split(";")[0].strip().lower()
    suffix = Path(filename or "").suffix.lower()
    if clean_type in ALLOWED_MIME_TYPES:
        return clean_type
    if clean_type in {"application/octet-stream", "binary/octet-stream", ""}:
        if suffix == ".pdf" or data.startswith(b"%PDF-"):
            return "application/pdf"
        if suffix in {".jpg", ".jpeg"} or data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if suffix == ".png" or data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
    if clean_type in {"application/x-pdf", "application/acrobat", "applications/vnd.pdf", "text/pdf", "text/x-pdf"}:
        return "application/pdf"
    if suffix == ".pdf" and data.startswith(b"%PDF-"):
        return "application/pdf"
    return clean_type


def _slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")[:80]
