# Klasbot — Implementation Plan

## Context

Klasbot is an offline-first AI teaching assistant for **GIDA (Geographically Isolated and Disadvantaged Areas)** schools in the Philippines. It runs on a shared Raspberry Pi kiosk, lets one teacher at a time log in with a PIN, and generates DepEd-style lesson plans and assessments using a locally hosted Gemma 4 model via Ollama. No internet is required at the school. The MVP must ship in **2–3 weeks (solo developer)**, so scope is held tight; everything beyond the printable, regenerable, savable lesson-plan + assessment loop is deferred to later phases.

### Locked decisions (from clarification round)

| Area | Decision |
| --- | --- |
| Hardware | Raspberry Pi 5, 8 GB RAM |
| AI runtime | Ollama + **Gemma 4** (e2B primary, e4B fallback if quality demands). Exact Ollama tag to be confirmed on Day 1 of setup — likely `gemma4:e2b` / `gemma4:e4b` but check the Ollama library page since this model post-dates the assistant's training data. |
| Stack | Python 3.11 + FastAPI backend, vanilla HTML/CSS/JS frontend in Chromium kiosk |
| Auth | PIN per teacher (admin pre-registers) |
| Language (MVP) | English only |
| Templates | DepEd-style — user will provide DLP / SDLP / DLL reference docs; prompts seeded from them |
| MVP output | Generate → inline edit (basic) → save → regenerate → print (CUPS) |
| Networking | Offline by default; one-command updater for occasional tethered sync |
| Peripherals | USB keyboard + mouse + printer |

### Explicitly out of scope for MVP (deferred to later phases)

DOCX/PDF export, Bluetooth file send, Filipino/regional languages, Android client, exam photo grading, score tracking, learning insights, offline reference library, rich-text WYSIWYG editor.

---

## Architecture (one diagram in words)

```
[Chromium kiosk @ http://127.0.0.1:8000]
                │
                ▼
        FastAPI app (uvicorn, systemd service)
        ├── /auth         (PIN login, session cookie)
        ├── /generate     (SSE stream → Ollama)
        ├── /library      (CRUD over SQLite outputs)
        ├── /print        (writes tmp HTML → wkhtmltopdf → lp)
        └── static/       (HTML/CSS/JS)
                │
                ▼
        Ollama @ 127.0.0.1:11434  (Gemma 4 e2B)
                │
        SQLite file at /var/lib/klasbot/klasbot.db
        CUPS for printer; BlueZ deferred to phase 2
```

Why this shape:
- Localhost-only FastAPI = no CORS, no auth-over-network worries, trivial to harden later.
- SSE for streaming generation gives the teacher instant feedback (Gemma 4 e2B on Pi 5 is expected to be in the ~5–10 tok/s band based on the on-device-efficient variant lineage; a 600-token lesson plan ≈ 60–120 s, unbearable without streaming). Actual numbers must be measured on Day 2.
- Same FastAPI surface can be exposed on the LAN later for the phase-2 Android app — no rewrite.

---

## Repository layout (to create)

```
D:\programs\klasbot_\
├── README.md
├── pyproject.toml                # FastAPI, uvicorn, httpx, jinja2, pydantic, weasyprint, passlib
├── klasbot/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app + uvicorn entry
│   ├── config.py                 # paths, Ollama URL, model name
│   ├── db.py                     # SQLite via sqlite3 stdlib; schema + migrations
│   ├── auth.py                   # PIN hashing (passlib argon2), session cookies
│   ├── ollama_client.py          # async httpx wrapper, streaming generate()
│   ├── prompts/
│   │   ├── lesson_plan.py        # builds prompt from template + inputs
│   │   ├── assessment.py
│   │   └── templates/            # DepEd reference text (user-provided), embedded as constants
│   ├── routers/
│   │   ├── auth.py
│   │   ├── generate.py           # SSE streaming endpoint
│   │   ├── library.py            # save/list/delete/reopen
│   │   └── print.py              # render HTML → PDF → CUPS lp
│   ├── static/
│   │   ├── index.html            # login + main shell
│   │   ├── app.js                # fetch + EventSource for streaming
│   │   ├── styles.css            # large hit targets, print stylesheet
│   │   └── print.css             # @page rules for clean printing
│   └── templates/                # Jinja2 server-rendered shells
├── deploy/
│   ├── klasbot.service           # systemd unit
│   ├── kiosk.sh                  # autologin + chromium --kiosk
│   ├── setup-pi.sh               # one-shot: apt deps, ollama install, model pull, cups
│   └── update.sh                 # tethered-update flow
├── scripts/
│   ├── seed_admin.py             # creates initial admin PIN
│   └── prompt_eval.py            # runs prompt against Ollama for offline iteration
└── tests/
    ├── test_prompts.py
    ├── test_auth.py
    └── test_library.py
```

---

## Database schema (SQLite)

