from pathlib import PurePosixPath
from typing import Any

from backend.app import discovery
from backend.app.launcher import route_for_game
from backend.app.settings import Settings

EMULATOR_COMMANDS = {
    "dolphin": 'dolphin-emu -b -e "$ROM_PATH" >/tmp/romm-link-dolphin.log 2>&1 &',
    "pcsx2": 'pcsx2-qt -batch -fullscreen "$ROM_PATH" >/tmp/romm-link-pcsx2.log 2>&1 &',
    "rpcs3": 'rpcs3 --no-gui "$ROM_PATH" >/tmp/romm-link-rpcs3.log 2>&1 &',
}


def _clean_path(value: str) -> str:
    return value.strip().replace("\\", "/").strip("/")


def build_emulator_rom_path(game: dict[str, Any], settings: Settings) -> str:
    raw_file_path = game.get("file_path") or game.get("fs_path")
    if raw_file_path:
        romm_path = _clean_path(str(raw_file_path))
    else:
        raw_dir = game.get("path") or ""
        raw_name = game.get("file_name") or game.get("fs_name") or game.get("name") or ""
        romm_path = _clean_path(str(PurePosixPath(_clean_path(str(raw_dir))) / str(raw_name)))

    romm_prefix = _clean_path(settings.romm_path_prefix)
    emulator_prefix = settings.emulator_rom_path_prefix.rstrip("/") or "/roms"

    relative = romm_path
    if romm_prefix and (relative == romm_prefix or relative.startswith(f"{romm_prefix}/")):
        relative = relative[len(romm_prefix):].lstrip("/")

    return str(PurePosixPath(emulator_prefix) / relative)


def _emulator_by_key(discovery_result: dict[str, Any], key: str) -> dict[str, Any] | None:
    return next((item for item in discovery_result.get("emulators", []) if item.get("key") == key), None)


def launch_game(game: dict[str, Any], discovery_result: dict[str, Any], settings: Settings) -> dict[str, Any]:
    route = route_for_game(game, discovery_result)
    if not route.get("supported"):
        return route

    emulator_key = route.get("emulator_key")
    command = EMULATOR_COMMANDS.get(str(emulator_key))
    emulator = _emulator_by_key(discovery_result, str(emulator_key)) if emulator_key else None
    container_name = emulator.get("name") if emulator else None
    if not command or not container_name:
        return route

    rom_path = build_emulator_rom_path(game, settings)
    container = discovery.get_docker_client().containers.get(container_name)
    container.exec_run(
        ["sh", "-lc", command],
        detach=True,
        environment={"DISPLAY": settings.emulator_display, "ROM_PATH": rom_path},
    )

    return {
        **route,
        "action": "launch_rom",
        "rom_path": rom_path,
        "message": f"Started {route['emulator_key']} for {game.get('name') or game.get('id')}. Opening emulator UI...",
    }
