
"""Anchor1 API – Render‑ready entry point (with /get_full_state)
---------------------------------------------------------------
• POST‑only ingress for user input (/send_input, /run_tick)
• NEW: GET /get_full_state  → returns full Anchor snapshot
• Redis persistence so sessions survive container restarts
"""

import os, json
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import redis.asyncio as redis

from anchor_core_engine import AnchorSession
from api_interface import AnchorAPI
from seed import apply_seed
from seed_registry import resolve_seed
from bridge_utils import get_anchor_state

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

app = FastAPI(title="Anchor1 API (Render)", version="1.1")

# ---------- Session helpers ---------- #
async def _get_session(sid: str = "default") -> AnchorSession:
    """Load session from Redis or bootstrap from seed registry."""
    key = f"anchor:{sid}"
    cached = await redis_client.get(key)
    if cached:
        sess = AnchorSession()
        sess.import_state(json.loads(cached))
    else:
        sess = AnchorSession()
        seed_id = resolve_seed(sid) or sid
        apply_seed(sess, seed_id, seeds_dir="seeds")
    return sess

async def _save_session(sid: str, session: AnchorSession):
    """Persist session to Redis (24 h TTL)."""
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
    if data.get("show_full_state"):
        result["full_state"] = get_anchor_state(session)
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

@app.get("/get_full_state")
async def get_full_state(session_id: str = "default"):
    """Return the complete Anchor snapshot for the given session_id."""
    session = await _get_session(session_id)
    return get_anchor_state(session)
