# Thin-compat shim for legacy imports.
# Allows any remaining `from anchor_core_engine_v6 import AnchorSession`
# statements to succeed without further edits.

from anchor_core_engine import AnchorSession  # re-export
