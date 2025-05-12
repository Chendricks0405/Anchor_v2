"""
Anchor1 API – Render‑ready entry point
• POST‑only ingress (stable through proxies)
• Redis persistence so sessions survive container restarts
No existing project files are touched; use this as a drop‑in replacement
for main.py when deploying to Render.
"""
import os, json
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import redis.asyncio as redis

from anchor_core_engine import AnchorSession
from api_interface import AnchorAPI
from seed import apply_seed

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

app = FastAPI(title="Anchor1 API (Render)", version="1.0")

# ---------- Session helpers ---------- #
async def _get_session(sid: str = "default") -> AnchorSession:
    key = f"anchor:{sid}"
    cached = await redis_client.get(key)
    if cached:
        sess = AnchorSession()
        sess.import_state(json.loads(cached))
    else:
        sess = AnchorSession()
        apply_seed(sess, sid)
    return sess

async def _save_session(sid: str, session: AnchorSession):
    # Persist for 24 h (adjust as needed)
    await redis_client.set(
        f"anchor:{sid}",
        json.dumps(session.export_state()),
        ex=60 * 60 * 24,
    )

# ---------- Routes ---------- #
@app.get("/")
async def health():
    return {"status": "Anchor1 API running on Render"}

@app.post("/send_input")
async def send_input(request: Request):
    data = await request.json()
    sid = data.get("session_id", "default")
    session = await _get_session(sid)
    result = AnchorAPI(session).send_input(data.get("input", ""))
    await _save_session(sid, session)
    return result

@app.post("/run_tick")
async def run_tick(request: Request):
    data = await request.json()
    sid = data.get("session_id", "default")
    session = await _get_session(sid)
    result = AnchorAPI(session).run_tick(data.get("anchor_updates", {}))
    await _save_session(sid, session)
    return result

# ---------- Local dev ---------- #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_render:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
