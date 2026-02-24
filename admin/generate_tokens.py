# ============================================================
# admin/generate_tokens.py
#
# ADMIN ONLY — run this script once before the assignment opens.
#
# What it does:
#   1. Creates the tokens table in the SQLite database if
#      it doesn't already exist
#   2. Generates N unique random tokens
#   3. Saves them all to the database (unused)
#   4. Prints the full list to the terminal so you can
#      copy and distribute them one by one
#
# Tokens are completely anonymous — no name, matric, or email
# is attached. You decide who gets which token.
#
# USAGE:
#   cd cos201_system
#   python admin/generate_tokens.py 60
#
#   (replace 60 with however many tokens you need)
#   Always generate a few more than your class size.
# ============================================================

import sys
import os
import secrets
import string
import sqlite3
from datetime import datetime

# Make sure we can import config from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


def generate_token(length: int = 12) -> str:
    """
    Generate a single cryptographically random token.
    Uses uppercase letters and digits only — easy to read
    and type without ambiguous characters (0/O, 1/l removed).

    Example output: 'K7F2MNP9XQ3L'
    """
    alphabet = (
        string.ascii_uppercase.replace("O", "").replace("I", "")
        + string.digits.replace("0", "").replace("1", "")
    )
    return "".join(secrets.choice(alphabet) for _ in range(length))


def init_db():
    """Create the tokens table if it doesn't exist."""
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


def generate_and_store(count: int) -> list:
    """
    Generate `count` unique tokens, store them all in the database,
    and return the list.

    If a generated token collides with an existing one (extremely
    unlikely with 12 chars), it retries automatically.
    """
    init_db()
    conn   = sqlite3.connect(DB_PATH)
    tokens = []
    stored = 0

    while stored < count:
        token = generate_token()
        try:
            conn.execute(
                "INSERT INTO tokens (token, used) VALUES (?, 0)",
                (token,)
            )
            conn.commit()
            tokens.append(token)
            stored += 1
        except sqlite3.IntegrityError:
            # Collision — regenerate (practically impossible but handled)
            continue

    conn.close()
    return tokens


def print_tokens(tokens: list):
    """Print tokens in a clean numbered list for easy copying."""
    print(f"\n{'='*50}")
    print(f"  {len(tokens)} TOKENS GENERATED — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Database: {DB_PATH}")
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
    print(f"Generating {count} tokens...")
    tokens = generate_and_store(count)
    print_tokens(tokens)
