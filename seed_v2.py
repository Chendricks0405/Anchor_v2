import json
import os

def apply_seed(session, seed_id='default', seeds_dir='seeds'):
    """
    Load and apply a personality seed to the given session.
    Returns True if loaded, False if no seed found.
    """
    seed_path = os.path.join(seeds_dir, f"{seed_id}.json")
    if not os.path.exists(seed_path):
        return False

    with open(seed_path, 'r') as f:
        seed = json.load(f)

    vec = seed.get("last_known_vector", {})
    # Accept dual labels or core keys
    if "Instability" in vec or "Stability" in vec:
        inst = vec.get("Instability", session.core.get("Fear"))
        stab = vec.get("Stability", session.core.get("Safety"))
        session.core["Fear"], session.core["Safety"] = inst, stab
    else:
        for k in ("Fear", "Safety", "Time", "Choice"):
            if k in vec:
                session.core[k] = vec[k]

    # Apply extended metadata fields
    for field in ("persona_style", "anchor_weights", "feature_flags"):
        if field in seed:
            setattr(session, field, seed[field])

    # Replay legacy collapse events
    for ev in seed.get("collapse_events", []):
        tick = ev.get("tick")
        tag = ev.get("trigger")
        if hasattr(session, "behavior_log"):
            session.behavior_log.append(f"[Seed Event @ {tick}] {tag}")

    return True
