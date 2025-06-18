# plugins/cyber/plugin.py
# --------------------------------------------------------------------
# Cyber Plug-in for Anchor Engine
# Adds adaptive playbook handling + soft 30-min learning timer
# --------------------------------------------------------------------

class MiniScheduler:
    """Lightweight tick-based scheduler (plug-in local)."""
    def __init__(self):
        self.jobs = {}

    def every(self, ticks, fn, job_id):
        self.jobs[job_id] = {"type": "repeat", "int": ticks, "next": ticks, "fn": fn}

    def delay(self, ticks, fn, job_id):
        self.jobs[job_id] = {"type": "once", "next": ticks, "fn": fn}

    def cancel(self, job_id):
        self.jobs.pop(job_id, None)

    def tick(self):
        for jid, job in list(self.jobs.items()):
            job["next"] -= 1
            if job["next"] <= 0:
                job["fn"]()
                if job["type"] == "once":
                    self.jobs.pop(jid, None)
                else:
                    job["next"] = job["int"]

# --------------------------------------------------------------------
class Plugin:
    """Cyber-specific hooks wired into AnchorSession."""

    def on_session_start(self, session):
        # attach scheduler to session if not present
        if not hasattr(session, "cx_sched"):
            session.cx_sched = MiniScheduler()

    def on_tick(self, session):
        if hasattr(session, "cx_sched"):
            session.cx_sched.tick()

    # ------------------------------------------------------------
    def on_playbook_applied(self, session, playbook):
        """Adaptive thresholds + 30-min soft-learn after rollback."""
        thresh = playbook.get("adaptive_threshold")
        if not thresh:
            return

        target = float(thresh.get("instability_max", 1.0))
        learn  = bool(thresh.get("whitelist_learn", False))
        job_id = f"{session.id}-pb-{playbook['id']}"

        # Repeat check every 5 ticks
        def _rollback():
            if session.compute_instability() < target:
                for step in playbook["steps"]:
                    session.deactivate_control(step)
                session.behavior_log.append(f"[Rollback] {playbook['id']}")
                session.cx_sched.cancel(job_id)

                # Schedule soft-learn 30 ticks (~30 min) later
                def _soft_learn():
                    if learn and session.last_src_ip:
                        session.dynamic_whitelist[session.last_src_ip] = session.ticks + 288
                        session.behavior_log.append(f"[Soft-learn] {session.last_src_ip} whitelisted 24h")
                    session.cx_sched.cancel(job_id + \"-soft\")
                session.cx_sched.delay(30, _soft_learn, job_id + \"-soft\")

        session.cx_sched.every(5, _rollback, job_id)
