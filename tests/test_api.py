from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from tests.conftest import login


def test_login_logout_and_me(client):
    response = client.get("/api/me")
    assert response.status_code == 401

    teacher = login(client)
    assert teacher["name"] == "Admin"

    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json()["teacher"]["is_admin"] is True

    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert client.get("/api/me").status_code == 401


def test_admin_teacher_management(client):
    login(client)

    response = client.post(
        "/api/admin/teachers",
        json={"name": "New Teacher", "pin": "3333", "is_admin": False},
    )
    assert response.status_code == 201
    teacher_id = response.json()["teacher"]["id"]

    response = client.get("/api/admin/teachers")
    assert response.status_code == 200
    assert any(teacher["name"] == "New Teacher" for teacher in response.json()["teachers"])

    response = client.post(f"/api/admin/teachers/{teacher_id}/reset-pin", json={"pin": "4444"})
    assert response.status_code == 200

    client.post("/api/auth/logout")
    response = client.post("/api/auth/login", json={"pin": "4444"})
    assert response.status_code == 200


def test_non_admin_cannot_manage_teachers(client):
    login(client, "2222")

    response = client.get("/api/admin/teachers")

    assert response.status_code == 403


def test_admin_can_update_lesson_plan_format_used_by_prompt(client):
    login(client, "1111")

    response = client.get("/api/admin/lesson-plan-formats")
    assert response.status_code == 200
    assert {item["format"] for item in response.json()["formats"]} >= {"DLP", "SDLP", "DLL"}

    custom_requirements = """# Custom Admin DLP
## Required Pilot Section
"""
    response = client.put(
        "/api/admin/lesson-plan-formats/DLP",
        json={"title": "Pilot Detailed Lesson Plan", "requirements": custom_requirements},
    )
    assert response.status_code == 200

    from klasbot.prompts.lesson_plan import build_lesson_plan_prompt

    prompt = build_lesson_plan_prompt(
        {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_levels": ["Grade 3"],
            "resources": ["paper"],
            "curriculum_context": "Science context",
        }
    )

    assert "# Custom Admin DLP" in prompt
    assert "Science context" in prompt
    assert "Teacher inputs:" in prompt
    assert "Return markdown with exactly this structure:" in prompt
    assert "# Detailed Lesson Plan (DLP)" not in prompt


def test_admin_lesson_plan_format_api_returns_structure_only(client):
    login(client, "1111")

    response = client.get("/api/admin/lesson-plan-formats")

    assert response.status_code == 200
    dlp = next(item for item in response.json()["formats"] if item["format"] == "DLP")
    assert dlp["requirements"].startswith("# Detailed Lesson Plan (DLP)")
    assert "Teacher inputs:" not in dlp["requirements"]
    assert "Uploaded curriculum context:" not in dlp["requirements"]
    assert "Return markdown with exactly this structure:" not in dlp["requirements"]


def test_lesson_plan_formats_endpoint_initializes_missing_table(client):
    from klasbot import db

    login(client, "1111")
    with db.connect() as connection:
        connection.execute("DROP TABLE lesson_plan_formats")

    response = client.get("/api/admin/lesson-plan-formats")

    assert response.status_code == 200
    assert [item["format"] for item in response.json()["formats"]] == ["DLP", "SDLP", "DLL"]


def test_non_admin_cannot_update_lesson_plan_formats(client):
    login(client, "2222")

    response = client.put(
        "/api/admin/lesson-plan-formats/DLP",
        json={"title": "Blocked", "requirements": "# Blocked"},
    )

    assert response.status_code == 403


def test_library_crud_and_cross_teacher_denial(client):
    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Math",
            "topic": "Fractions",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
        },
        "content_md": "# Draft",
    }
    response = client.post("/api/library", json=payload)
    assert response.status_code == 201
    output_id = response.json()["output"]["id"]

    response = client.get("/api/library")
    assert len(response.json()["outputs"]) == 1

    response = client.put(f"/api/library/{output_id}", json={"content_md": "# Edited"})
    assert response.status_code == 200
    assert response.json()["output"]["content_md"] == "# Edited"

    client.post("/api/auth/logout")
    login(client, "2222")
    assert client.get(f"/api/library/{output_id}").status_code == 404
    assert client.delete(f"/api/library/{output_id}").status_code == 404