```sql
CREATE TABLE teachers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  pin_hash TEXT NOT NULL,                  -- argon2
  is_admin INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE outputs (
  id INTEGER PRIMARY KEY,
  teacher_id INTEGER NOT NULL REFERENCES teachers(id),
  kind TEXT NOT NULL CHECK (kind IN ('lesson_plan','assessment')),
  format TEXT,                              -- DLP | SDLP | DLL | quiz | exam
  subject TEXT,
  topic TEXT,
  grade_levels TEXT,                        -- comma-separated
  resources TEXT,                           -- comma-separated
  inputs_json TEXT NOT NULL,                -- raw form snapshot for regenerate
  content_md TEXT NOT NULL,                 -- markdown body
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE sessions (
  token TEXT PRIMARY KEY,
  teacher_id INTEGER NOT NULL REFERENCES teachers(id),
  expires_at TEXT NOT NULL
);
```

---

## MVP build sequence — 3-week solo schedule

The order is deliberate: **highest-risk items first (hardware + AI throughput), UI last.** If hardware delays eat days, the slip is in polish, not in the critical generation loop.

### Week 1 — Hardware foundation + AI prove-out

Goal: a Pi that boots into Chromium kiosk and can stream a lesson plan from Gemma 4.

- Day 1–2: Pi 5 setup. Flash Pi OS Bookworm (64-bit), update firmware, enable autologin, install `chromium-browser`, `cups`, build deps. Capture a baseline SD card image.
- Day 2–3: Install Ollama for ARM64. **First, confirm the exact Gemma 4 tag** on the Ollama library (e.g. `gemma4:e2b`); pull it. Benchmark token throughput, peak RAM, thermals on a representative prompt (target: 600-token lesson plan ≤ 90 s, no thermal throttle with active cooling). If e2B falls short on quality, repeat with e4B and decide on the trade-off. If Gemma 4 is not yet on Ollama for ARM64, the fallback is the previous on-device Google model — make this decision explicitly, do not silently swap.
- Day 3–4: Lock in prompt drafts on a **laptop**, not the Pi (Pi inference is too slow for prompt iteration). Use `scripts/prompt_eval.py` against a remote/local Ollama. Cover: DLP, SDLP, DLL, quiz, exam — one prompt template each, parameterised on subject/topic/grade/resources.
- Day 4–5: FastAPI skeleton — `/healthz`, `/generate` SSE endpoint that proxies streaming tokens from Ollama, basic HTML page that consumes the stream. Run end-to-end on the Pi.
- Day 5: Decide on printer model and verify CUPS prints a hard-coded HTML page via `wkhtmltopdf` → `lp`. Printers are the most common hardware blocker — surface this risk early.

**Risk gate:** If by end of Day 5 the Pi cannot stream a coherent lesson plan in under ~90 s and print it, escalate the trade-off (smaller model? trim prompt? Pi 5 with active cooling?) before building UI on top.

### Week 2 — Core app + persistence

- Day 6: SQLite schema, migrations, `db.py`. Seed-admin script. PIN auth with argon2 + signed session cookie. Kiosk login screen with on-screen number pad (works for both touch and keyboard).
- Day 7: Generation form — subject, topic, grade levels (multi-select), resources (free-text + chip suggestions), output type (lesson plan / assessment), format (DLP/SDLP/DLL/quiz/exam). Posts to `/generate`, streams output into a panel.
- Day 8: Save to library: button on output panel persists `inputs_json` + `content_md`. "My Library" list per teacher with re-open and delete.
- Day 9: Regenerate: re-runs `/generate` with the saved `inputs_json`. Basic inline edit: a `contenteditable` div over the rendered markdown — saves back as markdown via `turndown`-style serialiser, or simpler: edit raw markdown in a textarea with a live preview.
- Day 10: Print pipeline: render the markdown via Jinja + a print-friendly CSS to HTML, hand to `weasyprint` (or `wkhtmltopdf`) for PDF, send to default CUPS printer with `lp`. Include school-name header and date footer.

### Week 3 — Hardening + pilot prep

- Day 11: systemd service for FastAPI; kiosk autostart script (`startx` → `chromium --kiosk http://127.0.0.1:8000 --noerrdialogs --disable-pinch`). Reboot test.
- Day 12: `setup-pi.sh` consolidates everything for a fresh Pi: apt deps, Ollama install, model pull, CUPS config, app install, systemd enable. `update.sh` for tethered-mode updates (git pull + `pip install` + restart).
- Day 13: Manual QA pass — every output type × DLP/SDLP/DLL/quiz/exam, with at least 3 grade-level combos and 3 resource sets. Capture failure modes; fix the top three.
- Day 14: Print quality pass — page breaks, font sizes, multi-page lesson plans. Tweak `print.css`.
- Day 15 (buffer): Documentation, admin guide for adding teachers, golden SD card image for cloning.

---

## Prompt strategy

One template per output type, all in `klasbot/prompts/`. Each template:
1. **System block** — role ("DepEd-aligned teaching assistant for GIDA schools"), tone, hard constraints (English only, must use only the listed resources, must address all listed grade levels).
2. **Few-shot exemplar** — one short reference DLP/SDLP/DLL pulled from the user-provided docs (token-budgeted; trim aggressively for e2B).
3. **User block** — the form inputs in a structured, numbered form.
4. **Output contract** — explicit markdown headers the AI must produce (Objectives / Materials / Procedure / Assessment / Adaptations), so the renderer can rely on them.

