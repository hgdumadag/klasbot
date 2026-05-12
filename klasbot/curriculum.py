from __future__ import annotations

import re
import shutil
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from klasbot import db
from klasbot.config import CURRICULUM_UPLOAD_DIR


HEADER_RE = re.compile(
    r"GRADE\s+(?P<grade>\d+)\s*\W\s*QUARTER\s+(?P<quarter>\d+)\s*:\s*"
    r"(?P<domain>.*?)\s+Content\s+Content Standards"
    r"(?:(?!GRADE\s+\d+\s*\W\s*QUARTER).)*?Learning Competen(?:cy|cies)\s+The learners(?:…|:)",
    re.IGNORECASE | re.DOTALL,
)
MATH_HEADER_RE = re.compile(
    r"GRADE\s+(?P<grade>\d+)\s*\W\s*QUARTER\s+(?P<quarter>\d+)\s+CONTENT DOMAIN\s+CONTENT STANDARDS"
    r"(?:(?!GRADE\s+\d+\s*\W\s*QUARTER).)*?LEARNING COMPETENCIES\s+The learners\s*(?:…|\.\.\.)",
    re.IGNORECASE | re.DOTALL,
)
FILIPINO_HEADER_RE = re.compile(
    r"BAITANG\s+(?P<grade>\d+)\s*\W\s*(?P<markahan>UNANG|IKALAWANG|IKATLONG|IKAAPAT NA)\s+MARKAHAN",
    re.IGNORECASE,
)
FILIPINO_QUARTERS = {
    "UNANG": 1,
    "IKALAWANG": 2,
    "IKATLONG": 3,
    "IKAAPAT NA": 4,
}
MATH_DOMAINS = (
    "Number and Algebra",
    "Measurement and Geometry",
    "Data and Probability",
)
FILIPINO_DOMAINS = (
    "Kamalayang Ponolohikal",
    "Palabigkasan at Pag-aaral ng Salita",
    "Palabigkasan at Pag- aaral ng Salita",
    "Paglinang ng Talasalitaan",
    "Gramatika",
    "Pag-unawa at Pagsusuri ng Teksto",
    "Pagbuo ng Teksto",
    "Pakikinig at Pagbasa",
    "Pagsasalita at Pagsulat",
    "Panonood at Presentasyon",
)
FILIPINO_COMPETENCY_START_RE = re.compile(
    r"\b(?=(?:Na|Naka|Nai|Nasu|Napa|Nau|Nabi|Nagi|Nais|Natut|Nagagamit|Natutukoy|Nabibigkas|Nababasa|Nakasusulat|Nauunawaan|Naibibigay|Nakikilala|Naisasaayos|Nakabubuo|Nasusuri|Nakapagpapahayag|Nakapagsasalaysay|Nailalarawan|Naihahambing|Nailalapat|Natutugunan))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedUnit:
    grade_level: str
    quarter: int
    domain: str
    content: str
    content_standards: str
    learning_competencies: list[str]
    performance_standard: str
    suggested_tasks: str
    source_pages: str
    raw_text: str
    confidence: float
    warnings: list[str]


def infer_subject(filename: str) -> str:
    stem = Path(filename).stem
    match = re.search(r"MATATAG\s+(.+?)\s+CG\b", stem, re.IGNORECASE)
    if match:
        return _title_subject(match.group(1))
    return _title_subject(stem)


def ingest_pdf(
    *,
    source_path: Path,
    original_filename: str,
    subject: str | None,
    version_label: str | None,
    uploaded_by: int,
) -> dict[str, Any]:
    parsed = parse_curriculum_pdf(source_path)
    diagnostics = build_parse_diagnostics(parsed)
    clean_subject = (subject or infer_subject(original_filename)).strip()
    clean_version = (version_label or "").strip() or "Uploaded curriculum"

    CURRICULUM_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = _safe_filename(original_filename)

    with db.connect() as connection:
        connection.execute(
            "UPDATE curriculum_documents SET active = 0 WHERE subject = ?",
            (clean_subject,),
        )
        document_id = db.create_curriculum_document(
            connection,
            {
                "subject": clean_subject,
                "title": Path(original_filename).stem,
                "filename": original_filename,
                "stored_path": "",
                "version_label": clean_version,
                "uploaded_by": uploaded_by,
                "active": True,
                "parse_summary": diagnostics,
            },
        )
        stored_path = CURRICULUM_UPLOAD_DIR / f"{document_id}-{stored_name}"
        shutil.copyfile(source_path, stored_path)
        db.update_curriculum_document_path(connection, document_id, str(stored_path))
        db.replace_curriculum_units(connection, document_id, clean_subject, parsed)
        document = db.get_curriculum_document(connection, document_id)

    assert document is not None
    document["unit_count"] = len(parsed)
    document["parse_summary"] = diagnostics
    return document


def ingest_json(
    *,
    source_path: Path,
    uploaded_by: int | None = None,
) -> dict[str, Any]:
    data = json.loads(source_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Curriculum JSON must contain a document object and units list")
    document_payload = data.get("document")
    units_payload = data.get("units")
    if not isinstance(document_payload, dict) or not isinstance(units_payload, list):
        raise ValueError("Curriculum JSON must contain top-level 'document' and 'units'")

    subject = _required_text(document_payload, "subject")
    title = (document_payload.get("title") or source_path.stem).strip()
    version_label = (document_payload.get("version_label") or "Imported curriculum").strip()
    filename = (
        document_payload.get("filename")
        or document_payload.get("source_filename")
        or source_path.name
    )
    parsed_units = [_parsed_unit_from_json(unit, index) for index, unit in enumerate(units_payload)]
    parse_summary = _json_parse_summary(document_payload, parsed_units)

    with db.connect() as connection:
        connection.execute(
            "UPDATE curriculum_documents SET active = 0 WHERE subject = ?",
            (subject,),
        )
        document_id = db.create_curriculum_document(
            connection,
            {
                "subject": subject,
                "title": title,
                "filename": str(filename),
                "stored_path": str(source_path),
                "version_label": version_label,
                "uploaded_by": uploaded_by,
                "active": True,
                "parse_summary": parse_summary,
            },
        )
        db.replace_curriculum_units(connection, document_id, subject, parsed_units)
        document = db.get_curriculum_document(connection, document_id)

    assert document is not None
    document["unit_count"] = len(parsed_units)
    document["parse_summary"] = parse_summary
    return document


def parse_curriculum_pdf(path: Path) -> list[ParsedUnit]:
    reader = PdfReader(str(path))
    page_texts = [_clean_page_text(page.extract_text() or "") for page in reader.pages]
    page_offsets: list[tuple[int, int]] = []
    cursor = 0
    chunks: list[str] = []
    for index, text in enumerate(page_texts, start=1):
        page_offsets.append((cursor, index))
        chunks.append(text)
        cursor += len(text) + 1
    full_text = "\n".join(chunks)

    matches = list(HEADER_RE.finditer(full_text))
    if not matches:
        math_units = _parse_math_units(full_text, page_offsets)
        if math_units:
            return math_units
        return _parse_filipino_units(full_text, page_offsets)

    units: list[ParsedUnit] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)
        raw_text = _normalize_space(full_text[match.start() : next_start])
        body = full_text[match.end() : next_start]
        page_start = _page_for_offset(page_offsets, match.start())
        page_end = _page_for_offset(page_offsets, max(match.end(), next_start - 1))
        units.append(
            _parse_unit(
                grade=match.group("grade"),
                quarter=int(match.group("quarter")),
                domain=_normalize_space(match.group("domain")),
                body=body,
                source_pages=f"{page_start}-{page_end}" if page_start != page_end else str(page_start),
                raw_text=raw_text,
            )
        )
    return units


def _parse_math_units(full_text: str, page_offsets: list[tuple[int, int]]) -> list[ParsedUnit]:
    matches = list(MATH_HEADER_RE.finditer(full_text))
    units: list[ParsedUnit] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)
        raw_text = _normalize_space(full_text[match.start() : next_start])
        body = full_text[match.end() : next_start]
        page_start = _page_for_offset(page_offsets, match.start())
        page_end = _page_for_offset(page_offsets, max(match.end(), next_start - 1))
        units.append(
            _parse_math_unit(
                grade=match.group("grade"),
                quarter=int(match.group("quarter")),
                body=body,
                source_pages=f"{page_start}-{page_end}" if page_start != page_end else str(page_start),
                raw_text=raw_text,
            )
        )
    return units


