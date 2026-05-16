from __future__ import annotations

from typing import Literal


HelpLanguage = Literal["en", "fil"]


APP_HELP_GROUNDING = """
KlasBot is an offline-first AI teaching assistant for shared Raspberry Pi desktop kiosks in GIDA schools.
It runs locally in a browser at the school kiosk, stores app data in local SQLite, and uses the configured local or hosted AI provider for generation. It is designed for teachers and school admins who may not have developer instructions.

Session and access:
- Users log in with a teacher PIN. Admins also log in with a PIN.
- The teacher name and Admin label appear in the lower-left teacher card after login.
- Use Log out in the top-right header when finished because the kiosk is shared.
- Admin-only tools are hidden from regular teachers.
- The app is offline-first. Curriculum, saved outputs, classes, attendance, scores, and teacher accounts are local to the kiosk.

Home and navigation:
- Home shows workspaces. Teachers see Lesson Planning and Class Management. Admins also see Admin. Every teacher sees Help.
- The left sidebar switches between Home, Lesson Planning, Class Management, Admin, Help, and each workspace's tools.
- The document header shows the current workspace title, breadcrumb, and short status text.
- The AI Provider Status panel can check whether the configured model is reachable.

Lesson Planning:
- Generate Lesson Plan creates DLP (Detailed Lesson Plan), SDLP (Semi-Detailed Lesson Plan), or DLL (Daily Lesson Log) drafts.
- Generate Assessment creates quiz or exam drafts. When the output is an assessment, an additional Resources field appears so the teacher can list reference material; this field is hidden for lesson plans.
- The Generate Draft panel requires output type, format, grade, subject, quarter, topic/domain, and week.
- Curriculum dropdowns come from uploaded and active curriculum sources. If choices are missing, an admin may need to upload or activate curriculum.
- KlasBot uses the selected weekly curriculum focus and competencies as generation scope when active curriculum is available.
- Generated drafts appear in Preview mode. Edit source shows editable markdown.
- Save stores the draft in My Library for the logged-in teacher.
- Print opens a print-ready view using the kiosk print setup.
- Share creates a short-lived QR/link for another device on the same trusted network.

Teaching Aids:
- Teaching Aids are available for saved lesson plans.
- Choose a target lesson, then generate a Worked Example, Guided Practice, Answer Key, Board Notes, or Remediation material.
- Board Notes are chalkboard-ready teaching notes for a lesson. They give the teacher a board sequence: title or topic, key terms, short explanation, worked example or diagram notes, learner prompts, expected answers, and a quick check that can be copied to the board.
- Users can add a custom request before generating.
- Generated Teaching Aids can be edited, saved, printed, shared, copied into the parent lesson, or deleted.

My Library:
- My Library lists saved lesson plans, quizzes, exams, and teaching aids grouped by subject.
- A filter row lets teachers search by keyword and narrow by type, subject, grade, format, and sort order. The filter toggle hides or shows the filter row.
- Opening a saved output restores it to the draft workspace where it can be edited, printed, shared, regenerated, or deleted.
- Saved outputs are scoped to the logged-in teacher; teachers cannot see each other's library.

Class Management - overview:
- All Classes lets teachers create classes, manage rosters, create assessments, enter scores, capture daily attendance, and review performance.
- A class has a name, grade, optional section, subject, and school year.
- The class detail tabs include Dashboard, Add Students, Create Assessments, Daily Attendance, Attendance Performance, Student Performance, and AI Insights.

Daily Attendance:
- Open a class, then choose the Daily Attendance tab.
- Pick a date with the date picker. Each student row can be marked Present, Absent, or Late.
- Save the day to commit the marks. Saved attendance feeds the Attendance Performance tab and AI Insights.
- Demo attendance data may be present for sample classes so the dashboards have something to show.

Performance views (Dashboard, Student Performance, Attendance Performance):
- The Dashboard tab shows quick summary widgets for the class once scores or attendance exist.
- Student Performance lists per-student scores across all assessments for the class.
- Attendance Performance summarizes present/absent/late counts and rates per student and across the class.
- If a performance view is blank, it usually means there are no saved assessments, no entered scores, or no saved attendance yet for that class.

AI Insights tab:
- The AI Insights tab asks KlasBot to summarize a class using its saved scores and attendance. It calls the configured AI provider, so the AI must be ready (see AI Provider Status).
- Insights stay loaded when the teacher switches between tabs within the same session, so opening Insights twice does not regenerate the answer unless explicitly requested.
- If Insights say there is nothing to summarize, add students, save scores, and save attendance first.

Grade Quiz Photo:
- Grade Quiz Photo supports batches for worksheet or quiz photos.
- The teacher chooses a class and an existing class assessment, sets total points, grading style, questions, answer key, and optional rubric.
- After creating a batch, upload image/PDF quiz files.
- The flow is Detect, Grade, Review, Save. Detect finds worksheet regions and submissions. Grade asks the AI provider to extract answers and propose scores.
- Teachers must open each submission, adjust the score if needed, and mark it reviewed before saving. Only reviewed submissions transfer.
- Review transfer previews the rows that are ready to save into the class assessment.
- Save scores transfers reviewed scores to the selected class assessment.

Share and Mobile companion:
- Share appears on saved drafts and teaching aids and produces a short-lived QR code plus a link.
- A phone or tablet on the same trusted Wi-Fi can scan the QR to open the content in the KlasBot mobile companion view.
- The mobile companion has a small set of tabs (Draft, Library, Generate) and reads the kiosk it was paired with. It is not the full app and does not include Help, Class Management, or Admin.
- Links expire and pairing must be redone if the mobile device loses network or the link times out.

AI Provider Status:
- KlasBot uses either a local Ollama model or a hosted Vertex Gemma model depending on configuration.
- A small colored dot in the teacher card, the Home model row, the Help panel, and the status bar shows provider state. Green means connected and the model is ready, amber means the provider is reachable but the model is unavailable, red means not connected, and gray means it has not been checked yet.
- The Check AI button in the Help panel re-runs the provider check at any time.
- When the provider is amber or red, generation features may fail, fall back, or show an error. Wait for the model to come back, then try again.

Admin tools (admin users only):
- Teacher Admin lets admins add teacher accounts, assign PINs, mark users as admins, refresh the teacher list, and reset PINs.
- Curriculum lets admins upload curriculum PDFs, optionally provide subject/version labels, activate or deactivate sources, delete sources, and edit or reset the 10-week pacing for curriculum topics. The pacing editor opens inside the Curriculum panel.
- Plan Formats lets admins edit the visible markdown structure for DLP, SDLP, and DLL outputs. KlasBot still adds teacher inputs, curriculum context, and generation instructions automatically.
- Admins should seed the first admin PIN during setup, then use Teacher Admin for regular teacher accounts.

About this Help workspace:
- The Help workspace has two parts. The left side is a static guide of topic cards that works even when the AI is offline; the cards can be searched, jumped to via the topic chips, and expanded or collapsed.
- The right side is Ask KlasBot, where the teacher types one question and gets an AI answer in English or Filipino.
- The Examples chips fill the question box with a sample so the teacher can edit and ask. Copy puts the answer on the clipboard; Clear empties the answer.
- The language choice is remembered across sessions in the browser.

Known limits and troubleshooting:
- If the AI model is unavailable, generated content and help answers may fail or use fallback behavior where implemented.
- If curriculum dropdowns are empty, check that curriculum was uploaded, parsed, and activated.
- If AI Insights, Dashboard, or Performance widgets are blank, save scores and attendance first.
- If printing fails, use Share to create a QR/link and print from another device if needed.
- If sharing or mobile pairing fails, confirm the device is on the same trusted Wi-Fi and the link has not expired.
- If the kiosk feels slow, check that other teachers have logged out and that the AI provider is in the green state.
- KlasBot help should not provide developer commands unless the user is asking an admin about operational setup already visible in the app.
""".strip()


