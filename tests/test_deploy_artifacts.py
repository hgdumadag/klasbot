from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_systemd_unit_exposes_lan_app_for_share_links():
    service = (ROOT / "deploy" / "klasbot.service").read_text(encoding="utf-8")

    assert "ExecStart=/opt/klasbot/.venv/bin/python -m uvicorn klasbot.main:app" in service
    assert "--host 0.0.0.0 --port 8000" in service
    assert "KLASBOT_DB_PATH=/var/lib/klasbot/klasbot.db" in service


def test_pi_scripts_are_strict_and_use_expected_services():
    setup = (ROOT / "deploy" / "setup-pi.sh").read_text(encoding="utf-8")
    update = (ROOT / "deploy" / "update.sh").read_text(encoding="utf-8")
    kiosk = (ROOT / "deploy" / "kiosk.sh").read_text(encoding="utf-8")

    for script in (setup, update, kiosk):
        assert "set -euo pipefail" in script

    assert "systemctl enable --now klasbot.service" in setup
    assert "ollama pull" in setup
    assert "systemctl restart klasbot.service" in update
    assert "--kiosk" in kiosk


def test_week3_docs_exist():
    assert (ROOT / "README.md").exists()
    assert (ROOT / "docs" / "ADMIN_GUIDE.md").exists()
    assert (ROOT / "docs" / "PILOT_QA.md").exists()


def test_package_discovery_includes_subpackages():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.setuptools.packages.find]" in pyproject
    assert 'include = ["klasbot*"]' in pyproject


def test_vercel_fastapi_entrypoint_uses_project_script():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert '[project.scripts]' in pyproject
    assert 'app = "klasbot.main:app"' in pyproject
    assert "google-auth" in requirements
    assert not (ROOT / "vercel.json").exists()
