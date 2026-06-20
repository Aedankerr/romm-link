from pydantic import BaseModel


class EmulatorInfo(BaseModel):
    key: str
    name: str
    container: str
    web_url: str
    platforms: list[str]


class LaunchRequest(BaseModel):
    platform: str
    game_id: int | str | None = None
    rom_path: str | None = None


class LaunchResponse(BaseModel):
    emulator: str
    container: str
    status: str
    web_url: str
