from __future__ import annotations


def test_demo_seed_creates_admin_and_sample_classes_idempotently(tmp_path, monkeypatch):
    monkeypatch.setenv("KLASBOT_DB_PATH", str(tmp_path / "klasbot.db"))

    from klasbot import db
    from klasbot.auth import find_teacher_by_pin
    from klasbot.demo_seed import seed_demo_data

    db.init_db()
    first = seed_demo_data("Judge Demo", "1111", include_curriculum=False)
    second = seed_demo_data("Judge Demo", "1111", include_curriculum=False)

    teachers = db.list_teachers()
    assert len([teacher for teacher in teachers if teacher["name"] == "Judge Demo"]) == 1
    assert find_teacher_by_pin("1111")["name"] == "Judge Demo"
    assert len(first["classes"]) == len(second["classes"]) == 4
    class_records = db.list_class_records(int(first["teacher"]["id"]))
    assert len(class_records) == 4
    expected_student_counts = {
        "Grade 4 - English": 10,
        "Grade 5 - Mathematics": 10,
        "Grade 6 - Science": 10,
        "Grade 7 - Araling Panlipunan": 40,
    }
    assert {class_record["name"]: class_record["student_count"] for class_record in class_records} == expected_student_counts
    for class_record in class_records:
        expected_student_count = expected_student_counts[class_record["name"]]
        students = db.list_class_students(int(first["teacher"]["id"]), int(class_record["id"]))
        assert students is not None
        assert len(students) == expected_student_count
        assessments = db.list_class_assessments(int(first["teacher"]["id"]), int(class_record["id"]))
        assert assessments is not None
        assert len(assessments) == 3
        for assessment in assessments:
            grid = db.get_score_grid(int(first["teacher"]["id"]), int(assessment["id"]))
            assert grid is not None
            assert len(grid["rows"]) == expected_student_count
            assert all(row["score"] is not None for row in grid["rows"])
        attendance = db.get_attendance_summary(int(first["teacher"]["id"]), int(class_record["id"]), 30)
        assert attendance is not None
        assert len(attendance["dates"]) == 15
        assert len(attendance["students"]) == expected_student_count
        assert all(
            len(student["attendance_records"]) == 15
            for student in attendance["students"]
        )


def test_demo_seed_finds_curriculum_json_from_working_directory(tmp_path, monkeypatch):
    curriculum_dir = tmp_path / "curriculum_json"
    curriculum_dir.mkdir()
    expected = curriculum_dir / "sample.json"
    expected.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    from klasbot import demo_seed

    paths = demo_seed._curriculum_paths()

    assert expected in paths


def test_demo_seed_finds_packaged_curriculum_json():
    from klasbot import demo_seed

    paths = demo_seed._curriculum_paths()

    assert any(path.parts[-2:] == ("curriculum_json", "matatag_mathematics_cg.json") for path in paths)


def test_demo_seed_reimports_when_documents_exist_without_grades(tmp_path, monkeypatch):
    monkeypatch.setenv("KLASBOT_DB_PATH", str(tmp_path / "klasbot.db"))

    from klasbot import db
    from klasbot.demo_seed import seed_demo_data

    db.init_db()
    with db.connect() as connection:
        db.create_curriculum_document(
            connection,
            {
                "subject": "Mathematics",
                "title": "Broken stale import",
                "filename": "broken.json",
                "stored_path": "broken.json",
                "version_label": "Broken",
                "uploaded_by": None,
                "active": True,
                "parse_summary": {},
            },
        )

    seed_demo_data("Judge Demo", "1111")

    assert "Grade 4" in db.curriculum_grades()
