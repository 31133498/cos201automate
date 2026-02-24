# ============================================================
# pipeline/token_manager.py
#
# Handles everything related to tokens:
#   - Creating the database table
#   - Validating and consuming a token when a student submits
#
# Tokens are completely anonymous — no name, no matric, no email
# stored against them. The student provides their own details
# at submission time. The token just proves they have permission.
# ============================================================

import sqlite3
from datetime import datetime
from config import DB_PATH


def init_db():
    """
    Create the tokens table if it doesn't already exist.
    Called once at app startup. Safe to call multiple times.
    
    Table structure:
        token    — the unique code e.g. 'K7F2MNP9XQ3L'
        used     — 0 (unused) or 1 (consumed)
        used_at  — ISO timestamp of when it was consumed, or NULL
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token    TEXT PRIMARY KEY,
            used     INTEGER DEFAULT 0,
            used_at  TEXT
        )
    """)
    conn.commit()
    conn.close()


def validate_and_consume(token: str) -> bool:
    """
    Check if a token exists and is unused.
    If valid: mark it as used immediately and return True.
    If invalid or already used: return False.

    The token is marked used the instant it is validated —
    before any processing starts — so even if the pipeline
    crashes halfway through, the token cannot be reused.
    """
    conn = sqlite3.connect(DB_PATH)

    row = conn.execute(
        "SELECT token FROM tokens WHERE token = ? AND used = 0",
        (token,)
    ).fetchone()

    if row is None:
        conn.close()
        return False

    # Consume immediately
    conn.execute(
        "UPDATE tokens SET used = 1, used_at = ? WHERE token = ?",
        (datetime.now().isoformat(), token)
    )
    conn.commit()
    conn.close()
    return True


def get_all_token_status() -> list:
    """
    Return all tokens and their status.
    Used by the admin to see who has collected and who hasn't.
    Returns a list of dicts: {token, used, used_at}
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT token, used, used_at FROM tokens ORDER BY used, token"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
