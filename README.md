# romm-link

romm-link is an Unraid-first companion launcher for RomM.

It connects RomM to browser-accessible emulator containers such as:

- PCSX2
- RPCS3
- Dolphin

## What this MVP does

- Provides a FastAPI backend.
- Provides a simple frontend.
- Reads config from environment variables.
- Exposes emulator launch endpoints.
- Uses Docker socket access to start existing emulator containers.
- Includes an Unraid XML template starter.

## What this MVP does not do yet

- It does not inject ROM files directly into emulators.
- It does not provide true WebRTC game streaming.
- It does not manage controller passthrough.
- It does not replace RomM.

## Quick test

```bash
docker compose up --build
```

Open:

```text
http://localhost:8787
```

Backend health:

```text
http://localhost:8787/api/health
```

## Environment variables

```env
ROMM_URL=http://romm:8080
ROMM_API_KEY=
PCSX2_CONTAINER=pcsx2
RPCS3_CONTAINER=rpcs3
DOLPHIN_CONTAINER=dolphin
PCSX2_WEB_URL=http://192.168.1.200:3000
RPCS3_WEB_URL=http://192.168.1.200:3001
DOLPHIN_WEB_URL=http://192.168.1.200:3002
```

## Unraid notes

This container needs access to:

```text
/var/run/docker.sock
```

That allows romm-link to start and stop emulator containers.
