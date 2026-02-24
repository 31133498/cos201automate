# ============================================================
# admin/token_status.py
#
# ADMIN ONLY — check which tokens have been used.
#
# USAGE:
#   cd cos201_system
#   python admin/token_status.py
#
#   Optional filter:
#   python admin/token_status.py used     (show only used)
#   python admin/token_status.py unused   (show only unused)
# ============================================================

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


def show_status(filter_by: str = "all"):
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Run admin/generate_tokens.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = "SELECT token, used, used_at FROM tokens"
    if filter_by == "used":
        query += " WHERE used = 1"
    elif filter_by == "unused":
        query += " WHERE used = 0"
    query += " ORDER BY used, token"

    rows = conn.execute(query).fetchall()
    conn.close()

    total  = conn.execute("SELECT COUNT(*) FROM sqlite3.connect(DB_PATH)").fetchone()[0] if False else None
    conn2  = sqlite3.connect(DB_PATH)
    total  = conn2.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
    used   = conn2.execute("SELECT COUNT(*) FROM tokens WHERE used=1").fetchone()[0]
    unused = total - used
    conn2.close()

    print(f"\n{'='*60}")
    print(f"  TOKEN STATUS REPORT")
    print(f"  Database : {DB_PATH}")
    print(f"  Total    : {total}  |  Used: {used}  |  Unused: {unused}")
    print(f"{'='*60}")
    print(f"  {'TOKEN':<15} {'STATUS':<12} {'USED AT'}")
    print(f"  {'-'*55}")

    for row in rows:
        status  = "✅ USED" if row["used"] else "⏳ UNUSED"
        used_at = row["used_at"] or ""
        print(f"  {row['token']:<15} {status:<12} {used_at}")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    filter_by = sys.argv[1] if len(sys.argv) > 1 else "all"
    show_status(filter_by)
