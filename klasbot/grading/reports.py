from __future__ import annotations

from typing import Any


def batch_report_markdown(batch: dict[str, Any]) -> str:
    submissions = batch.get("submissions") or []
    lines = [
        "# Quiz Photo Grading Report",
        "",
        f"- Subject: {batch.get('subject') or 'Not specified'}",
        f"- Grade: {batch.get('grade_level') or 'Not specified'}",
        f"- Topic: {batch.get('topic') or 'Not specified'}",
        f"- Quarter: {batch.get('quarter') or 'Not specified'}",
        f"- Week topic: {_week_label(batch)}",
        f"- Total points: {batch.get('total_points')}",
        f"- Status: {batch.get('status')}",
        "",
        "| Student | Score | Confidence | Reviewed | Warnings |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for submission in submissions:
        result = submission.get("grading_result") or {}
        warnings = "; ".join(result.get("warnings") or [])
        score = submission.get("score")
        max_score = submission.get("max_score")
        score_label = "Needs review" if score is None else f"{score:g} / {max_score:g}"
        lines.append(
            "| {student} | {score} | {confidence} | {reviewed} | {warnings} |".format(
                student=submission.get("student_name") or submission.get("student_identifier") or "Unassigned",
                score=score_label,
                confidence=f"{float(submission.get('confidence') or 0):.2f}",
                reviewed="Yes" if submission.get("teacher_reviewed") else "No",
                warnings=warnings or "None",
            )
        )
    for submission in submissions:
        lines.extend(_student_section(submission))
    return "\n".join(lines)


def _week_label(batch: dict[str, Any]) -> str:
    if not batch.get("week_number") and not batch.get("week_topic"):
        return "Not specified"
    return f"Week {batch.get('week_number') or '?'} - {batch.get('week_topic') or 'No focus'}"


def _student_section(submission: dict[str, Any]) -> list[str]:
    result = submission.get("grading_result") or {}
    name = submission.get("student_name") or submission.get("student_identifier") or "Unassigned student"
    lines = ["", f"## {name}", "", result.get("overall_feedback") or "No feedback yet.", ""]
    items = result.get("items") or []
    if items:
        lines.extend(["| Item | Student answer | Correct answer | Score | Feedback |", "| --- | --- | --- | ---: | --- |"])
        for item in items:
            lines.append(
                "| {number} | {student} | {correct} | {score} / {max_score} | {feedback} |".format(
                    number=item.get("item_number") or "",
                    student=item.get("student_answer") or "",
                    correct=item.get("correct_answer") or "",
                    score=item.get("score") if item.get("score") is not None else "",
                    max_score=item.get("max_score") if item.get("max_score") is not None else "",
                    feedback=item.get("feedback") or "",
                )
            )
    return lines
