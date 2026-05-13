from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps
from pypdf import PdfReader

from klasbot.grading import scoring


SYSTEM_PROMPT = """You extract and grade student quiz or worksheet submissions.
Return only valid JSON. Do not include Markdown.
Do not invent a student name or answer. If handwriting or text is unclear, leave the answer blank or mark it uncertain in warnings.
Use the teacher-provided questions, answer key, rubric, grading style, and total points when present.
Give item-level scores and concise feedback. Teacher review is still required."""


async def extract_and_grade_submission(
    *,
    ollama_client: Any,
    model: str,
    batch: dict[str, Any],
    submission: dict[str, Any],
    image: dict[str, Any] | None,
) -> dict[str, Any]:
    fallback = scoring.build_review_grading_result(submission=submission, batch=batch)
    if not image:
        fallback["grading_result"]["warnings"].append("No source image was found for this submission.")
        return fallback

    messages, preflight_warnings = _build_messages(batch=batch, submission=submission, image=image)
    if not messages:
        fallback["grading_result"]["warnings"].extend(preflight_warnings)
        fallback["grading_result"]["overall_feedback"] = (
            "Model extraction could not run for this file. Review the worksheet and enter scores manually."
        )
        return fallback

    try:
        content = await ollama_client.chat(model, messages, format="json")
        parsed = _parse_json_object(content)
    except Exception as exc:
        fallback["grading_result"]["warnings"].append(f"Ollama extraction failed: {exc}")
        fallback["grading_result"]["overall_feedback"] = (
            "Model extraction failed. Review the worksheet and enter scores manually."
        )
        return fallback

    try:
        result = normalize_model_result(parsed, batch=batch, submission=submission)
    except ValueError as exc:
        fallback["grading_result"]["warnings"].append(f"Ollama returned unusable grading JSON: {exc}")
        fallback["grading_result"]["overall_feedback"] = (
            "Model extraction returned an invalid structure. Review the worksheet and enter scores manually."
        )
        return fallback

    result["grading_result"]["warnings"] = preflight_warnings + result["grading_result"].get("warnings", [])
    return result


