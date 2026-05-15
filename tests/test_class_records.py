from __future__ import annotations

from tests.conftest import login


def _create_class(client) -> int:
    response = client.post(
        "/api/class-records/classes",
        json={
            "name": "Grade 6A Science",
            "grade_level": "6",
            "section": "A",
            "subject": "Science",
            "school_year": "2026-2027",
        },
    )
    assert response.status_code == 201
    return response.json()["class"]["id"]


def _add_student(client, class_id: int, first_name: str, last_name: str) -> int:
    response = client.post(
        f"/api/class-records/classes/{class_id}/students",
        json={"first_name": first_name, "last_name": last_name},
    )
    assert response.status_code == 201
    return response.json()["student"]["id"]


def _create_assessment(client, class_id: int, title: str = "Quiz 1") -> int:
    response = client.post(
        f"/api/class-records/classes/{class_id}/assessments",
        json={
            "title": title,
            "assessment_type": "quiz",
            "assessment_date": "2026-06-15",
            "max_score": 20,
        },
    )
    assert response.status_code == 201
    return response.json()["assessment"]["id"]


def test_class_records_crud_score_entry_and_dashboards(client):
    login(client, "1111")
    class_id = _create_class(client)
    first_student = _add_student(client, class_id, "Ana", "Santos")
    second_student = _add_student(client, class_id, "Ben", "Reyes")
    assessment_id = _create_assessment(client, class_id)

    grid = client.get(f"/api/class-records/assessments/{assessment_id}/scores")
    assert grid.status_code == 200
    assert len(grid.json()["rows"]) == 2

    response = client.put(
        f"/api/class-records/assessments/{assessment_id}/scores",
        json={
            "scores": [
                {"student_id": first_student, "score": 18, "notes": "Strong"},
                {"student_id": second_student, "is_absent": True, "notes": "Absent"},
            ]
        },
    )
    assert response.status_code == 200

    class_dashboard = client.get(f"/api/class-records/classes/{class_id}/dashboard")
    assert class_dashboard.status_code == 200
    dashboard = class_dashboard.json()["dashboard"]
    assert dashboard["student_count"] == 2
    assert dashboard["class_average"] == 90
    assert dashboard["missing_or_absent_count"] == 1
    assert dashboard["below_target_count"] == 0
    assert dashboard["assessment_count"] == 1
    assert dashboard["students"][0]["status_indicator"] in {"On Track", "No Data", "Watch"}
    students_by_name = {student["display_name"]: student for student in dashboard["students"]}
    assert students_by_name["Ana Santos"]["assessment_results"][0]["percentage"] == 90
    assert students_by_name["Ana Santos"]["assessment_results"][0]["is_below_target"] is False
    assert students_by_name["Ben Reyes"]["assessment_results"][0]["is_absent"] is True
    assert students_by_name["Ben Reyes"]["assessment_results"][0]["percentage"] is None

    assessment_dashboard = client.get(f"/api/class-records/assessments/{assessment_id}/dashboard")
    assert assessment_dashboard.status_code == 200
    assert assessment_dashboard.json()["dashboard"]["distribution"]["90-100%"] == 1
    assert len(assessment_dashboard.json()["dashboard"]["absent_or_missing_students"]) == 1


def test_class_records_reject_score_above_max(client):
    login(client, "1111")
    class_id = _create_class(client)
    student_id = _add_student(client, class_id, "Cara", "Lim")
    assessment_id = _create_assessment(client, class_id)

    response = client.put(
        f"/api/class-records/assessments/{assessment_id}/scores",
        json={"scores": [{"student_id": student_id, "score": 21}]},
    )

    assert response.status_code == 400
    assert "maximum" in response.json()["detail"]


def test_class_records_daily_attendance_grid_and_summary(client):
    login(client, "1111")
    class_id = _create_class(client)
    first_student = _add_student(client, class_id, "Ana", "Santos")
    second_student = _add_student(client, class_id, "Ben", "Reyes")

    empty_grid = client.get(
        f"/api/class-records/classes/{class_id}/attendance",
        params={"attendance_date": "2026-06-17"},
    )
    assert empty_grid.status_code == 200
    assert len(empty_grid.json()["rows"]) == 2
    assert empty_grid.json()["rows"][0]["status"] == "present"
    assert empty_grid.json()["summary"]["missing"] == 2

    response = client.put(
        f"/api/class-records/classes/{class_id}/attendance",
        json={
            "attendance_date": "2026-06-17",
            "rows": [
                {"student_id": first_student, "status": "present", "notes": ""},
                {"student_id": second_student, "status": "absent", "notes": "Sick"},
            ],
        },
    )
    assert response.status_code == 200
    saved = response.json()
    assert saved["summary"]["present"] == 1
    assert saved["summary"]["absent"] == 1
    assert saved["summary"]["attendance_rate"] == 50

    summary = client.get(f"/api/class-records/classes/{class_id}/attendance/summary")
    assert summary.status_code == 200
    data = summary.json()["summary"]
    assert data["dates"] == ["2026-06-17"]
    assert data["day_summaries"][0]["absent"] == 1
    students_by_name = {student["display_name"]: student for student in data["students"]}
    assert students_by_name["Ana Santos"]["attendance_records"][0]["status"] == "present"
    assert students_by_name["Ben Reyes"]["attendance_records"][0]["status"] == "absent"


def test_class_records_are_scoped_to_teacher(client):
    login(client, "1111")
    class_id = _create_class(client)
    student_id = _add_student(client, class_id, "Dina", "Cruz")
    assessment_id = _create_assessment(client, class_id)

    client.post("/api/auth/logout")
    login(client, "2222")

    assert client.get(f"/api/class-records/classes/{class_id}").status_code == 404
    assert client.get(f"/api/class-records/classes/{class_id}/students").status_code == 404
    assert client.get(f"/api/class-records/assessments/{assessment_id}/scores").status_code == 404
    assert client.get(f"/api/class-records/classes/{class_id}/attendance").status_code == 404
    response = client.patch(
        f"/api/class-records/students/{student_id}",
        json={"first_name": "Blocked", "last_name": "Teacher", "status": "active"},
    )
    assert response.status_code == 404


def test_class_records_db_helpers_are_teacher_scoped(tmp_path, monkeypatch):
    monkeypatch.setenv("KLASBOT_DB_PATH", str(tmp_path / "klasbot.db"))

    from klasbot import db
    from klasbot.auth import hash_pin

    db.init_db()
    first = db.create_teacher("One", hash_pin("1234"))
    second = db.create_teacher("Two", hash_pin("5678"))
    class_record = db.create_class_record(
        first["id"],
        {
            "name": "Grade 6 Science",
            "grade_level": "6",
            "section": "A",
            "subject": "Science",
            "school_year": "2026-2027",
        },
    )

    assert len(db.list_class_records(first["id"])) == 1
    assert db.get_class_record(second["id"], class_record["id"]) is None
