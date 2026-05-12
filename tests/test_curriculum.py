from __future__ import annotations

from pathlib import Path

from tests.conftest import login


ROOT = Path(__file__).resolve().parents[1]
SCIENCE_PDF = ROOT / "MATATAG Curriculum" / "FINAL MATATAG Science CG 2023 Grades 3-10.pdf"
MATH_PDF = ROOT / "MATATAG Curriculum" / "FINAL MATATAG Mathematics CG 2023 Grades 1-10.pdf"
FILIPINO_PDF = ROOT / "MATATAG Curriculum" / "FINAL MATATAG FILIPINO CG 2023 Grades 2-10.pdf"


def test_science_pdf_parser_detects_units_and_topics():
    from klasbot.curriculum import build_parse_diagnostics, parse_curriculum_pdf

    units = parse_curriculum_pdf(SCIENCE_PDF)
    diagnostics = build_parse_diagnostics(units)

    assert len(units) == 32
    assert diagnostics["unit_count"] == 32
    assert diagnostics["average_confidence"] == 1.0
    assert diagnostics["warning_count"] == 0
    assert units[0].grade_level == "Grade 3"
    assert units[0].quarter == 1
    assert units[0].domain == "MATERIALS"
    assert units[0].confidence == 1.0
    assert units[0].warnings == []
    assert any(
        unit.grade_level == "Grade 7" and unit.quarter == 2 and unit.domain == "LIFE SCIENCE"
        for unit in units
    )
    grade_7_life = next(
        unit for unit in units if unit.grade_level == "Grade 7" and unit.quarter == 2
    )
    assert any("compound microscope" in competency for competency in grade_7_life.learning_competencies)


def test_math_pdf_parser_detects_grade_quarter_tables():
    from klasbot.curriculum import build_parse_diagnostics, parse_curriculum_pdf

    units = parse_curriculum_pdf(MATH_PDF)
    diagnostics = build_parse_diagnostics(units)

    assert len(units) == 40
    assert diagnostics["unit_count"] == 40
    assert diagnostics["average_confidence"] == 1.0
    assert diagnostics["warning_count"] == 0
    assert units[0].grade_level == "Grade 1"
    assert units[0].quarter == 1
    assert units[0].domain == "Number and Algebra / Measurement and Geometry"
    assert any("2-dimensional shapes" in competency for competency in units[0].learning_competencies)
    assert units[-1].grade_level == "Grade 10"
    assert units[-1].quarter == 4


def test_filipino_pdf_parser_detects_baitang_markahan_tables():
    from klasbot.curriculum import build_parse_diagnostics, parse_curriculum_pdf

    units = parse_curriculum_pdf(FILIPINO_PDF)
    diagnostics = build_parse_diagnostics(units)

    assert len(units) == 36
    assert diagnostics["unit_count"] == 36
    assert diagnostics["average_confidence"] == 1.0
    assert diagnostics["warning_count"] == 0
    assert units[0].grade_level == "Grade 2"
    assert units[0].quarter == 1
    assert "Kamalayang Ponolohikal" in units[0].domain
    assert any("Alpabetong Filipino" in competency for competency in units[0].learning_competencies)
    assert units[-1].grade_level == "Grade 10"
    assert units[-1].quarter == 4


def test_admin_upload_populates_dropdowns_and_context(client):
    login(client, "1111")

    with SCIENCE_PDF.open("rb") as pdf_file:
        response = client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science", "version_label": "MATATAG 2023"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )

    assert response.status_code == 201
    assert response.json()["document"]["unit_count"] == 32
    assert response.json()["document"]["parse_summary"]["average_confidence"] == 1.0
    assert response.json()["document"]["parse_summary"]["warning_count"] == 0

    assert "Grade 7" in client.get("/api/curriculum/grades").json()["grades"]
    assert client.get("/api/curriculum/subjects?grade=Grade%207").json()["subjects"] == ["Science"]
    assert client.get(
        "/api/curriculum/quarters?grade=Grade%207&subject=Science"
    ).json()["quarters"] == [1, 2, 3, 4]

    topics = client.get(
        "/api/curriculum/topics?grade=Grade%207&subject=Science&quarter=2"
    ).json()["topics"]
    assert topics == [{"id": topics[0]["id"], "domain": "LIFE SCIENCE", "source_pages": "47"}]

    context = client.get(
        "/api/curriculum/context?grade=Grade%207&subject=Science&quarter=2&topic=LIFE%20SCIENCE"
    ).json()["context"]
    assert context["domain"] == "LIFE SCIENCE"
    assert context["confidence"] == 1.0
    assert context["warnings"] == []
    assert any("compound microscope" in item["competency_text"] for item in context["competencies"])

    pacing = client.get(
        "/api/curriculum/pacing?grade=Grade%207&subject=Science&quarter=2&topic=LIFE%20SCIENCE"
    ).json()["pacing"]
    assert pacing["unit"]["domain"] == "LIFE SCIENCE"
    assert len(pacing["weeks"]) == 10
    assert any(week["competencies"] for week in pacing["weeks"])


