# Quiz Photo Grading Feature Plan

## Goal

Add a teacher workflow where a teacher uploads or captures one or more photos of completed student quizzes or worksheets, Klasbot extracts each student's submission, asks the grading LLM to evaluate the work against an answer key or rubric, and returns per-student results plus an overall summary that the teacher can review, edit, save, and print.

This is a post-MVP feature. It should not block the existing offline lesson-plan and assessment-generation loop.

## Intended teacher workflow

1. The teacher opens **Grade Quiz Photo** from the Klasbot home screen.
2. The teacher enters quiz metadata:
   - subject;
   - grade level;
   - topic or competency;
   - total possible points;
   - grading style: exact-answer, partial-credit, rubric-based, or teacher-review only;
   - optional answer key and optional rubric.
3. The teacher uploads or captures photos:
   - one photo may contain one student worksheet;
   - one photo may contain multiple worksheets from different students;
   - a grading batch may contain multiple photos.
4. Klasbot creates a preview of detected student submissions. The teacher can confirm, split, merge, rotate, crop, or assign names before grading.
5. Klasbot runs extraction and grading for each detected student submission.
6. The teacher reviews a table with:
   - student name or detected identifier;
   - detected student answer per item;
   - expected correct answer per item;
   - item-level score and feedback;
   - overall score, percentage, and rating;
   - confidence and warnings when handwriting, cropping, or answer-key matching is uncertain.
7. The teacher edits corrections if needed, saves the graded batch, and optionally prints a report.

## Scope

### In scope for the first implementation

- Upload/capture images from the existing web UI.
- Support PNG and JPEG images.
- Store original images locally with private batch ownership scoped to the logged-in teacher.
- Detect whether a photo contains one worksheet or multiple worksheet regions.
- Let the teacher confirm student boundaries before final grading.
- OCR or vision extraction of printed text and handwritten answers.
- Grade using a teacher-provided answer key or rubric.
- Return structured JSON that can be rendered into an editable grading table.
- Save grading batches and per-student grading results in SQLite.
- Print a batch summary and individual student feedback sheets.

### Out of scope for the first implementation

- Fully automatic grade-book analytics across a whole school.
- High-stakes exam certification without teacher review.
- Long-term student performance dashboards beyond saving batch results.
- Cloud-only processing as the default path.
- Guaranteed recognition of very poor handwriting, blurred photos, or missing answer keys.

## Key product decisions to make before implementation

| Decision | Recommended default | Reason |
| --- | --- | --- |
| Vision engine | Two-stage OCR/segmentation plus LLM grading | A pure LLM-vision call is simpler, but a structured OCR layer improves debuggability and teacher review. |
| Offline behavior | Keep an offline-first path; allow an optional online/high-quality provider later | Klasbot's core deployment target is offline GIDA schools. |
| Answer key | Require an answer key for exact-answer quizzes; allow rubric-only for open-ended work | Reduces hallucinated grading and makes the output auditable. |
| Multiple worksheets in one photo | Detect regions automatically, then require teacher confirmation | Prevents one student's answers from being mixed with another student's score. |
| Final authority | Teacher review required before saving official results | LLM grading can be wrong, especially for handwriting and partial credit. |

## Proposed architecture

```text
[Teacher web UI]
  └── POST /api/grading/batches
      └── creates batch metadata
  └── POST /api/grading/batches/{id}/images
      └── stores original image files
      └── creates image records
  └── POST /api/grading/batches/{id}/detect-submissions
      └── image preprocessing + worksheet region detection
      └── teacher confirmation screen
  └── POST /api/grading/batches/{id}/grade
      └── OCR/vision extraction
      └── LLM grading with structured JSON output
      └── validation and confidence warnings
  └── PATCH /api/grading/submissions/{id}
      └── teacher edits names, extracted answers, scores, or feedback
  └── POST /api/grading/batches/{id}/print
      └── printable summary and per-student reports
```

### Backend components

