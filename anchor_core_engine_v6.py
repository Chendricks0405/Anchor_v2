"""
anchor_core_engine_v6.py
------------------------
Legacy shim so that old imports like

    from anchor_core_engine_v6 import AnchorSession

continue to work now that the engine lives in `anchor_core_engine.py`.
"""
from anchor_core_engine import AnchorSession  # re-export
