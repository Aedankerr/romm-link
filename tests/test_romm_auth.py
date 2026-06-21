import asyncio

from backend.app.settings import Settings
from backend.app import romm


class FakeResponse:
    def __init__(self, status_code=200, payload=None, request_url="http://romm:8080/api/test"):
        self.status_code = status_code
        self._payload = payload or {}
        self.request = romm.httpx.Request("GET", request_url)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise romm.httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=self.request,
                response=romm.httpx.Response(self.status_code, request=self.request),
            )


class FakeAsyncClient:
    calls = []

    def __init__(self, *args, **kwargs):
        self.headers = kwargs.get("headers", {})
        self.auth = kwargs.get("auth")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None):
        self.calls.append(("POST", url, data, dict(self.headers), self.auth))
        return FakeResponse(payload={"access_token": "test-token"})

    async def get(self, url, params=None):
        self.calls.append(("GET", url, params, dict(self.headers), self.auth))
        return FakeResponse(
            payload={
                "roms": [
                    {"id": 1, "name": "Gran Turismo 4", "platform": {"name": "PlayStation 2"}}
                ]
            }
        )


class TokenRejectingAsyncClient(FakeAsyncClient):
    async def post(self, url, data=None):
        self.calls.append(("POST", url, data, dict(self.headers), self.auth))
        return FakeResponse(status_code=401, request_url=url)


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
        None,
    )
    assert FakeAsyncClient.calls[1] == (
        "GET",
        "http://romm:8080/api/roms",
        {"limit": 200},
        {"Authorization": "Bearer test-token"},
        None,
    )


def test_fetch_roms_falls_back_to_basic_auth_when_token_login_is_rejected(monkeypatch):
    TokenRejectingAsyncClient.calls = []
    monkeypatch.setattr(romm.httpx, "AsyncClient", TokenRejectingAsyncClient)
    settings = Settings(ROMM_URL="http://romm:8080", ROMM_USERNAME="aedan", ROMM_PASSWORD="secret")

    games = asyncio.run(romm.fetch_roms(settings))

    assert games == [{"id": 1, "name": "Gran Turismo 4", "platform": "PlayStation 2", "path": None}]
    assert TokenRejectingAsyncClient.calls[0][0:3] == (
        "POST",
        "http://romm:8080/api/token",
        {"grant_type": "password", "username": "aedan", "password": "secret"},
    )
    assert TokenRejectingAsyncClient.calls[1][0:4] == (
        "GET",
        "http://romm:8080/api/roms",
        {"limit": 200},
        {},
    )
    basic_auth = TokenRejectingAsyncClient.calls[1][4]
    assert isinstance(basic_auth, romm.httpx.BasicAuth)
