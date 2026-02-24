# ============================================================
# admin/generate_tokens.py
#
# ADMIN ONLY — run this once before the assignment opens.
# Generates N anonymous tokens and inserts them into the
# PostgreSQL database via SQLAlchemy.
#
# USAGE:
#   cd cos201_system
#   python admin/generate_tokens.py 60
#
# Always generate a few more than your class size.
# ============================================================

import sys
import os
import secrets
import string
from datetime import datetime

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def generate_token(length: int = 12) -> str:
    """
    Cryptographically random token — uppercase letters and digits.
    Ambiguous characters (0, O, 1, I) removed for readability.
    Example: 'K7F2MNP9XQ3L'
    """
    alphabet = (
        string.ascii_uppercase.replace("O", "").replace("I", "")
        + string.digits.replace("0", "").replace("1", "")
    )
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_and_store(count: int) -> list:
    """
    Generate `count` tokens and insert into the tokens table.
    Returns the list of token strings.
    """
    engine  = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    # Ensure the table exists
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tokens (
                token   VARCHAR(32) PRIMARY KEY,
                used    BOOLEAN DEFAULT FALSE NOT NULL,
                used_at TIMESTAMP
            )
        """))
        conn.commit()

    session = Session()
    tokens  = []
    stored  = 0

    while stored < count:
        token = generate_token()
        try:
            session.execute(
                text("INSERT INTO tokens (token, used) VALUES (:t, FALSE)"),
                {"t": token}
            )
            session.commit()
            tokens.append(token)
            stored += 1
        except Exception:
            # Collision (astronomically rare) — retry
            session.rollback()

    session.close()
    return tokens


def print_tokens(tokens: list):
    print(f"\n{'='*50}")
    print(f"  {len(tokens)} TOKENS GENERATED — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    print(f"  {'#':<5} {'TOKEN'}")
    print(f"  {'-'*30}")
    for i, token in enumerate(tokens, 1):
        print(f"  {i:<5} {token}")
    print(f"{'='*50}")
    print(f"\n  Distribute each token to one student individually.")
    print(f"  Each token can only be used once.\n")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print(f"Generating {count} tokens into PostgreSQL...")
    tokens = generate_and_store(count)
    print_tokens(tokens)
