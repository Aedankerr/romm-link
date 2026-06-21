from typing import Any

import httpx

from backend.app.settings import Settings, get_settings


async def _headers(settings: Settings) -> dict[str, str]:
    if settings.romm_api_key:
        return {"Authorization": f"Bearer {settings.romm_api_key}"}
    if settings.romm_username and settings.romm_password:
        try:
            return {"Authorization": f"Bearer {await fetch_token(settings)}"}
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {401, 403}:
                raise
    return {}


def _basic_auth(settings: Settings) -> httpx.BasicAuth | None:
    if settings.romm_username and settings.romm_password:
        return httpx.BasicAuth(settings.romm_username, settings.romm_password)
    return None


async def fetch_token(settings: Settings) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _api_url(settings, "token"),
            data={
                "grant_type": "password",
                "username": settings.romm_username,
                "password": settings.romm_password,
                "scope": "read:roms read:platforms",
            },
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError("RomM token response did not include access_token")
        return token


def _api_url(settings: Settings, path: str) -> str:
    return f"{settings.romm_url.rstrip('/')}/api/{path.lstrip('/')}"


def _extract_platform_name(raw: dict[str, Any]) -> str | None:
    platform = raw.get("platform") or raw.get("platform_slug") or raw.get("platform_name")
    if isinstance(platform, dict):
        return platform.get("name") or platform.get("slug") or platform.get("fs_slug")
    return platform


def normalize_rom(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "id": raw.get("id"),
        "name": raw.get("name") or raw.get("fs_name") or raw.get("file_name") or "Unknown ROM",
        "platform": _extract_platform_name(raw),
        "path": raw.get("path") or raw.get("fs_path") or raw.get("file_path"),
    }
    for source_key, target_key in (
        ("file_path", "file_path"),
        ("fs_path", "file_path"),
        ("file_name", "file_name"),
        ("fs_name", "file_name"),
    ):
        if raw.get(source_key) and target_key not in normalized:
            normalized[target_key] = raw[source_key]
    return normalized


def _items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "roms", "data", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _single_item(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        for key in ("rom", "item", "data", "result"):
            value = data.get(key)
            if isinstance(value, dict):
                return value
        return data
    return {}


async def fetch_romm_status(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    health_url = _api_url(settings, "heartbeat")
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=await _headers(settings)) as client:
            response = await client.get(health_url)
    except httpx.HTTPError as exc:
        return {"reachable": False, "url": settings.romm_url, "error": str(exc)}

    return {
        "reachable": response.status_code < 500,
        "url": settings.romm_url,
        "status_code": response.status_code,
    }


async def _get_json(settings: Settings, path: str, params: dict[str, Any] | None = None) -> Any:
    headers = await _headers(settings)
    auth = None if headers else _basic_auth(settings)
    async with httpx.AsyncClient(timeout=15.0, headers=headers, auth=auth) as client:
        response = await client.get(_api_url(settings, path), params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            basic_auth = _basic_auth(settings)
            if exc.response.status_code in {401, 403} and headers and basic_auth:
                async with httpx.AsyncClient(timeout=15.0, headers={}, auth=basic_auth) as retry_client:
                    retry_response = await retry_client.get(_api_url(settings, path), params=params)
                    retry_response.raise_for_status()
                    return retry_response.json()
            raise
        return response.json()


async def fetch_roms(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    data = await _get_json(settings, "roms", params={"limit": 200})
    return [normalize_rom(item) for item in _items(data)]


async def fetch_rom(settings: Settings | None, rom_id: int) -> dict[str, Any]:
    settings = settings or get_settings()
    return normalize_rom(_single_item(await _get_json(settings, f"roms/{rom_id}")))
