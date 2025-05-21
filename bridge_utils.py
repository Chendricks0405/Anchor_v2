# bridge_utils.py  – lightweight compatibility shims
# ---------------------------------------------------
# Provides:
#   • load_memory(json_path)               – read memory JSON
#   • initialize_anchor1_memory(session, memory_data)
#   • bridge_input(...) & get_anchor_state(...) stubs
#
# These keep api_interface.py imports happy until you wire
# real perception + language generation.

import json, os
from typing import Any, Dict
from anchor_core_engine import AnchorSession


# ---------------- Memory helpers (compat) -------------------
def load_memory(json_path: str):
    """Load a JSON memory file and return its parsed content."""
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def initialize_anchor1_memory(session: AnchorSession, memory_data):
    """Attach memory nodes to the session in-place."""
    if not hasattr(session, "memory_orbit"):
        session.memory_orbit = []
    existing_ids = {n.get("id") for n in session.memory_orbit if isinstance(n, dict)}
    for node in memory_data:
        if isinstance(node, dict) and node.get("id") not in existing_ids:
            session.memory_orbit.append(node)


# ---------------- Stubbed bridge I/O ------------------------
def bridge_input(session: AnchorSession, input_data: str) -> Dict[str, Any]:
    """Placeholder; replace with real perception-LLM bridge."""
    return {"reply": "stub", "tick": session.ticks}


def get_anchor_state(session: AnchorSession) -> Dict[str, Any]:
    """Return diagnostic view if available, else persistence snapshot."""
    if hasattr(session, "export_view"):
        return session.export_view()
    return session.export_state()