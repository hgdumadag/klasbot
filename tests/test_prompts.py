from __future__ import annotations


def test_dlp_prompt_uses_scripted_deped_structure():
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    prompt = build_lesson_plan_prompt(
        {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_levels": ["Grade 3"],
            "resources": ["paper"],
            "curriculum_context": "Content Standards: Science context",
        }
    )

    assert "# Detailed Lesson Plan (DLP)" in prompt
    assert "## I. Objectives" in prompt
    assert "### Content Standards" in prompt
    assert "### Performance Standards" in prompt
    assert "### Learning Competencies/Objectives" in prompt
    assert "## IV. Procedures" in prompt
    assert "Procedure Step | Teacher Activity | Learner Activity" in prompt
    assert "A. Reviewing previous lesson/Presenting new lesson." in prompt
    assert "J. Additional activities for application or remediation." in prompt
    assert "## V. Remarks" in prompt
    assert "## VI. Reflection" in prompt
    assert "LC Code: Not specified in provided curriculum context" in prompt


def test_sdlp_prompt_uses_4as_structure_from_sample():
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    prompt = build_lesson_plan_prompt(
        {
            "kind": "lesson_plan",
            "format": "SDLP",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_levels": ["Grade 3"],
            "quarter": 1,
            "resources": ["paper"],
            "curriculum_context": "Science context",
        }
    )

    assert "# Semi-Detailed Lesson Plan (SDLP)" in prompt
    assert "## I. Objectives" in prompt
    assert "At the end of the lesson, the learners are expected to:" in prompt
    assert "## II. Subject Matter" in prompt
    assert "Values Integration" in prompt
    assert "## III. Materials" in prompt
    assert "## IV. Procedure (4As)" in prompt
    assert "### A. Activity (Motivation)" in prompt
    assert "### B. Analysis" in prompt
    assert "### C. Abstraction" in prompt
    assert "### D. Application" in prompt
    assert "Teacher's Activity" in prompt
    assert "Learners' Activity" in prompt
    assert "Guide Questions" in prompt
    assert "Science, or notation-heavy examples" in prompt
    assert "display math as $$...$$" in prompt
    assert "## V. Evaluation" in prompt
    assert "checklist or rubric" in prompt
    assert "## VI. Assignment" in prompt
    assert "# Detailed Lesson Plan (DLP)" not in prompt


def test_unknown_lesson_format_keeps_generic_structure():
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    prompt = build_lesson_plan_prompt(
        {
            "kind": "lesson_plan",
            "format": "Custom",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_levels": ["Grade 3"],
            "resources": ["paper"],
            "curriculum_context": "Science context",
        }
    )

    assert "# Custom Lesson Plan" in prompt
    assert "# Semi-Detailed Lesson Plan (SDLP)" not in prompt
    assert "# Detailed Lesson Plan (DLP)" not in prompt


def test_dll_prompt_uses_weekly_matrix_structure():
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    prompt = build_lesson_plan_prompt(
        {
            "kind": "lesson_plan",
            "format": "DLL",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_levels": ["Grade 3"],
            "quarter": 1,
            "resources": ["paper"],
            "curriculum_context": "Science context",
        }
    )

    assert "# Daily Lesson Log (DLL)" in prompt
    assert "spanning Monday to Friday" in prompt
    assert "Section | Monday | Tuesday | Wednesday | Thursday | Friday" in prompt
    assert "### I. Objectives" in prompt
    assert "### III. Learning Resources" in prompt
    assert "### IV. Procedures" in prompt
    assert "A. Reviewing previous lesson or presenting the new lesson" in prompt
    assert "J. Additional activities for application or remediation" in prompt
    assert "## V. Remarks" in prompt
    assert "## VI. Reflection" in prompt
    assert "Leave all reflection entries blank" in prompt


