import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


class FakeContainer:
    def __init__(
        self,
        name,
        image="example/image",
        status="running",
        networks=None,
        image_property=None,
        ports=None,
    ):
        self.name = name
        self._image = image if image_property is None else image_property
        self.status = status
        self.attrs = {
            "Config": {"Image": image},
            "NetworkSettings": {"Networks": networks or {"romm": {}}, "Ports": ports or {}},
        }

    @property
    def image(self):
        if isinstance(self._image, Exception):
            raise self._image
        return self._image


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
    assert body["emulator_browser_scheme"] == "http"
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


def test_docker_discovery_reports_browser_urls_from_host_port_bindings(monkeypatch):
    from backend.app import discovery

    fake_client = FakeDockerClient(
        [
            FakeContainer("romm", "rommapp/romm:latest"),
            FakeContainer(
                "pcsx2",
                "lscr.io/linuxserver/pcsx2",
                ports={"3000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3000"}]},
            ),
            FakeContainer(
                "rpcs3",
                "lscr.io/linuxserver/rpcs3",
                ports={"3000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3001"}]},
            ),
            FakeContainer(
                "dolphin",
                "lscr.io/linuxserver/dolphin",
                ports={"3000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3002"}]},
            ),
        ]
    )
    monkeypatch.setattr(discovery, "get_docker_client", lambda: fake_client)
    client = TestClient(app)

    response = client.get("/api/discovery/docker", headers={"host": "192.168.1.10:8766"})

    assert response.status_code == 200
    body = response.json()
    assert [item["browser_url"] for item in body["emulators"]] == [
        "http://192.168.1.10:3000",
        "http://192.168.1.10:3001",
        "http://192.168.1.10:3002",
    ]


def test_docker_discovery_defaults_browser_urls_to_http_even_when_romm_link_uses_https(monkeypatch):
    from backend.app import discovery

    fake_client = FakeDockerClient(
        [
            FakeContainer("romm", "rommapp/romm:latest"),
            FakeContainer(
                "pcsx2",
                "lscr.io/linuxserver/pcsx2",
                ports={"3000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3000"}]},
            ),
        ]
    )
    monkeypatch.setattr(discovery, "get_docker_client", lambda: fake_client)
    client = TestClient(app, base_url="https://romm-link.example.test")

    response = client.get("/api/discovery/docker")

    assert response.status_code == 200
    assert response.json()["emulators"][0]["browser_url"] == "http://romm-link.example.test:3000"


def test_docker_discovery_reports_unavailable_socket(monkeypatch):
    from backend.app import discovery

    def raise_socket_error():
        raise RuntimeError("docker socket unavailable")

    monkeypatch.setattr(discovery, "get_docker_client", raise_socket_error)
    client = TestClient(app)

    response = client.get("/api/discovery/docker")

    assert response.status_code == 503
    assert response.json()["detail"] == "docker socket unavailable"


def test_docker_discovery_uses_config_image_when_docker_image_inspect_is_missing(monkeypatch):
    from backend.app import discovery

    fake_client = FakeDockerClient(
        [
            FakeContainer("romm", "rommapp/romm:latest"),
            FakeContainer(
                "old-emulator",
                "linuxserver/pcsx2:old",
                image_property=RuntimeError("No such image: sha256:missing"),
            ),
        ]
    )
    monkeypatch.setattr(discovery, "get_docker_client", lambda: fake_client)
    client = TestClient(app)

    response = client.get("/api/discovery/docker")

    assert response.status_code == 200
    assert response.json()["emulators"][0]["image"] == "linuxserver/pcsx2:old"


def test_docker_discovery_does_not_treat_romm_link_as_romm(monkeypatch):
    from backend.app import discovery

    fake_client = FakeDockerClient(
        [
            FakeContainer("romm-link", "ghcr.io/aedankerr/romm-link:dev"),
            FakeContainer("pcsx2", "lscr.io/linuxserver/pcsx2"),
        ]
    )
    monkeypatch.setattr(discovery, "get_docker_client", lambda: fake_client)
    client = TestClient(app)

    response = client.get("/api/discovery/docker")

    assert response.status_code == 200
    assert response.json()["romm"] is None
    assert response.json()["emulators"][0]["key"] == "pcsx2"


def test_romm_status_endpoint_returns_client_result(monkeypatch):
    from backend.app import romm

    async def fake_fetch(settings):
        return {"reachable": True, "url": settings.romm_url, "status_code": 200}

    monkeypatch.setattr(romm, "fetch_romm_status", fake_fetch)
    client = TestClient(app)

    response = client.get("/api/romm/status")

    assert response.status_code == 200
    assert response.json() == {"reachable": True, "url": "http://romm:8080", "status_code": 200}


def test_romm_games_endpoint_enriches_games_with_launch_urls(monkeypatch):
    from backend.app import discovery, romm

    async def fake_roms(settings):
        return [{"id": 1, "name": "Gran Turismo 4", "platform": "PlayStation 2"}]

    def fake_discovery(settings, browser_host=None, scheme="http"):
        return {"emulators": [{"key": "pcsx2", "browser_url": "http://192.168.1.10:3000"}]}

    monkeypatch.setattr(romm, "fetch_roms", fake_roms)
    monkeypatch.setattr(discovery, "discover_docker", fake_discovery)
    client = TestClient(app)

    response = client.get("/api/romm/games")

    assert response.status_code == 200
    assert response.json()["games"] == [
        {
            "id": 1,
            "name": "Gran Turismo 4",
            "platform": "PlayStation 2",
            "emulator_key": "pcsx2",
            "launch_url": "http://192.168.1.10:3000",
            "supported": True,
        }
    ]


def test_launch_endpoint_returns_open_emulator_plan(monkeypatch):
    from backend.app import discovery, romm

    async def fake_rom(settings, rom_id):
        return {"id": rom_id, "name": "Gran Turismo 4", "platform": "PlayStation 2"}

    def fake_discovery(settings, browser_host=None, scheme="http"):
        return {"emulators": [{"key": "pcsx2", "browser_url": "http://192.168.1.10:3000"}]}

    monkeypatch.setattr(romm, "fetch_rom", fake_rom)
    monkeypatch.setattr(discovery, "discover_docker", fake_discovery)
    client = TestClient(app)

    response = client.post("/api/launch/1")

    assert response.status_code == 200
    assert response.json()["launch_url"] == "http://192.168.1.10:3000"
    assert response.json()["emulator_key"] == "pcsx2"
