from backend.app.config import settings


EMULATORS = {
    "ps2": {
        "key": "pcsx2",
        "name": "PCSX2",
        "container": settings.pcsx2_container,
        "web_url": settings.pcsx2_web_url,
        "platforms": ["ps2", "sony-playstation-2", "playstation-2"],
    },
    "ps3": {
        "key": "rpcs3",
        "name": "RPCS3",
        "container": settings.rpcs3_container,
        "web_url": settings.rpcs3_web_url,
        "platforms": ["ps3", "sony-playstation-3", "playstation-3"],
    },
    "wii": {
        "key": "dolphin",
        "name": "Dolphin",
        "container": settings.dolphin_container,
        "web_url": settings.dolphin_web_url,
        "platforms": ["wii", "nintendo-wii", "gamecube", "nintendo-gamecube"],
    },
}


def normalise_platform(platform: str) -> str:
    return platform.strip().lower().replace("_", "-").replace(" ", "-")


def get_emulator_for_platform(platform: str):
    target = normalise_platform(platform)
    for emulator in EMULATORS.values():
        if target in emulator["platforms"]:
            return emulator
    return None


def list_emulators():
    return list(EMULATORS.values())
