from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from tests.conftest import login


class FakeGradingOllama:
    def __init__(self):
        self.messages = []

    async def chat(self, model, messages, format=None):
        self.messages.append(messages)
        assert model == "gemma4:e2b"
        assert format == "json"
        assert messages
        return """
        {
          "student_name": "Ana Reyes",
          "student_identifier": "S-001",
          "items": [
            {
              "item_number": "1",
              "student_answer": "Heart",
              "correct_answer": "Heart",
              "score": 1,
              "max_score": 1,
              "feedback": "Correct.",
              "confidence": 0.91,
              "warnings": []
            },
            {
              "item_number": "2",
              "student_answer": "Lungs",
              "correct_answer": "Lungs",
              "score": 1,
              "max_score": 1,
              "feedback": "Correct.",
              "confidence": 0.9,
              "warnings": []
            }
          ],
          "total_score": 2,
          "max_score": 2,
          "rating": "100%",
          "overall_feedback": "Answers were extracted from the uploaded worksheet.",
          "confidence": 0.9,
          "warnings": []
        }
        """


class SlowGradingOllama:
    async def chat(self, model, messages, format=None):
        await asyncio.sleep(1)
        return "{}"


def _png_bytes(width: int = 1000, height: int = 800) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(612, 792))
    pdf.drawString(72, 720, "Quiz worksheet")
    pdf.drawString(72, 690, "1. Heart")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def test_quiz_photo_grading_batch_upload_detect_grade_review_and_delete(client, monkeypatch):
    from klasbot import main

    monkeypatch.setattr(main, "ollama_client", FakeGradingOllama())
    login(client, "1111")
    response = client.post(
        "/api/grading/batches",
        json={
            "subject": "Science",
            "grade_level": "Grade 6",
            "topic": "Human Body Systems",
            "quarter": 1,
            "week_number": 3,
            "week_topic": "Circulatory and respiratory system review",
            "total_points": 2,
            "grading_style": "exact",
            "questions": "1. What organ pumps blood?\n2. What organ helps breathing?",
            "answer_key": "1. Heart\n2. Lungs",
        },
    )
    assert response.status_code == 201
    batch = response.json()["batch"]
    assert batch["week_number"] == 3
    assert batch["week_topic"] == "Circulatory and respiratory system review"

    upload = client.post(
        f"/api/grading/batches/{batch['id']}/images",
        files={"file": ("worksheet.png", _png_bytes(), "image/png")},
    )
    assert upload.status_code == 201
    image = upload.json()["image"]
    assert Path(image["original_path"]).exists()
    assert Path(image["thumbnail_path"]).exists()

    thumbnail = client.get(f"/api/grading/images/{image['id']}/thumbnail")
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"].startswith("image/jpeg")

    detected = client.post(f"/api/grading/batches/{batch['id']}/detect-submissions")
    assert detected.status_code == 200
    submissions = detected.json()["submissions"]
    assert len(submissions) == 1
    assert submissions[0]["crop_box"]["right"] == 1000

    graded = client.post(f"/api/grading/batches/{batch['id']}/grade")
    assert graded.status_code == 200
    submission = graded.json()["submissions"][0]
    assert submission["max_score"] == 2
    assert submission["score"] == 2
    assert submission["extracted_answers"]["items"][0]["student_answer"] == "Heart"
    assert [item["correct_answer"] for item in submission["grading_result"]["items"]] == ["Heart", "Lungs"]
    assert "No OCR answer extracted yet" not in submission["grading_result"]["items"][0]["feedback"]

    edited_result = submission["grading_result"]
    edited_result["items"][0]["student_answer"] = "Heart"
    edited_result["items"][0]["score"] = 1
    response = client.patch(
        f"/api/grading/submissions/{submission['id']}",
        json={
            "student_name": "Ana Reyes",
            "student_identifier": "S-001",
            "extracted_answers": submission["extracted_answers"],
            "grading_result": edited_result,
            "score": 1,
            "max_score": 2,
            "confidence": 0.8,
            "teacher_reviewed": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["submission"]["student_name"] == "Ana Reyes"
    assert response.json()["submission"]["teacher_reviewed"] is True

    report = client.post(f"/api/grading/batches/{batch['id']}/print")
    assert report.status_code == 200
    assert "Ana Reyes" in report.text

    client.post("/api/auth/logout")
    login(client, "2222")
    assert client.get(f"/api/grading/batches/{batch['id']}").status_code == 404
    assert client.get(f"/api/grading/images/{image['id']}/thumbnail").status_code == 404

    client.post("/api/auth/logout")
    login(client, "1111")
    delete = client.delete(f"/api/grading/batches/{batch['id']}")
    assert delete.status_code == 200
    assert not Path(image["original_path"]).exists()
    assert not Path(image["thumbnail_path"]).exists()


def test_exact_answer_grading_requires_answer_key(client):
    login(client, "1111")

    response = client.post(
        "/api/grading/batches",
        json={
            "subject": "Math",
            "grade_level": "Grade 4",
            "topic": "Fractions",
            "total_points": 10,
            "grading_style": "exact",
        },
    )

    assert response.status_code == 400
    assert "answer key" in response.json()["detail"].lower()


def test_wide_quiz_photo_detects_two_candidate_submissions(client):
    login(client, "1111")
    batch = client.post(
        "/api/grading/batches",
        json={
            "subject": "English",
            "grade_level": "Grade 5",
            "topic": "Vocabulary",
            "total_points": 5,
            "grading_style": "review_only",
        },
    ).json()["batch"]
    client.post(
        f"/api/grading/batches/{batch['id']}/images",
        files={"file": ("wide.png", _png_bytes(2000, 800), "image/png")},
    )

    response = client.post(f"/api/grading/batches/{batch['id']}/detect-submissions")

    assert response.status_code == 200
    assert len(response.json()["submissions"]) == 2


def test_quiz_photo_grading_accepts_pdf_uploads(client):
    login(client, "1111")
    batch = client.post(
        "/api/grading/batches",
        json={
            "subject": "Science",
            "grade_level": "Grade 6",
            "topic": "Body Systems",
            "total_points": 5,
            "grading_style": "review_only",
        },
    ).json()["batch"]

    upload = client.post(
        f"/api/grading/batches/{batch['id']}/images",
        files={"file": ("worksheet.pdf", _pdf_bytes(), "application/pdf")},
    )

    assert upload.status_code == 201
    image = upload.json()["image"]
    assert image["mime_type"] == "application/pdf"
    assert image["width"] == 612
    assert image["height"] == 792
    assert Path(image["original_path"]).suffix == ".pdf"
    assert Path(image["original_path"]).exists()
    assert Path(image["thumbnail_path"]).exists()
    assert any("PDF uploaded" in warning for warning in image["quality_warnings"])

    thumbnail = client.get(f"/api/grading/images/{image['id']}/thumbnail")
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"].startswith("image/jpeg")

    detected = client.post(f"/api/grading/batches/{batch['id']}/detect-submissions")
    assert detected.status_code == 200
    assert len(detected.json()["submissions"]) == 1

    delete = client.delete(f"/api/grading/batches/{batch['id']}")
    assert delete.status_code == 200
    assert not Path(image["original_path"]).exists()
    assert not Path(image["thumbnail_path"]).exists()


def test_quiz_photo_grading_accepts_pdf_when_browser_sends_octet_stream(client):
    login(client, "1111")
    batch = client.post(
        "/api/grading/batches",
        json={
            "subject": "Science",
            "grade_level": "Grade 6",
            "topic": "Body Systems",
            "total_points": 5,
            "grading_style": "review_only",
        },
    ).json()["batch"]

    upload = client.post(
        f"/api/grading/batches/{batch['id']}/images",
        files={"file": ("worksheet.pdf", _pdf_bytes(), "application/octet-stream")},
    )

    assert upload.status_code == 201
    assert upload.json()["image"]["mime_type"] == "application/pdf"


def test_pdf_grading_sends_rendered_pages_to_ollama(client, monkeypatch):
    from klasbot import main
    from klasbot.grading import extraction

    fake_ollama = FakeGradingOllama()
    monkeypatch.setattr(main, "ollama_client", fake_ollama)
    monkeypatch.setattr(extraction, "_encode_pdf_pages", lambda path: (["encoded-page"], []))

    login(client, "1111")
    batch = client.post(
        "/api/grading/batches",
        json={
            "subject": "English",
            "grade_level": "Grade 6",
            "topic": "Short response",
            "questions": "Explain the main idea.",
            "total_points": 2,
            "grading_style": "rubric",
            "rubric": "2 points for a complete explanation.",
        },
    ).json()["batch"]
    client.post(
        f"/api/grading/batches/{batch['id']}/images",
        files={"file": ("worksheet.pdf", _pdf_bytes(), "application/pdf")},
    )
    client.post(f"/api/grading/batches/{batch['id']}/detect-submissions")

    response = client.post(f"/api/grading/batches/{batch['id']}/grade")

    assert response.status_code == 200
    assert fake_ollama.messages[0][1]["images"] == ["encoded-page"]


def test_grading_timeout_returns_manual_review_result(client, monkeypatch):
    from klasbot import main

    monkeypatch.setattr(main, "ollama_client", SlowGradingOllama())
    monkeypatch.setattr(main, "OLLAMA_GRADING_TIMEOUT_SECONDS", 0.01)
    login(client, "1111")
    batch = client.post(
        "/api/grading/batches",
        json={
            "subject": "Science",
            "grade_level": "Grade 6",
            "topic": "Human Body Systems",
            "total_points": 1,
            "grading_style": "exact",
            "answer_key": "1. Heart",
        },
    ).json()["batch"]
    client.post(
        f"/api/grading/batches/{batch['id']}/images",
        files={"file": ("worksheet.png", _png_bytes(), "image/png")},
    )
    client.post(f"/api/grading/batches/{batch['id']}/detect-submissions")

    response = client.post(f"/api/grading/batches/{batch['id']}/grade")

    assert response.status_code == 200
    submission = response.json()["submissions"][0]
    assert submission["score"] == 0
    assert any("timed out" in warning for warning in submission["grading_result"]["warnings"])
