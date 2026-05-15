from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from klasbot.config import get_db_path
from klasbot.lesson_formats import DEFAULT_LESSON_PLAN_FORMATS, editable_lesson_format_structure


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS teachers (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              pin_hash TEXT NOT NULL,
              is_admin INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS outputs (
              id INTEGER PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              kind TEXT NOT NULL CHECK (kind IN ('lesson_plan','assessment')),
              format TEXT,
              subject TEXT,
              topic TEXT,
              week_number INTEGER,
              grade_levels TEXT,
              resources TEXT,
              inputs_json TEXT NOT NULL,
              content_md TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
              token TEXT PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              expires_at TEXT NOT NULL,
              csrf_token TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS mobile_pairing_tokens (
              token TEXT PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              expires_at TEXT NOT NULL,
              consumed_at TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS shared_exports (
              token TEXT PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              output_id INTEGER NOT NULL REFERENCES outputs(id) ON DELETE CASCADE,
              filename TEXT NOT NULL,
              file_path TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              download_count INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS teaching_aids (
              id INTEGER PRIMARY KEY,
              output_id INTEGER NOT NULL REFERENCES outputs(id) ON DELETE CASCADE,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              aid_type TEXT NOT NULL,
              title TEXT NOT NULL,
              source_section TEXT NOT NULL DEFAULT '',
              inputs_json TEXT NOT NULL,
              content_md TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS curriculum_documents (
              id INTEGER PRIMARY KEY,
              subject TEXT NOT NULL,
              title TEXT NOT NULL,
              filename TEXT NOT NULL,
              stored_path TEXT NOT NULL,
              version_label TEXT NOT NULL,
              active INTEGER NOT NULL DEFAULT 1,
              parse_summary_json TEXT NOT NULL DEFAULT '{}',
              uploaded_by INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS curriculum_units (
              id INTEGER PRIMARY KEY,
              document_id INTEGER NOT NULL REFERENCES curriculum_documents(id) ON DELETE CASCADE,
              subject TEXT NOT NULL,
              grade_level TEXT NOT NULL,
              quarter INTEGER NOT NULL,
              domain TEXT NOT NULL,
              content TEXT NOT NULL,
              content_standards TEXT NOT NULL,
              performance_standard TEXT NOT NULL,
              suggested_tasks TEXT NOT NULL,
              source_pages TEXT NOT NULL,
              raw_text TEXT NOT NULL,
              confidence REAL NOT NULL DEFAULT 0,
              warnings_json TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS curriculum_competencies (
              id INTEGER PRIMARY KEY,
              unit_id INTEGER NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,
              sequence INTEGER NOT NULL,
              competency_text TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS curriculum_unit_weeks (
              id INTEGER PRIMARY KEY,
              unit_id INTEGER NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,
              week_number INTEGER NOT NULL CHECK (week_number BETWEEN 1 AND 10),
              focus TEXT NOT NULL,
              notes TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now')),
              UNIQUE(unit_id, week_number)
            );

            CREATE TABLE IF NOT EXISTS curriculum_unit_week_competencies (
              week_id INTEGER NOT NULL REFERENCES curriculum_unit_weeks(id) ON DELETE CASCADE,
              competency_id INTEGER NOT NULL REFERENCES curriculum_competencies(id) ON DELETE CASCADE,
              PRIMARY KEY (week_id, competency_id)
            );

            CREATE TABLE IF NOT EXISTS lesson_plan_formats (
              format TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              requirements TEXT NOT NULL,
              updated_by INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS grading_batches (
              id INTEGER PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
              assessment_id INTEGER REFERENCES assessments(id) ON DELETE SET NULL,
              subject TEXT,
              grade_level TEXT,
              topic TEXT,
              quarter INTEGER,
              week_number INTEGER,
              week_topic TEXT,
              questions_text TEXT,
              total_points REAL NOT NULL,
              grading_style TEXT NOT NULL CHECK (grading_style IN ('exact','partial','rubric','review_only')),
              answer_key_json TEXT,
              rubric_json TEXT,
              status TEXT NOT NULL DEFAULT 'draft',
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS grading_images (
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

            CREATE TABLE IF NOT EXISTS grading_submissions (
              id INTEGER PRIMARY KEY,
              batch_id INTEGER NOT NULL REFERENCES grading_batches(id) ON DELETE CASCADE,
              image_id INTEGER REFERENCES grading_images(id) ON DELETE SET NULL,
              student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
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

            CREATE TABLE IF NOT EXISTS classes (
              id INTEGER PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              name TEXT NOT NULL,
              grade_level TEXT NOT NULL,
              section TEXT,
              subject TEXT NOT NULL,
              school_year TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS students (
              id INTEGER PRIMARY KEY,
              teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
              learner_reference_number TEXT,
              first_name TEXT NOT NULL,
              middle_name TEXT,
              last_name TEXT NOT NULL,
              display_name TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','transferred')),
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS class_enrollments (
              id INTEGER PRIMARY KEY,
              class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
              student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
              enrolled_at TEXT NOT NULL DEFAULT (datetime('now')),
              UNIQUE (class_id, student_id)
            );

            CREATE TABLE IF NOT EXISTS assessments (
              id INTEGER PRIMARY KEY,
              class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
              title TEXT NOT NULL,
              assessment_type TEXT NOT NULL CHECK (assessment_type IN ('exam','quiz','project','performance_task','assignment','other')),
              assessment_date TEXT NOT NULL,
              max_score REAL NOT NULL CHECK (max_score > 0),
              weight REAL,
              notes TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scores (
              id INTEGER PRIMARY KEY,
              assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
              student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
              score REAL CHECK (score >= 0),
              is_absent INTEGER NOT NULL DEFAULT 0,
              notes TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now')),
              UNIQUE (assessment_id, student_id)
            );

            CREATE TABLE IF NOT EXISTS schema_migrations (
              name TEXT PRIMARY KEY,
              applied_at TEXT NOT NULL
            );
            """
        )
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS curriculum_fts USING fts5(
              subject,
              grade_level,
              quarter,
              domain,
              content,
              content_standards,
              competencies,
              performance_standard,
              suggested_tasks,
              unit_id UNINDEXED
            )
            """
        )
        _ensure_column(connection, "curriculum_documents", "parse_summary_json", "TEXT NOT NULL DEFAULT '{}'")
        _ensure_column(connection, "curriculum_units", "confidence", "REAL NOT NULL DEFAULT 0")
        _ensure_column(connection, "curriculum_units", "warnings_json", "TEXT NOT NULL DEFAULT '[]'")
        _ensure_column(connection, "outputs", "week_number", "INTEGER")
        _ensure_column(connection, "sessions", "csrf_token", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(connection, "grading_batches", "quarter", "INTEGER")
        _ensure_column(connection, "grading_batches", "week_number", "INTEGER")
        _ensure_column(connection, "grading_batches", "week_topic", "TEXT")
        _ensure_column(connection, "grading_batches", "questions_text", "TEXT")
        _ensure_column(connection, "grading_batches", "class_id", "INTEGER REFERENCES classes(id) ON DELETE SET NULL")
        _ensure_column(connection, "grading_batches", "assessment_id", "INTEGER REFERENCES assessments(id) ON DELETE SET NULL")
        _ensure_column(connection, "grading_submissions", "student_id", "INTEGER REFERENCES students(id) ON DELETE SET NULL")
        _run_weekly_pacing_migration(connection)
        _run_weekly_pacing_focus_migration(connection)
        ensure_all_curriculum_pacing(connection)
        _seed_lesson_plan_formats(connection)


def _run_weekly_pacing_migration(connection: sqlite3.Connection) -> None:
    migration_name = "weekly_pacing_v1_drop_outputs"
    row = connection.execute(
        "SELECT name FROM schema_migrations WHERE name = ?",
        (migration_name,),
    ).fetchone()
    if row:
        return
    connection.execute("DELETE FROM shared_exports")
    connection.execute("DELETE FROM outputs")
    connection.execute(
        "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
        (migration_name, utc_now()),
    )


def _run_weekly_pacing_focus_migration(connection: sqlite3.Connection) -> None:
    migration_name = "weekly_pacing_v2_descriptive_focus"
    row = connection.execute(
        "SELECT name FROM schema_migrations WHERE name = ?",
        (migration_name,),
    ).fetchone()
    if row:
        return
    rows = connection.execute("SELECT id FROM curriculum_units ORDER BY id").fetchall()
    for row in rows:
        reset_curriculum_unit_pacing(connection, int(row["id"]))
    connection.execute(
        "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
        (migration_name, utc_now()),
    )


def _ensure_column(
    connection: sqlite3.Connection, table_name: str, column_name: str, definition: str
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def _seed_lesson_plan_formats(connection: sqlite3.Connection) -> None:
    now = utc_now()
    for format_name, defaults in DEFAULT_LESSON_PLAN_FORMATS.items():
        connection.execute(
            """
            INSERT OR IGNORE INTO lesson_plan_formats (
              format, title, requirements, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (format_name, defaults["title"], defaults["requirements"], now, now),
        )


def list_lesson_plan_formats() -> list[dict[str, Any]]:
    try:
        return _list_lesson_plan_formats()
    except sqlite3.OperationalError as exc:
        if "lesson_plan_formats" not in str(exc):
            raise
        init_db()
        return _list_lesson_plan_formats()


def _list_lesson_plan_formats() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT format, title, requirements, updated_by, created_at, updated_at
            FROM lesson_plan_formats
            ORDER BY CASE format
              WHEN 'DLP' THEN 1
              WHEN 'SDLP' THEN 2
              WHEN 'DLL' THEN 3
              ELSE 4
            END, format COLLATE NOCASE
            """
        ).fetchall()
        if not rows:
            _seed_lesson_plan_formats(connection)
            rows = connection.execute(
                """
                SELECT format, title, requirements, updated_by, created_at, updated_at
                FROM lesson_plan_formats
                ORDER BY CASE format
                  WHEN 'DLP' THEN 1
                  WHEN 'SDLP' THEN 2
                  WHEN 'DLL' THEN 3
                  ELSE 4
                END, format COLLATE NOCASE
                """
            ).fetchall()
        formats = [dict(row) for row in rows]
        for format_config in formats:
            format_config["requirements"] = editable_lesson_format_structure(format_config["requirements"])
        return formats


def get_lesson_plan_format(format_name: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT format, title, requirements, updated_by, created_at, updated_at
            FROM lesson_plan_formats
            WHERE upper(format) = upper(?)
            """,
            (format_name,),
        ).fetchone()
        format_config = row_to_dict(row)
        if format_config:
            format_config["requirements"] = editable_lesson_format_structure(format_config["requirements"])
        return format_config


def update_lesson_plan_format(
    format_name: str,
    title: str,
    requirements: str,
    updated_by: int | None,
) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        cursor = connection.execute(
            """
            UPDATE lesson_plan_formats
            SET title = ?, requirements = ?, updated_by = ?, updated_at = ?
            WHERE upper(format) = upper(?)
            """,
            (title.strip(), requirements.strip(), updated_by, now, format_name),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            """
            SELECT format, title, requirements, updated_by, created_at, updated_at
            FROM lesson_plan_formats
            WHERE upper(format) = upper(?)
            """,
            (format_name,),
        ).fetchone()
        format_config = row_to_dict(row)
        if format_config:
            format_config["requirements"] = editable_lesson_format_structure(format_config["requirements"])
        return format_config


def reset_lesson_plan_format(format_name: str, updated_by: int | None) -> dict[str, Any] | None:
    defaults = DEFAULT_LESSON_PLAN_FORMATS.get(format_name.upper())
    if not defaults:
        return None
    return update_lesson_plan_format(
        format_name,
        defaults["title"],
        defaults["requirements"],
        updated_by,
    )


def create_teacher(name: str, pin_hash: str, is_admin: bool = False) -> dict[str, Any]:
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO teachers (name, pin_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name.strip(), pin_hash, int(is_admin), utc_now()),
        )
        row = connection.execute(
            "SELECT id, name, is_admin, created_at FROM teachers WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return dict(row)


def list_teachers(include_hash: bool = False) -> list[dict[str, Any]]:
    columns = "id, name, pin_hash, is_admin, created_at" if include_hash else "id, name, is_admin, created_at"
    with connect() as connection:
        rows = connection.execute(
            f"SELECT {columns} FROM teachers ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [dict(row) for row in rows]


def get_teacher(teacher_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, is_admin, created_at FROM teachers WHERE id = ?",
            (teacher_id,),
        ).fetchone()
        return row_to_dict(row)


def update_teacher_pin(teacher_id: int, pin_hash: str) -> dict[str, Any] | None:
    with connect() as connection:
        connection.execute(
            "UPDATE teachers SET pin_hash = ? WHERE id = ?",
            (pin_hash, teacher_id),
        )
        row = connection.execute(
            "SELECT id, name, is_admin, created_at FROM teachers WHERE id = ?",
            (teacher_id,),
        ).fetchone()
        return row_to_dict(row)


def create_session(token: str, teacher_id: int, expires_at: str, csrf_token: str = "") -> None:
    with connect() as connection:
        connection.execute(
            "INSERT INTO sessions (token, teacher_id, expires_at, csrf_token) VALUES (?, ?, ?, ?)",
            (token, teacher_id, expires_at, csrf_token),
        )


def delete_session(token: str) -> None:
    with connect() as connection:
        connection.execute("DELETE FROM sessions WHERE token = ?", (token,))


def get_session(token: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT sessions.token, sessions.teacher_id, sessions.expires_at, sessions.csrf_token,
                   teachers.name, teachers.is_admin
            FROM sessions
            JOIN teachers ON teachers.id = sessions.teacher_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
        return row_to_dict(row)


def prune_expired_sessions() -> None:
    with connect() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now(),))


def create_mobile_pairing_token(token: str, teacher_id: int, expires_at: str) -> dict[str, Any]:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO mobile_pairing_tokens (token, teacher_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, teacher_id, expires_at, utc_now()),
        )
        pairing = get_mobile_pairing_token(token, connection=connection)
        assert pairing is not None
        return pairing


def get_mobile_pairing_token(
    token: str, connection: sqlite3.Connection | None = None
) -> dict[str, Any] | None:
    close_connection = connection is None
    active_connection = connection or connect()
    try:
        row = active_connection.execute(
            """
            SELECT mobile_pairing_tokens.token, mobile_pairing_tokens.teacher_id,
                   mobile_pairing_tokens.expires_at, mobile_pairing_tokens.consumed_at,
                   mobile_pairing_tokens.created_at, teachers.name, teachers.is_admin
            FROM mobile_pairing_tokens
            JOIN teachers ON teachers.id = mobile_pairing_tokens.teacher_id
            WHERE mobile_pairing_tokens.token = ?
            """,
            (token,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        if close_connection:
            active_connection.close()


def consume_mobile_pairing_token(token: str) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        pairing = get_mobile_pairing_token(token, connection=connection)
        if not pairing or pairing["consumed_at"] or pairing["expires_at"] <= now:
            return None
        connection.execute(
            "UPDATE mobile_pairing_tokens SET consumed_at = ? WHERE token = ?",
            (now, token),
        )
        pairing["consumed_at"] = now
        return pairing


def prune_mobile_pairing_tokens() -> None:
    with connect() as connection:
        connection.execute(
            "DELETE FROM mobile_pairing_tokens WHERE expires_at <= ? OR consumed_at IS NOT NULL",
            (utc_now(),),
        )


def create_shared_export(
    token: str,
    teacher_id: int,
    output_id: int,
    filename: str,
    file_path: str,
    expires_at: str,
) -> dict[str, Any]:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO shared_exports (
              token, teacher_id, output_id, filename, file_path, expires_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (token, teacher_id, output_id, filename, file_path, expires_at, utc_now()),
        )
        row = connection.execute(
            """
            SELECT token, teacher_id, output_id, filename, file_path, expires_at,
                   download_count, created_at
            FROM shared_exports
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
        export = row_to_dict(row)
        assert export is not None
        return export


def get_shared_export(token: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT token, teacher_id, output_id, filename, file_path, expires_at,
                   download_count, created_at
            FROM shared_exports
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
        return row_to_dict(row)


def increment_shared_export_download(token: str) -> None:
    with connect() as connection:
        connection.execute(
            "UPDATE shared_exports SET download_count = download_count + 1 WHERE token = ?",
            (token,),
        )


def list_expired_shared_exports() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT token, file_path
            FROM shared_exports
            WHERE expires_at <= ?
            """,
            (utc_now(),),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_shared_exports(tokens: Iterable[str]) -> None:
    token_list = list(tokens)
    if not token_list:
        return
    placeholders = ",".join("?" for _ in token_list)
    with connect() as connection:
        connection.execute(
            f"DELETE FROM shared_exports WHERE token IN ({placeholders})",
            token_list,
        )


def _json_list(values: Iterable[str]) -> str:
    return json.dumps([value for value in values if value])


def create_output(teacher_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO outputs (
              teacher_id, kind, format, subject, topic, week_number, grade_levels, resources,
              inputs_json, content_md, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                teacher_id,
                payload["kind"],
                payload.get("format"),
                payload.get("subject"),
                payload.get("topic"),
                payload.get("week_number") or (payload.get("inputs") or {}).get("week_number"),
                _json_list(payload.get("grade_levels", [])),
                _json_list(payload.get("resources", [])),
                json.dumps(payload["inputs"]),
                payload["content_md"],
                now,
                now,
            ),
        )
        output = get_output_by_id(connection, teacher_id, cursor.lastrowid)
        assert output is not None
        return output


def list_outputs(teacher_id: int) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, kind, format, subject, topic, week_number, grade_levels, resources,
                   inputs_json, content_md, created_at, updated_at
            FROM outputs
            WHERE teacher_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (teacher_id,),
        ).fetchall()
        return [_decode_output(row) for row in rows]


def get_output(teacher_id: int, output_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return get_output_by_id(connection, teacher_id, output_id)


def get_output_by_id(
    connection: sqlite3.Connection, teacher_id: int, output_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT id, kind, format, subject, topic, week_number, grade_levels, resources,
               inputs_json, content_md, created_at, updated_at
        FROM outputs
        WHERE teacher_id = ? AND id = ?
        """,
        (teacher_id, output_id),
    ).fetchone()
    return _decode_output(row) if row else None


def update_output(teacher_id: int, output_id: int, content_md: str) -> dict[str, Any] | None:
    with connect() as connection:
        current = get_output_by_id(connection, teacher_id, output_id)
        if not current:
            return None
        updated_at = utc_now()
        if updated_at <= current["updated_at"]:
            updated_at = (
                datetime.fromisoformat(current["updated_at"]) + timedelta(seconds=1)
            ).replace(microsecond=0).isoformat()
        connection.execute(
            "UPDATE outputs SET content_md = ?, updated_at = ? WHERE teacher_id = ? AND id = ?",
            (content_md, updated_at, teacher_id, output_id),
        )
        return get_output_by_id(connection, teacher_id, output_id)


def delete_output(teacher_id: int, output_id: int) -> bool:
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM outputs WHERE teacher_id = ? AND id = ?",
            (teacher_id, output_id),
        )
        return cursor.rowcount > 0


def _decode_output(row: sqlite3.Row) -> dict[str, Any]:
    output = dict(row)
    output["grade_levels"] = json.loads(output["grade_levels"] or "[]")
    output["resources"] = json.loads(output["resources"] or "[]")
    output["inputs"] = json.loads(output.pop("inputs_json"))
    return output


def list_teaching_aids(teacher_id: int, output_id: int) -> list[dict[str, Any]]:
    with connect() as connection:
        if not get_output_by_id(connection, teacher_id, output_id):
            return []
        rows = connection.execute(
            """
            SELECT id, output_id, teacher_id, aid_type, title, source_section,
                   inputs_json, content_md, created_at, updated_at
            FROM teaching_aids
            WHERE teacher_id = ? AND output_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (teacher_id, output_id),
        ).fetchall()
        return [_decode_teaching_aid(row) for row in rows]


def create_teaching_aid(teacher_id: int, output_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        output = get_output_by_id(connection, teacher_id, output_id)
        if not output:
            return None
        cursor = connection.execute(
            """
            INSERT INTO teaching_aids (
              output_id, teacher_id, aid_type, title, source_section,
              inputs_json, content_md, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                output_id,
                teacher_id,
                payload["aid_type"],
                payload["title"],
                payload.get("source_section") or "",
                json.dumps(payload.get("inputs") or {}),
                payload["content_md"],
                now,
                now,
            ),
        )
        return get_teaching_aid_by_id(connection, teacher_id, output_id, cursor.lastrowid)


def get_teaching_aid(teacher_id: int, output_id: int, aid_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return get_teaching_aid_by_id(connection, teacher_id, output_id, aid_id)


def get_teaching_aid_by_id(
    connection: sqlite3.Connection, teacher_id: int, output_id: int, aid_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT id, output_id, teacher_id, aid_type, title, source_section,
               inputs_json, content_md, created_at, updated_at
        FROM teaching_aids
        WHERE teacher_id = ? AND output_id = ? AND id = ?
        """,
        (teacher_id, output_id, aid_id),
    ).fetchone()
    return _decode_teaching_aid(row) if row else None


def update_teaching_aid(
    teacher_id: int,
    output_id: int,
    aid_id: int,
    title: str,
    content_md: str,
) -> dict[str, Any] | None:
    with connect() as connection:
        current = get_teaching_aid_by_id(connection, teacher_id, output_id, aid_id)
        if not current:
            return None
        updated_at = utc_now()
        if updated_at <= current["updated_at"]:
            updated_at = (
                datetime.fromisoformat(current["updated_at"]) + timedelta(seconds=1)
            ).replace(microsecond=0).isoformat()
        connection.execute(
            """
            UPDATE teaching_aids
            SET title = ?, content_md = ?, updated_at = ?
            WHERE teacher_id = ? AND output_id = ? AND id = ?
            """,
            (title, content_md, updated_at, teacher_id, output_id, aid_id),
        )
        return get_teaching_aid_by_id(connection, teacher_id, output_id, aid_id)


def delete_teaching_aid(teacher_id: int, output_id: int, aid_id: int) -> bool:
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM teaching_aids WHERE teacher_id = ? AND output_id = ? AND id = ?",
            (teacher_id, output_id, aid_id),
        )
        return cursor.rowcount > 0


def _decode_teaching_aid(row: sqlite3.Row) -> dict[str, Any]:
    aid = dict(row)
    aid["inputs"] = json.loads(aid.pop("inputs_json") or "{}")
    return aid


def create_grading_batch(teacher_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as connection:
        class_id = int(payload["class_id"])
        assessment_id = int(payload["assessment_id"])
        class_record = get_class_record_by_id(connection, teacher_id, class_id)
        assessment = get_assessment_by_id(connection, teacher_id, assessment_id)
        if not class_record or not assessment or int(assessment["class_id"]) != class_id:
            raise ValueError("Selected assessment must belong to the selected class")
        if float(payload["total_points"]) != float(assessment["max_score"]):
            raise ValueError("Total points must match the selected assessment maximum")
        cursor = connection.execute(
            """
            INSERT INTO grading_batches (
              teacher_id, class_id, assessment_id, subject, grade_level, topic, quarter, week_number, week_topic, questions_text, total_points, grading_style,
              answer_key_json, rubric_json, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
            """,
            (
                teacher_id,
                class_id,
                assessment_id,
                class_record.get("subject", "").strip(),
                class_record.get("grade_level", "").strip(),
                assessment.get("title", "").strip(),
                payload.get("quarter"),
                payload.get("week_number"),
                payload.get("week_topic", "").strip(),
                payload.get("questions", "").strip(),
                float(payload["total_points"]),
                payload["grading_style"],
                json.dumps(payload.get("answer_key") or {}),
                json.dumps(payload.get("rubric") or {}),
                now,
                now,
            ),
        )
        batch = get_grading_batch_by_id(connection, teacher_id, int(cursor.lastrowid))
        assert batch is not None
        return batch


def list_grading_batches(teacher_id: int) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT grading_batches.*,
                   classes.name AS class_name,
                   assessments.title AS assessment_title,
                   assessments.max_score AS assessment_max_score,
                   COUNT(DISTINCT grading_images.id) AS image_count,
                   COUNT(DISTINCT grading_submissions.id) AS submission_count
            FROM grading_batches
            LEFT JOIN classes ON classes.id = grading_batches.class_id
            LEFT JOIN assessments ON assessments.id = grading_batches.assessment_id
            LEFT JOIN grading_images ON grading_images.batch_id = grading_batches.id
            LEFT JOIN grading_submissions ON grading_submissions.batch_id = grading_batches.id
            WHERE grading_batches.teacher_id = ?
            GROUP BY grading_batches.id
            ORDER BY grading_batches.updated_at DESC, grading_batches.id DESC
            """,
            (teacher_id,),
        ).fetchall()
        return [_decode_grading_batch(row) for row in rows]


def get_grading_batch(teacher_id: int, batch_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        batch = get_grading_batch_by_id(connection, teacher_id, batch_id)
        if not batch:
            return None
        batch["images"] = list_grading_images_by_batch(connection, teacher_id, batch_id)
        batch["submissions"] = list_grading_submissions_by_batch(connection, teacher_id, batch_id)
        batch["class_students"] = (
            _list_class_students_by_connection(connection, teacher_id, int(batch["class_id"]))
            if batch.get("class_id")
            else []
        )
        return batch


def get_grading_batch_by_id(
    connection: sqlite3.Connection, teacher_id: int, batch_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT grading_batches.*,
               classes.name AS class_name,
               assessments.title AS assessment_title,
               assessments.max_score AS assessment_max_score,
               COUNT(DISTINCT grading_images.id) AS image_count,
               COUNT(DISTINCT grading_submissions.id) AS submission_count
        FROM grading_batches
        LEFT JOIN classes ON classes.id = grading_batches.class_id
        LEFT JOIN assessments ON assessments.id = grading_batches.assessment_id
        LEFT JOIN grading_images ON grading_images.batch_id = grading_batches.id
        LEFT JOIN grading_submissions ON grading_submissions.batch_id = grading_batches.id
        WHERE grading_batches.teacher_id = ? AND grading_batches.id = ?
        GROUP BY grading_batches.id
        """,
        (teacher_id, batch_id),
    ).fetchone()
    return _decode_grading_batch(row) if row else None


def update_grading_batch_status(
    connection: sqlite3.Connection, teacher_id: int, batch_id: int, status_value: str
) -> None:
    connection.execute(
        """
        UPDATE grading_batches
        SET status = ?, updated_at = ?
        WHERE teacher_id = ? AND id = ?
        """,
        (status_value, utc_now(), teacher_id, batch_id),
    )


def create_grading_image(teacher_id: int, batch_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        if not get_grading_batch_by_id(connection, teacher_id, batch_id):
            return None
        cursor = connection.execute(
            """
            INSERT INTO grading_images (
              batch_id, original_path, thumbnail_path, mime_type, width, height,
              quality_warnings_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                payload["original_path"],
                payload.get("thumbnail_path"),
                payload["mime_type"],
                payload.get("width"),
                payload.get("height"),
                json.dumps(payload.get("quality_warnings") or []),
                now,
            ),
        )
        update_grading_batch_status(connection, teacher_id, batch_id, "uploaded")
        return get_grading_image_by_id(connection, teacher_id, int(cursor.lastrowid))


def get_grading_image(teacher_id: int, image_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return get_grading_image_by_id(connection, teacher_id, image_id)


def get_grading_image_by_id(
    connection: sqlite3.Connection, teacher_id: int, image_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT grading_images.*
        FROM grading_images
        JOIN grading_batches ON grading_batches.id = grading_images.batch_id
        WHERE grading_batches.teacher_id = ? AND grading_images.id = ?
        """,
        (teacher_id, image_id),
    ).fetchone()
    return _decode_grading_image(row) if row else None


def list_grading_images_by_batch(
    connection: sqlite3.Connection, teacher_id: int, batch_id: int
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT grading_images.*
        FROM grading_images
        JOIN grading_batches ON grading_batches.id = grading_images.batch_id
        WHERE grading_batches.teacher_id = ? AND grading_images.batch_id = ?
        ORDER BY grading_images.id
        """,
        (teacher_id, batch_id),
    ).fetchall()
    return [_decode_grading_image(row) for row in rows]


def replace_grading_submissions(
    teacher_id: int, batch_id: int, submissions: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    now = utc_now()
    with connect() as connection:
        if not get_grading_batch_by_id(connection, teacher_id, batch_id):
            return None
        connection.execute("DELETE FROM grading_submissions WHERE batch_id = ?", (batch_id,))
        for submission in submissions:
            connection.execute(
                """
                INSERT INTO grading_submissions (
                  batch_id, image_id, student_id, student_name, student_identifier, crop_box_json,
                  extracted_answers_json, grading_result_json, score, max_score,
                  confidence, teacher_reviewed, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    submission.get("image_id"),
                    submission.get("student_id"),
                    submission.get("student_name", "").strip(),
                    submission.get("student_identifier", "").strip(),
                    json.dumps(submission.get("crop_box") or {}),
                    json.dumps(submission.get("extracted_answers") or {}),
                    json.dumps(submission.get("grading_result") or {}),
                    submission.get("score"),
                    submission.get("max_score"),
                    submission.get("confidence"),
                    int(bool(submission.get("teacher_reviewed"))),
                    now,
                    now,
                ),
            )
        update_grading_batch_status(connection, teacher_id, batch_id, "detected")
        return list_grading_submissions_by_batch(connection, teacher_id, batch_id)


def list_grading_submissions_by_batch(
    connection: sqlite3.Connection, teacher_id: int, batch_id: int
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT grading_submissions.*
        FROM grading_submissions
        JOIN grading_batches ON grading_batches.id = grading_submissions.batch_id
        WHERE grading_batches.teacher_id = ? AND grading_submissions.batch_id = ?
        ORDER BY grading_submissions.id
        """,
        (teacher_id, batch_id),
    ).fetchall()
    return [_decode_grading_submission(row) for row in rows]


def get_grading_submission(teacher_id: int, submission_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return get_grading_submission_by_id(connection, teacher_id, submission_id)


def get_grading_submission_by_id(
    connection: sqlite3.Connection, teacher_id: int, submission_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT grading_submissions.*
        FROM grading_submissions
        JOIN grading_batches ON grading_batches.id = grading_submissions.batch_id
        WHERE grading_batches.teacher_id = ? AND grading_submissions.id = ?
        """,
        (teacher_id, submission_id),
    ).fetchone()
    return _decode_grading_submission(row) if row else None


def update_grading_submission(
    teacher_id: int, submission_id: int, payload: dict[str, Any]
) -> dict[str, Any] | None:
    with connect() as connection:
        current = get_grading_submission_by_id(connection, teacher_id, submission_id)
        if not current:
            return None
        result = payload.get("grading_result", current.get("grading_result") or {})
        extracted = payload.get("extracted_answers", current.get("extracted_answers") or {})
        connection.execute(
            """
            UPDATE grading_submissions
            SET student_name = ?, student_identifier = ?, extracted_answers_json = ?,
                student_id = ?, grading_result_json = ?, score = ?, max_score = ?, confidence = ?,
                teacher_reviewed = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                payload.get("student_name", current.get("student_name") or "").strip(),
                payload.get("student_identifier", current.get("student_identifier") or "").strip(),
                json.dumps(extracted),
                payload.get("student_id", current.get("student_id")),
                json.dumps(result),
                payload.get("score", current.get("score")),
                payload.get("max_score", current.get("max_score")),
                payload.get("confidence", current.get("confidence")),
                int(bool(payload.get("teacher_reviewed", current.get("teacher_reviewed")))),
                utc_now(),
                submission_id,
            ),
        )
        update_grading_batch_status(connection, teacher_id, int(current["batch_id"]), "reviewed")
        return get_grading_submission_by_id(connection, teacher_id, submission_id)


def save_grading_results(
    teacher_id: int, batch_id: int, graded_submissions: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    now = utc_now()
    with connect() as connection:
        if not get_grading_batch_by_id(connection, teacher_id, batch_id):
            return None
        for submission in graded_submissions:
            connection.execute(
                """
                UPDATE grading_submissions
                SET student_name = ?, student_identifier = ?, extracted_answers_json = ?,
                    student_id = ?, grading_result_json = ?, score = ?, max_score = ?, confidence = ?,
                    updated_at = ?
                WHERE id = ? AND batch_id = ?
                """,
                (
                    submission.get("student_name", ""),
                    submission.get("student_identifier", ""),
                    json.dumps(submission.get("extracted_answers") or {}),
                    submission.get("student_id"),
                    json.dumps(submission.get("grading_result") or {}),
                    submission.get("score"),
                    submission.get("max_score"),
                    submission.get("confidence"),
                    now,
                    submission["id"],
                    batch_id,
                ),
            )
        update_grading_batch_status(connection, teacher_id, batch_id, "graded")
        return list_grading_submissions_by_batch(connection, teacher_id, batch_id)


def list_grading_batch_file_paths(teacher_id: int, batch_id: int) -> list[str]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT grading_images.original_path, grading_images.thumbnail_path
            FROM grading_images
            JOIN grading_batches ON grading_batches.id = grading_images.batch_id
            WHERE grading_batches.teacher_id = ? AND grading_images.batch_id = ?
            """,
            (teacher_id, batch_id),
        ).fetchall()
        paths: list[str] = []
        for row in rows:
            paths.extend([path for path in (row["original_path"], row["thumbnail_path"]) if path])
        return paths


def delete_grading_batch(teacher_id: int, batch_id: int) -> bool:
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM grading_batches WHERE teacher_id = ? AND id = ?",
            (teacher_id, batch_id),
        )
        return cursor.rowcount > 0


def _decode_grading_batch(row: sqlite3.Row) -> dict[str, Any]:
    batch = dict(row)
    batch["answer_key"] = json.loads(batch.pop("answer_key_json") or "{}")
    batch["rubric"] = json.loads(batch.pop("rubric_json") or "{}")
    batch["questions"] = batch.pop("questions_text", "") or ""
    batch["image_count"] = int(batch.get("image_count") or 0)
    batch["submission_count"] = int(batch.get("submission_count") or 0)
    return batch


def _decode_grading_image(row: sqlite3.Row) -> dict[str, Any]:
    image = dict(row)
    image["quality_warnings"] = json.loads(image.pop("quality_warnings_json") or "[]")
    return image


def _decode_grading_submission(row: sqlite3.Row) -> dict[str, Any]:
    submission = dict(row)
    submission["crop_box"] = json.loads(submission.pop("crop_box_json") or "{}")
    submission["extracted_answers"] = json.loads(submission.pop("extracted_answers_json") or "{}")
    submission["grading_result"] = json.loads(submission.pop("grading_result_json") or "{}")
    submission["teacher_reviewed"] = bool(submission["teacher_reviewed"])
    return submission


def _student_display_name(payload: dict[str, Any]) -> str:
    provided = str(payload.get("display_name") or "").strip()
    if provided:
        return provided
    parts = [
        str(payload.get("first_name") or "").strip(),
        str(payload.get("middle_name") or "").strip(),
        str(payload.get("last_name") or "").strip(),
    ]
    return " ".join(part for part in parts if part)


def create_class_record(teacher_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO classes (
              teacher_id, name, grade_level, section, subject, school_year, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                teacher_id,
                payload["name"].strip(),
                payload["grade_level"].strip(),
                (payload.get("section") or "").strip(),
                payload["subject"].strip(),
                (payload.get("school_year") or "").strip(),
                now,
                now,
            ),
        )
        class_record = get_class_record_by_id(connection, teacher_id, int(cursor.lastrowid))
        assert class_record is not None
        return class_record


def list_class_records(teacher_id: int) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT classes.*,
                   COUNT(DISTINCT class_enrollments.student_id) AS student_count,
                   MAX(assessments.assessment_date) AS latest_assessment_date
            FROM classes
            LEFT JOIN class_enrollments ON class_enrollments.class_id = classes.id
            LEFT JOIN assessments ON assessments.class_id = classes.id
            WHERE classes.teacher_id = ?
            GROUP BY classes.id
            ORDER BY classes.updated_at DESC, classes.id DESC
            """,
            (teacher_id,),
        ).fetchall()
        records = [dict(row) for row in rows]
        for record in records:
            record["student_count"] = int(record.get("student_count") or 0)
            record["latest_average"] = _class_average(connection, int(record["id"]))
        return records


def get_class_record(teacher_id: int, class_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return get_class_record_by_id(connection, teacher_id, class_id)


def get_class_record_by_id(
    connection: sqlite3.Connection, teacher_id: int, class_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT classes.*,
               COUNT(DISTINCT class_enrollments.student_id) AS student_count
        FROM classes
        LEFT JOIN class_enrollments ON class_enrollments.class_id = classes.id
        WHERE classes.teacher_id = ? AND classes.id = ?
        GROUP BY classes.id
        """,
        (teacher_id, class_id),
    ).fetchone()
    if not row:
        return None
    record = dict(row)
    record["student_count"] = int(record.get("student_count") or 0)
    return record


def update_class_record(teacher_id: int, class_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    with connect() as connection:
        current = get_class_record_by_id(connection, teacher_id, class_id)
        if not current:
            return None
        connection.execute(
            """
            UPDATE classes
            SET name = ?, grade_level = ?, section = ?, subject = ?, school_year = ?, updated_at = ?
            WHERE teacher_id = ? AND id = ?
            """,
            (
                payload.get("name", current["name"]).strip(),
                payload.get("grade_level", current["grade_level"]).strip(),
                (payload.get("section", current.get("section")) or "").strip(),
                payload.get("subject", current["subject"]).strip(),
                (payload.get("school_year", current.get("school_year")) or "").strip(),
                utc_now(),
                teacher_id,
                class_id,
            ),
        )
        return get_class_record_by_id(connection, teacher_id, class_id)


def list_class_students(teacher_id: int, class_id: int) -> list[dict[str, Any]] | None:
    with connect() as connection:
        if not get_class_record_by_id(connection, teacher_id, class_id):
            return None
        rows = connection.execute(
            """
            SELECT students.*, class_enrollments.enrolled_at
            FROM class_enrollments
            JOIN students ON students.id = class_enrollments.student_id
            WHERE class_enrollments.class_id = ? AND students.teacher_id = ?
            ORDER BY students.last_name COLLATE NOCASE, students.first_name COLLATE NOCASE
            """,
            (class_id, teacher_id),
        ).fetchall()
        students = [dict(row) for row in rows]
        for student in students:
            summary = _student_summary(connection, class_id, int(student["id"]))
            student.update(summary)
        return students


def create_or_enroll_student(teacher_id: int, class_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        if not get_class_record_by_id(connection, teacher_id, class_id):
            return None
        student_id = payload.get("student_id")
        if student_id:
            row = connection.execute(
                "SELECT id FROM students WHERE teacher_id = ? AND id = ?",
                (teacher_id, int(student_id)),
            ).fetchone()
            if not row:
                return None
            clean_student_id = int(student_id)
        else:
            display_name = _student_display_name(payload)
            cursor = connection.execute(
                """
                INSERT INTO students (
                  teacher_id, learner_reference_number, first_name, middle_name,
                  last_name, display_name, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    teacher_id,
                    (payload.get("learner_reference_number") or "").strip(),
                    payload["first_name"].strip(),
                    (payload.get("middle_name") or "").strip(),
                    payload["last_name"].strip(),
                    display_name,
                    payload.get("status") or "active",
                    now,
                    now,
                ),
            )
            clean_student_id = int(cursor.lastrowid)
        connection.execute(
            "INSERT OR IGNORE INTO class_enrollments (class_id, student_id, enrolled_at) VALUES (?, ?, ?)",
            (class_id, clean_student_id, now),
        )
        return get_student_by_id(connection, teacher_id, clean_student_id)


def get_student_by_id(connection: sqlite3.Connection, teacher_id: int, student_id: int) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM students WHERE teacher_id = ? AND id = ?",
        (teacher_id, student_id),
    ).fetchone()
    return dict(row) if row else None


def update_student(teacher_id: int, student_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    with connect() as connection:
        current = get_student_by_id(connection, teacher_id, student_id)
        if not current:
            return None
        next_payload = {**current, **payload}
        connection.execute(
            """
            UPDATE students
            SET learner_reference_number = ?, first_name = ?, middle_name = ?, last_name = ?,
                display_name = ?, status = ?, updated_at = ?
            WHERE teacher_id = ? AND id = ?
            """,
            (
                (next_payload.get("learner_reference_number") or "").strip(),
                next_payload["first_name"].strip(),
                (next_payload.get("middle_name") or "").strip(),
                next_payload["last_name"].strip(),
                _student_display_name(next_payload),
                next_payload.get("status") or "active",
                utc_now(),
                teacher_id,
                student_id,
            ),
        )
        return get_student_by_id(connection, teacher_id, student_id)


def list_class_assessments(teacher_id: int, class_id: int) -> list[dict[str, Any]] | None:
    with connect() as connection:
        if not get_class_record_by_id(connection, teacher_id, class_id):
            return None
        rows = connection.execute(
            """
            SELECT assessments.*
            FROM assessments
            WHERE assessments.class_id = ?
            ORDER BY assessments.assessment_date DESC, assessments.id DESC
            """,
            (class_id,),
        ).fetchall()
        assessments = [dict(row) for row in rows]
        for assessment in assessments:
            summary = _assessment_stats(connection, int(assessment["id"]))
            assessment.update(summary)
        return assessments


def create_assessment(teacher_id: int, class_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        if not get_class_record_by_id(connection, teacher_id, class_id):
            return None
        cursor = connection.execute(
            """
            INSERT INTO assessments (
              class_id, title, assessment_type, assessment_date, max_score,
              weight, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                class_id,
                payload["title"].strip(),
                payload["assessment_type"],
                payload["assessment_date"],
                float(payload["max_score"]),
                payload.get("weight"),
                (payload.get("notes") or "").strip(),
                now,
                now,
            ),
        )
        return get_assessment_by_id(connection, teacher_id, int(cursor.lastrowid))


def get_assessment_by_id(
    connection: sqlite3.Connection, teacher_id: int, assessment_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT assessments.*, classes.teacher_id
        FROM assessments
        JOIN classes ON classes.id = assessments.class_id
        WHERE classes.teacher_id = ? AND assessments.id = ?
        """,
        (teacher_id, assessment_id),
    ).fetchone()
    return dict(row) if row else None


def update_assessment(teacher_id: int, assessment_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    with connect() as connection:
        current = get_assessment_by_id(connection, teacher_id, assessment_id)
        if not current:
            return None
        max_score = float(payload.get("max_score", current["max_score"]))
        row = connection.execute(
            """
            SELECT MAX(score) AS max_entered
            FROM scores
            WHERE assessment_id = ? AND is_absent = 0
            """,
            (assessment_id,),
        ).fetchone()
        if row and row["max_entered"] is not None and float(row["max_entered"]) > max_score:
            raise ValueError("Maximum score is below an existing score")
        connection.execute(
            """
            UPDATE assessments
            SET title = ?, assessment_type = ?, assessment_date = ?, max_score = ?,
                weight = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                payload.get("title", current["title"]).strip(),
                payload.get("assessment_type", current["assessment_type"]),
                payload.get("assessment_date", current["assessment_date"]),
                max_score,
                payload.get("weight", current.get("weight")),
                (payload.get("notes", current.get("notes")) or "").strip(),
                utc_now(),
                assessment_id,
            ),
        )
        return get_assessment_by_id(connection, teacher_id, assessment_id)


def get_score_grid(teacher_id: int, assessment_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return get_score_grid_by_id(connection, teacher_id, assessment_id)


def get_score_grid_by_id(
    connection: sqlite3.Connection, teacher_id: int, assessment_id: int
) -> dict[str, Any] | None:
    assessment = get_assessment_by_id(connection, teacher_id, assessment_id)
    if not assessment:
        return None
    student_rows = connection.execute(
        """
        SELECT students.*, class_enrollments.enrolled_at
        FROM class_enrollments
        JOIN students ON students.id = class_enrollments.student_id
        WHERE class_enrollments.class_id = ? AND students.teacher_id = ?
        ORDER BY students.last_name COLLATE NOCASE, students.first_name COLLATE NOCASE
        """,
        (assessment["class_id"], teacher_id),
    ).fetchall()
    students = [dict(row) for row in student_rows]
    for student in students:
        student.update(_student_summary(connection, int(assessment["class_id"]), int(student["id"])))
    score_rows = connection.execute(
        "SELECT * FROM scores WHERE assessment_id = ?",
        (assessment_id,),
    ).fetchall()
    score_by_student = {int(row["student_id"]): dict(row) for row in score_rows}
    rows = []
    for student in students:
        score = score_by_student.get(int(student["id"]))
        rows.append(
            {
                "student": student,
                "score": score["score"] if score else None,
                "is_absent": bool(score["is_absent"]) if score else False,
                "notes": score["notes"] if score else "",
                "score_id": score["id"] if score else None,
            }
        )
    return {"assessment": assessment, "rows": rows}


def save_score_grid(teacher_id: int, assessment_id: int, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    now = utc_now()
    with connect() as connection:
        assessment = get_assessment_by_id(connection, teacher_id, assessment_id)
        if not assessment:
            return None
        enrolled_ids = {
            int(row["student_id"])
            for row in connection.execute(
                "SELECT student_id FROM class_enrollments WHERE class_id = ?",
                (assessment["class_id"],),
            ).fetchall()
        }
        for item in rows:
            student_id = int(item["student_id"])
            if student_id not in enrolled_ids:
                raise ValueError("Score includes a student outside this class")
            is_absent = bool(item.get("is_absent"))
            raw_score = item.get("score")
            score = None if raw_score in (None, "") or is_absent else float(raw_score)
            if score is not None and score > float(assessment["max_score"]):
                raise ValueError("Score cannot exceed the assessment maximum")
            connection.execute(
                """
                INSERT INTO scores (
                  assessment_id, student_id, score, is_absent, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(assessment_id, student_id) DO UPDATE SET
                  score = excluded.score,
                  is_absent = excluded.is_absent,
                  notes = excluded.notes,
                  updated_at = excluded.updated_at
                """,
                (
                    assessment_id,
                    student_id,
                    score,
                    int(is_absent),
                    (item.get("notes") or "").strip(),
                    now,
                    now,
                ),
            )
        return get_score_grid_by_id(connection, teacher_id, assessment_id)


def preview_grading_score_transfer(teacher_id: int, batch_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return _grading_score_transfer(connection, teacher_id, batch_id, apply=False)


def transfer_grading_scores(teacher_id: int, batch_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        return _grading_score_transfer(connection, teacher_id, batch_id, apply=True)


def _grading_score_transfer(
    connection: sqlite3.Connection,
    teacher_id: int,
    batch_id: int,
    *,
    apply: bool,
) -> dict[str, Any] | None:
    batch = get_grading_batch_by_id(connection, teacher_id, batch_id)
    if not batch:
        return None
    assessment_id = batch.get("assessment_id")
    class_id = batch.get("class_id")
    if not assessment_id or not class_id:
        raise ValueError("Grading batch is not linked to a class assessment")
    assessment = get_assessment_by_id(connection, teacher_id, int(assessment_id))
    if not assessment or int(assessment["class_id"]) != int(class_id):
        raise ValueError("Linked assessment was not found for this class")
    if float(batch["total_points"]) != float(assessment["max_score"]):
        raise ValueError("Batch total points must match the assessment maximum before transfer")

    students = _list_class_students_by_connection(connection, teacher_id, int(class_id))
    score_rows = connection.execute(
        "SELECT * FROM scores WHERE assessment_id = ?",
        (assessment_id,),
    ).fetchall()
    scores_by_student = {int(row["student_id"]): dict(row) for row in score_rows}
    submissions = list_grading_submissions_by_batch(connection, teacher_id, batch_id)
    now = utc_now()
    rows = []
    saved_count = 0
    for submission in submissions:
        student = _match_transfer_student(submission, students)
        existing = scores_by_student.get(int(student["id"])) if student else None
        score = submission.get("score")
        status_value = "ready"
        reason = ""
        if not submission.get("teacher_reviewed"):
            status_value = "needs_review"
            reason = "Teacher review is required before transfer."
        elif not student:
            status_value = "needs_match"
            reason = "Match this submission to a student in the selected class."
        elif existing and (existing.get("score") is not None or existing.get("is_absent")):
            status_value = "skipped_existing_score"
            reason = "This student already has a score or absent mark for the assessment."
        elif score is None:
            status_value = "needs_score"
            reason = "Enter a reviewed score before transfer."
        elif float(score) > float(assessment["max_score"]):
            status_value = "score_exceeds_max"
            reason = "Reviewed score exceeds the selected assessment maximum."

        if apply and status_value == "ready" and student:
            note = f"Imported from quiz photo batch #{batch_id}, submission #{submission['id']}"
            if existing:
                cursor = connection.execute(
                    """
                    UPDATE scores
                    SET score = ?, is_absent = 0, notes = ?, updated_at = ?
                    WHERE assessment_id = ? AND student_id = ? AND score IS NULL AND is_absent = 0
                    """,
                    (float(score), note, now, assessment_id, int(student["id"])),
                )
            else:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO scores (
                      assessment_id, student_id, score, is_absent, notes, created_at, updated_at
                    )
                    VALUES (?, ?, ?, 0, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        int(student["id"]),
                        float(score),
                        note,
                        now,
                        now,
                    ),
                )
            if cursor.rowcount:
                saved_count += 1
                scores_by_student[int(student["id"])] = {
                    "student_id": int(student["id"]),
                    "score": float(score),
                    "is_absent": 0,
                }
                connection.execute(
                    "UPDATE grading_submissions SET student_id = ?, updated_at = ? WHERE id = ?",
                    (int(student["id"]), now, int(submission["id"])),
                )
                status_value = "saved"
                reason = "Score transferred."
            else:
                status_value = "skipped_existing_score"
                reason = "This student received a score before transfer was saved."

        rows.append(
            {
                "submission_id": submission["id"],
                "student": student,
                "submission_name": submission.get("student_name") or "",
                "student_identifier": submission.get("student_identifier") or "",
                "score": score,
                "max_score": submission.get("max_score"),
                "teacher_reviewed": submission.get("teacher_reviewed"),
                "status": status_value,
                "reason": reason,
                "existing_score": existing["score"] if existing else None,
                "existing_is_absent": bool(existing["is_absent"]) if existing else False,
            }
        )
    if apply and saved_count:
        update_grading_batch_status(connection, teacher_id, batch_id, "transferred")
    return {
        "batch": get_grading_batch_by_id(connection, teacher_id, batch_id),
        "assessment": assessment,
        "rows": rows,
        "saved_count": saved_count,
    }


def _list_class_students_by_connection(
    connection: sqlite3.Connection, teacher_id: int, class_id: int
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT students.*, class_enrollments.enrolled_at
        FROM class_enrollments
        JOIN students ON students.id = class_enrollments.student_id
        WHERE class_enrollments.class_id = ? AND students.teacher_id = ?
        ORDER BY students.last_name COLLATE NOCASE, students.first_name COLLATE NOCASE
        """,
        (class_id, teacher_id),
    ).fetchall()
    return [dict(row) for row in rows]


def _match_transfer_student(submission: dict[str, Any], students: list[dict[str, Any]]) -> dict[str, Any] | None:
    explicit_id = submission.get("student_id")
    if explicit_id:
        for student in students:
            if int(student["id"]) == int(explicit_id):
                return student
    identifier = _normalize_match_text(submission.get("student_identifier"))
    if identifier:
        for student in students:
            if identifier == _normalize_match_text(student.get("learner_reference_number")):
                return student
    name = _normalize_match_text(submission.get("student_name"))
    if name:
        for student in students:
            names = {
                _normalize_match_text(student.get("display_name")),
                _normalize_match_text(f"{student.get('first_name', '')} {student.get('last_name', '')}"),
                _normalize_match_text(f"{student.get('last_name', '')} {student.get('first_name', '')}"),
            }
            if name in names:
                return student
    return None


def _normalize_match_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def get_class_dashboard(teacher_id: int, class_id: int, target: float = 75.0) -> dict[str, Any] | None:
    with connect() as connection:
        class_record = get_class_record_by_id(connection, teacher_id, class_id)
        if not class_record:
            return None
        students = list_class_students(teacher_id, class_id) or []
        assessments = list_class_assessments(teacher_id, class_id) or []
        student_rows = []
        for student in students:
            average = student.get("average_percentage")
            missing_absent = int(student.get("missing_count") or 0) + int(student.get("absent_count") or 0)
            status_label = "No Data" if average is None else "Watch" if average < target or missing_absent >= 2 else "On Track"
            student_rows.append(
                {
                    **student,
                    "status_indicator": status_label,
                    "assessment_results": _student_assessment_results(
                        connection,
                        int(student["id"]),
                        assessments,
                        target,
                    ),
                }
            )
        assessment_averages = [
            assessment["average_percentage"]
            for assessment in assessments
            if assessment.get("average_percentage") is not None
        ]
        class_average = _class_average(connection, class_id)
        below_target_count = sum(
            1
            for student in student_rows
            if student.get("average_percentage") is not None and float(student["average_percentage"]) < target
        )
        return {
            "class": class_record,
            "student_count": len(students),
            "assessment_count": len(assessments),
            "class_average": class_average,
            "target_percentage": target,
            "highest_assessment_average": max(assessment_averages) if assessment_averages else None,
            "lowest_assessment_average": min(assessment_averages) if assessment_averages else None,
            "missing_or_absent_count": sum(int(student.get("missing_count") or 0) + int(student.get("absent_count") or 0) for student in students),
            "below_target_count": below_target_count,
            "recent_assessments": assessments[:5],
            "assessments": assessments,
            "students": student_rows,
        }


def get_assessment_dashboard(teacher_id: int, assessment_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        assessment = get_assessment_by_id(connection, teacher_id, assessment_id)
        if not assessment:
            return None
        grid = get_score_grid(teacher_id, assessment_id)
        rows = grid["rows"] if grid else []
        percentages = []
        absent_or_missing = []
        buckets = {"0-59%": 0, "60-74%": 0, "75-89%": 0, "90-100%": 0}
        max_score = float(assessment["max_score"])
        for row in rows:
            score = row.get("score")
            if row.get("is_absent") or score is None:
                absent_or_missing.append(row["student"])
                continue
            percentage = float(score) / max_score * 100
            percentages.append(percentage)
            if percentage < 60:
                buckets["0-59%"] += 1
            elif percentage < 75:
                buckets["60-74%"] += 1
            elif percentage < 90:
                buckets["75-89%"] += 1
            else:
                buckets["90-100%"] += 1
        return {
            "assessment": assessment,
            "average_percentage": round(sum(percentages) / len(percentages), 2) if percentages else None,
            "highest_score": round(max(percentages) * max_score / 100, 2) if percentages else None,
            "lowest_score": round(min(percentages) * max_score / 100, 2) if percentages else None,
            "distribution": buckets,
            "absent_or_missing_students": absent_or_missing,
        }


def _assessment_stats(connection: sqlite3.Connection, assessment_id: int) -> dict[str, Any]:
    assessment = connection.execute("SELECT max_score, class_id FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    if not assessment:
        return {}
    enrolled_count = connection.execute(
        "SELECT COUNT(*) AS count FROM class_enrollments WHERE class_id = ?",
        (assessment["class_id"],),
    ).fetchone()["count"]
    rows = connection.execute(
        "SELECT score, is_absent FROM scores WHERE assessment_id = ?",
        (assessment_id,),
    ).fetchall()
    percentages = [
        float(row["score"]) / float(assessment["max_score"]) * 100
        for row in rows
        if not row["is_absent"] and row["score"] is not None
    ]
    present_scores = [float(row["score"]) for row in rows if not row["is_absent"] and row["score"] is not None]
    absent_count = sum(1 for row in rows if row["is_absent"])
    missing_count = max(0, int(enrolled_count) - len(rows))
    return {
        "average_percentage": round(sum(percentages) / len(percentages), 2) if percentages else None,
        "highest_score": max(present_scores) if present_scores else None,
        "lowest_score": min(present_scores) if present_scores else None,
        "completion_count": len(present_scores),
        "missing_count": missing_count,
        "absent_count": absent_count,
    }


def _student_summary(connection: sqlite3.Connection, class_id: int, student_id: int) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT assessments.max_score, scores.score, scores.is_absent
        FROM assessments
        LEFT JOIN scores
          ON scores.assessment_id = assessments.id AND scores.student_id = ?
        WHERE assessments.class_id = ?
        """,
        (student_id, class_id),
    ).fetchall()
    percentages = [
        float(row["score"]) / float(row["max_score"]) * 100
        for row in rows
        if row["score"] is not None and not row["is_absent"]
    ]
    absent_count = sum(1 for row in rows if row["is_absent"])
    missing_count = sum(1 for row in rows if row["score"] is None and not row["is_absent"])
    return {
        "average_percentage": round(sum(percentages) / len(percentages), 2) if percentages else None,
        "missing_count": missing_count,
        "absent_count": absent_count,
    }


def _student_assessment_results(
    connection: sqlite3.Connection,
    student_id: int,
    assessments: list[dict[str, Any]],
    target: float,
) -> list[dict[str, Any]]:
    score_rows = connection.execute(
        """
        SELECT assessment_id, score, is_absent
        FROM scores
        WHERE student_id = ?
        """,
        (student_id,),
    ).fetchall()
    scores_by_assessment = {int(row["assessment_id"]): dict(row) for row in score_rows}
    results = []
    for assessment in assessments:
        assessment_id = int(assessment["id"])
        score = scores_by_assessment.get(assessment_id)
        max_score = float(assessment["max_score"])
        raw_score = score.get("score") if score else None
        is_absent = bool(score.get("is_absent")) if score else False
        percentage = None
        if raw_score is not None and not is_absent and max_score:
            percentage = round(float(raw_score) / max_score * 100, 2)
        results.append(
            {
                "assessment_id": assessment_id,
                "title": assessment["title"],
                "assessment_type": assessment["assessment_type"],
                "max_score": max_score,
                "score": raw_score,
                "percentage": percentage,
                "is_absent": is_absent,
                "is_missing": score is None,
                "is_below_target": percentage is not None and percentage < target,
            }
        )
    return results


def _class_average(connection: sqlite3.Connection, class_id: int) -> float | None:
    student_ids = [
        int(row["student_id"])
        for row in connection.execute(
            "SELECT student_id FROM class_enrollments WHERE class_id = ?",
            (class_id,),
        ).fetchall()
    ]
    averages = [
        summary["average_percentage"]
        for summary in (_student_summary(connection, class_id, student_id) for student_id in student_ids)
        if summary["average_percentage"] is not None
    ]
    return round(sum(averages) / len(averages), 2) if averages else None


def create_curriculum_document(connection: sqlite3.Connection, payload: dict[str, Any]) -> int:
    cursor = connection.execute(
        """
        INSERT INTO curriculum_documents (
          subject, title, filename, stored_path, version_label, active,
          parse_summary_json, uploaded_by, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["subject"],
            payload["title"],
            payload["filename"],
            payload["stored_path"],
            payload["version_label"],
            int(payload.get("active", True)),
            json.dumps(payload.get("parse_summary") or {}),
            payload.get("uploaded_by"),
            utc_now(),
        ),
    )
    return int(cursor.lastrowid)


def update_curriculum_document_path(
    connection: sqlite3.Connection, document_id: int, stored_path: str
) -> None:
    connection.execute(
        "UPDATE curriculum_documents SET stored_path = ? WHERE id = ?",
        (stored_path, document_id),
    )


def get_curriculum_document(
    connection: sqlite3.Connection, document_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT curriculum_documents.id, curriculum_documents.subject, title, filename,
               stored_path, version_label, active, parse_summary_json, uploaded_by,
               curriculum_documents.created_at, teachers.name AS uploaded_by_name
        FROM curriculum_documents
        LEFT JOIN teachers ON teachers.id = curriculum_documents.uploaded_by
        WHERE curriculum_documents.id = ?
        """,
        (document_id,),
    ).fetchone()
    if not row:
        return None
    document = dict(row)
    document["active"] = bool(document["active"])
    document["parse_summary"] = json.loads(document.pop("parse_summary_json") or "{}")
    return document


def list_curriculum_documents() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT curriculum_documents.id, curriculum_documents.subject, title, filename,
                   version_label, active, parse_summary_json, uploaded_by, curriculum_documents.created_at,
                   teachers.name AS uploaded_by_name,
                   COUNT(curriculum_units.id) AS unit_count
            FROM curriculum_documents
            LEFT JOIN teachers ON teachers.id = curriculum_documents.uploaded_by
            LEFT JOIN curriculum_units ON curriculum_units.document_id = curriculum_documents.id
            GROUP BY curriculum_documents.id
            ORDER BY curriculum_documents.created_at DESC, curriculum_documents.id DESC
            """
        ).fetchall()
        documents = [dict(row) for row in rows]
        for document in documents:
            document["active"] = bool(document["active"])
            document["parse_summary"] = json.loads(document.pop("parse_summary_json") or "{}")
        return documents


def activate_curriculum_document(document_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        document = get_curriculum_document(connection, document_id)
        if not document:
            return None
        connection.execute(
            "UPDATE curriculum_documents SET active = 0 WHERE subject = ?",
            (document["subject"],),
        )
        connection.execute(
            "UPDATE curriculum_documents SET active = 1 WHERE id = ?",
            (document_id,),
        )
        return get_curriculum_document(connection, document_id)


def deactivate_curriculum_document(document_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        document = get_curriculum_document(connection, document_id)
        if not document:
            return None
        connection.execute(
            "UPDATE curriculum_documents SET active = 0 WHERE id = ?",
            (document_id,),
        )
        return get_curriculum_document(connection, document_id)


def delete_inactive_curriculum_document(document_id: int) -> bool:
    with connect() as connection:
        row = connection.execute(
            "SELECT active FROM curriculum_documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if not row or row["active"]:
            return False
        connection.execute(
            """
            DELETE FROM curriculum_fts
            WHERE unit_id IN (SELECT id FROM curriculum_units WHERE document_id = ?)
            """,
            (document_id,),
        )
        cursor = connection.execute(
            "DELETE FROM curriculum_documents WHERE id = ?",
            (document_id,),
        )
        return cursor.rowcount > 0


def get_curriculum_document_path(document_id: int) -> str | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT stored_path FROM curriculum_documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        return row["stored_path"] if row else None


def replace_curriculum_units(
    connection: sqlite3.Connection,
    document_id: int,
    subject: str,
    units: list[Any],
) -> None:
    connection.execute(
        """
        DELETE FROM curriculum_fts
        WHERE unit_id IN (SELECT id FROM curriculum_units WHERE document_id = ?)
        """,
        (document_id,),
    )
    connection.execute("DELETE FROM curriculum_units WHERE document_id = ?", (document_id,))
    for unit in units:
        cursor = connection.execute(
            """
            INSERT INTO curriculum_units (
              document_id, subject, grade_level, quarter, domain, content,
              content_standards, performance_standard, suggested_tasks, source_pages,
              raw_text, confidence, warnings_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                subject,
                unit.grade_level,
                unit.quarter,
                unit.domain,
                unit.content,
                unit.content_standards,
                unit.performance_standard,
                unit.suggested_tasks,
                unit.source_pages,
                unit.raw_text,
                unit.confidence,
                json.dumps(unit.warnings),
            ),
        )
        unit_id = int(cursor.lastrowid)
        for sequence, competency in enumerate(unit.learning_competencies, start=1):
            connection.execute(
                """
                INSERT INTO curriculum_competencies (unit_id, sequence, competency_text)
                VALUES (?, ?, ?)
                """,
                (unit_id, sequence, competency),
            )
        competencies = " ".join(unit.learning_competencies)
        connection.execute(
            """
            INSERT INTO curriculum_fts (
              subject, grade_level, quarter, domain, content, content_standards,
              competencies, performance_standard, suggested_tasks, unit_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subject,
                unit.grade_level,
                str(unit.quarter),
                unit.domain,
                unit.content,
                unit.content_standards,
                competencies,
                unit.performance_standard,
                unit.suggested_tasks,
                unit_id,
            ),
        )
        reset_curriculum_unit_pacing(connection, unit_id)


def ensure_all_curriculum_pacing(connection: sqlite3.Connection) -> None:
    rows = connection.execute("SELECT id FROM curriculum_units ORDER BY id").fetchall()
    for row in rows:
        existing_count = connection.execute(
            "SELECT COUNT(*) AS count FROM curriculum_unit_weeks WHERE unit_id = ?",
            (row["id"],),
        ).fetchone()["count"]
        if int(existing_count) < 10:
            reset_curriculum_unit_pacing(connection, int(row["id"]))


def reset_curriculum_unit_pacing(connection: sqlite3.Connection, unit_id: int) -> None:
    connection.execute(
        "DELETE FROM curriculum_unit_weeks WHERE unit_id = ?",
        (unit_id,),
    )
    competencies = connection.execute(
        """
        SELECT id, sequence, competency_text
        FROM curriculum_competencies
        WHERE unit_id = ?
        ORDER BY sequence
        """,
        (unit_id,),
    ).fetchall()
    buckets: list[list[sqlite3.Row]] = [[] for _ in range(10)]
    for index, competency in enumerate(competencies):
        week_index = min(9, index * 10 // max(1, len(competencies)))
        buckets[week_index].append(competency)
    now = utc_now()
    for week_number in range(1, 11):
        bucket = buckets[week_number - 1]
        focus = _default_week_focus(week_number, bucket)
        cursor = connection.execute(
            """
            INSERT INTO curriculum_unit_weeks (unit_id, week_number, focus, notes, created_at, updated_at)
            VALUES (?, ?, ?, '', ?, ?)
            """,
            (unit_id, week_number, focus, now, now),
        )
        week_id = int(cursor.lastrowid)
        for competency in bucket:
            connection.execute(
                """
                INSERT INTO curriculum_unit_week_competencies (week_id, competency_id)
                VALUES (?, ?)
                """,
                (week_id, competency["id"]),
            )


def _default_week_focus(week_number: int, competencies: list[sqlite3.Row]) -> str:
    if not competencies:
        return f"Week {week_number} review, practice, remediation, or enrichment"
    sequences = [int(competency["sequence"]) for competency in competencies]
    prefix = f"Competency {sequences[0]}" if len(sequences) == 1 else f"Competencies {sequences[0]}-{sequences[-1]}"
    competency_text = "; ".join(_short_focus(str(competency["competency_text"])) for competency in competencies)
    return f"{prefix}: {competency_text}"


def _short_focus(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .;")
    if len(cleaned) <= 110:
        return cleaned
    return f"{cleaned[:107].rstrip()}..."


def curriculum_grades() -> list[str]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT curriculum_units.grade_level
            FROM curriculum_units
            JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
            WHERE curriculum_documents.active = 1
            ORDER BY CAST(REPLACE(curriculum_units.grade_level, 'Grade ', '') AS INTEGER)
            """
        ).fetchall()
        return [row["grade_level"] for row in rows]


def curriculum_subjects(grade_level: str) -> list[str]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT curriculum_units.subject
            FROM curriculum_units
            JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
            WHERE curriculum_documents.active = 1 AND curriculum_units.grade_level = ?
            ORDER BY curriculum_units.subject COLLATE NOCASE
            """,
            (grade_level,),
        ).fetchall()
        return [row["subject"] for row in rows]


def curriculum_quarters(grade_level: str, subject: str) -> list[int]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT curriculum_units.quarter
            FROM curriculum_units
            JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
            WHERE curriculum_documents.active = 1
              AND curriculum_units.grade_level = ?
              AND curriculum_units.subject = ?
            ORDER BY curriculum_units.quarter
            """,
            (grade_level, subject),
        ).fetchall()
        return [int(row["quarter"]) for row in rows]


def curriculum_topics(grade_level: str, subject: str, quarter: int) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT curriculum_units.id, curriculum_units.domain, curriculum_units.source_pages
            FROM curriculum_units
            JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
            WHERE curriculum_documents.active = 1
              AND curriculum_units.grade_level = ?
              AND curriculum_units.subject = ?
              AND curriculum_units.quarter = ?
            ORDER BY curriculum_units.domain COLLATE NOCASE
            """,
            (grade_level, subject, quarter),
        ).fetchall()
        return [dict(row) for row in rows]


def get_curriculum_unit(
    *,
    grade_level: str,
    subject: str,
    quarter: int | str | None,
    topic: str,
    connection: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    if not grade_level or not subject or quarter in (None, ""):
        return None
    close_connection = connection is None
    active_connection = connection or connect()
    try:
        row = active_connection.execute(
            """
            SELECT curriculum_units.*, curriculum_documents.title AS document_title,
                   curriculum_documents.version_label
            FROM curriculum_units
            JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
            WHERE curriculum_documents.active = 1
              AND curriculum_units.grade_level = ?
              AND curriculum_units.subject = ?
              AND curriculum_units.quarter = ?
              AND curriculum_units.domain = ?
            LIMIT 1
            """,
            (grade_level, subject, int(quarter), topic),
        ).fetchone()
        if not row:
            row = active_connection.execute(
                """
                SELECT curriculum_units.*, curriculum_documents.title AS document_title,
                       curriculum_documents.version_label
                FROM curriculum_fts
                JOIN curriculum_units ON curriculum_units.id = curriculum_fts.unit_id
                JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
                WHERE curriculum_documents.active = 1
                  AND curriculum_units.grade_level = ?
                  AND curriculum_units.subject = ?
                  AND curriculum_units.quarter = ?
                  AND curriculum_fts MATCH ?
                ORDER BY bm25(curriculum_fts)
                LIMIT 1
                """,
                (grade_level, subject, int(quarter), _fts_query(topic)),
            ).fetchone()
        if not row:
            return None
        context = dict(row)
        context["warnings"] = json.loads(context.pop("warnings_json") or "[]")
        return context
    finally:
        if close_connection:
            active_connection.close()


def get_curriculum_pacing(
    *,
    grade_level: str,
    subject: str,
    quarter: int | str | None,
    topic: str,
) -> dict[str, Any] | None:
    with connect() as connection:
        unit = get_curriculum_unit(
            grade_level=grade_level,
            subject=subject,
            quarter=quarter,
            topic=topic,
            connection=connection,
        )
        if not unit:
            return None
        ensure_curriculum_unit_pacing(connection, int(unit["id"]))
        competencies = _unit_competencies(connection, int(unit["id"]))
        return {
            "unit": unit,
            "competencies": competencies,
            "weeks": _unit_weeks(connection, int(unit["id"])),
        }


def get_curriculum_week_context(
    *,
    grade_level: str,
    subject: str,
    quarter: int | str | None,
    topic: str,
    week_number: int | str | None,
) -> dict[str, Any] | None:
    if week_number in (None, ""):
        return None
    with connect() as connection:
        unit = get_curriculum_unit(
            grade_level=grade_level,
            subject=subject,
            quarter=quarter,
            topic=topic,
            connection=connection,
        )
        if not unit:
            return None
        ensure_curriculum_unit_pacing(connection, int(unit["id"]))
        week = _unit_week(connection, int(unit["id"]), int(week_number))
        if not week:
            return None
        unit["competencies"] = _unit_competencies(connection, int(unit["id"]))
        week["competencies"] = _week_competencies(connection, int(week["id"]))
        return {"unit": unit, "week": week}


def update_curriculum_pacing(unit_id: int, weeks: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(weeks) != 10:
        raise ValueError("Pacing must contain exactly 10 weeks")
    with connect() as connection:
        unit_row = connection.execute("SELECT id FROM curriculum_units WHERE id = ?", (unit_id,)).fetchone()
        if not unit_row:
            return None
        valid_competency_ids = {
            int(row["id"])
            for row in connection.execute(
                "SELECT id FROM curriculum_competencies WHERE unit_id = ?",
                (unit_id,),
            ).fetchall()
        }
        connection.execute("DELETE FROM curriculum_unit_weeks WHERE unit_id = ?", (unit_id,))
        now = utc_now()
        for week in sorted(weeks, key=lambda item: int(item.get("week_number") or 0)):
            week_number = int(week.get("week_number") or 0)
            if week_number < 1 or week_number > 10:
                raise ValueError("Week numbers must be from 1 to 10")
            focus = str(week.get("focus") or "").strip()
            if not focus:
                raise ValueError("Every week needs a focus")
            cursor = connection.execute(
                """
                INSERT INTO curriculum_unit_weeks (unit_id, week_number, focus, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (unit_id, week_number, focus, str(week.get("notes") or "").strip(), now, now),
            )
            week_id = int(cursor.lastrowid)
            competency_ids = week.get("competency_ids") or []
            for competency_id in competency_ids:
                clean_id = int(competency_id)
                if clean_id not in valid_competency_ids:
                    raise ValueError("Pacing includes a competency outside this curriculum unit")
                connection.execute(
                    """
                    INSERT OR IGNORE INTO curriculum_unit_week_competencies (week_id, competency_id)
                    VALUES (?, ?)
                    """,
                    (week_id, clean_id),
                )
        return get_curriculum_pacing_by_unit(connection, unit_id)


def reset_curriculum_pacing(unit_id: int) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT id FROM curriculum_units WHERE id = ?", (unit_id,)).fetchone()
        if not row:
            return None
        reset_curriculum_unit_pacing(connection, unit_id)
        return get_curriculum_pacing_by_unit(connection, unit_id)


def get_curriculum_pacing_by_unit(connection: sqlite3.Connection, unit_id: int) -> dict[str, Any]:
    unit = dict(connection.execute(
        """
        SELECT curriculum_units.*, curriculum_documents.title AS document_title,
               curriculum_documents.version_label
        FROM curriculum_units
        JOIN curriculum_documents ON curriculum_documents.id = curriculum_units.document_id
        WHERE curriculum_units.id = ?
        """,
        (unit_id,),
    ).fetchone())
    unit["warnings"] = json.loads(unit.pop("warnings_json") or "[]")
    return {
        "unit": unit,
        "competencies": _unit_competencies(connection, unit_id),
        "weeks": _unit_weeks(connection, unit_id),
    }


def ensure_curriculum_unit_pacing(connection: sqlite3.Connection, unit_id: int) -> None:
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM curriculum_unit_weeks WHERE unit_id = ?",
        (unit_id,),
    ).fetchone()["count"]
    if int(count) < 10:
        reset_curriculum_unit_pacing(connection, unit_id)


def _unit_competencies(connection: sqlite3.Connection, unit_id: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT id, sequence, competency_text
        FROM curriculum_competencies
        WHERE unit_id = ?
        ORDER BY sequence
        """,
        (unit_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _unit_weeks(connection: sqlite3.Connection, unit_id: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT id, unit_id, week_number, focus, notes, created_at, updated_at
        FROM curriculum_unit_weeks
        WHERE unit_id = ?
        ORDER BY week_number
        """,
        (unit_id,),
    ).fetchall()
    weeks = [dict(row) for row in rows]
    for week in weeks:
        week["competencies"] = _week_competencies(connection, int(week["id"]))
        week["competency_ids"] = [item["id"] for item in week["competencies"]]
    return weeks


def _unit_week(connection: sqlite3.Connection, unit_id: int, week_number: int) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT id, unit_id, week_number, focus, notes, created_at, updated_at
        FROM curriculum_unit_weeks
        WHERE unit_id = ? AND week_number = ?
        """,
        (unit_id, week_number),
    ).fetchone()
    return dict(row) if row else None


def _week_competencies(connection: sqlite3.Connection, week_id: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT curriculum_competencies.id, curriculum_competencies.sequence,
               curriculum_competencies.competency_text
        FROM curriculum_unit_week_competencies
        JOIN curriculum_competencies
          ON curriculum_competencies.id = curriculum_unit_week_competencies.competency_id
        WHERE curriculum_unit_week_competencies.week_id = ?
        ORDER BY curriculum_competencies.sequence
        """,
        (week_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_curriculum_context(
    *,
    grade_level: str,
    subject: str,
    quarter: int | str | None,
    topic: str,
) -> dict[str, Any] | None:
    with connect() as connection:
        context = get_curriculum_unit(
            grade_level=grade_level,
            subject=subject,
            quarter=quarter,
            topic=topic,
            connection=connection,
        )
        if not context:
            return None
        context["competencies"] = _unit_competencies(connection, int(context["id"]))
        return context


def _fts_query(value: str) -> str:
    terms = re.findall(r"[A-Za-z0-9]+", value)
    return " OR ".join(terms) if terms else '""'
