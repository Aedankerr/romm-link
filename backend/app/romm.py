from typing import Any

import httpx

from backend.app.settings import Settings, get_settings


def _headers(settings: Settings) -> dict[str, str]:
    if not settings.romm_api_key:
        return {}
    return {"Authorization": f"Bearer {settings.romm_api_key}"}


async def fetch_romm_status(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    health_url = f"{settings.romm_url.rstrip('/')}/api/heartbeat"
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=_headers(settings)) as client:
            response = await client.get(health_url)
    except httpx.HTTPError as exc:
        return {"reachable": False, "url": settings.romm_url, "error": str(exc)}

    return {
        "reachable": response.status_code < 500,
        "url": settings.romm_url,
        "status_code": response.status_code,
    }
