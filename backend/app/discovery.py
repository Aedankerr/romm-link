from dataclasses import dataclass
from typing import Any

import docker

from backend.app.settings import Settings, get_settings


@dataclass(frozen=True)
class DiscoveredContainer:
    key: str | None
    name: str
    image: str
    status: str
    networks: list[str]
    web_url: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "image": self.image,
            "status": self.status,
            "networks": self.networks,
        }
        if self.key is not None:
            data["key"] = self.key
        if self.web_url is not None:
            data["web_url"] = self.web_url
        return data


def get_docker_client():
    return docker.from_env()


def _container_image(container: Any) -> str:
    config_image = getattr(container, "attrs", {}).get("Config", {}).get("Image")
    if config_image:
        return str(config_image)

    try:
        image = getattr(container, "image", "")
    except Exception:
        return "unknown"

    if isinstance(image, str):
        return image
    tags = getattr(image, "tags", None)
    if tags:
        return tags[0]
    return str(image)


def _container_networks(container: Any) -> list[str]:
    networks = (
        getattr(container, "attrs", {})
        .get("NetworkSettings", {})
        .get("Networks", {})
    )
    return sorted(networks.keys())


def _discovered_container(container: Any, key: str | None = None, web_url: str | None = None) -> DiscoveredContainer:
    return DiscoveredContainer(
        key=key,
        name=getattr(container, "name", "unknown"),
        image=_container_image(container),
        status=getattr(container, "status", "unknown"),
        networks=_container_networks(container),
        web_url=web_url,
    )


def _matches(container: Any, *needles: str) -> bool:
    haystack = f"{getattr(container, 'name', '')} {_container_image(container)}".lower()
    return any(needle.lower() in haystack for needle in needles)


def _is_romm_container(container: Any) -> bool:
    name = getattr(container, "name", "").lower()
    image = _container_image(container).lower()
    if name == "romm":
        return True
    if "romm-link" in name or "romm-link" in image:
        return False
    return image.startswith("rommapp/romm") or image.startswith("ghcr.io/rommapp/romm")


def discover_docker(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    client = get_docker_client()
    containers = client.containers.list(all=True)
    emulators_config = settings.emulator_config()

    romm = next((container for container in containers if _is_romm_container(container)), None)
    emulators = []
    for key, config in emulators_config.items():
        container_name = config["container"]
        match = next(
            (
                container
                for container in containers
                if getattr(container, "name", "").lower() == container_name.lower()
                or _matches(container, key)
            ),
            None,
        )
        if match is not None:
            emulators.append(_discovered_container(match, key=key, web_url=config["web_url"]).as_dict())

    return {
        "network": settings.docker_network,
        "romm": _discovered_container(romm).as_dict() if romm is not None else None,
        "emulators": emulators,
    }
