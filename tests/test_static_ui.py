from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_non_admin_login_forces_admin_panel_closed():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")

    assert "const isAdmin = Boolean(state.teacher.is_admin);" in app_js
    assert "els.adminAreaButton.classList.toggle('hidden', !isAdmin);" in app_js
    assert "els.adminHomeCard.classList.toggle('hidden', !isAdmin);" in app_js
    assert "els.adminPanel.classList.add('hidden');" in app_js
    assert "els.formatAdminPanel.classList.add('hidden');" in app_js
    assert "els.teacherList.innerHTML = '';" in app_js


def test_desktop_home_hub_is_role_aware_default_workspace():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")
    styles_css = (ROOT / "klasbot" / "static" / "styles.css").read_text(encoding="utf-8")

    assert "activeWorkspace: 'home'" in app_js
    assert "switchWorkspace('home');" in app_js
    assert 'id="home-panel"' in index_html
    assert 'id="home-button"' in index_html
    assert 'id="lesson-area-button"' in index_html
    assert 'id="class-area-button"' in index_html
    assert 'id="admin-area-button" class="rail-item rail-area-item hidden"' in index_html
    assert 'id="admin-home-card" class="home-card home-card--admin hidden"' in index_html
    assert "Lesson Planning" in index_html
    assert "Class Management" in index_html
    assert ">Admin<" in index_html
    assert "related" not in index_html.lower()
    assert "workspace-frame--no-inspector" in styles_css
    assert "setInspectorVisibility" in app_js
    assert "const showInspector = workspace === 'draft';" in app_js


def test_curriculum_generation_uses_dropdown_controls():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")

    assert 'document.getElementById(\'grade-level\')' in app_js
    assert 'document.getElementById(\'quarter\')' in app_js
    assert 'document.getElementById(\'week-number\')' in app_js
    assert "loadCurriculumTopics" in app_js
    assert "loadCurriculumPacing" in app_js
    assert "formatParseWarnings" in app_js
    assert "Parse confidence" in app_js
    assert "previewPrompt" in app_js
    assert "/api/dev/prompt-preview" in app_js
    assert "/api/admin/lesson-plan-formats" in app_js
    assert '<select id="subject" required>' in index_html
    assert '<select id="topic" required>' in index_html
    assert '<select id="week-number" required>' in index_html
    assert 'id="preview-prompt-button"' in index_html
    assert 'id="format-admin-panel"' in index_html
    assert "Only the structure below is editable here" in index_html


def test_library_uses_middle_workspace_view():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")

    assert 'id="library-button"' in index_html
    assert 'id="library-panel"' in index_html
    assert 'id="library-search"' in index_html
    assert 'id="library-type-filter"' in index_html
    assert 'id="library-subject-filter"' in index_html
    assert 'id="library-grade-filter"' in index_html
    assert 'id="library-format-filter"' in index_html
    assert 'id="library-sort"' in index_html
    assert "My Library <span>Refresh</span>" not in index_html
    assert "function switchWorkspace" in app_js
    assert "function renderLibraryView" in app_js
    assert "function groupedBySubject" in app_js
    assert "outputMetadataText" in app_js


def test_grading_setup_uses_curriculum_dropdown_controls():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")

    assert '<select id="grading-grade" required>' in index_html
    assert '<select id="grading-subject" required>' in index_html
    assert '<select id="grading-topic" required>' in index_html
    assert '<select id="grading-week-topic" required>' in index_html
    assert 'id="grading-questions"' in index_html
    assert 'id="grading-status"' in index_html
    assert 'id="grading-upload-button"' in index_html
    assert "loadGradingCurriculumGrades" in app_js
    assert "loadGradingCurriculumSubjects" in app_js
    assert "loadGradingCurriculumTopics" in app_js
    assert "loadGradingCurriculumWeeks" in app_js
    assert "week_topic" in app_js
    assert "questions" in app_js
    assert "setGradingStatus" in app_js
    assert "Upload complete" in app_js


def test_class_records_forms_do_not_overflow_workspace():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")
    styles_css = (ROOT / "klasbot" / "static" / "styles.css").read_text(encoding="utf-8")

    assert 'class="class-record-create-panel"' in index_html
    assert index_html.index('id="class-record-form"') < index_html.index('class="class-records-layout"')
    assert 'class="record-field--title"' in app_js
    assert 'class="record-field--notes"' in app_js
    assert "class-records-panel--detail" in app_js
    assert "data-close-active-class" in app_js
    assert "data-class-tab" in app_js
    assert "Dashboard" in app_js
    assert "Add Students" in app_js
    assert "Create Assessments" in app_js
    assert "Student Performance" in app_js
    assert ".class-record-create-form" in styles_css
    assert ".class-records-panel--detail .class-record-create-panel" in styles_css
    assert ".class-records-panel--detail .class-records-layout" in styles_css
    assert ".class-tab--on" in styles_css
    assert ".class-dashboard-grid" in styles_css
    assert ".inline-record-form .record-field--title" in styles_css
    assert ".inline-record-form input," in styles_css
    assert "min-width: 0;" in styles_css


