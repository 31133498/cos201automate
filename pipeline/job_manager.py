# ============================================================
# pipeline/job_manager.py
#
# Defines the Job model and job creation helper.
#
# IMPORTANT: Imports db from token_manager — NOT a new
# SQLAlchemy() instance. One db instance for the entire app.
# Creating a second SQLAlchemy() is what causes the
# "not registered with this SQLAlchemy instance" error.
#
# Job lifecycle:
#   pending → processing → completed
#                        → failed
# ============================================================

import uuid
from datetime import datetime
from pipeline.token_manager import db   # ← shared instance, not a new one


class Job(db.Model):
    __tablename__ = "jobs"

    id           = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token        = db.Column(db.String(32), nullable=False)
    matric_no    = db.Column(db.String(50), nullable=False)
    student_name = db.Column(db.String(200), nullable=False)
    student_email= db.Column(db.String(200), nullable=False)
    status       = db.Column(db.String(20), default="pending", nullable=False)
    zip_url      = db.Column(db.Text, nullable=True)
    message      = db.Column(db.Text, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)


def create_job(token: str, matric_no: str, student_name: str, student_email: str) -> str:
    """
    Create a new pending job and return its ID.

    The token is NOT consumed here — it is consumed inside
    run_pipeline() at processing time, after the worker
    picks up the job. This means the token is only burned
    when work actually starts.
    """
    job = Job(
        token         = token,
        matric_no     = matric_no,
        student_name  = student_name,
        student_email = student_email,
        status        = "pending",
    )
    db.session.add(job)
    db.session.commit()
    return job.id
