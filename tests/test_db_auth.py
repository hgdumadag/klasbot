from __future__ import annotations


def test_db_init_teacher_pin_and_library_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("KLASBOT_DB_PATH", str(tmp_path / "klasbot.db"))

    from klasbot import db
    from klasbot.auth import hash_pin, verify_pin

    db.init_db()
    db.init_db()
    first = db.create_teacher("One", hash_pin("1234"))
    second = db.create_teacher("Two", hash_pin("5678"))

    assert verify_pin("1234", db.list_teachers(include_hash=True)[0]["pin_hash"])

    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {"kind": "lesson_plan", "subject": "Math", "topic": "Fractions"},
        "content_md": "# Draft",
    }
    first_output = db.create_output(first["id"], payload)
    db.create_output(second["id"], {**payload, "topic": "Addition"})

    assert len(db.list_outputs(first["id"])) == 1
    assert db.get_output(second["id"], first_output["id"]) is None


def test_expired_session_is_rejected(client):
    from klasbot import db

    teacher = db.list_teachers()[0]
    db.create_session("expired-token", teacher["id"], "2000-01-01T00:00:00+00:00")

    response = client.get("/api/me", cookies={"klasbot_session": "expired-token"})

    assert response.status_code == 401
    assert db.get_session("expired-token") is None


def test_teaching_aids_are_scoped_and_cascade_with_parent_output(tmp_path, monkeypatch):
    monkeypatch.setenv("KLASBOT_DB_PATH", str(tmp_path / "klasbot.db"))

    from klasbot import db
    from klasbot.auth import hash_pin

    db.init_db()
    first = db.create_teacher("One", hash_pin("1234"))
    second = db.create_teacher("Two", hash_pin("5678"))
    output = db.create_output(
        first["id"],
        {
            "kind": "lesson_plan",
            "format": "SDLP",
            "subject": "Math",
            "topic": "Similarity",
            "grade_levels": ["Grade 9"],
            "resources": ["ruler"],
            "inputs": {"kind": "lesson_plan", "subject": "Math", "topic": "Similarity"},
            "content_md": "# Lesson",
        },
    )
    aid = db.create_teaching_aid(
        first["id"],
        output["id"],
        {
            "aid_type": "worked_example",
            "title": "Worked Example",
            "source_section": "Application",
            "inputs": {"aid_type": "worked_example"},
            "content_md": "# Worked Example",
        },
    )

    assert aid is not None
    assert len(db.list_teaching_aids(first["id"], output["id"])) == 1
    assert db.get_teaching_aid(second["id"], output["id"], aid["id"]) is None

    assert db.delete_output(first["id"], output["id"]) is True
    assert db.list_teaching_aids(first["id"], output["id"]) == []
