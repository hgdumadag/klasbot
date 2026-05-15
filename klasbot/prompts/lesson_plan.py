from __future__ import annotations

import sqlite3

from klasbot import db
from klasbot.lesson_formats import (
    DEFAULT_LESSON_PLAN_FORMATS,
    localize_lesson_format_requirements,
    render_lesson_format_requirements,
)
from klasbot.prompts.language import is_filipino_language_subject, language_instruction_for_subject


FORMAT_DESCRIPTIONS = {
    "DLP": """Create a scripted Detailed Lesson Plan (DLP) suitable for new teachers or Classroom Observation Tool (COT) use.
The Procedures section must be written as Teacher Activity vs. Learner Activity.
Keep Remarks and Reflection blank for the teacher to complete after teaching.
Generate one practical teachable lesson for the selected week only.""",
    "SDLP": """Create a Semi-Detailed Lesson Plan (SDLP) using the 4As instructional format.
The SDLP should be practical for a one-session lesson and less scripted than a DLP, but still specific enough for classroom use.
Include clear teacher actions, expected learner actions, guide questions, timing per major procedure step, evaluation, and assignment.
Generate one practical teachable lesson for the selected week only.""",
    "DLL": """Create a Daily Lesson Log (DLL), which is a weekly lesson log spanning Monday to Friday for the selected week.
The DLL must distribute only the selected weekly focus and competencies across Monday to Friday.
Use concise entries that fit a weekly DLL table. Keep Remarks and Reflection blank for the teacher to complete after teaching.""",
}


def build_lesson_plan_prompt(inputs: dict) -> str:
    grade_levels = ", ".join(inputs.get("grade_levels") or ["Not specified"])
    resources = ", ".join(inputs.get("resources") or ["locally available classroom materials"])
    format_name = inputs.get("format") or "DLP"
    language_instruction = language_instruction_for_subject(inputs.get("subject"))
    curriculum_context = inputs.get("curriculum_context") or "No matching uploaded curriculum context was found. Use only the teacher inputs and do not invent DepEd codes."
    configured_template = _configured_requirements(format_name)
    if configured_template:
        requirements = render_lesson_format_requirements(
            configured_template,
            inputs,
            grade_levels,
            resources,
            curriculum_context,
        )
        requirements = _lesson_requirements_without_teacher_resources(requirements)
        if is_filipino_language_subject(inputs.get("subject")):
            requirements = localize_lesson_format_requirements(requirements)
        return f"""{_lesson_plan_system_instructions(language_instruction)}
{_format_description(format_name)}

Teacher inputs:
1. Subject: {inputs.get("subject") or "Not specified"}
2. Topic: {inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Format: {format_name}
5. Selected week: {inputs.get("week_number") or "Not specified"}

Uploaded curriculum context:
{curriculum_context}

Return markdown with exactly this structure:
{requirements}
"""
    generic_requirements = f"""# {format_name} Lesson Plan
## Overview
## Objectives
## Materials
## Procedure
## Assessment
## Adaptations
## Teacher Notes"""
    if is_filipino_language_subject(inputs.get("subject")):
        generic_requirements = f"""# {format_name} Banghay-Aralin
## Buod
## Mga Layunin
## Mga Kagamitan
## Pamamaraan
## Pagtataya
## Mga Pag-aangkop
## Tala ng Guro"""
    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Do not invent DepEd codes.
Use the uploaded curriculum context below as the source of truth when it is available.

Reference style: produce a practical {format_name} lesson plan with clear objectives, simple materials,
teacher and learner activities, assessment, and adaptations for multigrade or low-resource classrooms.
When weekly curriculum context is present, do not cover the full quarter. Generate only for the selected week.
For Mathematics, Science, or notation-heavy examples, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep surrounding explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.

