# romm-link

romm-link is an Unraid-first companion launcher for RomM.

It discovers RomM and browser-accessible emulator containers such as:

- PCSX2
- RPCS3
- Dolphin

## MVP scope

This MVP includes:

- FastAPI backend
- Browser health/discovery dashboard served from FastAPI
- Docker socket discovery for RomM and supported emulator containers
- RomM API status client
- Docker Compose config using the existing external `romm` network
- Unraid template starter

## Quick test

```bash
python -m pip install -r backend/requirements.txt
python -m pytest tests/ -q
uvicorn backend.app.main:app --host 0.0.0.0 --port 8766
```

Open:

```text
http://localhost:8766
```

Backend endpoints:

```text
GET /api/health
GET /api/config
GET /api/discovery/docker
GET /api/romm/status
```

## Docker Compose

```bash
docker compose up --build
```

The compose file expects an existing external Docker network named `romm`:

```bash
docker network create romm
```

## Unraid test pull

The development branch publishes a test image to GitHub Container Registry:

```text
ghcr.io/aedankerr/romm-link:dev
```

Use this raw template URL for test installs before promoting to `main`:

```text
https://raw.githubusercontent.com/Aedankerr/romm-link/dev/unraid/romm-link.xml
```

On Unraid, make sure the external Docker network exists first:

```bash
docker network create romm
```

The template uses port `8766` and mounts `/var/run/docker.sock` so romm-link can discover RomM and emulator containers. It also reads Docker port bindings to generate browser-facing emulator links, so Unraid host ports can differ while internal container ports stay at `3000`. Generated emulator browser links default to `http` via `EMULATOR_BROWSER_SCHEME=http`; change it only if your emulator host ports actually serve HTTPS.

## Environment variables

```env
ROMM_URL=http://romm:8080
ROMM_API_KEY=
DOCKER_NETWORK=romm
PCSX2_CONTAINER=pcsx2
RPCS3_CONTAINER=rpcs3
DOLPHIN_CONTAINER=dolphin
PCSX2_WEB_URL=http://pcsx2:3000
RPCS3_WEB_URL=http://rpcs3:3000
DOLPHIN_WEB_URL=http://dolphin:3000
EMULATOR_BROWSER_SCHEME=http
```

## Unraid notes

This container needs access to:

```text
/var/run/docker.sock
```

That allows romm-link to discover emulator containers and their status.

Use Docker DNS on the shared `romm` network instead of fixed IP addresses:

```text
http://romm:8080
http://pcsx2:3000
http://rpcs3:3000
http://dolphin:3000
```

## Milestones

- v0.1: Discovery, health dashboard, Docker integration, RomM status integration, Unraid template
- v0.2: Emulator launch, ROM launch, BIOS detection
- v0.3: Streaming/session management
- v1.0: Production release
