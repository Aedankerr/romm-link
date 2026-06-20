from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    romm_url: str = "http://romm:8080"
    romm_api_key: str = ""

    pcsx2_container: str = "pcsx2"
    rpcs3_container: str = "rpcs3"
    dolphin_container: str = "dolphin"

    pcsx2_web_url: str = "http://localhost:3000"
    rpcs3_web_url: str = "http://localhost:3001"
    dolphin_web_url: str = "http://localhost:3002"

    class Config:
        env_file = ".env"


settings = Settings()
