from __future__ import annotations

from klasbot.prompts.language import language_instruction_for_subject


DIFFICULTY_GUIDANCE = {
    "easy": (
        # TODO(learning-mode): describe what "Easy" means for a DepEd GIDA classroom.
        # Suggested levers: recall vs. application, single-step vs. multi-step,
        # scaffolded directions, familiar vocabulary, obvious distractors.
        "Calibrate the questions to the easy difficulty level."
    ),
    "normal": (
        # TODO(learning-mode): describe what "Normal" means (the default).
        "Calibrate the questions to the normal/grade-level difficulty."
    ),
    "hard": (
        # TODO(learning-mode): describe what "Hard" means for stretch items
        # still aligned to the selected weekly competency.
        "Calibrate the questions to the hard difficulty level."
    ),
}


def build_assessment_prompt(inputs: dict) -> str:
    grade_levels = ", ".join(inputs.get("grade_levels") or ["Not specified"])
    resources = ", ".join(inputs.get("resources") or ["paper and pencil"])
    format_name = inputs.get("format") or "quiz"
    difficulty = (inputs.get("difficulty") or "normal").lower()
    if difficulty not in DIFFICULTY_GUIDANCE:
        difficulty = "normal"
    difficulty_guidance = DIFFICULTY_GUIDANCE[difficulty]
    language_instruction = language_instruction_for_subject(inputs.get("subject"))
    curriculum_context = inputs.get("curriculum_context") or "No matching uploaded curriculum context was found. Use only the teacher inputs and do not invent DepEd codes."
    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Make the assessment grade-appropriate and usable without internet.
Use only the resources listed by the teacher. Do not invent DepEd codes.
Use the uploaded curriculum context below as the source of truth when it is available.
Treat quarter curriculum context as background only. Treat the selected weekly focus and weekly competencies as the required assessment scope.
Do not cover the full quarter. Generate only for the selected week.
Make remediation concrete and usable in a low-resource classroom.
For Mathematics, Science, or notation-heavy questions, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep directions and explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.

Teacher inputs:
1. Subject: {inputs.get("subject") or "Not specified"}
2. Topic: {inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Available resources: {resources}
5. Assessment format: {format_name}
6. Selected week: {inputs.get("week_number") or "Not specified"}
7. Difficulty: {difficulty.title()} - {difficulty_guidance}

Uploaded curriculum context:
{curriculum_context}

Return markdown with exactly these headings:
# {format_name.title()} Assessment
## Directions
## Questions
## Answer Key
## Rubric
## Remediation
"""