def test_teaching_aids_crud_and_cross_teacher_denial(client):
    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "SDLP",
        "subject": "Math",
        "topic": "Triangle Similarity",
        "grade_levels": ["Grade 9"],
        "resources": ["ruler"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "SDLP",
            "subject": "Math",
            "topic": "Triangle Similarity",
            "grade_levels": ["Grade 9"],
            "resources": ["ruler"],
        },
        "content_md": "# SDLP\n\n## Application\nSolve a triangle similarity problem.",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]

    response = client.post(
        f"/api/library/{output_id}/teaching-aids",
        json={
            "aid_type": "worked_example",
            "title": "AA Similarity Worked Example",
            "source_section": "## Application",
            "custom_request": "Use AA similarity",
            "content_md": "# Worked Example\n\nStep-by-step solution",
        },
    )
    assert response.status_code == 201
    aid = response.json()["teaching_aid"]
    assert aid["aid_type"] == "worked_example"
    assert aid["source_section"] == "## Application"

    response = client.get(f"/api/library/{output_id}/teaching-aids")
    assert response.status_code == 200
    assert len(response.json()["teaching_aids"]) == 1

    response = client.put(
        f"/api/library/{output_id}/teaching-aids/{aid['id']}",
        json={"title": "Edited Aid", "content_md": "# Edited"},
    )
    assert response.status_code == 200
    assert response.json()["teaching_aid"]["title"] == "Edited Aid"

    client.post("/api/auth/logout")
    login(client, "2222")
    assert client.get(f"/api/library/{output_id}/teaching-aids").status_code == 404
    assert client.delete(f"/api/library/{output_id}/teaching-aids/{aid['id']}").status_code == 404


def test_teaching_aids_reject_assessment_outputs(client):
    login(client, "1111")
    payload = {
        "kind": "assessment",
        "format": "quiz",
        "subject": "Math",
        "topic": "Triangle Similarity",
        "grade_levels": ["Grade 9"],
        "resources": ["paper"],
        "inputs": {
            "kind": "assessment",
            "format": "quiz",
            "subject": "Math",
            "topic": "Triangle Similarity",
            "grade_levels": ["Grade 9"],
            "resources": ["paper"],
        },
        "content_md": "# Quiz",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]

    response = client.post(
        f"/api/library/{output_id}/teaching-aids/stream",
        json={"aid_type": "worked_example"},
    )

    assert response.status_code == 400
    assert "lesson plans only" in response.json()["detail"]


def test_teaching_aid_print_preview_and_share(client):
    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "SDLP",
        "subject": "Math",
        "topic": "Triangle Similarity",
        "grade_levels": ["Grade 9"],
        "resources": ["ruler"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "SDLP",
            "subject": "Math",
            "topic": "Triangle Similarity",
            "grade_levels": ["Grade 9"],
            "resources": ["ruler"],
        },
        "content_md": "# SDLP",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]
    aid = client.post(
        f"/api/library/{output_id}/teaching-aids",
        json={
            "aid_type": "worked_example",
            "title": "Worked Example",
            "content_md": "# Worked Example\n\nUse $a^2+b^2=c^2$ where useful.",
        },
    ).json()["teaching_aid"]

    response = client.post(
        "/api/print/preview",
        json={"output_id": output_id, "teaching_aid_id": aid["id"]},
    )
    assert response.status_code == 200
    assert "Worked Example" in response.text
    assert "katex" in response.text

    response = client.post(
        f"/api/library/{output_id}/teaching-aids/{aid['id']}/share",
        json={"expires_minutes": 15},
    )
    assert response.status_code == 201
    assert response.json()["filename"].endswith(".pdf")


def test_library_preserves_newlines_for_all_formats(client):
    login(client, "1111")
    cases = [
        ("lesson_plan", "DLP"),
        ("lesson_plan", "SDLP"),
        ("lesson_plan", "DLL"),
        ("assessment", "quiz"),
        ("assessment", "exam"),
    ]

    for kind, format_name in cases:
        content = f"# {format_name}\n\nFirst line\nSecond line\n\nAfter blank line"
        payload = {
            "kind": kind,
            "format": format_name,
            "subject": "Math",
            "topic": f"{format_name} newline check",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
            "inputs": {
                "kind": kind,
                "format": format_name,
                "subject": "Math",
                "topic": f"{format_name} newline check",
                "grade_levels": ["Grade 4"],
                "resources": ["paper"],
            },
            "content_md": content,
        }
        created = client.post("/api/library", json=payload).json()["output"]

        response = client.get(f"/api/library/{created['id']}")

        assert response.status_code == 200
        assert response.json()["output"]["content_md"] == content


def test_share_output_creates_public_pdf_download(client):
    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Math",
            "topic": "Fractions",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
        },
        "content_md": "# Draft\n\n- Use paper strips.",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]

    response = client.post(f"/api/library/{output_id}/share", json={"expires_minutes": 15})

    assert response.status_code == 201
    share = response.json()
    assert share["url"].endswith(f"/share/{share['token']}")
    assert share["download_url"].endswith(f"/share/{share['token']}/download")
    assert urlsplit(share["qr_url"]).path.endswith(f"/share/{share['token']}/qr.svg")
    assert parse_qs(urlsplit(share["qr_url"]).query)["target"] == [share["url"]]

    client.post("/api/auth/logout")
    page = client.get(f"/share/{share['token']}")
    assert page.status_code == 200
    assert "Download PDF" in page.text

    download = client.get(f"/share/{share['token']}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")

    qr = client.get(f"/share/{share['token']}/qr.svg")
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/svg+xml")


