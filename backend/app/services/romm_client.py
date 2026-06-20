import httpx

from backend.app.config import settings


class RomMClient:
    def __init__(self):
        self.base_url = settings.romm_url.rstrip("/")
        self.api_key = settings.romm_api_key

    @property
    def headers(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def health(self):
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(f"{self.base_url}/api/heartbeat", headers=self.headers)
                return {"ok": response.is_success, "status_code": response.status_code}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

    async def games(self):
        # RomM API routes vary by version. This MVP tries a common route first.
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/api/roms", headers=self.headers)
            response.raise_for_status()
            return response.json()