def test_parse_diagnostics_flags_missing_quarters_and_weak_units():
    from klasbot.curriculum import ParsedUnit, build_parse_diagnostics

    units = [
        ParsedUnit(
            grade_level="Grade 3",
            quarter=1,
            domain="Materials",
            content="",
            content_standards="",
            learning_competencies=[],
            performance_standard="",
            suggested_tasks="",
            source_pages="1",
            raw_text="short",
            confidence=0.2,
            warnings=["missing learning competencies"],
        )
    ]

    diagnostics = build_parse_diagnostics(units)

    assert diagnostics["unit_count"] == 1
    assert diagnostics["average_confidence"] == 0.2
    assert diagnostics["low_confidence_count"] == 1
    assert diagnostics["warning_count"] == 2
    assert "Grade 3: missing quarter(s) 2, 3, 4" in diagnostics["warnings"]


def test_non_admin_cannot_upload_curriculum(client):
    login(client, "2222")

    with SCIENCE_PDF.open("rb") as pdf_file:
        response = client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )

    assert response.status_code == 403


def test_admin_can_deactivate_curriculum_and_remove_dropdown_data(client):
    login(client, "1111")

    with SCIENCE_PDF.open("rb") as pdf_file:
        upload = client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science", "version_label": "MATATAG 2023"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )
    document_id = upload.json()["document"]["id"]

    response = client.post(f"/api/admin/curriculum/{document_id}/deactivate")

    assert response.status_code == 200
    assert response.json()["document"]["active"] is False
    assert "Grade 7" not in client.get("/api/curriculum/grades").json()["grades"]
    documents = client.get("/api/admin/curriculum").json()["documents"]
    assert documents[0]["active"] is False


def test_non_admin_cannot_deactivate_curriculum(client):
    login(client, "1111")
    with SCIENCE_PDF.open("rb") as pdf_file:
        upload = client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )
    document_id = upload.json()["document"]["id"]

    login(client, "2222")
    response = client.post(f"/api/admin/curriculum/{document_id}/deactivate")

    assert response.status_code == 403


def test_generation_prompt_includes_curriculum_context(client, monkeypatch):
    from klasbot import main

    seen = {}

    class FakeOllama:
        async def stream_generate(self, model, prompt):
            seen["prompt"] = prompt
            yield "ok"

    login(client, "1111")
    with SCIENCE_PDF.open("rb") as pdf_file:
        client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science", "version_label": "MATATAG 2023"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )
    monkeypatch.setattr(main, "ollama_client", FakeOllama())

    with client.stream(
        "GET",
        "/api/generate/stream?kind=lesson_plan&format=DLP&grade_level=Grade%207"
        "&subject=Science&quarter=2&topic=LIFE%20SCIENCE&week_number=1",
    ) as response:
        body = response.read().decode()

    assert response.status_code == 200
    assert "ok" in body
    assert "Uploaded curriculum context:" in seen["prompt"]
    assert "compound microscope" in seen["prompt"]
    assert "Selected weekly focus" in seen["prompt"]
    assert "Do not cover the full quarter" in seen["prompt"]


def test_generation_requires_week_when_curriculum_matches(client, monkeypatch):
    from klasbot import main

    login(client, "1111")
    with SCIENCE_PDF.open("rb") as pdf_file:
        client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science", "version_label": "MATATAG 2023"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )

    response = client.get(
        "/api/generate/stream?kind=lesson_plan&format=DLP&grade_level=Grade%207"
        "&subject=Science&quarter=2&topic=LIFE%20SCIENCE",
    )

    assert response.status_code == 400
    assert "pacing week" in response.json()["detail"]


def test_admin_can_update_and_reset_pacing(client):
    login(client, "1111")
    with SCIENCE_PDF.open("rb") as pdf_file:
        client.post(
            "/api/admin/curriculum/upload",
            data={"subject": "Science", "version_label": "MATATAG 2023"},
            files={"file": ("science.pdf", pdf_file, "application/pdf")},
        )
    pacing = client.get(
        "/api/curriculum/pacing?grade=Grade%207&subject=Science&quarter=2&topic=LIFE%20SCIENCE"
    ).json()["pacing"]
    unit_id = pacing["unit"]["id"]
    weeks = [
        {
            "week_number": week["week_number"],
            "focus": "Microscope handling" if week["week_number"] == 1 else week["focus"],
            "notes": "Use local specimens" if week["week_number"] == 1 else week["notes"],
            "competency_ids": week["competency_ids"],
        }
        for week in pacing["weeks"]
    ]

    update = client.put(f"/api/admin/curriculum/pacing/{unit_id}", json={"weeks": weeks})
    assert update.status_code == 200
    assert update.json()["pacing"]["weeks"][0]["focus"] == "Microscope handling"
    assert update.json()["pacing"]["weeks"][0]["notes"] == "Use local specimens"

    reset = client.post(f"/api/admin/curriculum/pacing/{unit_id}/reset")
    assert reset.status_code == 200
    assert reset.json()["pacing"]["weeks"][0]["focus"] != "Microscope handling"
