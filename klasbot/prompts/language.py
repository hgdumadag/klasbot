from __future__ import annotations


FILIPINO_LANGUAGE_SUBJECTS = {
    "araling panlipunan",
    "filipino",
    "gmrc and ve",
    "makabansa",
}

FILIPINO_LANGUAGE_INSTRUCTION = (
    "Write primarily in Filipino/Tagalog, using subject-appropriate Filipino terms. "
    "Use Filipino for lesson-plan framework headings and labels when a Filipino framework is provided."
)

ENGLISH_LANGUAGE_INSTRUCTION = "Write in English only."


def is_filipino_language_subject(subject: str | None) -> bool:
    normalized = (subject or "").strip().casefold()
    return normalized in FILIPINO_LANGUAGE_SUBJECTS


def language_instruction_for_subject(subject: str | None) -> str:
    if is_filipino_language_subject(subject):
        return FILIPINO_LANGUAGE_INSTRUCTION
    return ENGLISH_LANGUAGE_INSTRUCTION
