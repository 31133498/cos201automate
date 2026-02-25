#!/usr/bin/env python3
"""
Run this file directly to test each pipeline component independently.
Usage: python debug_local.py

It will tell you exactly which step fails and why.
"""

import sys
import os
sys.stdout.reconfigure(line_buffering=True)

# ── 1. Check environment variables ───────────────────────────
print("\n" + "="*50)
print("STEP 1: Checking environment variables")
print("="*50)

from dotenv import load_dotenv
load_dotenv()

checks = {
    "DATABASE_URL":          os.getenv("DATABASE_URL"),
    "OPENAI_API_KEY":        os.getenv("OPENAI_API_KEY"),
    "MODAL_TOKEN_ID":        os.getenv("MODAL_TOKEN_ID"),
    "MODAL_TOKEN_SECRET":    os.getenv("MODAL_TOKEN_SECRET"),
    "CLOUDINARY_CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "CLOUDINARY_API_KEY":    os.getenv("CLOUDINARY_API_KEY"),
    "CLOUDINARY_API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    "SMTP_EMAIL":            os.getenv("SMTP_EMAIL"),
    "SMTP_PASSWORD":         os.getenv("SMTP_PASSWORD"),
}

all_ok = True
for key, val in checks.items():
    if val:
        print(f"  ✅ {key} = {val[:12]}...")
    else:
        print(f"  ❌ {key} = NOT SET")
        all_ok = False

if not all_ok:
    print("\n⚠️  Fix missing env vars in .env before continuing.")
    sys.exit(1)

# ── 2. Test DB connection ─────────────────────────────────────
print("\n" + "="*50)
print("STEP 2: Testing database connection")
print("="*50)

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from pipeline.token_manager import db
        result = db.session.execute(db.text("SELECT 1")).fetchone()
        print(f"  ✅ DB connected: {result}")

        from pipeline.job_manager import Job
        count = Job.query.count()
        print(f"  ✅ Jobs table exists. Row count: {count}")

        # Check columns exist
        cols = db.session.execute(db.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='jobs'"
        )).fetchall()
        col_names = [c[0] for c in cols]
        print(f"  ✅ Columns: {col_names}")

        for required in ["current_step", "modal_call_id", "pipeline_data"]:
            if required in col_names:
                print(f"  ✅ Column '{required}' exists")
            else:
                print(f"  ❌ Column '{required}' MISSING — run migrations")

except Exception as e:
    print(f"  ❌ DB error: {e}")
    sys.exit(1)

# ── 3. Test dataset generation ────────────────────────────────
print("\n" + "="*50)
print("STEP 3: Testing dataset generation")
print("="*50)

try:
    import tempfile
    from pipeline.dataset_engine import generate_dataset
    tmpdir = tempfile.mkdtemp()
    info = generate_dataset("190401001", tmpdir)
    print(f"  ✅ Theme    : {info['display_name']}")
    print(f"  ✅ Rows     : {info['n_rows']}")
    print(f"  ✅ Target   : {info['target']}")
    print(f"  ✅ Features : {info['features']}")
except Exception as e:
    print(f"  ❌ Dataset error: {e}")
    sys.exit(1)

# ── 4. Test OpenAI ────────────────────────────────────────────
print("\n" + "="*50)
print("STEP 4: Testing OpenAI narrative generation")
print("="*50)

try:
    from pipeline.ai_narrator import generate_markdown_narrative
    narrative = generate_markdown_narrative("Test Student", "190401001", info)
    print(f"  ✅ Keys returned: {list(narrative.keys())}")
    print(f"  ✅ Intro preview : {narrative.get('intro','')[:100]}...")
except Exception as e:
    print(f"  ❌ OpenAI error: {e}")
    print("     (Check your OPENAI_API_KEY)")

# ── 5. Test notebook build ────────────────────────────────────
print("\n" + "="*50)
print("STEP 5: Testing notebook builder")
print("="*50)

try:
    from pipeline.notebook_builder import build_notebook
    nb_path, nb_name = build_notebook(
        matric_no    = "190401001",
        student_name = "Test Student",
        dataset_info = info,
        save_dir     = tmpdir,
        narrative    = narrative if 'narrative' in dir() else None,
    )
    size = os.path.getsize(nb_path)
    print(f"  ✅ Notebook built: {nb_name} ({size} bytes)")
except Exception as e:
    print(f"  ❌ Notebook build error: {e}")
    sys.exit(1)

# ── 6. Test Modal auth ────────────────────────────────────────
print("\n" + "="*50)
print("STEP 6: Testing Modal authentication")
print("="*50)

try:
    from pipeline.modal_runner import get_modal_client
    client = get_modal_client()
    print(f"  ✅ Modal client created successfully")
except Exception as e:
    print(f"  ❌ Modal auth error: {e}")
    print("     (Check MODAL_TOKEN_ID and MODAL_TOKEN_SECRET)")

# ── 7. Test job creation + progress_cb ───────────────────────
print("\n" + "="*50)
print("STEP 7: Testing progress_cb → DB write")
print("="*50)

try:
    with app.app_context():
        from pipeline.job_manager import Job, create_job, db

        # Create a test job
        jid = create_job("TESTTOKEN", "190401001", "Debug Student", "debug@test.com")
        print(f"  ✅ Test job created: {jid[:8]}...")

        # Simulate progress_cb updating current_step
        j = db.session.get(Job, jid)
        j.current_step = 2
        db.session.commit()

        # Read it back
        j2 = db.session.get(Job, jid)
        if j2.current_step == 2:
            print(f"  ✅ current_step read back correctly: {j2.current_step}")
        else:
            print(f"  ❌ current_step mismatch: expected 2, got {j2.current_step}")

        # Clean up test job
        db.session.delete(j2)
        db.session.commit()
        print(f"  ✅ Test job cleaned up")

except Exception as e:
    print(f"  ❌ Job/DB error: {e}")
    import traceback; traceback.print_exc()

print("\n" + "="*50)
print("✅ ALL LOCAL CHECKS DONE")
print("="*50)
print("\nIf all steps passed, your local setup is correct.")
print("If any step failed, fix that before testing the full flow.\n")
