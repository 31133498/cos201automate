# ============================================================
# app.py
# Flask web server — the entry point of the whole system.
#
# Routes:
#   GET  /         → serves the student form (form.html)
#   POST /submit   → receives form data, runs the pipeline,
#                    returns JSON {success, message, zip_url}
#
# Initialises the database at startup so the table always
# exists before any request comes in.
#
# To run locally:
#   pip install -r requirements.txt
#   python app.py
#
# To run on Render.com:
#   Set environment variables in the Render dashboard
#   Set start command to: python app.py
# ============================================================

from flask import Flask, request, jsonify, render_template
from config import FLASK_SECRET_KEY
from pipeline.token_manager import init_db
from pipeline import run_pipeline

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Initialise the database table on startup
init_db()


@app.route("/")
def index():
    """Serve the student-facing form."""
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    """
    Handle a student assignment request.

    Expects JSON body:
        {
            "student_name":  "Ada Okonkwo",
            "matric_no":     "190401001",
            "student_email": "ada@uni.edu",
            "token":         "K7F2MNP9XQ3L"
        }

    Returns JSON:
        { "success": true/false, "message": "...", "zip_url": "..." }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    # Extract and validate fields
    student_name  = data.get("student_name", "").strip()
    matric_no     = data.get("matric_no", "").strip()
    student_email = data.get("student_email", "").strip()
    token         = data.get("token", "").strip().upper()

    # Basic validation
    if not all([student_name, matric_no, student_email, token]):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    if not matric_no.isdigit():
        return jsonify({"success": False, "message": "Matric number must be numeric."}), 400

    # Run the full pipeline
    result = run_pipeline(
        token         = token,
        matric_no     = matric_no,
        student_name  = student_name,
        student_email = student_email
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    # For local development only
    # On Render, gunicorn handles serving
    app.run(debug=False, host="0.0.0.0", port=5000)
