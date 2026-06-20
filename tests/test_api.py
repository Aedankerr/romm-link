import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


class FakeContainer:
    def __init__(self, name, image="example/image", status="running", networks=None):
        self.name = name
        self.image = image
        self.status = status
        self.attrs = {
            "Config": {"Image": image},
            "NetworkSettings": {"Networks": networks or {"romm": {}}},
        }


class FakeContainers:
    def __init__(self, containers):
        self._containers = containers

    def list(self, all=True):
        return self._containers


class FakeDockerClient:
    def __init__(self, containers):
        self.containers = FakeContainers(containers)


def test_health_reports_service_and_configured_romm_url(monkeypatch):
    monkeypatch.setenv("ROMM_URL", "http://romm:8080")
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "romm-link",
        "romm_url": "http://romm:8080",
    }


def test_config_uses_docker_dns_defaults_not_ip_addresses(monkeypatch):
    monkeypatch.delenv("PCSX2_WEB_URL", raising=False)
    monkeypatch.delenv("RPCS3_WEB_URL", raising=False)
    monkeypatch.delenv("DOLPHIN_WEB_URL", raising=False)
    client = TestClient(app)

    response = client.get("/api/config")

    assert response.status_code == 200
    body = response.json()
    assert body["docker_network"] == "romm"
    assert body["romm_url"] == "http://romm:8080"
    assert body["emulators"] == {
        "pcsx2": {"container": "pcsx2", "web_url": "http://pcsx2:3000"},
        "rpcs3": {"container": "rpcs3", "web_url": "http://rpcs3:3000"},
        "dolphin": {"container": "dolphin", "web_url": "http://dolphin:3000"},
    }


def test_docker_discovery_finds_romm_and_supported_emulators(monkeypatch):
    from backend.app import discovery

    fake_client = FakeDockerClient(
        [
            FakeContainer("romm", "rommapp/romm:latest"),
            FakeContainer("pcsx2", "linuxserver/pcsx2:latest"),
            FakeContainer("rpcs3", "rpcs3/rpcs3:latest"),
            FakeContainer("dolphin", "dolphin-emu:latest"),
            FakeContainer("postgres", "postgres:16"),
        ]
    )
    monkeypatch.setattr(discovery, "get_docker_client", lambda: fake_client)
    client = TestClient(app)

    response = client.get("/api/discovery/docker")

    assert response.status_code == 200
    body = response.json()
    assert body["network"] == "romm"
    assert body["romm"]["name"] == "romm"
    assert [item["key"] for item in body["emulators"]] == ["pcsx2", "rpcs3", "dolphin"]
    assert body["emulators"][0]["web_url"] == "http://pcsx2:3000"


def test_docker_discovery_reports_unavailable_socket(monkeypatch):
    from backend.app import discovery

    def raise_socket_error():
        raise RuntimeError("docker socket unavailable")

    monkeypatch.setattr(discovery, "get_docker_client", raise_socket_error)
    client = TestClient(app)

    response = client.get("/api/discovery/docker")

    assert response.status_code == 503
    assert response.json()["detail"] == "docker socket unavailable"


def test_romm_status_endpoint_returns_client_result(monkeypatch):
    from backend.app import romm

    async def fake_fetch(settings):
        return {"reachable": True, "url": settings.romm_url, "status_code": 200}

    monkeypatch.setattr(romm, "fetch_romm_status", fake_fetch)
    client = TestClient(app)

    response = client.get("/api/romm/status")

    assert response.status_code == 200
    assert response.json() == {"reachable": True, "url": "http://romm:8080", "status_code": 200}
