from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editor_handles_enter_key_and_normalizes_line_endings():
    app_js = (ROOT / "klasbot" / "static" / "app.js").read_text(encoding="utf-8")

    assert "function normalizeLineEndings" in app_js
    assert "function insertAtCursor" in app_js
    assert "event.key !== 'Enter'" in app_js
    assert "insertAtCursor(els.editor, '\\n')" in app_js
