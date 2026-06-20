from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.app.api.routes import router

app = FastAPI(title="romm-link", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!doctype html>
<html>
  <head>
    <title>romm-link</title>
    <style>
      body { font-family: system-ui, sans-serif; background:#111827; color:#e5e7eb; margin:40px; }
      button { padding:10px 14px; margin:6px; border:0; border-radius:8px; cursor:pointer; }
      .card { background:#1f2937; padding:20px; border-radius:14px; max-width:800px; }
      code { background:#374151; padding:3px 6px; border-radius:5px; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>romm-link MVP</h1>
      <p>Launch browser-accessible emulator containers from one interface.</p>
      <button onclick="launch('ps2')">Launch PCSX2</button>
      <button onclick="launch('ps3')">Launch RPCS3</button>
      <button onclick="launch('wii')">Launch Dolphin</button>
      <pre id="output"></pre>
    </div>
    <script>
      async function launch(platform) {
        const res = await fetch('/api/launch', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({platform})
        });
        const data = await res.json();
        document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        if (data.web_url) window.open(data.web_url, '_blank');
      }
    </script>
  </body>
</html>
"""
