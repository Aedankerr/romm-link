from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.app import discovery, romm
from backend.app.launcher import enrich_games_with_emulators, route_for_game
from backend.app.settings import get_settings, runtime_config_public, save_runtime_config

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


@app.get("/api/runtime-config")
def get_runtime_config():
    return runtime_config_public(get_settings())


@app.post("/api/runtime-config")
def update_runtime_config(payload: dict[str, object]):
    save_runtime_config(get_settings(), payload)
    return {"saved": True, "config": runtime_config_public(get_settings())}


@app.get("/api/discovery/docker")
def docker_discovery(request: Request):
    try:
        settings = get_settings()
        return discovery.discover_docker(
            settings,
            browser_host=request.url.hostname,
            scheme=settings.emulator_browser_scheme,
        )
    except Exception as exc:  # pragma: no cover - exercised through HTTP behavior
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/romm/status")
async def romm_status():
    return await romm.fetch_romm_status(get_settings())


@app.get("/api/romm/games")
async def romm_games(request: Request):
    try:
        settings = get_settings()
        games = await romm.fetch_roms(settings)
        detected = discovery.discover_docker(
            settings,
            browser_host=request.url.hostname,
            scheme=settings.emulator_browser_scheme,
        )
        return {"games": enrich_games_with_emulators(games, detected)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/launch/{rom_id}")
async def launch_rom(rom_id: int, request: Request):
    try:
        settings = get_settings()
        game = await romm.fetch_rom(settings, rom_id)
        detected = discovery.discover_docker(
            settings,
            browser_host=request.url.hostname,
            scheme=settings.emulator_browser_scheme,
        )
        return route_for_game(game, detected)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
      .game-list { display:grid; gap:10px; margin-top:12px; }
      .game { display:flex; justify-content:space-between; gap:12px; align-items:center; background:#0f172a; border:1px solid #334155; border-radius:10px; padding:10px 12px; }
      .game small { color:#94a3b8; display:block; }
      label { display:block; color:#cbd5e1; font-size:13px; margin:10px 0 4px; }
      input { width:100%; box-sizing:border-box; padding:10px 12px; border-radius:8px; border:1px solid #334155; background:#020617; color:#e5e7eb; }
      .hint { color:#94a3b8; font-size:13px; }
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
          <h2>RomM login</h2>
          <p class="hint">Forgot to set RomM auth in Docker? Save it here. Values are stored in /config/settings.json and secrets are never displayed.</p>
          <form id="runtime-config-form" onsubmit="saveRuntimeConfig(event)">
            <label for="romm-url">RomM URL</label>
            <input id="romm-url" name="romm_url" placeholder="http://romm:8080" />
            <label for="romm-username">RomM username</label>
            <input id="romm-username" name="romm_username" autocomplete="username" />
            <label for="romm-password">RomM password</label>
            <input id="romm-password" name="romm_password" type="password" autocomplete="current-password" placeholder="Leave blank to keep existing password" />
            <label for="romm-api-key">RomM API key / bearer token</label>
            <input id="romm-api-key" name="romm_api_key" type="password" placeholder="Leave blank to use username/password" />
            <button type="submit">Save RomM settings</button>
            <span id="runtime-config-status" class="hint"></span>
          </form>
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
        <section class="card">
          <h2>Games</h2>
          <div id="games">Loading...</div>
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
      async function loadRuntimeConfig() {
        const res = await fetch('/api/runtime-config');
        const data = await res.json();
        if (!res.ok) return;
        document.getElementById('romm-url').value = data.romm_url || 'http://romm:8080';
        document.getElementById('romm-username').value = data.romm_username || '';
        document.getElementById('runtime-config-status').textContent = [
          data.romm_api_key_configured ? 'API key saved' : '',
          data.romm_password_configured ? 'password saved' : ''
        ].filter(Boolean).join(' · ');
      }
      async function saveRuntimeConfig(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = {
          romm_url: form.romm_url.value || 'http://romm:8080',
          romm_username: form.romm_username.value || '',
          romm_api_key: form.romm_api_key.value || '',
        };
        if (form.romm_password.value) payload.romm_password = form.romm_password.value;
        const status = document.getElementById('runtime-config-status');
        status.textContent = 'Saving...';
        const res = await fetch('/api/runtime-config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
          status.textContent = `Save failed: ${JSON.stringify(data)}`;
          status.className = 'warn';
          return;
        }
        form.romm_password.value = '';
        form.romm_api_key.value = '';
        status.textContent = 'Saved. Refreshing...';
        status.className = 'ok';
        refreshAll();
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
      function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
      }
      async function launchGame(id) {
        const res = await fetch(`/api/launch/${id}`, { method: 'POST' });
        const route = await res.json();
        if (route.launch_url) {
          window.open(route.launch_url, '_blank', 'noopener');
        }
        alert(route.message || JSON.stringify(route));
      }
      async function loadGames() {
        const el = document.getElementById('games');
        try {
          const res = await fetch('/api/romm/games');
          const data = await res.json();
          const games = data.games || [];
          if (!res.ok) throw new Error(JSON.stringify(data));
          if (!games.length) {
            el.innerHTML = '<p>No RomM games returned yet.</p>';
            return;
          }
          el.innerHTML = `<div class="game-list">${games.map((game) => `
            <div class="game">
              <div><strong>${escapeHtml(game.name)}</strong><small>${escapeHtml(game.platform || 'Unknown platform')} ${game.emulator_key ? '→ ' + escapeHtml(game.emulator_key) : ''}</small></div>
              ${game.supported ? `<button onclick="launchGame(${Number(game.id)})">Open emulator</button>` : '<span class="warn">Unsupported</span>'}
            </div>
          `).join('')}</div>`;
        } catch (err) {
          el.innerHTML = `<p class="warn">${escapeHtml(err.message || err)}</p>`;
        }
      }
      function refreshAll() {
        loadJson('/api/health', 'health');
        loadJson('/api/config', 'config');
        loadRuntimeConfig();
        loadDiscovery();
        loadJson('/api/romm/status', 'romm');
        loadGames();
      }
      refreshAll();
    </script>
  </body>
</html>
"""
