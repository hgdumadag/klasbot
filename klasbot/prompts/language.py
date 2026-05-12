from __future__ import annotations


FILIPINO_LANGUAGE_SUBJECTS = {
    "araling panlipunan",
    "filipino",
    "gmrc and ve",
    "makabansa",
}

FILIPINO_LANGUAGE_INSTRUCTION = (
    "Write primarily in Filipino/Tagalog, using subject-appropriate Filipino terms. "
    "Keep required format headings unchanged when specified."
)

ENGLISH_LANGUAGE_INSTRUCTION = "Write in English only."


def language_instruction_for_subject(subject: str | None) -> str:
    normalized = (subject or "").strip().casefold()
    if normalized in FILIPINO_LANGUAGE_SUBJECTS:
        return FILIPINO_LANGUAGE_INSTRUCTION
    return ENGLISH_LANGUAGE_INSTRUCTION
