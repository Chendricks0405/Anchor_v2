
"""bridge_utils.py – patched 2025‑05‑23
------------------------------------------------
• Hides anchor jargon in normal replies
• Exposes full diagnostics only on:
    – chaos state
    – 'diagnose' / 'reveal state' keyword
    – show_full_state flag handled in main.py
• Keeps existing helper functions intact
"""

import re, json, uuid
from typing import Dict, Any

# ---------- existing helper imports ----------
from anchor_core_engine import AnchorSession

# ---------- State Serialization -------------------------------------------------
def get_anchor_state(session: AnchorSession) -> Dict[str, Any]:
    """Return full diagnostic snapshot of the session."""
    state = session.export_view()
    state.update({
        "id": str(uuid.uuid4()),
        "tick": session.ticks,
        "last_behavior": session.behavior_log[-1] if session.behavior_log else None,
        "memory_nodes": session.memory_orbit,
    })
    return state

# ---------- Natural‑language generation stub ------------------------------------
def _generate_reply(session: AnchorSession, user_text: str) -> str:
    """Generate a plain‑language reply without exposing anchor jargon.
    This is a stub; replace with your LLM call if desired."""
    # Simple echo for placeholder
    if "hello" in user_text.lower():
        return "Hello. How can I help you explore this further?"
    return "Let's explore that together."

# ---------- Bridge I/O ----------------------------------------------------------
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
        "tick": session.ticks,
        "status": "stable" if not session.is_in_chaos() else "chaos"
    }

# For compatibility with existing code
def bridge_input(session: AnchorSession, input_data: str) -> Dict[str, Any]:
    # apply perception logic elsewhere, then:
    return conditional_anchor_response(session, input_data)