def test_lesson_prompt_uses_filipino_for_selected_subjects():
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    for subject in ["Araling Panlipunan", "Filipino", "GMRC and VE", "Makabansa"]:
        prompt = build_lesson_plan_prompt(
            {
                "kind": "lesson_plan",
                "format": "DLP",
                "subject": subject,
                "topic": "MATERIALS",
                "grade_levels": ["Grade 3"],
                "resources": ["paper"],
                "curriculum_context": "Curriculum context",
            }
        )

        assert "Write primarily in Filipino/Tagalog" in prompt
        assert "Write in English only" not in prompt


def test_custom_lesson_prompt_uses_filipino_for_selected_subjects():
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    prompt = build_lesson_plan_prompt(
        {
            "kind": "lesson_plan",
            "format": "Custom",
            "subject": "Filipino",
            "topic": "Pangngalan",
            "grade_levels": ["Grade 3"],
            "resources": ["paper"],
            "curriculum_context": "Curriculum context",
        }
    )

    assert "Write primarily in Filipino/Tagalog" in prompt
    assert "Write in English only" not in prompt


def test_assessment_prompt_uses_filipino_for_selected_subjects():
    from klasbot.prompts.assessment import build_assessment_prompt

    prompt = build_assessment_prompt(
        {
            "kind": "assessment",
            "format": "quiz",
            "subject": "Makabansa",
            "topic": "Komunidad",
            "grade_levels": ["Grade 3"],
            "resources": ["paper"],
            "curriculum_context": "Curriculum context",
        }
    )

    assert "Write primarily in Filipino/Tagalog" in prompt
    assert "Write in English only" not in prompt


def test_non_filipino_subject_prompts_keep_english_instruction():
    from klasbot.prompts.assessment import build_assessment_prompt
    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    base_inputs = {
        "topic": "MATERIALS",
        "grade_levels": ["Grade 3"],
        "resources": ["paper"],
        "curriculum_context": "Curriculum context",
    }

    lesson_prompt = build_lesson_plan_prompt(
        {"kind": "lesson_plan", "format": "DLP", "subject": "Science", **base_inputs}
    )
    assessment_prompt = build_assessment_prompt(
        {"kind": "assessment", "format": "quiz", "subject": "Science", **base_inputs}
    )

    assert "Write in English only" in lesson_prompt
    assert "Write in English only" in assessment_prompt


def test_assessment_prompt_allows_latex_for_science_equations():
    from klasbot.prompts.assessment import build_assessment_prompt

    prompt = build_assessment_prompt(
        {
            "kind": "assessment",
            "format": "quiz",
            "subject": "Science",
            "topic": "Force and motion",
            "grade_levels": ["Grade 8"],
            "resources": ["paper"],
            "curriculum_context": "Science context",
        }
    )

    assert "Science, or notation-heavy questions" in prompt
    assert "valid LaTeX for formulas and equations" in prompt


def test_teaching_aid_prompt_requires_classroom_usable_worked_example():
    from klasbot.prompts.teaching_aid import build_teaching_aid_prompt

    prompt = build_teaching_aid_prompt(
        {
            "kind": "lesson_plan",
            "format": "SDLP",
            "subject": "Mathematics",
            "topic": "Triangle Similarity",
            "week_number": 4,
            "grade_levels": ["Grade 9"],
            "resources": ["ruler"],
            "inputs": {"kind": "lesson_plan", "subject": "Mathematics"},
            "content_md": "# SDLP\n\n## Application\nUse AA similarity.",
        },
        {
            "aid_type": "worked_example",
            "source_section": "## Application",
            "custom_request": "Use AA similarity",
            "curriculum_context": "Weekly Competencies: apply triangle similarity",
        },
    )

    assert "Do not generate another lesson plan" in prompt
    assert "classroom-usable Teaching Aids" in prompt
    assert "Step-by-Step Solution" in prompt
    assert "Teacher Talk Track" in prompt
    assert "Common Learner Mistake" in prompt
    assert "Similar Practice Item" in prompt
    assert "Weekly Competencies: apply triangle similarity" in prompt
    assert "## Application" in prompt
    assert "valid LaTeX" in prompt
