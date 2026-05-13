from __future__ import annotations

from typing import Any


def detect_submission_regions(image: dict[str, Any]) -> list[dict[str, Any]]:
    width = int(image.get("width") or 0)
    height = int(image.get("height") or 0)
    if width <= 0 or height <= 0:
        return [_region(image, 0, 0, 1, 1, 0.2, ["Image dimensions unavailable; using whole image."])]

    warnings = list(image.get("quality_warnings") or [])
    aspect_ratio = width / max(1, height)
    if aspect_ratio >= 1.85:
        midpoint = width // 2
        return [
            _region(image, 0, 0, midpoint, height, 0.52, warnings + ["Wide photo split into left candidate worksheet."]),
            _region(image, midpoint, 0, width, height, 0.52, warnings + ["Wide photo split into right candidate worksheet."]),
        ]
    return [_region(image, 0, 0, width, height, 0.68, warnings)]


def _region(
    image: dict[str, Any],
    left: int,
    top: int,
    right: int,
    bottom: int,
    confidence: float,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "image_id": image["id"],
        "student_name": "",
        "student_identifier": "",
        "crop_box": {"left": left, "top": top, "right": right, "bottom": bottom},
        "confidence": confidence,
        "extracted_answers": {},
        "grading_result": {
            "items": [],
            "warnings": warnings,
            "overall_feedback": "Confirm this worksheet region before grading.",
        },
        "score": None,
        "max_score": None,
    }