def _parse_filipino_units(full_text: str, page_offsets: list[tuple[int, int]]) -> list[ParsedUnit]:
    matches = list(FILIPINO_HEADER_RE.finditer(full_text))
    units: list[ParsedUnit] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)
        raw_text = _normalize_space(full_text[match.start() : next_start])
        body = full_text[match.end() : next_start]
        page_start = _page_for_offset(page_offsets, match.start())
        page_end = _page_for_offset(page_offsets, max(match.end(), next_start - 1))
        units.append(
            _parse_filipino_unit(
                grade=match.group("grade"),
                quarter=FILIPINO_QUARTERS[_normalize_space(match.group("markahan")).upper()],
                markahan=_normalize_space(match.group("markahan")).title(),
                body=body,
                source_pages=f"{page_start}-{page_end}" if page_start != page_end else str(page_start),
                raw_text=raw_text,
            )
        )
    return units


def build_parse_diagnostics(units: list[ParsedUnit]) -> dict[str, Any]:
    warnings: list[str] = []
    seen_by_grade: dict[str, set[int]] = {}
    for unit in units:
        seen_by_grade.setdefault(unit.grade_level, set()).add(unit.quarter)
        for warning in unit.warnings:
            warnings.append(f"{unit.grade_level} Q{unit.quarter} {unit.domain}: {warning}")

    for grade_level in sorted(seen_by_grade, key=_grade_sort_key):
        missing = sorted(set(range(1, 5)) - seen_by_grade[grade_level])
        if missing:
            warnings.append(f"{grade_level}: missing quarter(s) {', '.join(str(item) for item in missing)}")

    confidences = [unit.confidence for unit in units]
    low_confidence_units = [
        {
            "grade_level": unit.grade_level,
            "quarter": unit.quarter,
            "domain": unit.domain,
            "confidence": unit.confidence,
            "warnings": unit.warnings,
        }
        for unit in units
        if unit.confidence < 0.8
    ]
    return {
        "unit_count": len(units),
        "grade_count": len(seen_by_grade),
        "average_confidence": round(sum(confidences) / len(confidences), 2) if confidences else 0,
        "low_confidence_count": len(low_confidence_units),
        "warning_count": len(warnings),
        "warnings": warnings[:20],
        "low_confidence_units": low_confidence_units[:20],
    }


