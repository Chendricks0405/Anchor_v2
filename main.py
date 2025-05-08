# Updated main.py with System Call Structure for Different Models

from fastapi import FastAPI, Request
from anchor_core_engine import AnchorSession
from api_interface import AnchorAPI
from seed_loader import SeedLoader
from dotenv import load_dotenv
import os, uvicorn

load_dotenv()

app = FastAPI(title="Anchor Kernel Multi-Model API", version="1.2")

SESSIONS = {}
SEED_LOADER = SeedLoader()

def get_session(sid: str = "default"):
    if sid not in SESSIONS:
        sess = AnchorSession()
        SEED_LOADER.apply_seed(sess, sid)
        SESSIONS[sid] = sess
    return SESSIONS[sid]

@app.get("/")
async def health():
    return {"status": "Anchor Kernel API is running"}

@app.get("/get_full_state")
async def get_full_state(session_id: str = "default"):
    session = get_session(session_id)
    return AnchorAPI(session).get_full_state()

@app.post("/send_input")
async def send_input_post(request: Request):
    data = await request.json()
    sid = data.get("session_id", "default")
    session = get_session(sid)
    return AnchorAPI(session).send_input(data.get("input", ""))

@app.post("/run_tick")
async def run_tick(request: Request):
    data = await request.json()
    sid = data.get("session_id", "default")
    session = get_session(sid)
    return AnchorAPI(session).run_tick(data.get("anchor_updates", {}))

@app.post("/switch_seed")
async def switch_seed(request: Request):
    data = await request.json()
    sid = data.get("session_id", "default")
    new_seed_id = data.get("seed_id")
    session = get_session(sid)
    success = SEED_LOADER.apply_seed(session, new_seed_id)
    return {"status": "success" if success else "failure", "new_seed_applied": new_seed_id}

@app.post("/save_seed_state")
async def save_seed_state(request: Request):
    data = await request.json()
    sid = data.get("session_id", "default")
    session_summary = data.get("session_summary", "No summary provided.")
    session = get_session(sid)

    updated_seed = {
        "seed_id": sid,
        "persona_style": getattr(session, "persona_style", "default"),
        "consequence_drift_path": session.seed.get("consequence_drift_path", "default.json"),
        "anchor_weights": getattr(session, "anchor_weights", {}),
        "last_known_vector": session.core,
        "feature_flags": getattr(session, "feature_flags", {}),
        "collapse_events": [{"tick": session.current_tick, "trigger": "Session saved"}],
        "previous_session_summary": session_summary
    }

    seed_file_path = os.path.join(SEED_LOADER.seeds_dir, f"{sid}_updated.json")
    with open(seed_file_path, 'w') as file:
        json.dump(updated_seed, file, indent=2)

    return {"status": "success", "saved_seed": seed_file_path}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)