Teacher inputs:
1. Subject: {inputs.get("subject") or "Not specified"}
2. Topic: {inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Format: {format_name}
5. Selected week: {inputs.get("week_number") or "Not specified"}

Uploaded curriculum context:
{curriculum_context}

Return markdown with exactly these headings:
{generic_requirements}
"""


def _lesson_plan_system_instructions(language_instruction: str) -> str:
    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Use the uploaded curriculum context below as the source of truth when it is available.
Do not invent DepEd codes. If an LC code is not present in the uploaded curriculum context, write "LC Code: Not specified in provided curriculum context."
Treat quarter curriculum context as background only. Treat the selected weekly focus and weekly competencies as the required scope.
Do not cover the full quarter. Generate only for the selected week.
Make the output practical for daily teaching: concrete teacher actions, learner actions, timing, formative checks, and remediation.
For Mathematics, Science, or notation-heavy examples, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep surrounding explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.
"""


def _configured_requirements(format_name: str) -> str | None:
    normalized = (format_name or "").upper()
    try:
        format_config = db.get_lesson_plan_format(normalized)
    except sqlite3.Error:
        format_config = None
    if format_config and format_config.get("requirements"):
        return str(format_config["requirements"])
    defaults = DEFAULT_LESSON_PLAN_FORMATS.get(normalized)
    return defaults["requirements"] if defaults else None


def _format_description(format_name: str) -> str:
    normalized = (format_name or "").upper()
    return FORMAT_DESCRIPTIONS.get(
        normalized,
        f"Create a practical {format_name} lesson plan suitable for classroom use.",
    )


def _lesson_requirements_without_teacher_resources(requirements: str) -> str:
    return (
        requirements.replace(
            "- List only the resources provided by the teacher and reasonable low-resource classroom materials derived from them.",
            "- List practical materials for a low-resource classroom.",
        )
        .replace(
            "Give a short follow-up task that reinforces the lesson and can be done with available home or classroom resources.",
            "Give a short follow-up task that reinforces the lesson.",
        )
    )


def build_sdlp_prompt(
    inputs: dict,
    grade_levels: str,
    resources: str,
    curriculum_context: str,
) -> str:
    language_instruction = language_instruction_for_subject(inputs.get("subject"))
    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Use the uploaded curriculum context below as the source of truth when it is available.
Do not invent DepEd codes. If an LC code is not present in the uploaded curriculum context, write "LC Code: Not specified in provided curriculum context."
Treat quarter curriculum context as background only. Treat the selected weekly focus and weekly competencies as the required scope.
Do not cover the full quarter. Generate only for the selected week.
Make the output practical for daily teaching: concrete teacher actions, learner actions, timing, formative checks, and remediation.
For Mathematics, Science, or notation-heavy examples, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep surrounding explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.

Create a Semi-Detailed Lesson Plan (SDLP) using the 4As instructional format.
The SDLP should be practical for a one-session lesson and less scripted than a DLP, but still specific enough for classroom use.
Include clear teacher actions, expected learner actions, guide questions, timing per major procedure step, evaluation, and assignment.

Teacher inputs:
1. Subject: {inputs.get("subject") or "Not specified"}
2. Topic: {inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Format: SDLP
5. Selected week: {inputs.get("week_number") or "Not specified"}

Uploaded curriculum context:
{curriculum_context}

Return markdown with exactly this structure:
# Semi-Detailed Lesson Plan (SDLP)
## Header
- Lesson Plan in: {inputs.get("subject") or "Not specified"} - {grade_levels}
- Quarter: {inputs.get("quarter") or "Not specified"}
- Time Allotment:

## I. Objectives
Start with: "At the end of the lesson, the learners are expected to:"
- Include measurable objectives aligned to the uploaded curriculum context.
- Include knowledge, skill/performance, application, and values/attitude objectives when appropriate.
- Include the LC Code only if it is present in the context; otherwise write "LC Code: Not specified in provided curriculum context."

## II. Subject Matter
- Topic:
- Key Concepts:
- Values Integration:
- Curriculum Alignment:
  - Content Standards:
  - Performance Standards:
  - Learning Competencies:

## III. Materials
- List practical materials for a low-resource classroom.

## IV. Procedure (4As)
Use the 4As sequence below. For each part, include the suggested time, Teacher's Activity, Learners' Activity, and guide questions where useful.

### A. Activity (Motivation)
- Time:
- Teacher's Activity:
- Learners' Activity:
- Guide Questions:

### B. Analysis
- Time:
- Teacher's Activity:
- Learners' Activity:
- Guide Questions:

### C. Abstraction
- Time:
- Teacher's Discussion:
- Key Points:
- Generalization:

### D. Application
- Time:
- Teacher's Activity:
- Learners' Activity:
- Group or Individual Task:

## V. Evaluation
Include an assessment suited to the lesson. If performance-based, include a simple checklist or rubric with criteria and Yes/No or score columns.

## VI. Assignment
Give a short follow-up task that reinforces the lesson and can be done with available home or classroom resources.

"""


def build_dlp_prompt(
    inputs: dict,
    grade_levels: str,
    resources: str,
    curriculum_context: str,
) -> str:
    language_instruction = language_instruction_for_subject(inputs.get("subject"))
    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Use the uploaded curriculum context below as the source of truth when it is available.
Do not invent DepEd codes. If an LC code is not present in the uploaded curriculum context, write "LC Code: Not specified in provided curriculum context."
Treat quarter curriculum context as background only. Treat the selected weekly focus and weekly competencies as the required scope.
Do not cover the full quarter. Generate only for the selected week.
Make the output practical for daily teaching: concrete teacher actions, learner actions, timing, formative checks, and remediation.
For Mathematics, Science, or notation-heavy examples, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep surrounding explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.

Create a scripted Detailed Lesson Plan (DLP) suitable for new teachers or Classroom Observation Tool (COT) use.
The Procedures section must be written as Teacher Activity vs. Learner Activity.
Keep Remarks and Reflection blank for the teacher to complete after teaching.

Teacher inputs:
1. Subject: {inputs.get("subject") or "Not specified"}
2. Topic: {inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Format: DLP
5. Selected week: {inputs.get("week_number") or "Not specified"}

Uploaded curriculum context:
{curriculum_context}

Return markdown with exactly this structure:
# Detailed Lesson Plan (DLP)
## I. Objectives
### Content Standards
### Performance Standards
### Learning Competencies/Objectives
- Include specific learning competencies/objectives from the uploaded curriculum context.
- Include the LC Code only if it is present in the context; otherwise write "LC Code: Not specified in provided curriculum context."

## II. Content
- State the specific topic or subject matter for the lesson.

## III. Learning Resources
- Teacher's Guides:
- Learner's Materials:
- Textbooks:
- Additional Materials from the LR Portal:
- Other Learning Resources:

## IV. Procedures
Use a markdown table with exactly these columns: Procedure Step | Teacher Activity | Learner Activity.
Include exactly these procedure steps:
A. Reviewing previous lesson/Presenting new lesson.
B. Establishing a purpose for the lesson.
C. Presenting examples/instances.
D. Discussing new concepts and practicing new skills #1.
E. Discussing new concepts and practicing new skills #2.
F. Developing mastery (Leads to Formative Assessment).
G. Finding practical applications of concepts.
H. Making generalizations and abstractions.
I. Evaluating learning.
J. Additional activities for application or remediation.

## V. Remarks

## VI. Reflection
### A. Number of learners who earned 80% in the evaluation

### B. Number of learners who require additional activities for remediation

### C. Did the remedial lessons work? Number of learners who caught up with the lesson

### D. Number of learners who continue to require remediation

### E. Which teaching strategies worked well? Why did these work?

### F. What difficulties did I encounter that my principal or supervisor can help me solve?

### G. What innovation or localized materials did I use/discover which I wish to share with other teachers?

"""


def build_dll_prompt(
    inputs: dict,
    grade_levels: str,
    resources: str,
    curriculum_context: str,
) -> str:
    language_instruction = language_instruction_for_subject(inputs.get("subject"))
    return f"""You are a DepEd-aligned teaching assistant for a GIDA school in the Philippines.
{language_instruction} Use the uploaded curriculum context below as the source of truth when it is available.
Do not invent DepEd codes. If an LC code is not present in the uploaded curriculum context, write "LC Code: Not specified in provided curriculum context."
Treat quarter curriculum context as background only. Treat the selected weekly focus and weekly competencies as the required scope.
Do not cover the full quarter. Generate only for the selected week.
Make the output practical for daily teaching: concrete teacher actions, learner actions, timing, formative checks, and remediation.
For Mathematics, Science, or notation-heavy examples, you may use valid LaTeX for formulas and equations. Use inline math as $...$ and display math as $$...$$. Keep surrounding explanations in teacher-readable prose, and avoid LaTeX when plain text is clearer.

Create a Daily Lesson Log (DLL), which is a weekly lesson log spanning Monday to Friday for the selected week.
The DLL must distribute only the selected weekly focus and competencies across Monday to Friday.
Use concise entries that fit a weekly DLL table. Keep Remarks and Reflection blank for the teacher to complete after teaching.

Teacher inputs:
1. Subject: {inputs.get("subject") or "Not specified"}
2. Topic: {inputs.get("topic") or "Not specified"}
3. Grade level(s): {grade_levels}
4. Format: DLL
5. Selected week: {inputs.get("week_number") or "Not specified"}

Uploaded curriculum context:
{curriculum_context}

Return markdown with exactly this structure:
# Daily Lesson Log (DLL)

## Header
- School:
- Teacher:
- Teaching Dates and Time:
- Grade Level: {grade_levels}
- Learning Area: {inputs.get("subject") or "Not specified"}
- Quarter: {inputs.get("quarter") or "Not specified"}

## Weekly DLL Matrix
Use markdown tables with exactly these columns: Section | Monday | Tuesday | Wednesday | Thursday | Friday.

### I. Objectives
Rows:
- A. Content Standards
- B. Performance Standards
- C. Learning Competencies/Objectives (Write the LC code for each)

### II. Content
Rows:
- Content

### III. Learning Resources
Rows:
- A. References
- 1. Teacher's Guide pages
- 2. Learner's Materials pages
- 3. Textbook pages
- 4. Additional Materials from Learning Resource (LR) portal
- B. Other Learning Resources

### IV. Procedures
Rows:
- A. Reviewing previous lesson or presenting the new lesson
- B. Establishing a purpose for the lesson
- C. Presenting examples/instances of the new lesson
- D. Discussing new concepts and practicing new skills #1
- E. Discussing new concepts and practicing new skills #2
- F. Developing mastery (Leads to Formative Assessment)
- G. Finding practical applications of concepts and skills in daily living
- H. Making generalizations and abstractions about the lesson
- I. Evaluating learning
- J. Additional activities for application or remediation

## V. Remarks

## VI. Reflection
Leave all reflection entries blank for teacher input.
Rows:
- A. No. of learners who earned 80% in the evaluation
- B. No. of learners who require additional activities for remediation who scored below 80%
- C. Did the remedial lessons work? No. of learners who have caught up with the lesson
- D. No. of learners who continue to require remediation
- E. Which of my teaching strategies worked well? Why did these work?
- F. What difficulties did I encounter which my principal or supervisor can help me solve?
- G. What innovation or localized materials did I use/discover which I wish to share with other teachers?

"""
