from fastapi import APIRouter, HTTPException

from backend.app.models.schemas import LaunchRequest, LaunchResponse
from backend.app.services.docker_control import DockerController
from backend.app.services.emulators import get_emulator_for_platform, list_emulators
from backend.app.services.romm_client import RomMClient

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    return {"status": "ok", "service": "romm-link"}


@router.get("/romm/health")
async def romm_health():
    return await RomMClient().health()


@router.get("/emulators")
async def emulators():
    return list_emulators()


@router.get("/games")
async def games():
    return await RomMClient().games()


@router.post("/launch", response_model=LaunchResponse)
async def launch(request: LaunchRequest):
    emulator = get_emulator_for_platform(request.platform)
    if not emulator:
        raise HTTPException(status_code=400, detail=f"No emulator mapped for platform: {request.platform}")

    try:
        status = DockerController().start_container(emulator["container"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return LaunchResponse(
        emulator=emulator["name"],
        container=emulator["container"],
        status=status,
        web_url=emulator["web_url"],
    )


@router.post("/stop")
async def stop(request: LaunchRequest):
    emulator = get_emulator_for_platform(request.platform)
    if not emulator:
        raise HTTPException(status_code=400, detail=f"No emulator mapped for platform: {request.platform}")

    try:
        status = DockerController().stop_container(emulator["container"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"emulator": emulator["name"], "container": emulator["container"], "status": status}
