from __future__ import annotations

import json
import re
from typing import Any


def parse_answer_key(answer_key: Any, total_points: float) -> list[dict[str, Any]]:
    if isinstance(answer_key, dict):
        if isinstance(answer_key.get("items"), list):
            return [_normalize_item(item, total_points) for item in answer_key["items"]]
        return [
            {"item_number": str(key), "correct_answer": str(value), "max_score": 1.0}
            for key, value in answer_key.items()
            if str(value).strip()
        ]
    if isinstance(answer_key, list):
        return [_normalize_item(item, total_points) for item in answer_key]
    if isinstance(answer_key, str):
        text = answer_key.strip()
        if not text:
            return []
        try:
            return parse_answer_key(json.loads(text), total_points)
        except json.JSONDecodeError:
            return _parse_answer_key_text(text)
    return []


def build_review_grading_result(
    *,
    submission: dict[str, Any],
    batch: dict[str, Any],
) -> dict[str, Any]:
    total_points = float(batch.get("total_points") or 0)
    answer_items = parse_answer_key(batch.get("answer_key"), total_points)
    grading_style = batch.get("grading_style") or "review_only"
    warnings = list((submission.get("grading_result") or {}).get("warnings") or [])

    if grading_style == "review_only":
        items = []
        score = None
        confidence = min(float(submission.get("confidence") or 0.5), 0.5)
        feedback = "Teacher-review mode: enter scores after checking the worksheet image."
    elif not answer_items:
        items = []
        score = None
        confidence = min(float(submission.get("confidence") or 0.5), 0.45)
        warnings.append("No answer key or rubric items were available for automatic scoring.")
        feedback = "Needs manual grading because no answer key was provided."
    else:
        items = [
            {
                "item_number": item["item_number"],
                "student_answer": "",
                "correct_answer": item["correct_answer"],
                "score": 0,
                "max_score": item["max_score"],
                "feedback": "Model extraction was unavailable; teacher review required.",
                "confidence": 0.35,
                "warnings": ["Answer was not extracted automatically."],
            }
            for item in answer_items
        ]
        score = 0.0
        confidence = 0.35
        feedback = "Automatic extraction was unavailable. Review the worksheet and enter student answers or scores."

    max_score = total_points if total_points else sum(float(item.get("max_score") or 0) for item in answer_items)
    return {
        "extracted_answers": {"items": []},
        "grading_result": {
            "student_name": submission.get("student_name") or "",
            "student_identifier": submission.get("student_identifier") or "",
            "items": items,
            "total_score": score,
            "max_score": max_score,
            "rating": "" if score is None or not max_score else f"{round(score / max_score * 100)}%",
            "overall_feedback": feedback,
            "confidence": confidence,
            "warnings": warnings,
        },
        "score": score,
        "max_score": max_score,
        "confidence": confidence,
    }


def _normalize_item(item: Any, total_points: float) -> dict[str, Any]:
    if isinstance(item, dict):
        return {
            "item_number": str(item.get("item_number") or item.get("number") or ""),
            "correct_answer": str(item.get("correct_answer") or item.get("answer") or ""),
            "max_score": float(item.get("max_score") or item.get("points") or 1),
        }
    return {"item_number": "", "correct_answer": str(item), "max_score": 1.0}


def _parse_answer_key_text(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*[\).:\-]\s*(.+?)\s*$", line)
        if match:
            items.append({"item_number": match.group(1), "correct_answer": match.group(2), "max_score": 1.0})
    if items:
        return items
    return [
        {"item_number": str(index), "correct_answer": value.strip(), "max_score": 1.0}
        for index, value in enumerate(text.split(","), start=1)
        if value.strip()
    ]
