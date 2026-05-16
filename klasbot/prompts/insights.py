from __future__ import annotations


def build_insights_messages(class_record: dict, dashboard: dict) -> list[dict[str, str]]:
    target = float(dashboard.get("target_percentage") or 75.0)

    grade = class_record.get("grade_level", "")
    section = class_record.get("section", "")
    grade_section = f"Grade {grade}" + (f"-{section}" if section else "")
    header_lines = [
        f"Class: {class_record.get('name', 'Unknown')}",
        f"Grade/Section: {grade_section}",
        f"Subject: {class_record.get('subject', '')}",
        f"School Year: {class_record.get('school_year', '')}",
        f"Passing Target: {target:.0f}%",
    ]

    metrics_lines = [
        f"Students: {dashboard.get('student_count', 0)}",
        f"Assessments: {dashboard.get('assessment_count', 0)}",
        f"Class Average: {_fmt_pct(dashboard.get('class_average'))}",
        f"Highest Assessment Average: {_fmt_pct(dashboard.get('highest_assessment_average'))}",
        f"Lowest Assessment Average: {_fmt_pct(dashboard.get('lowest_assessment_average'))}",
        f"Students Below Target: {dashboard.get('below_target_count', 0)}",
        f"Students with Missing/Absent Issues: {dashboard.get('missing_or_absent_count', 0)}",
    ]

    students = dashboard.get("students") or []
    watch_students = [
        s for s in students
        if s.get("status_indicator") == "Watch"
        or (s.get("average_percentage") is not None and float(s["average_percentage"]) < target)
    ]
    watch_students.sort(key=lambda s: float(s.get("average_percentage") or 0))
    watch_students = watch_students[:15]

    watch_lines = []
    for s in watch_students:
        name = s.get("display_name", "Unknown")
        avg = _fmt_pct(s.get("average_percentage"))
        absent = int(s.get("absent_count") or 0)
        missing = int(s.get("missing_count") or 0)
        results = [r for r in (s.get("assessment_results") or []) if r.get("percentage") is not None]
        results.sort(key=lambda r: float(r["percentage"]))
        weak = ", ".join(f"{r['title']} ({_fmt_pct(r['percentage'])})" for r in results[:2])
        line = f"- {name}: avg {avg}, absent {absent}, missing {missing}"
        if weak:
            line += f"; weakest: {weak}"
        watch_lines.append(line)

    scored_students = [s for s in students if s.get("average_percentage") is not None]
    scored_students.sort(key=lambda s: float(s["average_percentage"]), reverse=True)
    top_lines = [
        f"- {s.get('display_name', 'Unknown')}: {_fmt_pct(s.get('average_percentage'))}"
        for s in scored_students[:3]
    ]

    assessments = dashboard.get("assessments") or []
    scored_assessments = [a for a in assessments if a.get("average_percentage") is not None]
    scored_assessments.sort(key=lambda a: float(a["average_percentage"]))
    concern_lines = []
    for a in scored_assessments[:3]:
        concern_lines.append(
            f"- {a.get('title', 'Unknown')} ({a.get('assessment_type', '')})"
            f" on {a.get('assessment_date', '')}"
            f": avg {_fmt_pct(a.get('average_percentage'))}"
            f", completion {a.get('completion_count', '?')}/{dashboard.get('student_count', '?')}"
        )

    recent_lines = [
        f"- {a.get('title', 'Unknown')} ({a.get('assessment_type', '')}) on {a.get('assessment_date', '')}: avg {_fmt_pct(a.get('average_percentage'))}"
        for a in assessments[:3]
    ]

    user_content = "\n\n".join([
        "CLASS INFORMATION\n" + "\n".join(header_lines),
        "CLASS METRICS\n" + "\n".join(metrics_lines),
        f"STUDENTS TO WATCH ({len(watch_students)} of {len(students)} students)\n"
        + ("\n".join(watch_lines) if watch_lines else "None — all students are on track."),
        "TOP PERFORMERS\n" + ("\n".join(top_lines) if top_lines else "No scores recorded yet."),
        "LOWEST-PERFORMING ASSESSMENTS\n" + ("\n".join(concern_lines) if concern_lines else "No assessment averages yet."),
        "RECENT ASSESSMENTS\n" + ("\n".join(recent_lines) if recent_lines else "No assessments yet."),
    ])

    system = """You are KlasBot Insights, a concise teaching assistant that analyzes class performance data and produces actionable briefings for teachers.

Rules:
- Always produce exactly four markdown sections with these exact headings: ## Class Snapshot, ## Students to Watch, ## Assessment Concerns, ## Suggested Actions
- Each section should have 3–6 bullet points maximum. Be specific — reference student names, assessment names, and percentages from the data.
- Frame Suggested Actions as concrete teaching moves the teacher can try this week: re-teaching a topic, pairing students, scheduling a 1-on-1 check-in, re-administering a short quiz, etc.
- Never invent students, assessments, or numbers not in the data provided.
- If a section has nothing to flag (e.g., all students are on track, or no assessments recorded), say so plainly in one bullet. Do not pad with generic advice.
- Synthesize and interpret: "6 of 10 students scored below 75% on Quiz 3 — this topic may need re-teaching" is more useful than just restating numbers.
- Keep the entire output under 400 words."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def _fmt_pct(value) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.1f}%"
