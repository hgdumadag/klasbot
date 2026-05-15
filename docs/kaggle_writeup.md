# Klasbot: Offline Gemma 4 Teaching Support for GIDA Schools

## A Raspberry Pi classroom kiosk that helps multigrade teachers plan, assess, print, and track learning without internet

**Recommended Track:** Impact Track - Future of Education  
**Also relevant:** Special Technology Track - Ollama

Klasbot was built for "Teacher Ana," a composite GIDA teacher in the Philippines who handles two or three grade levels in one room, commutes for hours, has limited electricity and internet, and still has to prepare lesson plans, assessments, reports, portfolios, and learner support materials. The central design question was: how might we help GIDA teachers prepare lessons, assess learners, and complete required documentation efficiently using offline-capable tools despite limited devices, learning materials, and connectivity?

Our answer is not a cloud chatbot. Klasbot is an offline-first AI teaching assistant that can run as a shared school kiosk on a Raspberry Pi. Teachers log in with a PIN, select subject, grade level, quarter, topic, week, output type, and available classroom resources, then generate DepEd-aligned drafts using a local Gemma 4 model served by Ollama. The teacher remains the final author: every generated output can be reviewed, edited, saved, printed, shared by QR/PDF, or reused as context for additional teaching aids.

## Architecture

The app is a FastAPI service with a static browser UI, SQLite persistence, local file storage, CUPS printing, and Ollama-backed inference. The deployment scripts install Python, Chromium, CUPS, Ollama, a `klasbot` system user, a systemd service, and a kiosk launcher so the school can boot directly into `http://127.0.0.1:8000`.

The backend is organized around teacher workflows:

- `klasbot/main.py` exposes the generation, library, curriculum, mobile pairing, sharing, printing, class record, and grading APIs.
- `klasbot/ollama_client.py` streams tokens from `/api/generate` and performs non-streaming structured chat calls for grading.
- `klasbot/prompts/` contains separate prompt builders for lesson plans, assessments, language behavior, and teaching aids.
- `klasbot/curriculum.py` ingests MATATAG curriculum PDFs or normalized JSON into structured units, competencies, and week pacing.
- `klasbot/db.py` initializes the SQLite schema for teachers, sessions, outputs, curriculum, teaching aids, class records, scores, grading batches, uploaded worksheets, and share tokens.
- `klasbot/grading/` handles worksheet image/PDF upload, quality checks, region detection, extraction, scoring normalization, and printable reports.
- `klasbot/print_utils.py` converts generated Markdown, tables, and math into printable HTML/PDF with KaTeX support in the browser.

This architecture matters for the target context. A single kiosk can serve multiple teachers without requiring every teacher to own a device. SQLite keeps data local and auditable. PIN sessions and teacher ownership checks separate each teacher's library, class records, and grading batches. Remote phones are deliberately constrained: mobile pairing uses short-lived, single-use QR tokens, CSRF is required for mobile writes, and unauthenticated remote clients can only open temporary share links.

## How Gemma 4 Is Used

Klasbot uses Gemma 4 through Ollama, configured by default as `OLLAMA_MODEL=gemma4:e2b`. The core generation endpoint builds a grounded prompt, then streams Gemma tokens to the UI using Server-Sent Events. This gives teachers immediate feedback instead of making them wait in silence on low-power hardware.

Gemma 4 is used in three concrete ways:

1. **Lesson and assessment generation.** The prompt layer grounds Gemma in the selected MATATAG curriculum context, selected week, grade level, subject, topic, and output format. It supports Detailed Lesson Plan, Semi-Detailed Lesson Plan, Daily Lesson Log, quiz, and exam generation. The prompts explicitly tell the model not to invent DepEd codes and to write "LC Code: Not specified in provided curriculum context" when the code is absent.

2. **Teaching aids from saved lessons.** After a teacher saves a lesson, Gemma can generate a worked example, guided practice, answer key, board notes, or remediation activity from the saved lesson and weekly curriculum context. This turns one planning session into several classroom-ready artifacts.

