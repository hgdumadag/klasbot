# KlasBot: Gemma 4 on a Raspberry Pi for the Classrooms That Cloud Forgot

**Offline-first AI lesson planning for GIDA schools in the Philippines — where the internet never arrives, but the lessons still must.**

---

## Motivation

Most AI tools for education share the same assumption: the teacher has a stable internet connection, a personal device, and a few quiet minutes to interact with a chatbot. For the 35,000+ teachers in Philippine GIDA (*Geographically Isolated and Disadvantaged Areas*) schools, none of those things are true.

We conducted structured empathy research — affinity mapping and persona construction — to understand the real problem. What emerged was not a missing app. It was a missing category. Teacher Ana, our composite persona built from GIDA school conditions, handles two or three grade levels simultaneously in one room, commutes two to three hours each way on unpaved roads, and spends more than half her working hours on DepEd-required paperwork: lesson plans, daily logs, assessment forms, and portfolios.

Cloud-based AI tools are not the answer. There is no cloud. General-purpose chatbots also require the teacher to know how to prompt effectively, understand DepEd curriculum frameworks, and manually reformat output into what administrators require. That cognitive overhead is the problem, not the solution.

We took the opposite approach: build for exactly one user, in exactly her conditions, and get every detail right.

---

## What KlasBot Does

KlasBot is a web application that runs entirely on a Raspberry Pi 5, acting as a shared school kiosk. Teachers log in with a short PIN and use **Gemma 4** — running fully locally via Ollama — to generate DepEd-aligned lesson plans, assessments, teaching aids, and quiz grading results, with no internet required. The Pi runs a systemd-managed Chromium kiosk that boots directly into the app. When sharing over the school's local Wi-Fi, teachers pair their phones via QR code and receive print-ready PDFs without touching a cable.

---

## Architecture

*(See Figure 1: System architecture diagram)*

The stack is intentionally minimal. **Ollama** runs `gemma4:e2b` as a local inference server on the Raspberry Pi 5. **KlasBot** is a FastAPI application (Python 3.10+) that exposes four API groups: `/api/generate` for SSE-streamed lesson content, `/api/curriculum` for PDF/JSON ingestion and context retrieval, `/api/grading` for the vision OCR pipeline, and `/api/classes` for class records and scores. A vanilla JS single-page UI is served from `/static` with zero build tooling. The only persistent store is **SQLite** — one file on disk, no server process, survives power cuts, backs up to a USB drive in under a second.

Authentication is **PIN-based**, hashed with Argon2, with CSRF tokens per session. No email, no password reset, no internet required to log in.

Deployment is a single `setup-pi.sh` that installs Python, Chromium, CUPS, Ollama, pulls the model, and registers the app as a systemd service. The school receives a self-managing appliance.

---

## How We Used Gemma 4

We chose **`gemma4:e2b`** — Gemma 4's two-billion-parameter efficient variant — because it fits fully in the Raspberry Pi 5's 8 GB of RAM without swapping. A full Detailed Lesson Plan generates in under 90 seconds on the Pi. That is acceptable during a class transition; it is not acceptable on a blank-screen wait, which is why streaming was non-negotiable.

**Two inference modes drive the whole app:**

**Streaming generation** (`/api/generate`) powers lesson plans, assessments, and teaching aids. Our `OllamaClient` opens a persistent HTTP stream and forwards each NDJSON token as an SSE frame. Multiline Markdown tokens required careful framing: a `#` arriving mid-frame with no newline renders as a paragraph in the browser. We hardened the SSE formatter to flush complete lines and escape pipe characters so tables never corrupt mid-stream.

**Vision chat** (`/api/chat`, non-streaming, JSON mode) powers quiz photo grading. The teacher photographs student worksheets; KlasBot sends the image to Gemma 4's multimodal endpoint with a prompt requiring strict JSON output — per-item student answers, correct answers, confidence scores, and overall grade. If the JSON fails schema validation, we retry once with a repair prompt; if it fails again, the batch is flagged for manual review. A teacher's gradebook should never contain a silently hallucinated score.

**Curriculum-grounded prompting** separates KlasBot from a generic chatbot wrapper. Before any Ollama call, KlasBot queries SQLite for the matching MATATAG Curriculum Guide entry — grade level, quarter, domain, weekly focus, and Learning Competencies — and injects it as a structured context block. Without this constraint, Gemma 4 produces overambitious plans that cover four weeks of content in a single lesson.