def normalize_model_result(
    payload: dict[str, Any],
    *,
    batch: dict[str, Any],
    submission: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(payload.get("submissions"), list):
        payload = payload["submissions"][0] if payload["submissions"] else {}
    if not isinstance(payload, dict):
        raise ValueError("top-level response is not an object")

    extracted = payload.get("extracted_answers")
    if not isinstance(extracted, dict):
        extracted = {
            "student_name": payload.get("student_name") or "",
            "student_identifier": payload.get("student_identifier") or "",
            "items": payload.get("answers") or payload.get("items") or [],
        }
    items = [_normalize_model_item(item) for item in (payload.get("items") or extracted.get("items") or [])]
    answer_items = scoring.parse_answer_key(batch.get("answer_key"), float(batch.get("total_points") or 0))
    if answer_items and not items:
        raise ValueError("missing item rows")

    if answer_items:
        keyed = {str(item.get("item_number")): item for item in items}
        merged_items = []
        for answer_item in answer_items:
            item_number = str(answer_item.get("item_number") or "")
            model_item = keyed.get(item_number, {})
            merged_items.append(
                {
                    "item_number": item_number,
                    "student_answer": str(model_item.get("student_answer") or ""),
                    "correct_answer": str(model_item.get("correct_answer") or answer_item.get("correct_answer") or ""),
                    "score": _optional_float(model_item.get("score"), default=0.0),
                    "max_score": _optional_float(model_item.get("max_score"), default=answer_item.get("max_score") or 1.0),
                    "feedback": str(model_item.get("feedback") or "Review this model-proposed score."),
                    "confidence": _clamp(_optional_float(model_item.get("confidence"), default=0.6), 0, 1),
                    "warnings": _string_list(model_item.get("warnings")),
                }
            )
        items = merged_items

    score = payload.get("total_score", payload.get("score"))
    if score is None and items:
        score = sum(float(item.get("score") or 0) for item in items)
    max_score = payload.get("max_score")
    if max_score is None:
        max_score = batch.get("total_points") or sum(float(item.get("max_score") or 0) for item in items)
    score_value = _optional_float(score)
    max_score_value = _optional_float(max_score, default=0.0)
    confidence = _clamp(_optional_float(payload.get("confidence"), default=_average_confidence(items)), 0, 1)

    student_name = str(payload.get("student_name") or extracted.get("student_name") or submission.get("student_name") or "")
    student_identifier = str(
        payload.get("student_identifier")
        or extracted.get("student_identifier")
        or submission.get("student_identifier")
        or ""
    )
    rating = str(payload.get("rating") or "")
    if not rating and score_value is not None and max_score_value:
        rating = f"{round(score_value / max_score_value * 100)}%"

    extracted_items = [
        {
            "item_number": item.get("item_number", ""),
            "student_answer": item.get("student_answer", ""),
            "confidence": item.get("confidence"),
            "warnings": item.get("warnings", []),
        }
        for item in items
    ]
    return {
        "student_name": student_name,
        "student_identifier": student_identifier,
        "extracted_answers": {
            "student_name": student_name,
            "student_identifier": student_identifier,
            "items": extracted_items,
            "raw_model": payload,
        },
        "grading_result": {
            "student_name": student_name,
            "student_identifier": student_identifier,
            "items": items,
            "total_score": score_value,
            "max_score": max_score_value,
            "rating": rating,
            "overall_feedback": str(payload.get("overall_feedback") or "Review the model-extracted answers and proposed scores."),
            "confidence": confidence,
            "warnings": _string_list(payload.get("warnings")),
        },
        "score": score_value,
        "max_score": max_score_value,
        "confidence": confidence,
    }


def _build_messages(
    *,
    batch: dict[str, Any],
    submission: dict[str, Any],
    image: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    mime_type = image.get("mime_type") or ""
    path = Path(image.get("original_path") or "")
    if not path.exists():
        return [], ["The uploaded source file is missing from local storage."]

    prompt = _build_user_prompt(batch=batch, submission=submission, image=image)
    if mime_type.startswith("image/"):
        encoded = _encode_image_region(path, submission.get("crop_box") or {})
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt, "images": [encoded]},
        ], warnings

    if mime_type == "application/pdf":
        pdf_text, pdf_warnings = _extract_pdf_text(path)
        warnings.extend(pdf_warnings)
        pdf_images, render_warnings = _encode_pdf_pages(path)
        warnings.extend(render_warnings)
        if pdf_text.strip():
            prompt = f"{prompt}\n\nExtracted PDF text:\n{pdf_text[:12000]}"
        if pdf_images:
            return [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt, "images": pdf_images},
            ], warnings
        if pdf_text.strip():
            return [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ], warnings
        return [], warnings + ["This PDF could not be rendered or read. Convert scanned PDF pages to images before grading."]

    return [], [f"Unsupported source MIME type for model extraction: {mime_type}"]


def _build_user_prompt(*, batch: dict[str, Any], submission: dict[str, Any], image: dict[str, Any]) -> str:
    context = {
        "subject": batch.get("subject") or "",
        "grade_level": batch.get("grade_level") or "",
        "topic": batch.get("topic") or "",
        "quarter": batch.get("quarter"),
        "week_number": batch.get("week_number"),
        "week_topic": batch.get("week_topic") or "",
        "total_points": batch.get("total_points"),
        "grading_style": batch.get("grading_style") or "review_only",
        "questions": batch.get("questions") or "",
        "answer_key": batch.get("answer_key") or "",
        "rubric": batch.get("rubric") or "",
        "current_student_name": submission.get("student_name") or "",
        "current_student_identifier": submission.get("student_identifier") or "",
        "crop_box": submission.get("crop_box") or {},
        "source_mime_type": image.get("mime_type") or "",
    }
    return (
        "Extract the student's answers from the attached worksheet or PDF text, then propose grades.\n"
        "Return exactly one JSON object with keys: student_name, student_identifier, extracted_answers, items, "
        "total_score, max_score, rating, overall_feedback, confidence, warnings.\n"
        "Each item must include: item_number, student_answer, correct_answer, score, max_score, feedback, confidence, warnings.\n"
        "Context JSON:\n"
        f"{json.dumps(context, ensure_ascii=True, indent=2)}"
    )