Iterate prompts on a laptop with `scripts/prompt_eval.py` before deploying — Pi-side iteration is too slow.

---

## Files referenced and reused

This is a greenfield project (the working directory is empty), so there is no existing code to reuse. The plan above creates everything. The only **external** components reused are:
- **Ollama** (`/usr/local/bin/ollama`, ARM64 build) — local LLM serving.
- **CUPS** (`lp`, `lpstat`) — printing.
- **WeasyPrint** or **wkhtmltopdf** — HTML → PDF.
- **systemd** + **Chromium** — kiosk launch.

---

## Verification (end-to-end smoke test)

Before declaring MVP done, the following must pass on the actual Pi:

1. **Cold boot test** — Power on Pi → kiosk Chromium loads `http://127.0.0.1:8000` automatically within 60 s, login screen visible.
2. **Auth** — Seed admin via `python scripts/seed_admin.py`, log in with PIN, register a second teacher, log out, log back in as second teacher.
3. **Generation latency** — From clicking "Generate" to the first streamed token: ≤ 5 s. Full DLP for Grade 4 Math (Topic: fractions, resources: paper/stones/bottle caps): completes in ≤ 120 s.
4. **Quality spot-check** — Output contains all required DepEd sections, grade-level appropriate, only references provided resources, no hallucinated DepEd codes.
5. **Save → reopen → regenerate** — Save the output, log out, log back in, reopen from "My Library", regenerate produces a different but equivalent draft.
6. **Edit + print** — Edit a typo inline, save, print. Printed page has correct margins, no cut headers, school name + date in header/footer.
7. **Offline test** — Unplug ethernet/Wi-Fi; repeat steps 2–6. Everything still works.
8. **Updater test** — Tether to phone; run `update.sh`; service restarts; everything still works.

---

## Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| **Gemma 4 e2B quality on DepEd templates is too low.** | Day 3 prompt prove-out is the gate. If it fails, swap to e4B (slower) or invest in a longer few-shot prompt. Decide before Day 6. |
| **Gemma 4 not yet packaged for Ollama on ARM64 / Pi 5.** | Verify availability on Day 1. If unavailable, the explicit fallback is the prior on-device Google model in the same e2B/e4B size class — do not silently swap; decide and document. |
| **Pi 5 thermal throttling under sustained generation.** | Active cooling (official Pi 5 cooler); monitor `vcgencmd measure_temp` during benchmark on Day 2. |
| **Printer driver missing on CUPS for the chosen printer.** | Pick the printer **before** Week 1; verify it's CUPS-supported (Brother / HP LaserJet are safest). Test printing on Day 5. |
| **2–3 week timeline slips.** | Cut targets in this order: (1) inline edit → regenerate-only, (2) one lesson-plan format only (DLP), (3) assessment generation moves to a 0.5 release. Save → reopen → regenerate is the last thing to drop — it's the heart of the value. |
| **Teachers reject outputs as "not DepEd enough".** | Pilot with 2–3 teachers in week 3 before declaring done; fold their corrections into the few-shot exemplars. |
| **PIN-only auth on a shared kiosk leaks privacy of saved outputs.** | Library is scoped per teacher in DB queries; admin can reset PINs but cannot read content. Document this as a known limitation. |

---

## Future-phase roadmap (post-MVP)

These are intentionally **not** implemented in the 2–3 week window. They are listed so the MVP architecture doesn't paint them into a corner.

### Phase 2 — Better outputs (~3–4 weeks after MVP)
- DOCX export via `python-docx` from the existing markdown.
- PDF download (already a build step internally — just expose it).
- Rich-text editor (Tiptap) replacing the basic inline edit.
- Filipino / Tagalog generation (test Gemma 4 quality; add prompt translation toggle).

### Phase 3 — Mobile + transfer (~4–6 weeks)
- Bluetooth OBEX file send to teacher phones (BlueZ; pairing UX is the hard part).
- LAN-exposed FastAPI + Android app (Kotlin/Compose or Flutter) that talks to the same API; school Wi-Fi optional.

### Phase 4 — Assessment lifecycle (~2 months)
- Camera-based exam photo capture → OCR (Tesseract) + Gemma scoring of free-response answers.
- Student score tracking, per-class dashboards.
- Learning-progress insights (which competencies a class is struggling with).

### Phase 5 — Offline reference library
- Curated, pre-loaded DepEd MELC reference docs, lesson exemplars, sample materials.
- Local search (SQLite FTS5) so teachers can browse references without internet.

Each phase keeps the localhost-FastAPI + SQLite + Ollama core intact; new features are additive routers and tables.

---

## Open items the user still owes

- **DepEd template reference docs** (DLP / SDLP / DLL samples). Needed before Day 3.
- **Printer model decision.** Needed before Day 5.
- **Pilot school identification** for end-of-week-3 user testing.
