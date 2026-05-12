from __future__ import annotations

from klasbot.prompts.assessment import build_assessment_prompt
from klasbot.prompts.lesson_plan import build_lesson_plan_prompt


def build_prompt(inputs: dict) -> str:
    if inputs["kind"] == "assessment":
        return build_assessment_prompt(inputs)
    return build_lesson_plan_prompt(inputs)
