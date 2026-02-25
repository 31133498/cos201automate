# ============================================================
# pipeline/worker.py
#
# Two threads:
#
# Thread 1 — job_worker:
#   Picks up "pending" jobs, runs phase 1 (local steps +
#   spawn Modal), saves call_id, marks "modal_pending".
#   Never blocks on Modal. Always free for next job.
#
# Thread 2 — modal_poller:
#   Every 10 seconds, finds "modal_pending" jobs and calls
#   collect_notebook_result(). If Modal is done, runs
#   phase 2 (guide, zip, email) and marks completed/failed.
# ============================================================

import threading
import time
import traceback
from datetime import datetime


def start_worker(app):
    # Thread 1: job worker
    t1 = threading.Thread(
        target=_job_worker_loop, args=(app,),
        daemon=True, name="job-worker"
    )
    t1.start()

    # Thread 2: modal poller
    t2 = threading.Thread(
        target=_modal_poller_loop, args=(app,),
        daemon=True, name="modal-poller"
    )
    t2.start()

    print("✅ job-worker and modal-poller threads started.", flush=True)


# ─── THREAD 1: Job Worker ────────────────────────────────────

def _job_worker_loop(app):
    while True:
        _process_pending_job(app)
        time.sleep(2)


def _process_pending_job(app):
    from pipeline.job_manager import Job
    from pipeline.token_manager import db
    from pipeline import run_pipeline_phase1

    with app.app_context():
        try:
            job = Job.query.filter_by(status="pending").order_by(Job.created_at).first()
            if not job:
                return

            job.status       = "processing"
            job.current_step = -1
            db.session.commit()
            job_id = job.id

            print(f"\n▶ [job-worker] Job {job_id} — {job.student_name}", flush=True)

            def progress_cb(n):
                with app.app_context():
                    j = db.session.get(Job, job_id)
                    if j:
                        j.current_step = n
                        db.session.commit()
                        print(f"  → step {n}", flush=True)

            result = run_pipeline_phase1(
                token         = job.token,
                matric_no     = job.matric_no,
                student_name  = job.student_name,
                student_email = job.student_email,
                progress_cb   = progress_cb,
            )

            with app.app_context():
                j = db.session.get(Job, job_id)
                if not j:
                    return

                if result["success"]:
                    j.status        = "modal_pending"
                    j.current_step  = 3     # waiting on Modal
                    j.modal_call_id = result["call_id"]
                    j.pipeline_data = result["pipeline_data"]
                    print(f"✅ [job-worker] Job {job_id} spawned Modal. Now modal_pending.", flush=True)
                else:
                    j.status       = "failed"
                    j.message      = result.get("message", "Phase 1 failed")
                    j.completed_at = datetime.utcnow()
                    print(f"❌ [job-worker] Job {job_id} phase 1 failed: {j.message}", flush=True)

                db.session.commit()

        except Exception as e:
            print(f"❌ [job-worker] Exception: {e}", flush=True)
            traceback.print_exc()


# ─── THREAD 2: Modal Poller ──────────────────────────────────

def _modal_poller_loop(app):
    # Wait a bit at startup so DB is ready
    time.sleep(5)
    while True:
        _poll_modal_jobs(app)
        time.sleep(10)   # check every 10 seconds


def _poll_modal_jobs(app):
    from pipeline.job_manager import Job
    from pipeline.token_manager import db
    from pipeline import run_pipeline_phase2

    with app.app_context():
        jobs = Job.query.filter_by(status="modal_pending").all()
        if not jobs:
            return

        print(f"[modal-poller] Checking {len(jobs)} modal_pending job(s)...", flush=True)

        for job in jobs:
            job_id = job.id
            try:
                def progress_cb(n):
                    with app.app_context():
                        j = db.session.get(Job, job_id)
                        if j:
                            j.current_step = n
                            db.session.commit()

                result = run_pipeline_phase2(
                    call_id       = job.modal_call_id,
                    pipeline_data = job.pipeline_data,
                    progress_cb   = progress_cb,
                )

                with app.app_context():
                    j = db.session.get(Job, job_id)
                    if not j:
                        continue

                    if result == "pending":
                        # Modal still running — leave as modal_pending, check again next poll
                        print(f"  [modal-poller] Job {job_id} still running on Modal.", flush=True)
                        continue

                    if result["success"]:
                        j.status       = "completed"
                        j.current_step = 6
                        j.zip_url      = result.get("zip_url")
                        j.message      = result.get("message")
                        print(f"✅ [modal-poller] Job {job_id} completed.", flush=True)
                    else:
                        j.status  = "failed"
                        j.message = result.get("message", "Phase 2 failed")
                        print(f"❌ [modal-poller] Job {job_id} failed: {j.message}", flush=True)

                    j.completed_at = datetime.utcnow()
                    db.session.commit()

            except Exception as e:
                print(f"❌ [modal-poller] Exception on job {job_id}: {e}", flush=True)
                traceback.print_exc()
                with app.app_context():
                    j = db.session.get(Job, job_id)
                    if j:
                        j.status       = "failed"
                        j.message      = str(e)
                        j.completed_at = datetime.utcnow()
                        db.session.commit()
