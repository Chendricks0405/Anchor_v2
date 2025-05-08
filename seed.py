import json
import os

def apply_seed(session, seed_id='default', seeds_dir='seeds', drift_lexicons_dir='drift_lexicons'):
    """
    Load and apply a personality seed to the given session.
    Conditionally loads the drift lexicon specified in seed metadata.
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

    # Conditional drift lexicon loading
    drift_lexicon_name = seed.get("consequence_drift_lexicon", "nrc_consequence_drift.json")
    drift_lexicon_path = os.path.join(drift_lexicons_dir, drift_lexicon_name)
    if os.path.exists(drift_lexicon_path):
        with open(drift_lexicon_path, 'r') as lexicon_file:
            session.consequence_drift_map = json.load(lexicon_file)
            if hasattr(session, "behavior_log"):
                session.behavior_log.append(f"Loaded drift lexicon: {drift_lexicon_name}")
    else:
        session.consequence_drift_map = {}
        if hasattr(session, "behavior_log"):
            session.behavior_log.append(f"Drift lexicon {drift_lexicon_name} not found. Loaded empty map.")

    return True