def test_share_qr_encodes_original_public_url_when_loaded_from_different_host(client, monkeypatch):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    captured = {}

    class FakeQr:
        def save(self, buffer):
            buffer.write(b"<svg></svg>")

    def fake_make(data, image_factory=None):
        captured["data"] = data
        captured["image_factory"] = image_factory
        return FakeQr()

    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Math",
            "topic": "Fractions",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
        },
        "content_md": "# Draft",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]
    share = client.post(f"/api/library/{output_id}/share", json={"expires_minutes": 15}).json()
    target = f"http://172.20.10.9:8000/share/{share['token']}"

    monkeypatch.setattr("klasbot.main.qrcode.make", fake_make)
    qr_client = TestClient(app, base_url="http://192.168.1.42:8000")
    response = qr_client.get(f"/share/{share['token']}/qr.svg", params={"target": target})

    assert response.status_code == 200
    assert captured["data"] == target


def test_remote_clients_can_only_open_share_routes(client):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    remote_client = TestClient(app, base_url="http://172.20.10.9:8000", client=("172.20.10.1", 52344))

    full_app = remote_client.get("/")
    assert full_app.status_code == 403
    assert "PDF sharing only" in full_app.text

    api_response = remote_client.get("/api/me")
    assert api_response.status_code == 403


def test_hosted_demo_mode_allows_remote_login(client, monkeypatch):
    from fastapi.testclient import TestClient
    from klasbot import main

    monkeypatch.setattr(main, "HOSTED_DEMO_ENABLED", True)
    remote_client = TestClient(main.app, base_url="https://klasbot-demo.vercel.app", client=("203.0.113.10", 52344))

    full_app = remote_client.get("/")
    assert full_app.status_code == 200
    assert "KlasBot" in full_app.text

    login_response = remote_client.post("/api/auth/login", json={"pin": "1111"})
    assert login_response.status_code == 200
    assert login_response.json()["teacher"]["is_admin"] is True


def test_mobile_pairing_allows_remote_teacher_library_access(client):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    login(client)
    pairing = client.post("/api/mobile/pairing-token").json()
    assert pairing["url"].endswith(f"/mobile/pair/{pairing['token']}")
    assert parse_qs(urlsplit(pairing["qr_url"]).query)["target"] == [pairing["url"]]
    assert pairing["expires_at"].endswith(" PHT")
    assert pairing["timezone"] == "Asia/Manila"
    assert pairing["expires_at_utc"].endswith("+00:00")

    remote_client = TestClient(app, base_url="http://172.20.10.9:8000", client=("172.20.10.1", 52344))
    pair_page = remote_client.get(f"/mobile/pair/{pairing['token']}")
    assert pair_page.status_code == 200
    assert "Pair this phone" in pair_page.text

    pair_response = remote_client.post(f"/mobile/pair/{pairing['token']}", follow_redirects=False)
    assert pair_response.status_code == 303
    assert "klasbot_session" in pair_response.headers["set-cookie"]

    me = remote_client.get("/api/me")
    assert me.status_code == 200
    csrf = me.json()["csrf_token"]

    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Math",
            "topic": "Fractions",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
        },
        "content_md": "# Draft",
    }
    created = remote_client.post("/api/library", json=payload, headers={"X-Klasbot-CSRF": csrf})
    assert created.status_code == 201
    assert remote_client.get("/api/library").json()["outputs"][0]["topic"] == "Fractions"


def test_mobile_pair_qr_encodes_original_public_url_when_loaded_from_different_host(client, monkeypatch):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    captured = {}

    class FakeQr:
        def save(self, buffer):
            buffer.write(b"<svg></svg>")

    def fake_make(data, image_factory=None):
        captured["data"] = data
        captured["image_factory"] = image_factory
        return FakeQr()

    login(client)
    token = client.post("/api/mobile/pairing-token").json()["token"]
    target = f"http://172.20.10.9:8000/mobile/pair/{token}"

    monkeypatch.setattr("klasbot.main.qrcode.make", fake_make)
    qr_client = TestClient(app, base_url="http://192.168.1.42:8000")
    response = qr_client.get(f"/mobile/pair/{token}/qr.svg", params={"target": target})

    assert response.status_code == 200
    assert captured["data"] == target