def _parsed_unit_from_json(unit: Any, index: int) -> ParsedUnit:
    if not isinstance(unit, dict):
        raise ValueError(f"Unit #{index + 1} must be an object")
    competencies = unit.get("competencies") or []
    if not isinstance(competencies, list):
        raise ValueError(f"Unit #{index + 1} competencies must be a list")
    competency_texts: list[str] = []
    for comp_index, competency in enumerate(competencies, start=1):
        if not isinstance(competency, dict):
            raise ValueError(f"Unit #{index + 1} competency #{comp_index} must be an object")
        text = str(competency.get("competency_text") or "").strip()
        if text:
            competency_texts.append(text)

    warnings = unit.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]

    parsed = ParsedUnit(
        grade_level=_required_text(unit, "grade_level"),
        quarter=int(unit.get("quarter")),
        domain=_required_text(unit, "domain"),
        content=str(unit.get("content") or "").strip(),
        content_standards=str(unit.get("content_standards") or "").strip(),
        learning_competencies=competency_texts,
        performance_standard=str(unit.get("performance_standard") or "").strip(),
        suggested_tasks=str(unit.get("suggested_tasks") or "").strip(),
        source_pages=str(unit.get("source_pages") or "").strip(),
        raw_text=str(unit.get("raw_text") or "").strip(),
        confidence=float(unit.get("confidence") or 0),
        warnings=[str(warning).strip() for warning in warnings if str(warning).strip()],
    )
    validation_warnings = _unit_warnings(
        domain=parsed.domain,
        content=parsed.content,
        content_standards=parsed.content_standards,
        competencies=parsed.learning_competencies,
        performance_standard=parsed.performance_standard,
        suggested_tasks="not applicable" if not parsed.suggested_tasks else parsed.suggested_tasks,
        raw_text=parsed.raw_text
        or " ".join(
            [
                parsed.content,
                parsed.content_standards,
                parsed.performance_standard,
                " ".join(parsed.learning_competencies),
            ]
        ),
    )
    merged_warnings = _dedupe_preserve_order([*parsed.warnings, *validation_warnings])
    confidence = parsed.confidence if parsed.confidence > 0 else _unit_confidence(merged_warnings)
    return ParsedUnit(
        grade_level=parsed.grade_level,
        quarter=parsed.quarter,
        domain=parsed.domain,
        content=parsed.content,
        content_standards=parsed.content_standards,
        learning_competencies=parsed.learning_competencies,
        performance_standard=parsed.performance_standard,
        suggested_tasks=parsed.suggested_tasks,
        source_pages=parsed.source_pages,
        raw_text=parsed.raw_text,
        confidence=round(max(0.0, min(1.0, confidence)), 2),
        warnings=merged_warnings,
    )


