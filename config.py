# ============================================================
# config.py
# Central configuration — loads everything from .env
# Every other file imports from here. Never hardcode
# credentials anywhere else.
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

# --- Flask ---
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback-dev-key")

# --- Database ---
# Production: full PostgreSQL URL from Render/Railway/Supabase
# e.g. postgresql://user:pass@host:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Render.com gives URLs starting with "postgres://" — SQLAlchemy
# requires "postgresql://". Fix it automatically if needed.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Add it to your .env file or deployment environment variables."
    )

# --- Cloudinary ---
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# --- Email ---
# Choose ONE: Gmail SMTP or SendGrid. Set the variables for whichever you use.
SMTP_EMAIL       = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD    = os.getenv("SMTP_PASSWORD")
SMTP_SERVER      = "smtp.gmail.com"
SMTP_PORT        = 587

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL     = os.getenv("SENDER_EMAIL")

# --- Startup validation ---
REQUIRED = {
    "CLOUDINARY_CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "CLOUDINARY_API_KEY":    CLOUDINARY_API_KEY,
    "CLOUDINARY_API_SECRET": CLOUDINARY_API_SECRET,
}

missing = [k for k, v in REQUIRED.items() if not v]
if missing:
    print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing)}")
    print("   Fill in your .env file before running the system.")

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Modal ---
# Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in your environment.
# Modal reads these automatically — no extra config needed here.
# Sign up at modal.com → Settings → API Tokens to get them.
