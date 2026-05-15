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
    assert len(first["classes"]) == len(second["classes"]) == 2
    assert len(db.list_class_records(int(first["teacher"]["id"]))) == 2


def test_demo_seed_finds_curriculum_json_from_working_directory(tmp_path, monkeypatch):
    curriculum_dir = tmp_path / "curriculum_json"
    curriculum_dir.mkdir()
    expected = curriculum_dir / "sample.json"
    expected.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    from klasbot import demo_seed

    paths = demo_seed._curriculum_paths()

    assert expected in paths
