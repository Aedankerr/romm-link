from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    romm_url: str = Field(default="http://romm:8080", alias="ROMM_URL")
    romm_api_key: str = Field(default="", alias="ROMM_API_KEY")
    docker_network: str = Field(default="romm", alias="DOCKER_NETWORK")

    pcsx2_container: str = Field(default="pcsx2", alias="PCSX2_CONTAINER")
    rpcs3_container: str = Field(default="rpcs3", alias="RPCS3_CONTAINER")
    dolphin_container: str = Field(default="dolphin", alias="DOLPHIN_CONTAINER")

    pcsx2_web_url: str = Field(default="http://pcsx2:3000", alias="PCSX2_WEB_URL")
    rpcs3_web_url: str = Field(default="http://rpcs3:3000", alias="RPCS3_WEB_URL")
    dolphin_web_url: str = Field(default="http://dolphin:3000", alias="DOLPHIN_WEB_URL")
    emulator_browser_scheme: str = Field(default="http", alias="EMULATOR_BROWSER_SCHEME")

    def emulator_config(self) -> dict[str, dict[str, str]]:
        return {
            "pcsx2": {"container": self.pcsx2_container, "web_url": self.pcsx2_web_url},
            "rpcs3": {"container": self.rpcs3_container, "web_url": self.rpcs3_web_url},
            "dolphin": {"container": self.dolphin_container, "web_url": self.dolphin_web_url},
        }

    def public_config(self) -> dict[str, object]:
        return {
            "romm_url": self.romm_url,
            "docker_network": self.docker_network,
            "emulator_browser_scheme": self.emulator_browser_scheme,
            "emulators": self.emulator_config(),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
