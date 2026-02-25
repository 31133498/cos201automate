# ============================================================
# app.py
# ============================================================

import sys
import os

# Force unbuffered output — must be done before anything else
# so ALL print() calls appear immediately in Render logs.
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ["PYTHONUNBUFFERED"] = "1"

from flask import Flask, request, jsonify, render_template
from config import FLASK_SECRET_KEY, DATABASE_URL
from pipeline.token_manager import init_db, validate_and_consume
from pipeline.job_manager import db, create_job, Job
from pipeline.worker import start_worker


def _run_migrations(app):
    from sqlalchemy import text
    from pipeline.token_manager import db

    migrations = [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS current_step  INTEGER NOT NULL DEFAULT -1",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS modal_call_id VARCHAR(200)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS pipeline_data TEXT",
    ]

    with app.app_context():
        for sql in migrations:
            try:
                db.session.execute(text(sql))
                db.session.commit()
                print(f"✅ Migration OK: {sql[:50]}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"⚠️  Migration skipped: {e}", flush=True)

    print("✅ DB migrations done.", flush=True)


def create_app():
    print("🚀 create_app() starting...", flush=True)

    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    app.config["SQLALCHEMY_DATABASE_URI"]        = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_size":     5,
        "max_overflow":  10,
        "pool_timeout":  30,
    }

    init_db(app)
    _run_migrations(app)
    start_worker(app)

    print("🚀 App ready. Routes and workers live.", flush=True)

    # ── Routes ────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("form.html")

    @app.route("/submit", methods=["POST"])
    def submit():
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data received."}), 400

        student_name  = data.get("student_name",  "").strip()
        matric_no     = data.get("matric_no",     "").strip()
        student_email = data.get("student_email", "").strip()
        token         = data.get("token",         "").strip().upper()

        if not all([student_name, matric_no, student_email, token]):
            return jsonify({"success": False, "message": "All fields are required."}), 400

        if not matric_no.isdigit():
            return jsonify({"success": False, "message": "Matric number must be numeric."}), 400

        if not validate_and_consume(token):
            return jsonify({
                "success": False,
                "message": "Invalid or already-used token. Please contact your lecturer."
            }), 400

        job_id = create_job(
            token         = token,
            matric_no     = matric_no,
            student_name  = student_name,
            student_email = student_email,
        )
        print(f"📥 Job created: {job_id} for {student_name}", flush=True)

        return jsonify({
            "success": True,
            "job_id":  job_id,
            "message": "Assignment generation started."
        })

    @app.route("/status/<job_id>")
    def job_status(job_id):
        job = db.session.get(Job, job_id)
        if not job:
            return jsonify({"success": False, "message": "Job not found."}), 404

        display_status = "processing" if job.status == "modal_pending" else job.status

        return jsonify({
            "status":       display_status,
            "current_step": job.current_step,
            "zip_url":      job.zip_url,
            "message":      job.message,
        })

    @app.route("/admin/test-modal")
    def test_modal():
        token_id  = os.environ.get("MODAL_TOKEN_ID", "")
        token_sec = os.environ.get("MODAL_TOKEN_SECRET", "")
        if not token_id or not token_sec:
            return jsonify({"modal_auth": "FAIL",
                            "error": "MODAL_TOKEN_ID or MODAL_TOKEN_SECRET not set"}), 500
        try:
            from pipeline.modal_runner import get_modal_client
            get_modal_client()
            return jsonify({"modal_auth": "ok", "token_id_prefix": token_id[:8] + "..."})
        except Exception as e:
            return jsonify({"modal_auth": "FAIL", "error": str(e)}), 500

    @app.route("/admin/job-log")
    def job_log():
        """Show last 20 jobs and their current state — useful for debugging."""
        jobs = Job.query.order_by(Job.created_at.desc()).limit(20).all()
        return jsonify([{
            "id":           j.id[:8],
            "name":         j.student_name,
            "status":       j.status,
            "current_step": j.current_step,
            "created":      str(j.created_at),
            "completed":    str(j.completed_at),
            "message":      j.message,
        } for j in jobs])

    return app


app = create_app()

if __name__ == "__main__":
    # use_reloader=False prevents Flask from starting TWO processes
    # (main + reloader child), which would spawn duplicate worker threads
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
