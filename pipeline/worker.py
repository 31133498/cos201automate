# ============================================================
# pipeline/worker.py
# ============================================================

import threading
import time
import traceback
from datetime import datetime


def start_worker(app):
    t1 = threading.Thread(target=_job_worker_loop,   args=(app,), daemon=True, name="job-worker")
    t2 = threading.Thread(target=_modal_poller_loop, args=(app,), daemon=True, name="modal-poller")
    t1.start()
    t2.start()
    print("✅ job-worker + modal-poller started.", flush=True)


# ── Thread 1: Job Worker ──────────────────────────────────────

def _job_worker_loop(app):
    while True:
        try:
            _process_pending_job(app)
        except Exception as e:
            print(f"❌ [job-worker] loop-level exception: {e}", flush=True)
            traceback.print_exc()
        time.sleep(2)


def _process_pending_job(app):
    from pipeline.job_manager import Job
    from pipeline.token_manager import db
    from pipeline import run_pipeline_phase1

    with app.app_context():
        try:
            # Simple ORM claim — works on both PostgreSQL and SQLite.
            # We rely on the 2-second poll interval being slow enough
            # that double-pickup is unlikely in production.
            # On PostgreSQL with a single worker thread this is safe.
            job = (
                Job.query
                .filter_by(status="pending")
                .order_by(Job.created_at)
                .first()
            )

            if not job:
                return

            # Mark as processing immediately so the next poll won't pick it up
            job_id       = job.id
            student_name = job.student_name
            token        = job.token
            matric_no    = job.matric_no
            student_email = job.student_email

            job.status       = "processing"
            job.current_step = -1
            db.session.commit()
            print(f"\n▶ [job-worker] {job_id[:8]} — {student_name}", flush=True)

        except Exception as e:
            print(f"❌ [job-worker] DB claim error: {e}", flush=True)
            traceback.print_exc()
            try: db.session.rollback()
            except: pass
            return

        # ── progress_cb: default arg captures job_id at definition time ──
        def progress_cb(n, _jid=job_id):
            with app.app_context():
                j = db.session.get(Job, _jid)
                if j:
                    j.current_step = n
                    db.session.commit()
            print(f"  [step {n}]", flush=True)

        try:
            result = run_pipeline_phase1(
                token         = token,
                matric_no     = matric_no,
                student_name  = student_name,
                student_email = student_email,
                progress_cb   = progress_cb,
            )
        except Exception as e:
            print(f"❌ [job-worker] phase1 exception: {e}", flush=True)
            traceback.print_exc()
            result = {"success": False, "message": str(e)}

        with app.app_context():
            j = db.session.get(Job, job_id)
            if not j:
                return

            if result.get("success"):
                j.status        = "modal_pending"
                j.current_step  = 3
                j.modal_call_id = result["call_id"]
                j.pipeline_data = result["pipeline_data"]
                print(f"✅ [job-worker] {job_id[:8]} → modal_pending", flush=True)
            else:
                j.status       = "failed"
                j.message      = result.get("message", "Phase 1 failed")
                j.completed_at = datetime.utcnow()
                print(f"❌ [job-worker] {job_id[:8]} failed: {j.message}", flush=True)

            db.session.commit()


# ── Thread 2: Modal Poller ────────────────────────────────────

def _modal_poller_loop(app):
    time.sleep(8)
    while True:
        try:
            _poll_modal_jobs(app)
        except Exception as e:
            print(f"❌ [modal-poller] loop-level exception: {e}", flush=True)
            traceback.print_exc()
        time.sleep(10)


def _poll_modal_jobs(app):
    from pipeline.job_manager import Job
    from pipeline.token_manager import db
    from pipeline import run_pipeline_phase2

    with app.app_context():
        try:
            jobs = Job.query.filter_by(status="modal_pending").all()
        except Exception as e:
            print(f"❌ [modal-poller] DB query error: {e}", flush=True)
            traceback.print_exc()
            try: db.session.rollback()
            except: pass
            return

        if not jobs:
            return

        print(f"[modal-poller] {len(jobs)} modal_pending job(s).", flush=True)

        for job in jobs:
            job_id        = job.id
            modal_call_id = job.modal_call_id
            pipeline_data = job.pipeline_data

            print(f"  checking {job_id[:8]}...", flush=True)

            def progress_cb(n, _jid=job_id):
                with app.app_context():
                    j = db.session.get(Job, _jid)
                    if j:
                        j.current_step = n
                        db.session.commit()
                print(f"  [step {n}]", flush=True)

            try:
                result = run_pipeline_phase2(
                    call_id       = modal_call_id,
                    pipeline_data = pipeline_data,
                    progress_cb   = progress_cb,
                )
            except Exception as e:
                print(f"❌ [modal-poller] phase2 exception on {job_id[:8]}: {e}", flush=True)
                traceback.print_exc()
                result = {"success": False, "message": str(e)}

            with app.app_context():
                j = db.session.get(Job, job_id)
                if not j:
                    continue

                if result == "pending":
                    print(f"  {job_id[:8]} still running on Modal.", flush=True)
                    continue

                if result.get("success"):
                    j.status       = "completed"
                    j.current_step = 6
                    j.zip_url      = result.get("zip_url")
                    j.message      = result.get("message")
                    print(f"✅ [modal-poller] {job_id[:8]} COMPLETED.", flush=True)
                else:
                    j.status  = "failed"
                    j.message = result.get("message", "Phase 2 failed")
                    print(f"❌ [modal-poller] {job_id[:8]} FAILED: {j.message}", flush=True)

                j.completed_at = datetime.utcnow()
                db.session.commit()