def _json_parse_summary(document_payload: dict[str, Any], units: list[ParsedUnit]) -> dict[str, Any]:
    supplied = document_payload.get("parse_summary")
    generated = build_parse_diagnostics(units)
    if not isinstance(supplied, dict):
        return generated
    supplied_warnings = supplied.get("warnings") if isinstance(supplied.get("warnings"), list) else []
    warnings = _dedupe_preserve_order([*generated["warnings"], *[str(item) for item in supplied_warnings]])
    return {
        "unit_count": len(units),
        "grade_count": generated["grade_count"],
        "average_confidence": generated["average_confidence"],
        "low_confidence_count": generated["low_confidence_count"],
        "warning_count": len(warnings),
        "warnings": warnings[:20],
        "low_confidence_units": generated["low_confidence_units"],
    }


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"Missing required field: {key}")
    return value


def build_curriculum_context(params: dict[str, Any]) -> str:
    grade_level = params.get("grade_level") or _first_grade(params.get("grade_levels"))
    context = db.get_curriculum_context(
        grade_level=grade_level,
        subject=params.get("subject") or "",
        quarter=params.get("quarter"),
        topic=params.get("topic") or "",
    )
    if not context:
        return ""

    week_number = params.get("week_number")
    if week_number in (None, ""):
        raise ValueError("Select a pacing week before generating from the active curriculum.")
    weekly_context = db.get_curriculum_week_context(
        grade_level=params.get("grade_level") or _first_grade(params.get("grade_levels")),
        subject=params.get("subject") or "",
        quarter=params.get("quarter"),
        topic=params.get("topic") or "",
        week_number=week_number,
    )
    if not weekly_context:
        raise ValueError("Selected pacing week was not found for this curriculum topic.")

    competencies = "\n".join(f"- {item['competency_text']}" for item in context["competencies"])
    week = weekly_context["week"]
    weekly_competencies = "\n".join(
        f"- {item['competency_text']}" for item in week["competencies"]
    )
    return f"""Source: {context['document_title']} ({context['version_label']}), pages {context['source_pages']}
Subject: {context['subject']}
Grade: {context['grade_level']}
Quarter: {context['quarter']}
Topic/Domain: {context['domain']}
Parse Confidence: {context.get('confidence', 0):.2f}

Quarter curriculum context (background only):
Content: {context['content']}
Content Standards: {context['content_standards']}
Quarter Learning Competencies:
{competencies or "- Not specified"}
Performance Standard: {context['performance_standard']}
Suggested Performance Tasks: {context['suggested_tasks']}

Selected weekly focus (required generation scope):
Week: {week['week_number']}
Focus: {week['focus']}
Weekly Competencies:
{weekly_competencies or "- No new competency assigned; use this week for review, remediation, enrichment, or practice aligned to the quarter context."}
Admin Notes: {week['notes'] or "None"}
"""


def _parse_unit(
    *,
    grade: str,
    quarter: int,
    domain: str,
    body: str,
    source_pages: str,
    raw_text: str,
) -> ParsedUnit:
    performance_split = re.split(r"\bPerformance Standard\b", body, maxsplit=1)
    before_performance = performance_split[0]
    after_performance = performance_split[1] if len(performance_split) > 1 else ""

    task_split = re.split(r"\bSuggested Performance Tasks?\b|\bSuggested Performance Task/s\b", after_performance, maxsplit=1)
    performance_standard = _normalize_space(task_split[0]) if task_split else ""
    suggested_tasks = _normalize_space(task_split[1]) if len(task_split) > 1 else ""

    segments = [_normalize_space(segment) for segment in re.split(r"\n\s*\n", before_performance) if segment.strip()]
    content = segments[0] if segments else ""
    content_standards = segments[1] if len(segments) > 1 else ""
    competencies_text = " ".join(segments[2:]) if len(segments) > 2 else ""
    competencies = _numbered_items(competencies_text)
    if not competencies:
        content, content_standards, competencies = _split_numbered_sections(before_performance)
    if not competencies and competencies_text:
        competencies = [competencies_text]
    warnings = _unit_warnings(
        domain=domain,
        content=content,
        content_standards=content_standards,
        competencies=competencies,
        performance_standard=performance_standard,
        suggested_tasks=suggested_tasks,
        raw_text=raw_text,
    )
    confidence = _unit_confidence(warnings)

    return ParsedUnit(
        grade_level=f"Grade {grade}",
        quarter=quarter,
        domain=domain,
        content=content,
        content_standards=content_standards,
        learning_competencies=competencies,
        performance_standard=performance_standard,
        suggested_tasks=suggested_tasks,
        source_pages=source_pages,
        raw_text=raw_text,
        confidence=confidence,
        warnings=warnings,
    )


