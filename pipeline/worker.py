# ============================================================
# pipeline/worker.py
#
# Background worker — picks up pending jobs and runs them.
# Passes a progress_cb to run_pipeline so current_step in
# the database is updated in real time as each stage runs.
# The frontend polls /status/:id and gets the real step.
# ============================================================

import threading
import time
import traceback
from datetime import datetime


def start_worker(app):
    def worker_loop():
        while True:
            _process_next_job(app)
            time.sleep(2)

    thread = threading.Thread(target=worker_loop, daemon=True, name="job-worker")
    thread.start()
    print("✅ Background worker started.", flush=True)


def _process_next_job(app):
    from pipeline.job_manager import Job
    from pipeline.token_manager import db
    from pipeline import run_pipeline

    with app.app_context():
        try:
            job = Job.query.filter_by(status="pending").order_by(Job.created_at).first()
            if not job:
                return

            job.status       = "processing"
            job.current_step = -1
            db.session.commit()

            print(f"\n▶ Worker picked up job {job.id} — {job.student_name} ({job.matric_no})", flush=True)

            # Capture job.id now for use inside the closure
            job_id = job.id

            def progress_cb(step_index: int):
                """Called by run_pipeline before each major step."""
                with app.app_context():
                    j = db.session.get(Job, job_id)
                    if j:
                        j.current_step = step_index
                        db.session.commit()
                        print(f"  → Step {step_index} started", flush=True)

            result = run_pipeline(
                token         = job.token,
                matric_no     = job.matric_no,
                student_name  = job.student_name,
                student_email = job.student_email,
                progress_cb   = progress_cb,
            )

            # Write final result
            with app.app_context():
                j = db.session.get(Job, job_id)
                if j:
                    if result["success"]:
                        j.status       = "completed"
                        j.current_step = 6   # all done
                        j.zip_url      = result.get("zip_url")
                        j.message      = result.get("message")
                        print(f"✅ Job {job_id} completed.", flush=True)
                    else:
                        j.status  = "failed"
                        j.message = result.get("message", "Unknown error")
                        print(f"❌ Job {job_id} failed: {j.message}", flush=True)
                    j.completed_at = datetime.utcnow()
                    db.session.commit()

        except Exception as e:
            print(f"❌ Worker exception: {e}", flush=True)
            traceback.print_exc()
            try:
                if 'job_id' in dir() and job_id:
                    with app.app_context():
                        j = db.session.get(Job, job_id)
                        if j:
                            j.status       = "failed"
                            j.message      = str(e)
                            j.completed_at = datetime.utcnow()
                            db.session.commit()
            except Exception:
                pass
