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
- Browser-facing emulator links from Docker port bindings
- RomM API status client
- RomM game list with PS2/PS3/GameCube/Wii emulator route hints
- Launch endpoint that starts the matching ROM inside the emulator container, then opens the emulator web UI
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
GET /api/romm/games
POST /api/launch/{rom_id}
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

The template uses port `8766` and mounts `/var/run/docker.sock` so romm-link can discover RomM and emulator containers, read Docker port bindings, and execute emulator launch commands inside those containers. Unraid host ports can differ while internal container ports stay at `3000`. Generated emulator browser links default to `http` via `EMULATOR_BROWSER_SCHEME=http`; change it only if your emulator host ports actually serve HTTPS.

Direct ROM launch assumes RomM reports paths under `ROMM_PATH_PREFIX=roms` and your emulator containers can see the same library at `EMULATOR_ROM_PATH_PREFIX=/roms`. For a RomM game path like `roms/wii/Game.rvz`, romm-link launches `/roms/wii/Game.rvz` inside the Dolphin container. Change these two variables if your containers use different mount points.

## Environment variables

```env
ROMM_URL=http://romm:8080
ROMM_API_KEY=
ROMM_USERNAME=
ROMM_PASSWORD=
DOCKER_NETWORK=romm
PCSX2_CONTAINER=pcsx2
RPCS3_CONTAINER=rpcs3
DOLPHIN_CONTAINER=dolphin
PCSX2_WEB_URL=http://pcsx2:3000
RPCS3_WEB_URL=http://rpcs3:3000
DOLPHIN_WEB_URL=http://dolphin:3000
EMULATOR_BROWSER_SCHEME=http
ROMM_PATH_PREFIX=roms
EMULATOR_ROM_PATH_PREFIX=/roms
EMULATOR_DISPLAY=:1
ROMM_LINK_CONFIG_PATH=/config/settings.json
```

RomM game listing requires authentication on current RomM builds. Set either `ROMM_API_KEY` to a bearer token/API key, or set `ROMM_USERNAME` and `ROMM_PASSWORD` so romm-link can request a scoped `/api/token` automatically (`read:roms read:platforms`). If token login is rejected or the scoped token is forbidden, romm-link falls back to HTTP Basic auth with the same username/password. Secrets are never returned by `/api/config`.

If auth was forgotten during Docker/Unraid setup, open the romm-link dashboard and use the **RomM login** form. The form writes runtime overrides to `/config/settings.json`, so map `/config` to persistent appdata if you want those changes to survive container replacement.

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
- v0.2: Direct emulator ROM launch, BIOS detection
- v0.3: Streaming/session management
- v1.0: Production release