def _parse_math_unit(
    *,
    grade: str,
    quarter: int,
    body: str,
    source_pages: str,
    raw_text: str,
) -> ParsedUnit:
    performance_split = re.split(r"\bPerformance Standards\b", body, maxsplit=1)
    before_performance = performance_split[0]
    performance_standard = _normalize_space(performance_split[1]) if len(performance_split) > 1 else ""
    content, content_standards, competencies = _split_numbered_sections(before_performance)
    domain = " / ".join(_extract_known_domains(before_performance, MATH_DOMAINS))
    if not domain:
        domain = f"Quarter {quarter} Mathematics"
    if not content:
        content = domain
    warnings = _unit_warnings(
        domain=domain,
        content=content,
        content_standards=content_standards,
        competencies=competencies,
        performance_standard=performance_standard,
        suggested_tasks="not applicable",
        raw_text=raw_text,
    )
    return ParsedUnit(
        grade_level=f"Grade {grade}",
        quarter=quarter,
        domain=domain,
        content=content,
        content_standards=content_standards,
        learning_competencies=competencies,
        performance_standard=performance_standard,
        suggested_tasks="",
        source_pages=source_pages,
        raw_text=raw_text,
        confidence=_unit_confidence(warnings),
        warnings=warnings,
    )


def _parse_filipino_unit(
    *,
    grade: str,
    quarter: int,
    markahan: str,
    body: str,
    source_pages: str,
    raw_text: str,
) -> ParsedUnit:
    content_standard = _between(body, "Pamantayang Pangnilalaman", "Pamantayan sa Pagganap")
    performance_standard = _between(body, "Pamantayan sa Pagganap", "SUB-DOMEYN")
    competencies_text = _after(body, "SUB-DOMEYN")
    domains = _extract_known_domains(competencies_text, FILIPINO_DOMAINS)
    normalized_domains = _dedupe_preserve_order([_normalize_filipino_domain(item) for item in domains])
    domain = " / ".join(normalized_domains[:4])
    if len(normalized_domains) > 4:
        domain = f"{domain} / More"
    if not domain:
        domain = f"{markahan} Markahan"
    competencies = _filipino_competencies(competencies_text)
    warnings = _unit_warnings(
        domain=domain,
        content=domain,
        content_standards=content_standard,
        competencies=competencies,
        performance_standard=performance_standard,
        suggested_tasks="not applicable",
        raw_text=raw_text,
    )
    return ParsedUnit(
        grade_level=f"Grade {grade}",
        quarter=quarter,
        domain=domain,
        content=domain,
        content_standards=content_standard,
        learning_competencies=competencies,
        performance_standard=performance_standard,
        suggested_tasks="",
        source_pages=source_pages,
        raw_text=raw_text,
        confidence=_unit_confidence(warnings),
        warnings=warnings,
    )


def _unit_warnings(
    *,
    domain: str,
    content: str,
    content_standards: str,
    competencies: list[str],
    performance_standard: str,
    suggested_tasks: str,
    raw_text: str,
) -> list[str]:
    warnings: list[str] = []
    if not domain:
        warnings.append("missing topic/domain")
    if "Content Standards" in domain:
        warnings.append("topic/domain may include extra table text")
    if not content:
        warnings.append("missing content topics")
    if not content_standards:
        warnings.append("missing content standards")
    if not competencies:
        warnings.append("missing learning competencies")
    if not performance_standard:
        warnings.append("missing performance standard")
    if not suggested_tasks:
        warnings.append("missing suggested performance tasks")
    if len(raw_text) < 400:
        warnings.append("parsed unit text is unusually short")
    if len(competencies) > 150:
        warnings.append("learning competency count is unusually high")
    return warnings


def _unit_confidence(warnings: list[str]) -> float:
    penalty = 0.12 * len(warnings)
    if any("missing learning competencies" in warning for warning in warnings):
        penalty += 0.2
    if any("topic/domain may include" in warning for warning in warnings):
        penalty += 0.15
    return round(max(0.0, min(1.0, 1.0 - penalty)), 2)