- `klasbot/grading/images.py` for upload validation, image normalization, rotation, compression, and thumbnail generation.
- `klasbot/grading/detection.py` for worksheet boundary detection and grouping.
- `klasbot/grading/extraction.py` for OCR or multimodal answer extraction.
- `klasbot/grading/prompts.py` for answer-key-aware grading prompts and JSON schema instructions.
- `klasbot/grading/scoring.py` for deterministic score calculation, validation, and confidence flags.
- `klasbot/grading/reports.py` for printable batch and student reports.
- `klasbot/grading/router.py` for the FastAPI endpoints.

### Frontend components

- Add a **Grade Quiz Photo** entry point to the main app shell.
- Add a batch setup form for quiz metadata and answer key/rubric entry.
- Add an upload/capture screen with image-quality hints.
- Add a worksheet-detection review screen where teachers can crop, split, merge, rotate, and assign student names.
- Add a grading review table with editable extracted answers, correct answers, scores, feedback, and warnings.
- Add print controls for batch summary and per-student reports.

## Data model

Add the following SQLite tables. Exact column names can be adjusted during implementation, but the model should preserve the separation between original image, detected submission, extracted answers, and teacher-approved score.

```sql
CREATE TABLE grading_batches (
  id INTEGER PRIMARY KEY,
  teacher_id INTEGER NOT NULL REFERENCES teachers(id),
  subject TEXT,
  grade_level TEXT,
  topic TEXT,
  total_points REAL NOT NULL,
  grading_style TEXT NOT NULL CHECK (grading_style IN ('exact','partial','rubric','review_only')),
  answer_key_json TEXT,
  rubric_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE grading_images (
  id INTEGER PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES grading_batches(id) ON DELETE CASCADE,
  original_path TEXT NOT NULL,
  thumbnail_path TEXT,
  mime_type TEXT NOT NULL,
  width INTEGER,
  height INTEGER,
  quality_warnings_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE grading_submissions (
  id INTEGER PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES grading_batches(id) ON DELETE CASCADE,
  image_id INTEGER REFERENCES grading_images(id) ON DELETE SET NULL,
  student_name TEXT,
  student_identifier TEXT,
  crop_box_json TEXT,
  extracted_answers_json TEXT,
  grading_result_json TEXT,
  score REAL,
  max_score REAL,
  confidence REAL,
  teacher_reviewed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Image processing plan

1. Validate file type and size.
2. Normalize orientation from EXIF metadata.
3. Generate a smaller preview and thumbnail for the UI.
4. Run quality checks:
   - blur detection;
   - low-light detection;
   - extreme perspective/skew;
   - low resolution;
   - large shadows or glare.
5. Detect worksheet boundaries:
   - first pass: page-like contour detection;
   - second pass: optional grid/region detection for photos with several worksheets;
   - fallback: whole image as one submission if boundaries are uncertain.
6. Present detected regions for teacher confirmation before grading.
7. Store crop boxes rather than duplicating large cropped images unless performance requires cached crops.

## LLM grading plan

### Prompt contract

The grading prompt must require structured JSON, not free-form prose. The response should include:

- batch-level warnings;
- one object per student submission;
- detected student name or identifier;
- item-level answers;
- item-level expected answer;
- item-level score;
- item-level feedback;
- overall score;
- confidence;
- evidence notes for uncertain handwriting or unclear image regions.

Example response shape:

```json
{
  "submissions": [
    {
      "student_name": "Detected or blank",
      "student_identifier": "Optional",
      "items": [
        {
          "item_number": "1",
          "student_answer": "...",
          "correct_answer": "...",
          "score": 1,
          "max_score": 1,
          "feedback": "Correct.",
          "confidence": 0.92,
          "warnings": []
        }
      ],
      "total_score": 8,
      "max_score": 10,
      "rating": "80%",
      "overall_feedback": "...",
      "warnings": ["Item 7 handwriting is unclear."]
    }
  ]
}
```

### Guardrails

- The model must not invent missing student names.
- The model must mark unreadable answers as uncertain instead of guessing.
- The model must use the teacher-provided answer key or rubric when present.
- The model must explain partial-credit decisions item by item.
- The model output must be schema-validated before it is saved.
- If validation fails, retry once with a repair prompt; if it still fails, mark the batch as needing manual review.

## Multiple-student photo handling

A photo with multiple worksheets should be treated as a batch image containing multiple candidate submissions.

1. Detect candidate worksheet regions.
2. Display region cards in the UI.
3. Let the teacher:
   - confirm a region;
   - delete false detections;
   - split one region into multiple submissions;
   - merge duplicate regions;
   - assign or edit student names.
4. Grade each confirmed region independently.
5. Save each student's results under the same batch.

This workflow is intentionally teacher-confirmed because automatic segmentation mistakes can cause serious grading errors.

## Teacher review and auditability

Every generated grade should remain editable and traceable:

- keep the original image path;
- keep the crop box used for each student;
- keep the extracted answer JSON separately from the final grading JSON;
- store whether the teacher reviewed the submission;
- show confidence and warnings prominently;
- allow the teacher to override extracted answers, item scores, total score, and feedback;
- print or export only teacher-reviewed results by default.

## Privacy and storage

- Store quiz images in a teacher-scoped local data directory, not in `klasbot/static`.
- Never expose original image paths directly through static file serving.
- Serve thumbnails and crops through authenticated routes that verify ownership.
- Add a batch-delete action that removes database rows and image files.
- Document that photos may contain student personal information and should be reviewed before sharing or printing.

## Suggested implementation phases

### Phase 1: Planning spike and UX prototype

- Add this plan to the project documentation.
- Create low-fidelity screens for batch setup, upload, detection review, and grading review.
- Decide the exact offline OCR and LLM-vision stack after testing on the target Raspberry Pi hardware.
- Define JSON schemas for answer extraction and grading output.

### Phase 2: Data model and image upload foundation

- Add migrations for grading tables.
- Add upload endpoints, image validation, thumbnail generation, and authenticated image preview routes.
- Add the batch setup and upload UI.
- Add tests for file validation, teacher ownership, and delete cleanup.

### Phase 3: Worksheet detection and teacher confirmation

- Implement image normalization and first-pass worksheet boundary detection.
- Add detection review UI for crop, rotate, split, merge, and name assignment.
- Add tests for one-worksheet, multi-worksheet, and low-quality-image cases.

### Phase 4: Extraction and grading

- Implement answer extraction.
- Implement answer-key/rubric-aware grading prompts.
- Validate LLM JSON responses and add repair retry.
- Add the editable grading table.
- Add tests using fixture images and mocked LLM responses.

### Phase 5: Reporting and pilot hardening

- Save final teacher-reviewed results.
- Add printable batch summary and per-student feedback sheets.
- Add image retention/delete documentation.
- Run a pilot QA pass with real teacher worksheets and capture known failure modes.

## Acceptance criteria

- A teacher can create a grading batch and upload at least one image.
- A single worksheet image produces one student submission.
- A multi-worksheet image can produce multiple confirmed student submissions.
- The teacher can assign or correct student names before grading.
- The LLM returns item-level student answers, correct answers, scores, feedback, and overall score.
- Teacher edits persist after saving.
- Results are scoped to the logged-in teacher.
- Batch deletion removes associated local image files.
- Printed reports include the quiz metadata, student score, item-level feedback, and any warnings.
- Low-confidence or unreadable answers are flagged instead of silently guessed.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Handwriting recognition is unreliable on low-cost hardware. | Require teacher review, show confidence warnings, and allow manual correction before saving. |
| The target local model may not support image input well enough. | Keep OCR/segmentation modular so a better offline or optional online provider can be swapped in. |
| Multiple worksheets are segmented incorrectly. | Require teacher confirmation and provide split/merge/crop controls. |
| LLM grading hallucination or unfair partial credit. | Require answer keys/rubrics, schema validation, deterministic score totals, and teacher approval. |
| Large images fill Raspberry Pi storage. | Generate thumbnails, compress previews, add retention settings, and delete files with batch deletion. |
| Student privacy leaks through static files. | Serve images through authenticated routes and keep files outside the public static directory. |

## Open questions

- What camera source should be prioritized first: phone upload over LAN, USB webcam, or file picker from the kiosk?
- Should answer keys be typed by the teacher, generated from an existing Klasbot assessment, or both?
- Should Klasbot support anonymous grading, named grading, or both?
- What is the minimum acceptable local grading accuracy before this feature is shown in pilot schools?
- How long should image files be retained after a batch is graded and printed?
