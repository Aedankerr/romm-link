from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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
    return {"status": "ok", "service": "romm-link"}


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
  <head>
    <title>romm-link</title>
    <style>
      body { font-family: system-ui, sans-serif; background:#111827; color:#e5e7eb; margin:40px; }
      button { padding:10px 14px; margin:6px; border:0; border-radius:8px; cursor:pointer; }
      .card { background:#1f2937; padding:20px; border-radius:14px; max-width:800px; }
      pre { background:#030712; padding:14px; border-radius:10px; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>romm-link MVP</h1>
      <p>Browser launcher shell for RomM-linked emulator containers.</p>
      <button onclick="health()">Test API</button>
      <pre id="output"></pre>
    </div>
    <script>
      async function health() {
        const res = await fetch('/api/health');
        const data = await res.json();
        document.getElementById('output').textContent = JSON.stringify(data, null, 2);
      }
    </script>
  </body>
</html>
"""
