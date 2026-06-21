from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.settings import reset_settings_cache


@pytest.fixture(autouse=True)
def clear_settings_cache():
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_runtime_config_save_updates_public_config(monkeypatch, tmp_path):
    config_path = tmp_path / "settings.json"
    monkeypatch.setenv("ROMM_LINK_CONFIG_PATH", str(config_path))
    reset_settings_cache()
    client = TestClient(app)

    response = client.post(
        "/api/runtime-config",
        json={
            "romm_url": "http://romm:8080",
            "romm_username": "aedan",
            "romm_password": "secret",
            "romm_api_key": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert Path(config_path).exists()

    config_response = client.get("/api/config")
    body = config_response.json()
    assert body["romm_url"] == "http://romm:8080"
    assert body["romm_auth_configured"] is True
    assert "secret" not in str(body)


def test_runtime_config_get_masks_secret_values(monkeypatch, tmp_path):
    config_path = tmp_path / "settings.json"
    config_path.write_text(
        '{"romm_url":"http://romm:8080","romm_username":"aedan","romm_password":"secret","romm_api_key":"token"}'
    )
    monkeypatch.setenv("ROMM_LINK_CONFIG_PATH", str(config_path))
    reset_settings_cache()
    client = TestClient(app)

    response = client.get("/api/runtime-config")

    assert response.status_code == 200
    assert response.json() == {
        "romm_url": "http://romm:8080",
        "romm_username": "aedan",
        "romm_api_key_configured": True,
        "romm_password_configured": True,
    }
    assert "secret" not in response.text
    assert "token" not in response.text


def test_dashboard_contains_runtime_config_form():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="runtime-config-form"' in response.text
    assert 'name="romm_username"' in response.text
    assert 'name="romm_password"' in response.text
