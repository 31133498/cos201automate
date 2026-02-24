# ============================================================
# pipeline/worker.py
#
# Background worker thread — polls for pending jobs and
# processes them one at a time.
#
# FIXED BUGS from original:
#
# BUG 1 — stop_event killed the thread immediately.
#   Original code called stop_event.set() then thread.join()
#   right after starting the thread, which stopped it before
#   it did any work. Removed entirely — daemon=True means
#   the thread dies cleanly when the main process exits.
#
# BUG 2 — run_pipeline() signature mismatch.
#   Worker called run_pipeline(token=job.token) but the
#   function requires matric_no, student_name, student_email
#   too. Fixed to pass all fields stored on the Job row.
#
# BUG 3 — app context on every iteration.
#   The original wrapped the entire while loop in one
#   with app.app_context() block. On Render/production this
#   can cause stale sessions. Fixed: push a fresh app context
#   for each individual job iteration using a helper.
#
# BUG 4 — no sleep on idle.
#   Without sleep the loop would hammer the database
#   thousands of times per second when no jobs are pending.
#   sleep(2) is already present — kept.
# ============================================================

import threading
import time
import traceback
from datetime import datetime


def start_worker(app):
    """
    Start the background worker as a daemon thread.
    Call this once inside create_app().
    """

    def worker_loop():
        while True:
            _process_next_job(app)
            time.sleep(2)   # poll every 2 seconds

    thread = threading.Thread(target=worker_loop, daemon=True, name="job-worker")
    thread.start()
    print("✅ Background worker started.")


def _process_next_job(app):
    """
    Pick up one pending job and run it.
    Uses a fresh app context per job to keep DB sessions clean.
    """
    # Import here to avoid circular imports at module load time
    from pipeline.job_manager import Job
    from pipeline.token_manager import db
    from pipeline import run_pipeline

    with app.app_context():
        try:
            # Fetch oldest pending job
            job = Job.query.filter_by(status="pending").order_by(Job.created_at).first()

            if not job:
                return  # nothing to do

            # Mark as processing immediately so no other worker picks it up
            job.status = "processing"
            db.session.commit()

            print(f"\n▶ Worker picked up job {job.id} — {job.student_name} ({job.matric_no})")

            # Run the full pipeline
            result = run_pipeline(
                token         = job.token,
                matric_no     = job.matric_no,
                student_name  = job.student_name,
                student_email = job.student_email,
            )

            # Update job with result
            if result["success"]:
                job.status  = "completed"
                job.zip_url = result.get("zip_url")
                job.message = result.get("message")
                print(f"✅ Job {job.id} completed.")
            else:
                job.status  = "failed"
                job.message = result.get("message", "Unknown error")
                print(f"❌ Job {job.id} failed: {job.message}")

            job.completed_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            # Catch everything so the worker thread never dies
            print(f"❌ Worker exception: {e}")
            traceback.print_exc()
            try:
                # Try to mark the job as failed if we have a reference to it
                if 'job' in dir() and job:
                    job.status  = "failed"
                    job.message = str(e)
                    job.completed_at = datetime.utcnow()
                    db.session.commit()
            except Exception:
                db.session.rollback()
