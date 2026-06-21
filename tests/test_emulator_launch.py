from backend.app import emulator_launch
from backend.app.settings import Settings


class FakeContainer:
    def __init__(self, name="dolphin"):
        self.name = name
        self.exec_calls = []

    def exec_run(self, command, detach=False, environment=None):
        self.exec_calls.append({"command": command, "detach": detach, "environment": environment})
        return "exec-id"


class FakeContainers:
    def __init__(self, containers):
        self._containers = {container.name: container for container in containers}

    def get(self, name):
        return self._containers[name]


class FakeDockerClient:
    def __init__(self, containers):
        self.containers = FakeContainers(containers)


def test_build_emulator_rom_path_rewrites_romm_relative_path_to_emulator_mount():
    settings = Settings(ROMM_PATH_PREFIX="roms", EMULATOR_ROM_PATH_PREFIX="/roms")
    game = {"path": "roms/wii", "name": "101-in-1 Sports [SOIEEB].rvz"}

    assert emulator_launch.build_emulator_rom_path(game, settings) == "/roms/wii/101-in-1 Sports [SOIEEB].rvz"


def test_build_emulator_rom_path_uses_romm_file_path_when_available():
    settings = Settings(ROMM_PATH_PREFIX="roms", EMULATOR_ROM_PATH_PREFIX="/mnt/roms")
    game = {"file_path": "roms/ps2/Gran Turismo 4.iso", "path": "roms/ps2", "name": "Gran Turismo 4"}

    assert emulator_launch.build_emulator_rom_path(game, settings) == "/mnt/roms/ps2/Gran Turismo 4.iso"


def test_launch_game_execs_dolphin_container_with_translated_rom_path(monkeypatch):
    container = FakeContainer("dolphin")
    monkeypatch.setattr(emulator_launch.discovery, "get_docker_client", lambda: FakeDockerClient([container]))
    settings = Settings(ROMM_PATH_PREFIX="roms", EMULATOR_ROM_PATH_PREFIX="/roms")
    game = {"id": 6789, "name": "101-in-1 Sports [SOIEEB].rvz", "platform": "wii", "path": "roms/wii"}
    discovered = {"emulators": [{"key": "dolphin", "name": "dolphin", "browser_url": "http://unraid:3004"}]}

    result = emulator_launch.launch_game(game, discovered, settings)

    assert result["supported"] is True
    assert result["action"] == "launch_rom"
    assert result["emulator_key"] == "dolphin"
    assert result["launch_url"] == "http://unraid:3004"
    assert result["rom_path"] == "/roms/wii/101-in-1 Sports [SOIEEB].rvz"
    assert container.exec_calls == [
        {
            "command": ["sh", "-lc", "dolphin-emu -b -e \"$ROM_PATH\" >/tmp/romm-link-dolphin.log 2>&1 &"],
            "detach": True,
            "environment": {"DISPLAY": ":1", "ROM_PATH": "/roms/wii/101-in-1 Sports [SOIEEB].rvz"},
        }
    ]
