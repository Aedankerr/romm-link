from typing import Any

PLATFORM_EMULATORS = {
    "ps2": "pcsx2",
    "playstation 2": "pcsx2",
    "sony playstation 2": "pcsx2",
    "ps3": "rpcs3",
    "playstation 3": "rpcs3",
    "sony playstation 3": "rpcs3",
    "gamecube": "dolphin",
    "nintendo gamecube": "dolphin",
    "gc": "dolphin",
    "wii": "dolphin",
    "nintendo wii": "dolphin",
}


def emulator_for_platform(platform: str | None) -> str | None:
    if not platform:
        return None
    normalized = platform.strip().lower().replace("_", "-")
    if normalized in PLATFORM_EMULATORS:
        return PLATFORM_EMULATORS[normalized]
    for token, emulator in PLATFORM_EMULATORS.items():
        if token in normalized:
            return emulator
    return None


def _emulators_by_key(discovery: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {emulator.get("key"): emulator for emulator in discovery.get("emulators", []) if emulator.get("key")}


def route_for_game(game: dict[str, Any], discovery: dict[str, Any]) -> dict[str, Any]:
    emulator_key = emulator_for_platform(game.get("platform"))
    emulator = _emulators_by_key(discovery).get(emulator_key) if emulator_key else None
    launch_url = emulator.get("browser_url") if emulator else None
    name = game.get("name") or f"ROM {game.get('id', '')}".strip()

    if emulator_key and launch_url:
        display_name = emulator_key.upper() if emulator_key != "pcsx2" else "PCSX2"
        return {
            "supported": True,
            "action": "open_emulator",
            "emulator_key": emulator_key,
            "launch_url": launch_url,
            "message": f"Open {display_name} for {name}. Direct ROM launch is not implemented yet.",
        }

    return {
        "supported": False,
        "action": "unsupported",
        "emulator_key": emulator_key,
        "launch_url": None,
        "message": f"No detected emulator route for {name} ({game.get('platform') or 'unknown platform'}).",
    }


def enrich_games_with_emulators(games: list[dict[str, Any]], discovery: dict[str, Any]) -> list[dict[str, Any]]:
    enriched = []
    for game in games:
        route = route_for_game(game, discovery)
        enriched.append(
            {
                **game,
                "emulator_key": route["emulator_key"],
                "launch_url": route["launch_url"],
                "supported": route["supported"],
            }
        )
    return enriched