def test_mobile_pairing_token_is_single_use(client):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    login(client)
    token = client.post("/api/mobile/pairing-token").json()["token"]
    first_phone = TestClient(app, base_url="http://172.20.10.9:8000", client=("172.20.10.1", 52344))
    second_phone = TestClient(app, base_url="http://172.20.10.9:8000", client=("172.20.10.2", 52344))

    assert first_phone.get(f"/mobile/pair/{token}").status_code == 200
    assert first_phone.post(f"/mobile/pair/{token}", follow_redirects=False).status_code == 303
    assert second_phone.get(f"/mobile/pair/{token}", follow_redirects=False).status_code == 410


def test_remote_mobile_session_cannot_use_admin_api(client):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    login(client)
    token = client.post("/api/mobile/pairing-token").json()["token"]
    remote_client = TestClient(app, base_url="http://172.20.10.9:8000", client=("172.20.10.1", 52344))
    remote_client.post(f"/mobile/pair/{token}", follow_redirects=False)

    response = remote_client.get("/api/admin/teachers")

    assert response.status_code == 403


def test_remote_mobile_writes_require_csrf(client):
    from fastapi.testclient import TestClient
    from klasbot.main import app

    login(client)
    token = client.post("/api/mobile/pairing-token").json()["token"]
    remote_client = TestClient(app, base_url="http://172.20.10.9:8000", client=("172.20.10.1", 52344))
    remote_client.post(f"/mobile/pair/{token}", follow_redirects=False)

    response = remote_client.post("/api/library", json={"content_md": "# Draft"})

    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]


def test_library_update_detects_stale_mobile_edits(client):
    login(client)
    payload = {
        "kind": "assessment",
        "format": "quiz",
        "subject": "Science",
        "topic": "Plants",
        "grade_levels": ["Grade 3"],
        "resources": ["leaves"],
        "inputs": {
            "kind": "assessment",
            "format": "quiz",
            "subject": "Science",
            "topic": "Plants",
            "grade_levels": ["Grade 3"],
            "resources": ["leaves"],
        },
        "content_md": "# Quiz",
    }
    output = client.post("/api/library", json=payload).json()["output"]
    client.put(f"/api/library/{output['id']}", json={"content_md": "# Kiosk edit"})

    response = client.put(
        f"/api/library/{output['id']}",
        json={"content_md": "# Phone edit", "expected_updated_at": output["updated_at"]},
    )

    assert response.status_code == 409
    assert response.json()["output"]["content_md"] == "# Kiosk edit"


def test_share_urls_use_public_base_url(client, monkeypatch):
    monkeypatch.setattr("klasbot.main.PUBLIC_BASE_URL", "http://172.20.10.9:8000")
    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Math",
            "topic": "Fractions",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
        },
        "content_md": "# Draft",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]

    response = client.post(f"/api/library/{output_id}/share", json={"expires_minutes": 15})

    share = response.json()
    assert share["url"].startswith("http://172.20.10.9:8000/share/")
    assert share["download_url"].startswith("http://172.20.10.9:8000/share/")
    assert share["qr_url"].startswith("http://172.20.10.9:8000/share/")


def test_share_output_respects_teacher_ownership(client):
    login(client, "1111")
    payload = {
        "kind": "assessment",
        "format": "quiz",
        "subject": "Science",
        "topic": "Plants",
        "grade_levels": ["Grade 3"],
        "resources": ["leaves"],
        "inputs": {
            "kind": "assessment",
            "format": "quiz",
            "subject": "Science",
            "topic": "Plants",
            "grade_levels": ["Grade 3"],
            "resources": ["leaves"],
        },
        "content_md": "# Quiz",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]
    client.post("/api/auth/logout")
    login(client, "2222")

    response = client.post(f"/api/library/{output_id}/share", json={"expires_minutes": 15})

    assert response.status_code == 404


def test_expired_share_link_fails(client):
    from klasbot import db

    login(client, "1111")
    payload = {
        "kind": "lesson_plan",
        "format": "DLP",
        "subject": "Math",
        "topic": "Fractions",
        "grade_levels": ["Grade 4"],
        "resources": ["paper"],
        "inputs": {
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Math",
            "topic": "Fractions",
            "grade_levels": ["Grade 4"],
            "resources": ["paper"],
        },
        "content_md": "# Draft",
    }
    output_id = client.post("/api/library", json=payload).json()["output"]["id"]
    share = client.post(f"/api/library/{output_id}/share", json={"expires_minutes": 15}).json()
    with db.connect() as connection:
        connection.execute(
            "UPDATE shared_exports SET expires_at = ? WHERE token = ?",
            ("2000-01-01T00:00:00+00:00", share["token"]),
        )

    response = client.get(f"/share/{share['token']}/download")

    assert response.status_code == 410
