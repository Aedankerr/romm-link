from fastapi.testclient import TestClient

from backend.app.main import app


def test_dashboard_uses_inline_launch_status_not_alerts():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "alert(" not in response.text
    assert 'id="launch-status"' in response.text
    assert "Open ${escapeHtml(game.emulator_key)}" in response.text
