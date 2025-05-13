
"""
bridge_utils.py  — patched 2025‑05‑13
------------------------------------------------
• Fix infinite recursion in `conditional_anchor_response`
• Return full state via `get_anchor_state` on chaos / diagnostic
• Correct key name `memory_nodes`
• Minor typing & docstrings
"""

import json, uuid, re
from typing import Dict, Any, List

# ---------- Memory helpers -------------------------------------------------
def load_memory(file_path: str) -> List[dict]:
    """Load memory nodes from *file_path*."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def initialize_anchor1_memory(session, memory_data: List[dict]) -> None:
    """Replace *session.memory_orbit* with *memory_data*."""
    session.memory_orbit = memory_data

# ---------- Input parsing ---------------------------------------------------
def parse_input(input_data: str) -> Dict[str, Any]:
    """Extract anchor deltas, memory triggers, and ripple tags from *input_data*."""
    result = {
        "anchor_deltas": {k: 0.0 for k in ("Fear", "Safety", "Time", "Choice")},
        "memory_trigger": None,
        "log": [],
        "ripple_tags": {},
    }
    text = input_data.lower()

    # Explicit anchor nudges e.g. "instability +0.2"
    for match in re.findall(r"instability *([+\-]\d*\.?\d+)", text):
        delta = float(match)
        result["anchor_deltas"]["Fear"] += delta
        result["log"].append(f"Instability cue: Fear {delta:+}")

    for match in re.findall(r"stability *([+\-]\d*\.?\d+)", text):
        delta = float(match)
        result["anchor_deltas"]["Safety"] += delta
        result["log"].append(f"Stability cue: Safety {delta:+}")

    # Simple semantic triggers
    if "loud noise" in text:
        result["anchor_deltas"]["Fear"] += 0.2
        result["anchor_deltas"]["Safety"] -= 0.1
        result["log"].append("External event: Loud noise")
        result["ripple_tags"]["loud_noise"] = 0.2
    elif "encouragement" in text:
        result["anchor_deltas"]["Safety"] += 0.2
        result["anchor_deltas"]["Fear"] -= 0.1
        result["log"].append("Social ripple: Encouragement")
        result["ripple_tags"]["encouragement"] = 0.2
    elif "the cave" in text:
        result["memory_trigger"] = "The Cave"
        result["log"].append("Memory trigger: The Cave")
        result["ripple_tags"]["memory_cave"] = 0.3

    return result

# ---------- Anchor helpers --------------------------------------------------
def apply_anchor_deltas(core: dict, deltas: dict, ripple_tags: dict, session):
    """Apply *deltas* to *core*, modulated by *ripple_tags*."""
    for tag, mag in ripple_tags.items():
        session.ripple_tags[tag] = mag
        for k in deltas:
            deltas[k] *= (1 + mag)

    for k, v in deltas.items():
        if k in core:
            core[k] = max(0.0, min(1.0, core[k] + v))

def trigger_memory(memory_orbit: list, memory_id: str) -> list:
    """Promote matching *memory_id* nodes to tier='active'."""
    triggered = []
    for mem in memory_orbit:
        if mem.get("id") == memory_id:
            mem["orbit"] = max(mem.get("orbit", 0.0) - 0.3, 0.0)
            mem["tier"] = "active"
            triggered.append(mem)
    return triggered

# ---------- State serialization ---------------------------------------------
def get_anchor_state(session) -> Dict[str, Any]:
    """Return full session snapshot suitable for external diagnostics."""
    state = session.export_state()
    state.update({
        "id": str(uuid.uuid4()),
        "tick": session.ticks,
        "last_behavior": session.behavior_log[-1] if session.behavior_log else None,
        "memory_nodes": session.memory_orbit,  # corrected key
    })
    return state

# ---------- Bridge I/O ------------------------------------------------------
def bridge_input(session, input_data: str) -> Dict[str, Any]:
    parsed = parse_input(input_data)

    # Identity calibration bookkeeping
    if parsed["memory_trigger"]:
        session.memory_driven += 1
    else:
        session.environment_driven += 1

    # Apply perception deltas
    apply_anchor_deltas(session.core, parsed["anchor_deltas"], parsed["ripple_tags"], session)

    # Memory trigger
    if parsed["memory_trigger"]:
        trigger_memory(session.memory_orbit, parsed["memory_trigger"])

    # Advance simulation
    session.tick(parsed["anchor_deltas"])

    # Behaviour log
    entry = f"[Bridge] Input: {input_data} -> {'; '.join(parsed['log']) or 'no cues'}"
    session.behavior_log.append(entry)

    return conditional_anchor_response(session, input_data)

def conditional_anchor_response(session, input_text: str) -> Dict[str, Any]:
    """Return either minimal or full state depending on chaos/diagnostics."""
    diagnostics = ("diagnose" in input_text.lower() or
                   "reveal state" in input_text.lower() or
                   session.is_in_chaos())

    if diagnostics:
        return get_anchor_state(session)

    return {
        "status": "stable",
        "tick": session.ticks,
        "last_behavior": session.behavior_log[-1] if session.behavior_log else None,
    }
