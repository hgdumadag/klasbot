# Student Management Feature Plan

## Goal

Add a basic, offline-first student management module to Klasbot so a teacher can record students, capture assessment scores, and review simple class performance dashboards. The first target scenario is a Grade 6 Science class, but the model should support other grades, sections, and subjects without redesign.

## MVP outcomes

Teachers should be able to:

1. Create or select a class such as `Grade 6 - Science`.
2. Add and edit students in that class.
3. Create assessment records for exams, quizzes, projects, performance tasks, or other teacher-defined assessment types.
4. Enter each student's score, total possible score, date, and optional notes.
5. View a minimal dashboard showing class average, highest and lowest scores, assessment trends, and students who may need attention.
6. Keep all records in the local SQLite database so the feature works without internet access.

## Non-goals for the first release

The first release should not include automated grading, photo-based answer checking, parent/student accounts, cloud sync, official grade transmutation rules, complex report cards, or district-level analytics. Those can be added after the basic data model and teacher workflow are proven in the classroom.

## User roles and permissions

| Role | Capability |
| --- | --- |
| Teacher | Manage only their own classes, students, assessments, scores, and dashboards. |
| Admin | Create teacher accounts and optionally help recover or archive class data. Admin access to student records should be treated as a future policy decision. |

## Core data model

The module should extend the existing SQLite database with normalized tables:

```sql
CREATE TABLE classes (
  id INTEGER PRIMARY KEY,
  teacher_id INTEGER NOT NULL REFERENCES teachers(id),
  name TEXT NOT NULL,
  grade_level TEXT NOT NULL,
  section TEXT,
  subject TEXT NOT NULL,
  school_year TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE students (
  id INTEGER PRIMARY KEY,
  teacher_id INTEGER NOT NULL REFERENCES teachers(id),
  learner_reference_number TEXT,
  first_name TEXT NOT NULL,
  middle_name TEXT,
  last_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','transferred')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE class_enrollments (
  id INTEGER PRIMARY KEY,
  class_id INTEGER NOT NULL REFERENCES classes(id),
  student_id INTEGER NOT NULL REFERENCES students(id),
  enrolled_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (class_id, student_id)
);

CREATE TABLE assessments (
  id INTEGER PRIMARY KEY,
  class_id INTEGER NOT NULL REFERENCES classes(id),
  title TEXT NOT NULL,
  assessment_type TEXT NOT NULL CHECK (assessment_type IN ('exam','quiz','project','performance_task','assignment','other')),
  assessment_date TEXT NOT NULL,
  max_score REAL NOT NULL CHECK (max_score > 0),
  weight REAL,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE scores (
  id INTEGER PRIMARY KEY,
  assessment_id INTEGER NOT NULL REFERENCES assessments(id),
  student_id INTEGER NOT NULL REFERENCES students(id),
  score REAL CHECK (score >= 0),
  is_absent INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (assessment_id, student_id)
);
```

Implementation notes:

- Scope every query by `teacher_id` through either `classes.teacher_id` or `students.teacher_id`.
- Store raw scores and `max_score`; calculate percentages at read time to preserve the original record.
- Allow blank scores for students who have not yet been graded, and use `is_absent` to distinguish absences from zero scores.
- Keep the schema simple enough for CSV import/export in a later release.

## Feature set

### 1. Class setup

- Teacher opens a new **Students** or **Class Records** area from the main app.
- Teacher creates a class with grade level, section, subject, school year, and a friendly name.
- Example: Grade Level `6`, Section `A`, Subject `Science`, School Year `2026-2027`, Name `Grade 6A Science`.

### 2. Student roster

- Teacher can add students one at a time with first name, last name, optional middle name, optional learner reference number, and active/inactive status.
- Teacher can enroll an existing student in one or more classes.
- Roster view should show student name, status, latest average, and missing/absent assessment count.
- For the MVP, avoid bulk import unless the UI is already straightforward; add CSV import after manual entry works reliably.

### 3. Assessment creation

- Teacher selects a class and creates an assessment.
- Required fields: title, type, date, and maximum score.
- Optional fields: weight and notes.
- Example: `Quiz 1: Human Body Systems`, type `quiz`, date `2026-06-15`, maximum score `20`.

### 4. Score entry

- Teacher opens an assessment and sees a roster-style table.
- Each row has student name, score input, absent checkbox, and optional note.
- Save should upsert score records so teachers can correct entries.
- Validate that scores do not exceed the assessment maximum unless the teacher explicitly changes the maximum score.
- Use large input controls and a simple keyboard-friendly flow for kiosk use.

### 5. Class dashboard

For a selected class, show:

- Class average percentage across selected assessments.
- Highest and lowest assessment averages.
- Number of enrolled students.
- Number of missing or absent scores.
- Recent assessments with average, highest score, lowest score, and completion count.
- Student performance table with each student's average percentage and status indicator.

Suggested simple indicators:

