import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    romm_url: str = Field(default="http://romm:8080", alias="ROMM_URL")
    romm_api_key: str = Field(default="", alias="ROMM_API_KEY")
    romm_username: str = Field(default="", alias="ROMM_USERNAME")
    romm_password: str = Field(default="", alias="ROMM_PASSWORD")
    docker_network: str = Field(default="romm", alias="DOCKER_NETWORK")

    pcsx2_container: str = Field(default="pcsx2", alias="PCSX2_CONTAINER")
    rpcs3_container: str = Field(default="rpcs3", alias="RPCS3_CONTAINER")
    dolphin_container: str = Field(default="dolphin", alias="DOLPHIN_CONTAINER")

    pcsx2_web_url: str = Field(default="http://pcsx2:3000", alias="PCSX2_WEB_URL")
    rpcs3_web_url: str = Field(default="http://rpcs3:3000", alias="RPCS3_WEB_URL")
    dolphin_web_url: str = Field(default="http://dolphin:3000", alias="DOLPHIN_WEB_URL")
    emulator_browser_scheme: str = Field(default="http", alias="EMULATOR_BROWSER_SCHEME")
    runtime_config_path: str = Field(default="/config/settings.json", alias="ROMM_LINK_CONFIG_PATH")

    def emulator_config(self) -> dict[str, dict[str, str]]:
        return {
            "pcsx2": {"container": self.pcsx2_container, "web_url": self.pcsx2_web_url},
            "rpcs3": {"container": self.rpcs3_container, "web_url": self.rpcs3_web_url},
            "dolphin": {"container": self.dolphin_container, "web_url": self.dolphin_web_url},
        }

    def public_config(self) -> dict[str, object]:
        return {
            "romm_url": self.romm_url,
            "romm_auth_configured": bool(self.romm_api_key or (self.romm_username and self.romm_password)),
            "docker_network": self.docker_network,
            "emulator_browser_scheme": self.emulator_browser_scheme,
            "emulators": self.emulator_config(),
        }


RUNTIME_CONFIG_KEYS = {"romm_url", "romm_api_key", "romm_username", "romm_password"}


def _runtime_config_path(settings: Settings) -> Path:
    return Path(settings.runtime_config_path)


def load_runtime_config(settings: Settings) -> dict[str, str]:
    path = _runtime_config_path(settings)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return {key: str(value) for key, value in data.items() if key in RUNTIME_CONFIG_KEYS and value is not None}


def save_runtime_config(settings: Settings, values: dict[str, Any]) -> dict[str, str]:
    current = load_runtime_config(settings)
    for key in RUNTIME_CONFIG_KEYS:
        if key in values:
            current[key] = "" if values[key] is None else str(values[key])
    path = _runtime_config_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, sort_keys=True))
    reset_settings_cache()
    return current


def runtime_config_public(settings: Settings) -> dict[str, object]:
    effective = apply_runtime_config(settings)
    return {
        "romm_url": effective.romm_url,
        "romm_username": effective.romm_username,
        "romm_api_key_configured": bool(effective.romm_api_key),
        "romm_password_configured": bool(effective.romm_password),
    }


def apply_runtime_config(settings: Settings) -> Settings:
    runtime = load_runtime_config(settings)
    if not runtime:
        return settings
    return settings.model_copy(update=runtime)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return apply_runtime_config(Settings())


def reset_settings_cache() -> None:
    get_settings.cache_clear()
