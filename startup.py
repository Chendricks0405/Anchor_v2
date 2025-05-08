from anchor_core_engine_v6 import AnchorSession
from seed import apply_seed

def initialize_anchor():
    session = AnchorSession()
    seed_id = "Anchor1_Explorer_Seed_v1"
    loaded = apply_seed(session, seed_id=seed_id, seeds_dir="seeds")
    if loaded:
        session.behavior_log.append(f"[Startup] Seed '{seed_id}' applied.")
    else:
        session.behavior_log.append(f"[Startup] Seed '{seed_id}' not found.")
    return session