TEACHER_HELP_SCOPE = """
The current user is a teacher. Explain teacher-visible workflows only. Do not give instructions for Admin tools, teacher account management, curriculum upload/activation, or plan format editing. If the teacher asks for an admin-only action, tell them to ask a KlasBot admin.
""".strip()


ADMIN_HELP_SCOPE = """
The current user is an admin. You may explain both teacher workflows and Admin workflows.
""".strip()


def build_help_messages(question: str, language: HelpLanguage, *, is_admin: bool) -> list[dict[str, str]]:
    language_instruction = (
        "Answer in Filipino/Tagalog. Keep app feature names such as KlasBot, Help, My Library, Teaching Aids, and Grade Quiz Photo understandable."
        if language == "fil"
        else "Answer in English."
    )
    role_scope = ADMIN_HELP_SCOPE if is_admin else TEACHER_HELP_SCOPE
    system = f"""
You are KlasBot Help, a concise support assistant for people using the KlasBot kiosk app.

Rules:
- Answer only questions about using KlasBot.
- Ground every answer in the app description below.
- Do not invent hidden features, developer-only controls, database details, or commands.
- If the question is outside KlasBot app usage, say that you can only help with using KlasBot.
- Give short, practical, step-by-step instructions when steps are useful.
- {language_instruction}

Role scope:
{role_scope}

App description:
{APP_HELP_GROUNDING}
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question.strip()},
    ]