3. **Worksheet/photo grading assistance.** For quiz photos or PDFs, the app sends worksheet images plus the teacher's questions, answer key, rubric, total points, and grading style to Gemma via Ollama chat with `format="json"`. The grading prompt requires valid JSON with item-level answers, scores, confidence, feedback, and warnings. The result is normalized before display, and the teacher must review/edit before scores are transferred.

We chose Ollama because it matches the deployment reality: local inference, no cloud account at teaching time, and a simple HTTP interface that works on a Raspberry Pi or local laptop. Gemma 4 was the right model family because the app needs an open model that can operate close to the classroom, handle grounded educational generation, and support multimodal/structured grading workflows without depending on unstable connectivity.

## Grounding, Scope Control, and Safety

The biggest technical risk was hallucination. A lesson plan that invents curriculum codes or covers the whole quarter would waste teacher time. Klasbot addresses this with retrieval and prompt constraints:

- Curriculum documents are parsed into units, standards, competencies, source pages, and week pacing.
- Generation is blocked if an active curriculum match exists but no pacing week is selected.
- The prompt treats quarter context as background and the selected weekly focus as required scope.
- Assessment prompts require the model to use only teacher-listed resources.
- Filipino subjects trigger Filipino output; other subjects default to English.
- Math and science outputs may use LaTeX, which the UI and print renderer preserve through KaTeX.

The second risk was over-automation in grading. Klasbot does not claim automatic grading is final. Exact-answer grading requires an answer key. The extraction prompt says not to invent names or answers. Image quality warnings flag low resolution, poor light, glare, or unusual aspect ratios. Timeouts and failed model responses fall back to manual-review results instead of silently producing fake certainty.

## Product Fit for GIDA Teachers

The design process identified workload, multigrade complexity, weak infrastructure, lack of materials, and teacher burnout as the urgent pain cluster. Klasbot maps directly to those constraints:

- **Offline-first:** generation runs through local Ollama; login, library, class records, printing, and saved outputs continue without internet.
- **Low-cost shared access:** a Raspberry Pi kiosk and local browser avoid a one-device-per-teacher assumption.
- **Resource-aware outputs:** prompts favor paper, pencils, stones, bottle caps, local examples, and other classroom materials.
- **Multigrade support:** teachers can select multiple grade levels and generate scoped plans or assessments.
- **Documentation support:** DLP, SDLP, DLL, assessments, reports, and printable grading summaries match actual teacher paperwork.
- **Teacher authority:** every AI output is editable, saveable, printable, and reviewable before use.

## Challenges Overcome

One challenge was making a local LLM feel responsive. Streaming tokens over SSE solved the perceived latency problem, while fallback drafts keep the workflow usable if Ollama is unavailable.

Another challenge was turning curriculum PDFs into useful context. The ingestion layer extracts grade, quarter, domain, standards, competencies, confidence, warnings, and source pages, then stores them in searchable SQLite/FTS tables. We also added editable weekly pacing because curriculum documents usually describe broad quarters, while teachers plan by week.

A third challenge was cross-device use without making the kiosk a public web app. Klasbot uses QR pairing for trusted teacher phones and temporary PDF share links for handoff. Remote access is intentionally narrowed to the routes teachers need.

Finally, grading required humility. The implemented flow separates upload, detection, extraction, model grading, teacher correction, score transfer, and print reporting. This makes the AI useful while keeping the teacher in control.

## Verification

The repository includes tests for prompt grounding, generation/printing, curriculum behavior, static UI structure, authentication/database behavior, mobile pairing, sharing, class records, deployment artifacts, and grading APIs. The pilot checklist verifies cold boot, PIN login, Ollama status, DLP/SDLP/DLL/quiz/exam generation, save/edit/reopen, printing, and offline operation on the target Raspberry Pi.

Klasbot is built as real field infrastructure for a specific teacher, not a generic AI demo. Gemma 4 provides the local intelligence; the surrounding engineering makes it usable in the places where cloud-first education tools usually fail.