| Indicator | Rule |
| --- | --- |
| On Track | Average is at or above the configured target, such as 75%. |
| Watch | Average is below target or missing multiple scores. |
| No Data | Student has no recorded scores yet. |

### 6. Assessment dashboard

For a selected assessment, show:

- Assessment average.
- Highest and lowest score.
- Score distribution buckets, such as `0-59%`, `60-74%`, `75-89%`, and `90-100%`.
- Students absent or missing scores.
- Quick edit button to return to score entry.

## User interface plan

Add one top-level navigation item: **Class Records**.

Recommended screens:

1. **Class List**: Teacher's classes with grade, subject, section, student count, and latest average.
2. **Class Detail**: Tabs for Dashboard, Students, Assessments, and Settings.
3. **Students Tab**: Roster list plus add/edit student dialog.
4. **Assessments Tab**: Assessment list plus create/edit assessment dialog.
5. **Score Entry Screen**: Table optimized for fast score entry.
6. **Dashboard Tab**: Cards and tables summarizing class and student performance.

Keep the MVP UI text-based with small tables and cards. Charts can be added later, but initial dashboard metrics should work without JavaScript chart dependencies.

## API plan

Add endpoints under `/api/class-records`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/classes` | List teacher's classes. |
| `POST` | `/classes` | Create class. |
| `GET` | `/classes/{class_id}` | Get class detail and dashboard summary. |
| `PATCH` | `/classes/{class_id}` | Update class metadata. |
| `GET` | `/classes/{class_id}/students` | List enrolled students. |
| `POST` | `/classes/{class_id}/students` | Create/enroll student. |
| `PATCH` | `/students/{student_id}` | Update student. |
| `GET` | `/classes/{class_id}/assessments` | List assessments. |
| `POST` | `/classes/{class_id}/assessments` | Create assessment. |
| `PATCH` | `/assessments/{assessment_id}` | Update assessment. |
| `GET` | `/assessments/{assessment_id}/scores` | Load score-entry grid. |
| `PUT` | `/assessments/{assessment_id}/scores` | Save score-entry grid. |
| `GET` | `/classes/{class_id}/dashboard` | Return dashboard metrics. |

All endpoints must validate that the logged-in teacher owns the requested class, assessment, or student before returning or changing data.

## Dashboard calculations

Use straightforward calculations first:

- Student assessment percentage: `score / max_score * 100`.
- Assessment average: average of non-absent, non-null percentages for that assessment.
- Student class average: average of the student's non-absent, non-null assessment percentages in the class.
- Class average: average of student class averages, excluding students with no data.
- Missing count: number of enrolled students without a score record for an assessment.
- Absent count: number of score records marked `is_absent = 1`.

Weighted grading can be introduced later by multiplying assessment percentages by `assessments.weight` only when a class has a complete weighting policy.

## Implementation phases

### Phase 1: Database and backend foundations

- Add SQLite migrations for classes, students, enrollments, assessments, and scores.
- Add Python data access helpers with teacher-scoped queries.
- Add API endpoints for class, roster, assessment, and score CRUD.
- Add backend validation and tests for authorization, score bounds, absent scores, and dashboard calculations.

### Phase 2: Manual entry workflow

- Add **Class Records** navigation.
- Build class list, class detail, student roster, assessment list, and score-entry screens.
- Keep interactions simple: form submit, fetch, render table, save.
- Add UI tests for creating a class, adding a student, creating an assessment, saving scores, and reopening saved scores.

### Phase 3: Minimal dashboards

- Add class dashboard summary endpoint and UI cards.
- Add assessment dashboard summary.
- Add warning states for missing data and students below target.
- Add print-friendly dashboard styles for teacher records.

### Phase 4: Pilot hardening

- Pilot with one teacher and one Grade 6 Science class.
- Test offline use, kiosk readability, and speed of score entry.
- Add CSV export if teachers need a backup copy before broader use.
- Defer CSV import, charts, and weighted grading until manual entry is stable.

## Acceptance criteria

The feature is ready for MVP pilot when:

1. A teacher can create `Grade 6 Science` and add at least 30 students.
2. A teacher can create an exam, quiz, and performance task for that class.
3. A teacher can enter, edit, and save scores for all students in each assessment.
4. Closing and reopening the app preserves all class, student, assessment, and score records.
5. The class dashboard displays class average, student count, missing or absent score count, and student status indicators.
6. The assessment dashboard displays average, highest score, lowest score, distribution buckets, and missing or absent students.
7. Tests cover teacher data isolation so one teacher cannot read or modify another teacher's class records.

## Future enhancements

- CSV import and export.
- Printable class record sheets.
- Weighted grading policies by subject or assessment category.
- Per-student history pages with notes and intervention reminders.
- Local-only backup and restore tools.
- Optional analytics generated from saved lesson plans and assessments.
- Parent-friendly progress summaries that can be printed without exposing other students' scores.
