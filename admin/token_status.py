# ============================================================
# admin/token_status.py
#
# ADMIN ONLY — check token usage against PostgreSQL.
#
# USAGE:
#   python admin/token_status.py            # all tokens
#   python admin/token_status.py used       # only used
#   python admin/token_status.py unused     # only unused
# ============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL
from sqlalchemy import create_engine, text


def show_status(filter_by: str = "all"):
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Counts
        total  = conn.execute(text("SELECT COUNT(*) FROM tokens")).scalar()
        used   = conn.execute(text("SELECT COUNT(*) FROM tokens WHERE used = TRUE")).scalar()
        unused = total - used

        # Rows
        if filter_by == "used":
            where = "WHERE used = TRUE"
        elif filter_by == "unused":
            where = "WHERE used = FALSE"
        else:
            where = ""

        rows = conn.execute(
            text(f"SELECT token, used, used_at FROM tokens {where} ORDER BY used, token")
        ).fetchall()

    print(f"\n{'='*65}")
    print(f"  TOKEN STATUS  |  Total: {total}  Used: {used}  Unused: {unused}")
    print(f"{'='*65}")
    print(f"  {'TOKEN':<15} {'STATUS':<14} {'USED AT'}")
    print(f"  {'-'*60}")
    for row in rows:
        status  = "✅ USED   " if row.used else "⏳ UNUSED "
        used_at = str(row.used_at) if row.used_at else ""
        print(f"  {row.token:<15} {status:<14} {used_at}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    filter_by = sys.argv[1] if len(sys.argv) > 1 else "all"
    show_status(filter_by)
