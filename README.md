# COS201 Assignment Delivery System

Automated assignment delivery for COS201. Students submit a form,
the system generates their personalised files and emails a download link.

---

## Project Structure

```
cos201_system/
├── app.py                        Flask web server
├── config.py                     Loads all settings from .env
├── requirements.txt              Python dependencies
├── .env                          YOUR CREDENTIALS (fill this in)
├── cos201_tokens.db              SQLite database (auto-created)
│
├── pipeline/
│   ├── __init__.py               Master pipeline (run_pipeline)
│   ├── token_manager.py          Token validation and consumption
│   ├── dataset_engine.py         Synthetic dataset generation (10 themes)
│   ├── notebook_builder.py       Builds .ipynb using nbformat (10 templates)
│   ├── notebook_runner.py        Executes notebook via nbconvert
│   ├── defense_guide.py          Generates defense_guide.txt
│   ├── packager.py               Zips all deliverable files
│   ├── uploader.py               Uploads to Cloudinary
│   └── mailer.py                 Gmail SMTP email delivery
│
├── admin/
│   ├── generate_tokens.py        Generate and store tokens (run once)
│   └── token_status.py           Check which tokens are used/unused
│
└── templates/
    └── form.html                 Student-facing web form
```

---

## Setup Instructions

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Fill in your .env file

Open `.env` and fill in every value:

```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
SMTP_EMAIL=youremail@gmail.com
SMTP_PASSWORD=your_16_char_app_password
FLASK_SECRET_KEY=any_long_random_string
DB_PATH=cos201_tokens.db
```

**Cloudinary:** Sign up free at cloudinary.com. Find your credentials
on the dashboard homepage.

**Gmail App Password:** Go to Google Account → Security →
2-Step Verification → App Passwords. Generate one for "Mail".
Use the 16-character code as SMTP_PASSWORD.

### 3. Generate tokens (admin step — run once)

```bash
python admin/generate_tokens.py 60
```

This generates 60 tokens, stores them in the database, and prints
the list. Copy each token and give one to each student individually.

### 4. Run the app locally

```bash
python app.py
```

Visit http://localhost:5000 to see the student form.

### 5. Check token usage

```bash
python admin/token_status.py          # all tokens
python admin/token_status.py used     # only used
python admin/token_status.py unused   # only unused
```

---

## Deploying to Render.com (Free)

1. Push this folder to a GitHub repository
2. Go to render.com → New Web Service → connect your repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`
5. Add environment variables in the Render dashboard
   (copy each line from your .env file)
6. Deploy — Render gives you a public URL like
   `https://cos201-system.onrender.com`

Share that URL with your students.

---

## What Each Student Receives

A ZIP file containing:

| File | Description |
|---|---|
| `{theme}.csv` | Their unique dataset (500–800 rows) |
| `{theme}_regression.ipynb` | Pre-executed Jupyter notebook |
| `heatmap.png` | Correlation heatmap |
| `scatter.png` | Actual vs Predicted plot |
| `residual.png` | Residual analysis plot |
| `defense_guide.txt` | Viva preparation guide with their real R² |

---

## Anti-Plagiarism Layers

1. **Unique dataset numbers** — seeded from matric number, every
   student's R², MSE, coefficients, and graph shapes are different
2. **10 dataset themes** — students are split across 10 topic areas
   (housing, healthcare, education, retail, etc.)
3. **10 code templates** — different variable names, plot colours,
   comment styles, and model ordering
4. **Row count variation** — each dataset has between 500 and 800 rows

---

## Notes

- Tokens are fully anonymous — not linked to any student in the database
- You decide who gets which token and distribute them manually
- Each token can only be used once
- If a student loses their token, you can re-run the pipeline manually
  from the admin console by calling run_pipeline() directly
- Temp folders are deleted immediately after delivery
- All files are stored on Cloudinary permanently (free tier: 25GB)
