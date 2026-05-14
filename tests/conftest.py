from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("KLASBOT_DB_PATH", str(tmp_path / "klasbot.db"))
    monkeypatch.setenv("KLASBOT_SHARE_DIR", str(tmp_path / "shared_exports"))
    monkeypatch.setenv("KLASBOT_GRADING_UPLOAD_DIR", str(tmp_path / "grading_uploads"))

    from klasbot import db
    from klasbot.auth import hash_pin
    from klasbot.main import app

    db.init_db()
    db.create_teacher("Admin", hash_pin("1111"), is_admin=True)
    db.create_teacher("Teacher", hash_pin("2222"), is_admin=False)

    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, pin: str = "1111") -> dict:
    response = client.post("/api/auth/login", json={"pin": pin})
    assert response.status_code == 200
    return response.json()["teacher"]
