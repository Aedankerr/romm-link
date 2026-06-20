from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.app import romm
from backend.app.discovery import discover_docker
from backend.app.settings import get_settings

app = FastAPI(title="romm-link", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    settings = get_settings()
    return {"status": "ok", "service": "romm-link", "romm_url": settings.romm_url}


@app.get("/api/config")
def config():
    return get_settings().public_config()


@app.get("/api/discovery/docker")
def docker_discovery(request: Request):
    try:
        settings = get_settings()
        return discover_docker(
            settings,
            browser_host=request.url.hostname,
            scheme=settings.emulator_browser_scheme,
        )
    except Exception as exc:  # pragma: no cover - exercised through HTTP behavior
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/romm/status")
async def romm_status():
    return await romm.fetch_romm_status(get_settings())


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html lang="en">
  <head>
    <title>romm-link</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root { color-scheme: dark; }
      body { font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#0f172a; color:#e5e7eb; margin:0; }
      main { max-width:1000px; margin:0 auto; padding:40px 20px; }
      h1 { margin:0 0 8px; font-size:42px; }
      p { color:#94a3b8; }
      button { padding:10px 14px; margin:6px 6px 6px 0; border:0; border-radius:8px; cursor:pointer; background:#38bdf8; color:#082f49; font-weight:700; }
      .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin-top:24px; }
      .card { background:#1e293b; border:1px solid #334155; padding:20px; border-radius:14px; box-shadow:0 18px 50px rgba(0,0,0,.24); }
      .ok { color:#86efac; }
      .warn { color:#fbbf24; }
      pre { background:#020617; padding:14px; border-radius:10px; overflow:auto; border:1px solid #1e293b; }
      a { color:#7dd3fc; }
      .emulator-link { display:inline-flex; align-items:center; margin:0 8px 8px 0; padding:10px 14px; border-radius:8px; background:#38bdf8; color:#082f49; font-weight:700; text-decoration:none; }
      .emulator-link.disabled { background:#334155; color:#94a3b8; cursor:not-allowed; }
    </style>
  </head>
  <body>
    <main>
      <h1>romm-link</h1>
      <p>Unraid-first RomM companion for discovering emulator containers and opening their browser interfaces.</p>
      <button onclick="refreshAll()">Refresh discovery</button>
      <div class="grid">
        <section class="card">
          <h2>Health</h2>
          <pre id="health">Loading...</pre>
        </section>
        <section class="card">
          <h2>Configuration</h2>
          <pre id="config">Loading...</pre>
        </section>
        <section class="card">
          <h2>Docker discovery</h2>
          <div id="emulator-links"></div>
          <pre id="docker">Loading...</pre>
        </section>
        <section class="card">
          <h2>RomM API</h2>
          <pre id="romm">Loading...</pre>
        </section>
      </div>
    </main>
    <script>
      async function loadJson(path, target) {
        const el = document.getElementById(target);
        try {
          const res = await fetch(path);
          const data = await res.json();
          el.textContent = JSON.stringify(data, null, 2);
          el.className = res.ok ? 'ok' : 'warn';
          return data;
        } catch (err) {
          el.textContent = String(err);
          el.className = 'warn';
          return null;
        }
      }
      function renderEmulatorLinks(discovery) {
        const el = document.getElementById('emulator-links');
        const emulators = discovery && discovery.emulators ? discovery.emulators : [];
        if (!emulators.length) {
          el.innerHTML = '<p>No emulator containers detected yet.</p>';
          return;
        }
        el.innerHTML = emulators.map((emu) => {
          const label = `${emu.key || emu.name} (${emu.status})`;
          if (emu.browser_url) {
            return `<a class="emulator-link" href="${emu.browser_url}" target="_blank" rel="noopener">Open ${label}</a>`;
          }
          return `<span class="emulator-link disabled" title="No host port binding detected">${label}</span>`;
        }).join('');
      }
      async function loadDiscovery() {
        const data = await loadJson('/api/discovery/docker', 'docker');
        renderEmulatorLinks(data);
      }
      function refreshAll() {
        loadJson('/api/health', 'health');
        loadJson('/api/config', 'config');
        loadDiscovery();
        loadJson('/api/romm/status', 'romm');
      }
      refreshAll();
    </script>
  </body>
</html>
"""
