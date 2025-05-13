"""
bridge_utils.py

Bridge utilities for AnchorSession:
- load_memory, initialize_anchor1_memory
- parse_input, apply_anchor_deltas, trigger_memory
- get_anchor_state, bridge_input
"""
import json
import uuid
import re

def load_memory(file_path: str):
    """Load memory data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def initialize_anchor1_memory(session, memory_data):
    """Initialize session memory orbit from data."""
    session.memory_orbit = memory_data

def parse_input(input_data: str) -> dict:
    response = {
        "anchor_deltas": {"Fear": 0.0, "Safety": 0.0, "Time": 0.0, "Choice": 0.0},
        "memory_trigger": None,
        "log": [],
        "ripple_tags": {}
    }
    lower = input_data.lower()
    # Instability/Stability quick cues
    for match in re.findall(r"instability *([+\-]\d*\.?\d+)", lower):
        delta = float(match)
        response["anchor_deltas"]["Fear"] += delta
        response["log"].append(f"Instability cue: Fear {delta:+}")
    for match in re.findall(r"stability *([+\-]\d*\.?\d+)", lower):
        delta = float(match)
        response["anchor_deltas"]["Safety"] += delta
        response["log"].append(f"Stability cue: Safety {delta:+}")
    # Simple triggers
    if "loud noise" in lower:
        response["anchor_deltas"]["Fear"] += 0.2
        response["anchor_deltas"]["Safety"] -= 0.1
        response["log"].append("External event: Loud noise")
        response["ripple_tags"]["loud_noise"] = 0.2
    elif "encouragement" in lower:
        response["anchor_deltas"]["Safety"] += 0.2
        response["anchor_deltas"]["Fear"] -= 0.1
        response["log"].append("Social ripple: Encouragement")
        response["ripple_tags"]["encouragement"] = 0.2
    elif "the cave" in lower:
        response["memory_trigger"] = "The Cave"
        response["log"].append("Memory trigger: The Cave")
        response["ripple_tags"]["memory_cave"] = 0.3
    return response

def apply_anchor_deltas(core: dict, deltas: dict, ripple_tags: dict, session):
    # Pre-weight deltas by ripple severity
    for tag, mag in ripple_tags.items():
        session.ripple_tags[tag] = mag
        for k in deltas:
            deltas[k] *= (1 + mag)
    # Apply clamped adjustments
    for k, v in deltas.items():
        if k in core:
            core[k] = max(0.0, min(1.0, core[k] + v))

def trigger_memory(memory_orbit: list, memory_id: str) -> list:
    triggered = []
    for mem in memory_orbit:
        if mem.get("id") == memory_id:
            mem["orbit"] = max(mem.get("orbit", 0.0) - 0.3, 0.0)
            mem["tier"] = "active"
            triggered.append(mem)
    return triggered

def get_anchor_state(session) -> dict:
    state = session.export_state()
    state.update({
        "id": str(uuid.uuid4()),
        "tick": session.ticks,
        "last_behavior": session.behavior_log[-1] if session.behavior_log else None, "memroy_nodes": session.memory_orbit #alias for CustomGPT
    })
    return state

def bridge_input(session, input_data: str) -> dict:
    parsed = parse_input(input_data)
    # Identity calibration
    if parsed["memory_trigger"]:
        session.memory_driven += 1
    else:
        session.environment_driven += 1
    # Apply deltas
    apply_anchor_deltas(session.core, parsed["anchor_deltas"], parsed["ripple_tags"], session)
    # Memory trigger
    triggered = []
    if parsed["memory_trigger"]:
        triggered = trigger_memory(session.memory_orbit, parsed["memory_trigger"])
    # Advance session
    session.tick(parsed["anchor_deltas"])
    # Log entry
    entry = f"[Bridge] Input: {input_data} -> {'; '.join(parsed['log'])}"
    if triggered:
        entry += f" | Memory: {', '.join([m['id'] for m in triggered])}"
    session.behavior_log.append(entry)
    return conditional_anchor_response(session, input_data)

def conditional_anchor_response(session, input_text: str) -> dict:
    """Return perceptual summary unless chaos or diagnostic trigger is found."""
    if session.is_in_chaos() or "diagnose" in input_text.lower() or "reveal state" in input_text.lower():
        return conditional_anchor_response(session, input_data)
    return {
        "status": "stable",
        "tick": session.ticks,
        "last_behavior": session.behavior_log[-1] if session.behavior_log else None
    }