**Subject-aware language routing** fixed a problem we discovered the hard way. Our initial prompts hardcoded `"Write in English only"`. Filipino, Araling Panlipunan, GMRC, and Makabansa are taught in Tagalog — but every plan came back in English. A `language_instruction_for_subject()` function now maps subject names to the correct language directive, and framework labels ("Objectives," "Procedures") localise to Tagalog equivalents at prompt build time.

**Offline math rendering** handles Science and Mathematics without a CDN. Prompts permit `$...$` and `$$...$$` LaTeX, rendered client-side with a bundled KaTeX. The ReportLab PDF export falls back to text approximations (`\frac{a}{b}` → `a/b`) since ReportLab has no KaTeX support.

---

## Challenges

### Silent blank lesson plans

**What broke:** Ollama's `/api/generate` endpoint can return HTTP 200 with zero `response` tokens when the model runs into a memory allocation failure under load. Our first implementation treated a clean stream as a successful generation — and dutifully saved a blank lesson plan to the teacher's library.

**What we tried first:** Checking response length after saving — too late, the blank was already in the database.

**What fixed it:** A guard that accumulates token count during the stream. If the stream closes with zero tokens, KlasBot discards it and saves a fallback draft for teacher review instead of silently producing an empty document.

---

### Parsing DepEd curriculum PDFs without a schema

**What broke:** The MATATAG Curriculum Guide PDFs are beautifully typeset — for humans. `pypdf` extracts text that loses all table structure: columns merge, section headers run together, and Tagalog section labels like *"Pamantayang Pangnilalaman"* appear mid-paragraph with no structural context.

**What we tried first:** A single regex pattern for all subjects — it matched nothing in Filipino or Math, which use entirely different layouts.

**What fixed it:** Three separate strategies: one for general subjects, one for Mathematics (different domain vocabulary and table structure), one for Filipino (*"Baitang"* for grade, *"Markahan"* for quarter, Tagalog section headers throughout). Each unit gets a `confidence` score that deducts 0.12 per missing field. A `build_parse_diagnostics()` function reports per-grade, per-quarter coverage gaps in the admin UI so staff know immediately if an upload was incomplete.

---

### QR code sharing that consumed itself

**What broke:** Our first QR code implementation encoded the Pi's IP address from a hardcoded environment variable. On most networks the variable was blank, so QR codes encoded `http:///share/<token>`, returning 404 on every phone. When we fixed the IP detection, a new problem appeared: many phone camera apps prefetch QR links before the user opens them, consuming the 15-minute share token before the teacher could tap "Pair this phone."

**What fixed it:** Runtime LAN IP detection from the active network interface. Pairing tokens changed from a single-use redirect to a confirmation page — consumed only when the teacher taps confirm, making scanner prefetch harmless. Mobile devices are restricted to `/share/` and `/mobile/` routes and cannot reach the teacher interface at all.

---

### Running Gemma 4 for remote judges without breaking offline integrity

**What broke:** The app is built for a Raspberry Pi with no internet. Judges cannot replicate that environment remotely. We needed a way to demonstrate the app live without shipping hardware.

**What we tried first:** The standard Gemini API. `gemma4:e2b` is not served there — Gemma 4 on Google Cloud requires **Vertex AI Model Garden**: a service account JSON key, IAM role grants, regional endpoint configuration, and model access approval. A meaningfully different credential path than most developers expect.

**What fixed it:** A provider abstraction. The same `OllamaClient` interface is backed by Vertex AI in online demo mode — no changes to prompt logic, streaming code, or response handling. The switch is one environment variable.

---

## Why These Choices Were Right

Every decision traces back to Teacher Ana's actual constraints:

- **SQLite** — no database server to maintain in a rural school
- **Argon2 PINs** — no email server to reset a forgotten password
- **SSE streaming** — watching a lesson appear line by line is usable; a 90-second spinner is not
- **Three PDF parsers** — DepEd's curriculum guides are inconsistent across subjects; one strategy left Filipino and Math teachers with no curriculum grounding
- **Gemma 4 `e2b`** — fits in 8 GB of RAM, handles streaming text and multimodal vision on the same local server, and produces plans in the exact DepEd formats — DLP, SDLP, DLL — that administrators require and auditors check

KlasBot does not replace Teacher Ana. It gives back the hours she spent alone at night, after a three-hour commute on unpaved roads, filling out paperwork by candlelight.
