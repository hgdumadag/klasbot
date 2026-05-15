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


FILIPINO_LESSON_FORMAT_REPLACEMENTS = (
    ("# Detailed Lesson Plan (DLP)", "# Detalyadong Banghay-Aralin (DLP)"),
    ("# Semi-Detailed Lesson Plan (SDLP)", "# Semi-Detalyadong Banghay-Aralin (SDLP)"),
    ("# Daily Lesson Log (DLL)", "# Pang-araw-araw na Tala ng Aralin (DLL)"),
    ("## Overview", "## Buod"),
    ("## Weekly DLL Matrix", "## Lingguhang DLL Matrix"),
    ("## Header", "## Paunang Impormasyon"),
    ("## I. Objectives", "## I. Mga Layunin"),
    ("### I. Objectives", "### I. Mga Layunin"),
    ("## II. Subject Matter", "## II. Paksa"),
    ("## II. Content", "## II. Nilalaman"),
    ("### II. Content", "### II. Nilalaman"),
    ("## III. Learning Resources", "## III. Mga Kagamitang Pampagkatuto"),
    ("### III. Learning Resources", "### III. Mga Kagamitang Pampagkatuto"),
    ("## III. Materials", "## III. Mga Kagamitan"),
    ("## Materials", "## Mga Kagamitan"),
    ("## IV. Procedure (4As)", "## IV. Pamamaraan (4As)"),
    ("## IV. Procedures", "## IV. Mga Pamamaraan"),
    ("### IV. Procedures", "### IV. Mga Pamamaraan"),
    ("## Procedure", "## Pamamaraan"),
    ("## V. Evaluation", "## V. Pagtataya"),
    ("## V. Remarks", "## V. Mga Tala"),
    ("## VI. Assignment", "## VI. Takdang-Aralin"),
    ("## VI. Reflection", "## VI. Pagninilay"),
    ("## Assessment", "## Pagtataya"),
    ("## Adaptations", "## Mga Pag-aangkop"),
    ("## Teacher Notes", "## Tala ng Guro"),
    ("### Content Standards", "### Pamantayang Pangnilalaman"),
    ("### Performance Standards", "### Pamantayan sa Pagganap"),
    ("### Learning Competencies/Objectives", "### Mga Kasanayan/Layunin sa Pagkatuto"),
    ("- Lesson Plan in:", "- Banghay-Aralin sa:"),
    ("- Quarter:", "- Markahan:"),
    ("- Time Allotment:", "- Inilaang Oras:"),
    ("- School:", "- Paaralan:"),
    ("- Teacher:", "- Guro:"),
    ("- Teaching Dates and Time:", "- Petsa at Oras ng Pagtuturo:"),
    ("- Grade Level:", "- Baitang:"),
    ("- Learning Area:", "- Asignatura:"),
    ("- Topic:", "- Paksa:"),
    ("- Key Concepts:", "- Mahahalagang Konsepto:"),
    ("- Values Integration:", "- Pagpapahalaga:"),
    ("- Curriculum Alignment:", "- Pag-uugnay sa Kurikulum:"),
    ("  - Content Standards:", "  - Pamantayang Pangnilalaman:"),
    ("  - Performance Standards:", "  - Pamantayan sa Pagganap:"),
    ("  - Learning Competencies:", "  - Mga Kasanayan sa Pagkatuto:"),
    ("- Teacher's Guides:", "- Gabay ng Guro:"),
    ("- Learner's Materials:", "- Kagamitang Pang-aaral:"),
    ("- Textbooks:", "- Aklat:"),
    ("- Additional Materials from the LR Portal:", "- Karagdagang Kagamitan mula sa LR Portal:"),
    ("- Other Learning Resources:", "- Iba pang Kagamitang Pampagkatuto:"),
    ("Procedure Step | Teacher Activity | Learner Activity", "Hakbang sa Pamamaraan | Gawain ng Guro | Gawain ng Mag-aaral"),
    ("Section | Monday | Tuesday | Wednesday | Thursday | Friday", "Bahagi | Lunes | Martes | Miyerkules | Huwebes | Biyernes"),
    ("Teacher's Activity", "Gawain ng Guro"),
    ("Teacher's Discussion", "Talakayan ng Guro"),
    ("Learners' Activity", "Gawain ng mga Mag-aaral"),
    ("Learner Activity", "Gawain ng Mag-aaral"),
    ("Teacher Activity", "Gawain ng Guro"),
    ("Guide Questions", "Mga Gabay na Tanong"),
    ("Key Points", "Mahahalagang Punto"),
    ("Generalization", "Paglalahat"),
    ("Group or Individual Task", "Pangkatang o Indibidwal na Gawain"),
    ("Rows:", "Mga Hanay:"),
    ("- A. Content Standards", "- A. Pamantayang Pangnilalaman"),
    ("- B. Performance Standards", "- B. Pamantayan sa Pagganap"),
    ("- C. Learning Competencies/Objectives (Write the LC code for each)", "- C. Mga Kasanayan/Layunin sa Pagkatuto (Isulat ang LC code para sa bawat isa)"),
    ("- Content", "- Nilalaman"),
    ("- A. References", "- A. Mga Sanggunian"),
    ("- 1. Teacher's Guide pages", "- 1. Mga pahina sa Gabay ng Guro"),
    ("- 2. Learner's Materials pages", "- 2. Mga pahina sa Kagamitang Pang-aaral"),
    ("- 3. Textbook pages", "- 3. Mga pahina sa Aklat"),
    ("- 4. Additional Materials from Learning Resource (LR) portal", "- 4. Karagdagang Kagamitan mula sa Learning Resource (LR) portal"),
    ("- B. Other Learning Resources", "- B. Iba pang Kagamitang Pampagkatuto"),
    ("- Time:", "- Oras:"),
    ("A. Reviewing previous lesson/Presenting new lesson.", "A. Pagbabalik-aral sa nakaraang aralin/Paglalahad ng bagong aralin."),
    ("A. Reviewing previous lesson or presenting the new lesson", "A. Pagbabalik-aral sa nakaraang aralin o paglalahad ng bagong aralin"),
    ("B. Establishing a purpose for the lesson.", "B. Pagtatakda ng layunin ng aralin."),
    ("B. Establishing a purpose for the lesson", "B. Pagtatakda ng layunin ng aralin"),
    ("C. Presenting examples/instances.", "C. Pagbibigay ng mga halimbawa."),
    ("C. Presenting examples/instances of the new lesson", "C. Pagbibigay ng mga halimbawa ng bagong aralin"),
    ("D. Discussing new concepts and practicing new skills #1.", "D. Pagtalakay ng bagong konsepto at pagsasanay sa bagong kasanayan #1."),
    ("D. Discussing new concepts and practicing new skills #1", "D. Pagtalakay ng bagong konsepto at pagsasanay sa bagong kasanayan #1"),
    ("E. Discussing new concepts and practicing new skills #2.", "E. Pagtalakay ng bagong konsepto at pagsasanay sa bagong kasanayan #2."),
    ("E. Discussing new concepts and practicing new skills #2", "E. Pagtalakay ng bagong konsepto at pagsasanay sa bagong kasanayan #2"),
    ("F. Developing mastery (Leads to Formative Assessment).", "F. Paglinang ng pagkatuto (Tungo sa Formative Assessment)."),
    ("F. Developing mastery (Leads to Formative Assessment)", "F. Paglinang ng pagkatuto (Tungo sa Formative Assessment)"),
    ("G. Finding practical applications of concepts.", "G. Paglalapat ng mga konsepto sa praktikal na sitwasyon."),
    ("G. Finding practical applications of concepts and skills in daily living", "G. Paglalapat ng mga konsepto at kasanayan sa pang-araw-araw na buhay"),
    ("H. Making generalizations and abstractions.", "H. Pagbuo ng paglalahat at abstraksiyon."),
    ("H. Making generalizations and abstractions about the lesson", "H. Pagbuo ng paglalahat at abstraksiyon tungkol sa aralin"),
    ("I. Evaluating learning.", "I. Pagtataya ng pagkatuto."),
    ("I. Evaluating learning", "I. Pagtataya ng pagkatuto"),
    ("J. Additional activities for application or remediation.", "J. Karagdagang gawain para sa aplikasyon o remediation."),
    ("J. Additional activities for application or remediation", "J. Karagdagang gawain para sa aplikasyon o remediation"),
    ("### A. Number of learners who earned 80% in the evaluation", "### A. Bilang ng mga mag-aaral na nakakuha ng 80% sa pagtataya"),
    ("### B. Number of learners who require additional activities for remediation", "### B. Bilang ng mga mag-aaral na nangangailangan ng karagdagang gawain para sa remediation"),
    ("### C. Did the remedial lessons work? Number of learners who caught up with the lesson", "### C. Nakatulong ba ang remedial lessons? Bilang ng mga mag-aaral na nakahabol sa aralin"),
    ("### D. Number of learners who continue to require remediation", "### D. Bilang ng mga mag-aaral na patuloy na nangangailangan ng remediation"),
    ("### E. Which teaching strategies worked well? Why did these work?", "### E. Aling mga estratehiya sa pagtuturo ang naging mabisa? Bakit naging mabisa ang mga ito?"),
    ("### F. What difficulties did I encounter that my principal or supervisor can help me solve?", "### F. Anong mga suliranin ang naranasan ko na maaaring matulungan ng punong-guro o superbisor?"),
    ("### G. What innovation or localized materials did I use/discover which I wish to share with other teachers?", "### G. Anong inobasyon o lokal na materyales ang ginamit/natuklasan ko na nais kong ibahagi sa ibang guro?"),
    ("- A. No. of learners who earned 80% in the evaluation", "- A. Bilang ng mga mag-aaral na nakakuha ng 80% sa pagtataya"),
    ("- B. No. of learners who require additional activities for remediation who scored below 80%", "- B. Bilang ng mga mag-aaral na nangangailangan ng karagdagang gawain para sa remediation dahil mas mababa sa 80% ang nakuha"),
    ("- C. Did the remedial lessons work? No. of learners who have caught up with the lesson", "- C. Nakatulong ba ang remedial lessons? Bilang ng mga mag-aaral na nakahabol sa aralin"),
    ("- D. No. of learners who continue to require remediation", "- D. Bilang ng mga mag-aaral na patuloy na nangangailangan ng remediation"),
    ("- E. Which of my teaching strategies worked well? Why did these work?", "- E. Aling mga estratehiya sa pagtuturo ang naging mabisa? Bakit naging mabisa ang mga ito?"),
    ("- F. What difficulties did I encounter which my principal or supervisor can help me solve?", "- F. Anong mga suliranin ang naranasan ko na maaaring matulungan ng punong-guro o superbisor?"),
    ("- G. What innovation or localized materials did I use/discover which I wish to share with other teachers?", "- G. Anong inobasyon o lokal na materyales ang ginamit/natuklasan ko na nais kong ibahagi sa ibang guro?"),
)


def localize_lesson_format_requirements(requirements: str) -> str:
    localized = requirements
    for english, filipino in FILIPINO_LESSON_FORMAT_REPLACEMENTS:
        localized = localized.replace(english, filipino)
    return localized


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
