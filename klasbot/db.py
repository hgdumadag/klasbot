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
