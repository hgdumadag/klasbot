from __future__ import annotations

from typing import Any

from klasbot.prompts.language import language_instruction_for_subject


TEACHING_AID_TYPES = {
    "worked_example": {
        "label": "Worked Example",
        "instructions": """Create one fully solved classroom example.
Include these markdown headings exactly:
# Worked Example
## Problem
## Given
## Concept or Theorem Used
## Step-by-Step Solution
## Final Answer
## Teacher Talk Track
## Common Learner Mistake
## Similar Practice Item
The similar practice item must include the answer.""",
    },
    "guided_practice": {
        "label": "Guided Practice",
        "instructions": """Create 3-5 scaffolded guided practice items.
For each item include the prompt, teacher cue, expected learner response, quick check, and answer.""",
    },
    "answer_key": {
        "label": "Answer Key",
        "instructions": """Create an answer key for activities, practice items, or evaluation questions found in the lesson.
Include short rationales or solution notes. If the lesson has too few items, add clearly labeled teacher-ready sample answers aligned to the lesson.""",
    },
    "board_notes": {
        "label": "Board Notes",
        "instructions": """Create concise board-ready notes.
Include definitions, key reminders, a short example, diagram instructions when useful, and a closing check question.""",
    },
    "remediation": {
        "label": "Remediation",
        "instructions": """Create a reteaching support activity.
Include the misconception to address, simpler explanation, easier examples, guided prompts, learner task, formative check, and exit ticket.""",
    },
}


def teaching_aid_label(aid_type: str) -> str:
    return TEACHING_AID_TYPES.get(aid_type, {}).get("label", "Teaching Aid")


def valid_teaching_aid_types() -> set[str]:
    return set(TEACHING_AID_TYPES)


def build_teaching_aid_prompt(parent_output: dict[str, Any], inputs: dict[str, Any]) -> str:
    aid_type = str(inputs.get("aid_type") or "")
    aid_config = TEACHING_AID_TYPES.get(aid_type)
    if not aid_config:
        raise ValueError("Unsupported teaching aid type")

    parent_inputs = parent_output.get("inputs") or {}
    subject = parent_output.get("subject") or parent_inputs.get("subject") or "Not specified"
    language_instruction = language_instruction_for_subject(subject)
    resources = ", ".join(parent_output.get("resources") or parent_inputs.get("resources") or ["locally available classroom materials"])
    grade_levels = ", ".join(parent_output.get("grade_levels") or parent_inputs.get("grade_levels") or ["Not specified"])
    source_section = str(inputs.get("source_section") or "").strip()
    custom_request = str(inputs.get("custom_request") or "").strip()
    curriculum_context = inputs.get("curriculum_context") or "No matching uploaded curriculum context was found. Use the parent lesson and teacher inputs only."

    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Create classroom-usable Teaching Aids for a teacher. Do not generate another lesson plan.
Use the saved lesson plan, selected weekly curriculum context, and available resources as the source of truth.
Treat quarter curriculum context as background only when present. Use the selected weekly focus and competencies as the required scope.
For Mathematics, Science, or notation-heavy examples, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep surrounding explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.

Teaching Aid type: {aid_config["label"]}
Teaching Aid requirements:
{aid_config["instructions"]}

Parent lesson metadata:
1. Subject: {subject}
2. Topic: {parent_output.get("topic") or parent_inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Format: {parent_output.get("format") or parent_inputs.get("format") or "Not specified"}
5. Selected week: {parent_output.get("week_number") or parent_inputs.get("week_number") or "Not specified"}
6. Available resources: {resources}

Uploaded curriculum context:
{curriculum_context}

Selected/source section:
{source_section or "No specific section selected. Use the whole saved lesson as context."}

Teacher custom request:
{custom_request or "None"}

Saved lesson plan markdown:
{parent_output.get("content_md") or ""}

Return only the Teaching Aid markdown. Make it immediately usable in class with concrete teacher actions, learner responses, checks for understanding, and answers where applicable.
"""
