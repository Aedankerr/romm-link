import docker


class DockerController:
    def __init__(self):
        self.client = docker.from_env()

    def start_container(self, name: str) -> str:
        container = self.client.containers.get(name)
        container.start()
        container.reload()
        return container.status

    def stop_container(self, name: str) -> str:
        container = self.client.containers.get(name)
        container.stop()
        container.reload()
        return container.status

    def container_status(self, name: str) -> str:
        container = self.client.containers.get(name)
        container.reload()
        return container.status
