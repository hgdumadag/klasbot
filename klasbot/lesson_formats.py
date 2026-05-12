from __future__ import annotations

from collections import defaultdict
from typing import Any


DEFAULT_LESSON_PLAN_FORMATS: dict[str, dict[str, str]] = {
    "DLP": {
        "title": "Detailed Lesson Plan",
        "requirements": """# Detailed Lesson Plan (DLP)
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
""",
    },
    "SDLP": {
        "title": "Semi-Detailed Lesson Plan",
        "requirements": """# Semi-Detailed Lesson Plan (SDLP)
## Header
- Lesson Plan in: {subject} - {grade_levels}
- Quarter: {quarter}
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
- List only the resources provided by the teacher and reasonable low-resource classroom materials derived from them.

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
""",
    },
    "DLL": {
        "title": "Daily Lesson Log",
        "requirements": """# Daily Lesson Log (DLL)

## Header
- School:
- Teacher:
- Teaching Dates and Time:
- Grade Level: {grade_levels}
- Learning Area: {subject}
- Quarter: {quarter}

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
""",
    },
}


class _SafeTemplateValues(defaultdict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def lesson_format_context(
    inputs: dict[str, Any],
    grade_levels: str,
    resources: str,
    curriculum_context: str,
) -> dict[str, str]:
    return _SafeTemplateValues(
        str,
        {
            "subject": str(inputs.get("subject") or "Not specified"),
            "topic": str(inputs.get("topic") or "Not specified"),
            "grade_levels": grade_levels,
            "grade_level": str(inputs.get("grade_level") or grade_levels or "Not specified"),
            "resources": resources,
            "quarter": str(inputs.get("quarter") or "Not specified"),
            "curriculum_context": curriculum_context,
        },
    )


def render_lesson_format_requirements(
    template: str,
    inputs: dict[str, Any],
    grade_levels: str,
    resources: str,
    curriculum_context: str,
) -> str:
    context = lesson_format_context(inputs, grade_levels, resources, curriculum_context)
    return editable_lesson_format_structure(template).format_map(context).strip()


def editable_lesson_format_structure(requirements: str) -> str:
    marker = "Return markdown with exactly this structure:"
    if marker in requirements:
        return requirements.split(marker, 1)[1].strip()
    return requirements.strip()
