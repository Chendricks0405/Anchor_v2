"""
bridge_utils.py – patched 2025-05-25
------------------------------------------------
• Hides anchor jargon in normal replies
• Exposes full diagnostics only on:
    – chaos state
    – 'diagnose' / 'reveal state' keyword
    – show_full_state flag handled in main.py
• Keeps existing helper functions intact
"""

import re
import json
import uuid
import os                       # ← added for resolve_memory_node
from typing import Dict, Any
from anchor_core_engine import AnchorSession

# ---------- Memory helpers (unchanged) -------------------
def load_memory(json_path: str):
    """Load a JSON memory file and return its parsed content."""
    import os, json
    if not os.path.exists(json_path):
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def initialize_anchor1_memory(session: AnchorSession, memory_data):
    """Attach memory nodes to the session in-place."""
    if not hasattr(session, "memory_orbit"):
        session.memory_orbit = []
    existing_ids = {n.get("id") for n in session.memory_orbit if isinstance(n, dict)}
    for node in memory_data:
        if isinstance(node, dict) and node.get("id") not in existing_ids:
            session.memory_orbit.append(node)

# ---------- Lazy node-loader (NEW) ------------------------------------
#
# Usage:
#     node = resolve_memory_node(session, "CA001")
#     linked = [resolve_memory_node(session, nid) for nid in node.get("linked_nodes",[])]
#
import os

def resolve_memory_node(session: AnchorSession, node_id: str):
    """
    Lazy-load a single memory node by ID.
    Cluster file = '<prefix>_cluster.json' where prefix = first 2 chars of node_id.
    Caches anything already fetched in session.memory_cache (dict[str, dict]).
    """
    # 0. Prep cache
    if not hasattr(session, "memory_cache"):
        session.memory_cache = {}

    if node_id in session.memory_cache:           # fast path
        return session.memory_cache[node_id]

    # 1. Derive cluster filename (CA → CA_cluster.json, GM → GM_cluster.json, …)
    cluster_file = f"{node_id[:2]}_cluster.json"
    cluster_path = os.path.join("memory", cluster_file)

    # 2. Load & search cluster
    if os.path.exists(cluster_path):
        for node in load_memory(cluster_path):
            if node.get("id") == node_id:
                session.memory_cache[node_id] = node        # cache hit
                return node

    # 3. Fallback – not found
    return None

# ---------- State serialisation -------------------------------------------
def get_anchor_state(session: AnchorSession) -> Dict[str, Any]:
    """Return a full diagnostic snapshot of the session."""
    state = session.export_view()          # human-readable vector
    state.update({
        "id": str(uuid.uuid4()),
        "tick": session.ticks,
        "last_behavior": session.behavior_log[-1] if session.behavior_log else None,
        "memory_nodes": session.memory_orbit,
    })
    return state

# ---------- NL-generation stub (replace with real LLM later) --------------
def _generate_reply(session: AnchorSession, user_text: str) -> str:
    if "hello" in user_text.lower():
        return "Hello. How can I help you explore this further?"
    return "Let's explore that together."

# ---------- Bridge I/O -----------------------------------------------------
def conditional_anchor_response(session: AnchorSession, input_text: str) -> Dict[str, Any]:
    """Return either a natural reply or full diagnostics based on context."""
    diagnostics = (
        session.is_in_chaos() or
        any(kw in input_text.lower() for kw in ("diagnose", "reveal state"))
    )

    if diagnostics:
        return get_anchor_state(session)

    return {
        "reply": _generate_reply(session, input_text),
        "tick":  session.ticks,
        "status": "chaos" if session.is_in_chaos() else "stable"
    }

# ---------- Compatibility wrapper -----------------------------------------
def bridge_input(session: AnchorSession, input_data: str) -> Dict[str, Any]:
    """Entry-point used by api_interface: routes through conditional logic."""
    return conditional_anchor_response(session, input_data)