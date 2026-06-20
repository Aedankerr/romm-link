import asyncio

from backend.app.settings import Settings
from backend.app import romm


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeAsyncClient:
    calls = []

    def __init__(self, *args, **kwargs):
        self.headers = kwargs.get("headers", {})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None):
        self.calls.append(("POST", url, data, dict(self.headers)))
        return FakeResponse(payload={"access_token": "test-token"})

    async def get(self, url, params=None):
        self.calls.append(("GET", url, params, dict(self.headers)))
        return FakeResponse(
            payload={
                "roms": [
                    {"id": 1, "name": "Gran Turismo 4", "platform": {"name": "PlayStation 2"}}
                ]
            }
        )


def test_fetch_roms_uses_password_token_when_no_bearer_token(monkeypatch):
    FakeAsyncClient.calls = []
    monkeypatch.setattr(romm.httpx, "AsyncClient", FakeAsyncClient)
    settings = Settings(ROMM_URL="http://romm:8080", ROMM_USERNAME="aedan", ROMM_PASSWORD="secret")

    games = asyncio.run(romm.fetch_roms(settings))

    assert games == [{"id": 1, "name": "Gran Turismo 4", "platform": "PlayStation 2", "path": None}]
    assert FakeAsyncClient.calls[0] == (
        "POST",
        "http://romm:8080/api/token",
        {"grant_type": "password", "username": "aedan", "password": "secret"},
        {},
    )
    assert FakeAsyncClient.calls[1] == (
        "GET",
        "http://romm:8080/api/roms",
        {"limit": 200},
        {"Authorization": "Bearer test-token"},
    )