def _encode_image_region(path: Path, crop_box: dict[str, Any]) -> str:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        left = int(float(crop_box.get("left", 0) or 0))
        top = int(float(crop_box.get("top", 0) or 0))
        right = int(float(crop_box.get("right", image.width) or image.width))
        bottom = int(float(crop_box.get("bottom", image.height) or image.height))
        left = max(0, min(left, image.width - 1))
        top = max(0, min(top, image.height - 1))
        right = max(left + 1, min(right, image.width))
        bottom = max(top + 1, min(bottom, image.height))
        image = image.crop((left, top, right, bottom))
        image.thumbnail((1600, 1600))
        buffer = BytesIO()
        image.save(buffer, "JPEG", quality=88, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _extract_pdf_text(path: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"--- Page {index} ---\n{text.strip()}")
    if len(reader.pages) > 1:
        warnings.append(f"PDF has {len(reader.pages)} pages; extracted text from all readable pages.")
    return "\n\n".join(pages), warnings


def _encode_pdf_pages(path: Path, max_pages: int = 3) -> tuple[list[str], list[str]]:
    executable = shutil.which("pdftoppm")
    if not executable:
        return [], ["PDF page rendering is unavailable because pdftoppm is not installed."]
    warnings: list[str] = []
    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
    except Exception:
        page_count = max_pages
    last_page = min(max_pages, max(1, page_count))
    if page_count > max_pages:
        warnings.append(f"Only the first {max_pages} PDF pages were sent to the vision model.")

    with tempfile.TemporaryDirectory(prefix="klasbot-pdf-render-") as tmp_dir:
        prefix = str(Path(tmp_dir) / "page")
        command = [
            executable,
            "-jpeg",
            "-r",
            "160",
            "-f",
            "1",
            "-l",
            str(last_page),
            str(path),
            prefix,
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=30)
        except Exception as exc:
            return [], [f"PDF page rendering failed: {exc}"]
        encoded_pages = []
        for page_path in sorted(Path(tmp_dir).glob("page-*.jpg")):
            encoded_pages.append(base64.b64encode(page_path.read_bytes()).decode("ascii"))
        return encoded_pages, warnings


def _parse_json_object(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise ValueError("empty response")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("response JSON is not an object")
    return data


def _normalize_model_item(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    return {
        "item_number": str(item.get("item_number") or item.get("number") or ""),
        "student_answer": str(item.get("student_answer") or item.get("answer") or ""),
        "correct_answer": str(item.get("correct_answer") or item.get("expected_answer") or ""),
        "score": _optional_float(item.get("score"), default=0.0),
        "max_score": _optional_float(item.get("max_score") or item.get("points"), default=1.0),
        "feedback": str(item.get("feedback") or ""),
        "confidence": _clamp(_optional_float(item.get("confidence"), default=0.6), 0, 1),
        "warnings": _string_list(item.get("warnings")),
    }


def _optional_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _average_confidence(items: list[dict[str, Any]]) -> float:
    values = [float(item.get("confidence")) for item in items if item.get("confidence") is not None]
    return sum(values) / len(values) if values else 0.6


def _clamp(value: float | None, minimum: float, maximum: float) -> float:
    if value is None:
        return minimum
    return max(minimum, min(maximum, float(value)))


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