def test_draft_has_teacher_preview_and_markdown_source():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")
    styles_css = (ROOT / "klasbot" / "static" / "styles.css").read_text(encoding="utf-8")

    assert 'id="preview-tab"' in index_html
    assert 'id="edit-tab"' in index_html
    assert 'id="draft-preview"' in index_html
    assert 'id="editor" class="hidden"' in index_html
    assert "function markdownToHtml" in app_js
    assert "function renderMarkdownTable" in app_js
    assert "/static/vendor/katex/katex.min.css" in index_html
    assert "/static/vendor/katex/katex.min.js" in index_html
    assert "function renderMathSegment" in app_js
    assert "fallbackLatexText" in app_js
    assert "setDraftView('preview')" in app_js
    assert ".draft-preview table" in styles_css


def test_desktop_teaching_aids_static_controls():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")
    styles_css = (ROOT / "klasbot" / "static" / "styles.css").read_text(encoding="utf-8")

    assert "Teaching Aids" in index_html
    assert 'id="teaching-aids-button"' in index_html
    assert 'id="teaching-aids-panel" class="workspace-panel teaching-aids-panel hidden"' in index_html
    assert 'id="teaching-aid-target"' in index_html
    assert 'id="teaching-aid-target-meta"' in index_html
    for aid_type in ["worked_example", "guided_practice", "answer_key", "board_notes", "remediation"]:
        assert f'data-aid-type="{aid_type}"' in index_html
    assert 'id="teaching-aid-editor"' in index_html
    assert 'id="save-teaching-aid"' in index_html
    assert 'id="print-teaching-aid"' in index_html
    assert 'id="share-teaching-aid"' in index_html
    assert 'id="copy-teaching-aid"' in index_html
    assert "/teaching-aids/stream" in app_js
    assert "source_section" in app_js
    assert "aid_type" in app_js
    assert "teachingAidTargetId" in app_js
    assert "function openTeachingAidsWorkspace" in app_js
    assert "function renderTeachingAidTargets" in app_js
    assert "function selectTeachingAidTarget" in app_js
    assert "switchWorkspace('teaching-aids')" in app_js
    assert "/api/library/${targetId}" in app_js
    assert "function generateTeachingAid" in app_js
    assert ".teaching-aids-panel" in styles_css
    assert ".teaching-aid-target" in styles_css


def test_admin_tools_use_middle_workspace_views():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")

    assert 'id="admin-panel" class="workspace-panel hidden"' in index_html
    assert 'id="curriculum-panel" class="workspace-panel hidden"' in index_html
    assert 'id="format-admin-panel" class="workspace-panel hidden"' in index_html
    assert 'id="format-admin-message"' in index_html
    assert "KlasBot Home" in index_html
    assert "My Library / Current Draft" not in index_html
    assert "document.querySelector('.breadcrumb').textContent = 'Lesson Planning / Current Draft';" in app_js
    assert 'id="admin-panel" class="inspector-group hidden"' not in index_html
    assert 'id="curriculum-panel" class="inspector-group hidden"' not in index_html
    assert 'id="format-admin-panel" class="inspector-group hidden"' not in index_html
    assert "switchWorkspace('teacher-admin')" in app_js
    assert "switchWorkspace('curriculum')" in app_js
    assert "switchWorkspace('plan-formats')" in app_js
    assert "Loading formats..." in app_js
    assert "Formats unavailable" in app_js
    assert "No formats configured" in app_js
    assert "Could not load plan formats:" in app_js
    assert "formatConfig.format === 'DLP'" in app_js
    assert "option.selected = option.value === defaultFormat;" in app_js
    assert "|| state.lessonPlanFormats[0]" in app_js


def test_mobile_teacher_workspace_static_assets():
    mobile_html = (ROOT / "klasbot" / "static" / "mobile.html").read_text(encoding="utf-8")
    mobile_js = (ROOT / "klasbot" / "static" / "mobile.js").read_text(encoding="utf-8")
    mobile_css = (ROOT / "klasbot" / "static" / "mobile.css").read_text(encoding="utf-8")
    index_html = (ROOT / "klasbot" / "static" / "index.html").read_text(encoding="utf-8")

    assert 'id="mobile-pair-button"' in index_html
    assert 'id="pair-view"' in mobile_html
    assert 'id="generate-form"' in mobile_html
    assert 'id="week-number"' in mobile_html
    assert "Teaching Aids" in mobile_html
    assert 'id="teaching-aid-editor"' in mobile_html
    assert 'id="library-list"' in mobile_html
    assert 'id="conflict-panel"' in mobile_html
    assert "/api/generate/stream" in mobile_js
    assert "/static/vendor/katex/katex.min.css" in mobile_html
    assert "/static/vendor/katex/katex.min.js" in mobile_html
    assert "function renderMathSegment" in mobile_js
    assert "function generateTeachingAid" in mobile_js
    assert "/teaching-aids/stream" in mobile_js
    assert "aid_type" in mobile_js
    assert "week_number" in mobile_js
    assert "/api/library" in mobile_js
    assert "X-Klasbot-CSRF" in mobile_js
    assert "expected_updated_at" in mobile_js
    assert "/api/admin/" not in mobile_html
    assert "/api/admin/" not in mobile_js
    assert "@media (max-width: 380px)" in mobile_css
    assert "min-width: 320px" in mobile_css
