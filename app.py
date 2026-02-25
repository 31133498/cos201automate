# ============================================================
# app.py
#
# Flask application factory.
#
# FIXED from original:
#
# FIX 1 — create_job() signature.
#   Original called create_job(token) with only one argument.
#   The function needs matric_no, student_name, student_email
#   too so the worker has everything it needs when it picks
#   up the job. All four fields now passed.
#
# FIX 2 — token validation before job creation.
#   Original created the job first then let the worker
#   validate the token. This means an invalid token would
#   create a job that immediately fails — wasting a queue
#   slot and confusing the student with a delayed error.
#   Token is now validated synchronously in /submit before
#   any job is created. If invalid, error returns immediately.
#
# FIX 3 — Job.query.get() is deprecated in SQLAlchemy 2.x.
#   Replaced with db.session.get(Job, job_id).
#
# FIX 4 — init_db and start_worker must be called after
#   db.init_app(). Order matters. Fixed sequence in create_app.
# ============================================================

from flask import Flask, request, jsonify, render_template
from config import FLASK_SECRET_KEY, DATABASE_URL
from pipeline.token_manager import init_db, validate_and_consume
from pipeline.job_manager import db, create_job, Job
from pipeline.worker import start_worker


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # --- Database configuration ---
    app.config["SQLALCHEMY_DATABASE_URI"]    = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_size":     5,
        "max_overflow":  10,
        "pool_timeout":  30,
    }

    # --- Initialise DB + create tables ---
    init_db(app)

    # --- Auto-generate tokens on first startup ---
    with app.app_context():
        from pipeline.token_manager import Token
        import secrets
        import string
        
        if Token.query.count() == 0:
            print("🔑 No tokens found. Generating 100 tokens...")
            alphabet = (string.ascii_uppercase.replace("O", "").replace("I", "") + 
                       string.digits.replace("0", "").replace("1", ""))
            
            for _ in range(100):
                token_str = "".join(secrets.choice(alphabet) for _ in range(12))
                token = Token(token=token_str, used=False)
                db.session.add(token)
            
            db.session.commit()
            print("✅ 100 tokens generated successfully!")

    # --- Start background worker ---
    start_worker(app)

    # ------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        """Serve the student-facing form."""
        return render_template("form.html")
    
    @app.route("/tokens")
    def list_tokens():
        """List all unused tokens (for admin use)."""
        from pipeline.token_manager import Token
        unused = Token.query.filter_by(used=False).all()
        return jsonify({
            "total": Token.query.count(),
            "unused": len(unused),
            "tokens": [t.token for t in unused[:100]]
        })

    @app.route("/admin")
    def admin():
        """Serve the admin panel (no token required)."""
        return render_template("admin.html")

    @app.route("/admin/generate", methods=["POST"])
    def admin_generate():
        """Admin endpoint - bypasses token validation."""
        from pipeline import run_pipeline
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data received."}), 400

        student_name  = data.get("student_name", "").strip()
        matric_no     = data.get("matric_no", "").strip()
        student_email = data.get("student_email", "").strip()

        if not all([student_name, matric_no, student_email]):
            return jsonify({"success": False, "message": "All fields are required."}), 400

        if not matric_no.isdigit():
            return jsonify({"success": False, "message": "Matric number must be numeric."}), 400

        # Run pipeline directly without token
        result = run_pipeline(
            token="ADMIN_BYPASS",
            matric_no=matric_no,
            student_name=student_name,
            student_email=student_email
        )

        if result and result.get("success"):
            return jsonify({
                "success": True,
                "zip_url": result.get("zip_url"),
                "message": "Assignment generated successfully!"
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get("message", "Generation failed")
            }), 500

    @app.route("/submit", methods=["POST"])
    def submit():
        """
        Validate the student's submission and queue a job.

        1. Validate all fields
        2. Validate token synchronously (fail fast, no queue slot wasted)
        3. Create job with all student details
        4. Return job_id for the frontend to poll
        """
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "No data received."}), 400

        student_name  = data.get("student_name",  "").strip()
        matric_no     = data.get("matric_no",     "").strip()
        student_email = data.get("student_email", "").strip()
        token         = data.get("token",         "").strip().upper()

        # Field presence check
        if not all([student_name, matric_no, student_email, token]):
            return jsonify({"success": False, "message": "All fields are required."}), 400

        # Matric number must be numeric
        if not matric_no.isdigit():
            return jsonify({"success": False, "message": "Matric number must be numeric."}), 400

        # Validate and consume token immediately — fail fast
        if not validate_and_consume(token):
            return jsonify({
                "success": False,
                "message": "Invalid or already-used token. Please contact your lecturer."
            }), 400

        # Token valid — create job with all details the worker needs
        job_id = create_job(
            token         = token,
            matric_no     = matric_no,
            student_name  = student_name,
            student_email = student_email,
        )

        return jsonify({
            "success": True,
            "job_id": job_id,
            "message": "Assignment generation started. This takes about 30–60 seconds."
        })

    @app.route("/status/<job_id>")
    def job_status(job_id):
        """
        Poll endpoint — frontend calls this every 3 seconds.
        Returns current job status, zip_url when done.
        """
        # db.session.get() is the correct SQLAlchemy 2.x API
        # Job.query.get() is deprecated and removed in 2.x
        job = db.session.get(Job, job_id)

        if not job:
            return jsonify({"success": False, "message": "Job not found."}), 404

        return jsonify({
            "status":  job.status,           # pending / processing / completed / failed
            "zip_url": job.zip_url,
            "message": job.message,
        })

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
