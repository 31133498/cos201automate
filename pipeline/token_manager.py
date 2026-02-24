# ============================================================
# pipeline/token_manager.py (Production Version)
# Uses PostgreSQL via SQLAlchemy
# Atomic token consumption
# ============================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Token(db.Model):
    __tablename__ = "tokens"

    token   = db.Column(db.String(32), primary_key=True)
    used    = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


def validate_and_consume(token_value: str) -> bool:
    """
    Atomic token validation.
    Uses SELECT FOR UPDATE to prevent race conditions.
    """

    try:
        token = (
            db.session.query(Token)
            .filter_by(token=token_value, used=False)
            .with_for_update()
            .first()
        )

        if not token:
            return False

        token.used = True
        token.used_at = datetime.utcnow()

        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def get_all_token_status():
    tokens = Token.query.order_by(Token.used, Token.token).all()
    return [
        {
            "token": t.token,
            "used": t.used,
            "used_at": t.used_at.isoformat() if t.used_at else None,
        }
        for t in tokens
    ]