def _numbered_items(text: str) -> list[str]:
    matches = list(re.finditer(r"(?:^|\s)(\d+)\.\s+", text))
    items: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        item = _normalize_space(text[start:end])
        if item:
            items.append(item)
    return items


def _filipino_competencies(text: str) -> list[str]:
    cleaned = re.sub(r"\b(?:PK|PS|PB|Psu|PN)\b", " ", text)
    cleaned = re.sub(r"[✓•●]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    starts = [match.start() for match in FILIPINO_COMPETENCY_START_RE.finditer(cleaned)]
    items: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(cleaned)
        item = _normalize_space(cleaned[start:end])
        if item and len(item) > 12 and not item.upper().startswith("SUB-DOMEYN"):
            items.append(item)
    return _dedupe_preserve_order(items)


def _split_numbered_sections(text: str) -> tuple[str, str, list[str]]:
    items = _numbered_items(text)
    if not items:
        return _normalize_space(text), "", []

    competency_index = len(items)
    for index, item in enumerate(items):
        if index >= 2 and _looks_like_competency(item):
            competency_index = index
            break

    pre_competency = items[:competency_index]
    competencies = items[competency_index:]
    standards_index = len(pre_competency)
    for index, item in enumerate(pre_competency):
        if _looks_like_standard(item):
            standards_index = index
            break

    content = " ".join(f"{index}. {item}" for index, item in enumerate(pre_competency[:standards_index], start=1))
    standards = " ".join(
        f"{index}. {item}" for index, item in enumerate(pre_competency[standards_index:], start=1)
    )
    return content, standards, competencies


def _extract_known_domains(text: str, domains: tuple[str, ...]) -> list[str]:
    normalized_text = _normalize_space(text).lower()
    found: list[str] = []
    for domain in domains:
        if _normalize_space(domain).lower() in normalized_text:
            found.append(domain)
    return _dedupe_preserve_order(found)


def _between(text: str, start_label: str, end_label: str) -> str:
    start = re.search(re.escape(start_label), text, re.IGNORECASE)
    if not start:
        return ""
    end = re.search(re.escape(end_label), text[start.end() :], re.IGNORECASE)
    if not end:
        return _normalize_space(text[start.end() :])
    return _normalize_space(text[start.end() : start.end() + end.start()])


def _after(text: str, label: str) -> str:
    match = re.search(re.escape(label), text, re.IGNORECASE)
    return text[match.end() :] if match else text


def _normalize_filipino_domain(domain: str) -> str:
    return domain.replace("Pag- aaral", "Pag-aaral")


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = _normalize_space(value).lower()
        if key and key not in seen:
            seen.add(key)
            result.append(_normalize_space(value))
    return result


def _looks_like_competency(item: str) -> bool:
    first_word = re.match(r"[A-Za-z]+", item)
    if first_word and first_word.group(0)[:1].islower():
        return True
    verbs = {
        "apply",
        "classify",
        "compare",
        "conduct",
        "describe",
        "differentiate",
        "discuss",
        "draw",
        "explain",
        "explore",
        "gather",
        "identify",
        "interpret",
        "investigate",
        "make",
        "observe",
        "participate",
        "recognize",
        "research",
        "use",
        "write",
    }
    return bool(first_word and first_word.group(0).lower() in verbs)


def _looks_like_standard(item: str) -> bool:
    lowered = f" {item.lower()} "
    indicators = (" is ", " are ", " can ", " have ", " has ", " leads ", " determine ", " provides ")
    return item.endswith(".") or any(indicator in lowered for indicator in indicators)


def _clean_page_text(text: str) -> str:
    text = re.sub(r"MATATAG Curriculum:.*?August 2023\s*", "", text)
    text = re.sub(r"Page\s+\d+\s+of\s+\d+\s*", "", text)
    return text.strip()


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip("-")
    return cleaned or "curriculum.pdf"


def _title_subject(value: str) -> str:
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.title() if value.isupper() else value


def _page_for_offset(page_offsets: list[tuple[int, int]], offset: int) -> int:
    page = 1
    for page_offset, page_number in page_offsets:
        if page_offset > offset:
            break
        page = page_number
    return page


def _grade_sort_key(grade_level: str) -> int:
    match = re.search(r"\d+", grade_level)
    return int(match.group(0)) if match else 999


def _first_grade(grade_levels: list[str] | None) -> str:
    return grade_levels[0] if grade_levels else ""
