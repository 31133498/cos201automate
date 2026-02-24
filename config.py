# ============================================================
# config.py
# Central configuration — loads everything from .env
# Every other file imports from here. You never hardcode
# credentials anywhere else in the project.
# ============================================================

import os
from dotenv import load_dotenv

# Load the .env file into environment variables
load_dotenv()

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Gmail SMTP
SMTP_EMAIL    = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")

# Database
DB_PATH = os.getenv("DB_PATH", "cos201_tokens.db")

# Validation — warn loudly at startup if anything is missing
REQUIRED = {
    "CLOUDINARY_CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "CLOUDINARY_API_KEY":    CLOUDINARY_API_KEY,
    "CLOUDINARY_API_SECRET": CLOUDINARY_API_SECRET,
    "SMTP_EMAIL":            SMTP_EMAIL,
    "SMTP_PASSWORD":         SMTP_PASSWORD,
}

missing = [k for k, v in REQUIRED.items() if not v]
if missing:
    print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing)}")
    print("   Fill in your .env file before running the system.")
