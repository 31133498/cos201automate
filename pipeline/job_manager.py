# ============================================================
# pipeline/job_manager.py
#
# Job model — added modal_call_id and "modal_pending" status
# to support non-blocking Modal execution.
#
# Job status flow:
#   pending → processing → modal_pending → completed
#                                        → failed
# ============================================================

import uuid
from datetime import datetime
from pipeline.token_manager import db


class Job(db.Model):
    __tablename__ = "jobs"

    id             = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    token          = db.Column(db.String(32),  nullable=False)
    matric_no      = db.Column(db.String(50),  nullable=False)
    student_name   = db.Column(db.String(200), nullable=False)
    student_email  = db.Column(db.String(200), nullable=False)
    status         = db.Column(db.String(20),  default="pending",  nullable=False)
    current_step   = db.Column(db.Integer,     default=-1,         nullable=False)
    modal_call_id  = db.Column(db.String(200), nullable=True)   # Modal function call ID
    zip_url        = db.Column(db.Text,        nullable=True)
    message        = db.Column(db.Text,        nullable=True)
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)
    completed_at   = db.Column(db.DateTime,    nullable=True)

    # Serialised intermediate data — dataset_info + notebook paths
    # stored as JSON so the modal poller can finish the job
    pipeline_data  = db.Column(db.Text,        nullable=True)


def create_job(token: str, matric_no: str, student_name: str, student_email: str) -> str:
    job = Job(
        token         = token,
        matric_no     = matric_no,
        student_name  = student_name,
        student_email = student_email,
        status        = "pending",
        current_step  = -1,
    )
    db.session.add(job)
    db.session.commit()
    return job.id
