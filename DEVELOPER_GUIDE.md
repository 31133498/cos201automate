# COS201 Automated Assignment System - Complete Developer Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Setup Instructions](#setup-instructions)
5. [Testing Guide](#testing-guide)
6. [How It Works](#how-it-works)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

This system automatically generates **unique, plagiarism-proof** machine learning assignments for students. Each student receives:
- A personalized dataset (550 rows, seeded by their matric number)
- An AI-generated Python script with unique variable names and comments
- Three visualization plots (heatmap, scatter, residual)
- A defense guide explaining their model

**Key Innovation:** Uses OpenAI to generate completely different code for each student, preventing plagiarism detection.

---

## 🏗️ Architecture

### Frontend (React + Tailwind CSS)
- **Purpose:** User interface with 3 states (form → loading → success)
- **Tech Stack:** React 18, Vite, Tailwind CSS, Lucide Icons
- **Key Feature:** Terminal-style loading animation (15 seconds)

### Backend (FastAPI + Python)
- **Purpose:** Dataset generation, AI code generation, execution, email delivery
- **Tech Stack:** FastAPI, SQLite, OpenAI API, NumPy, Pandas
- **Key Feature:** Subprocess execution with 20-second timeout

### Data Flow
```
User Form → Token Validation → Dataset Generation → AI Code Generation 
→ Script Execution → Zip Creation → Email Delivery → Cleanup
```

---

## 📁 Project Structure

```
cos201automate/
│
├── FRONTEND
│   ├── src/
│   │   ├── App.jsx              # Main component (form, loading, success states)
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Tailwind imports
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
└── cos201_backend/
    ├── main.py                  # FastAPI app & /generate endpoint
    ├── db_manager.py            # SQLite token management (init, insert, validate)
    ├── data_engine.py           # Multi-theme dataset generator (5 themes)
    ├── code_generator.py        # OpenAI GPT-4o-mini integration
    ├── mailer.py                # SMTP email with zip attachment
    ├── add_token.py             # Helper script to insert test tokens
    ├── requirements.txt         # Python dependencies
    └── .env.example             # Environment variables template
```

---

## 🚀 Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Gmail account with App Password ([Setup guide](https://support.google.com/accounts/answer/185833))

---

### STEP 1: Clone/Navigate to Project
```bash
cd "c:\Users\HP\Desktop\Shazily Projects\cos201automate"
```

---

### STEP 2: Frontend Setup

#### Install Dependencies
```bash
npm install
```

#### Update API Endpoint for Local Testing
Open `src/App.jsx` and change line 32:
```javascript
// FROM:
fetch('https://api.yourdomain.com/generate', {

// TO:
fetch('http://localhost:8000/generate', {
```

#### Start Development Server
```bash
npm run dev
```
✅ Frontend runs at: **http://localhost:5173**

---

### STEP 3: Backend Setup

#### Navigate to Backend Directory
```bash
cd cos201_backend
```

#### Create Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in `cos201_backend/`:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASSWORD=your_16_char_app_password
```

**CRITICAL:** 
- Use Gmail App Password, NOT your regular password
- Generate App Password: Google Account → Security → 2-Step Verification → App Passwords

#### Start Backend Server
```bash
uvicorn main:app --reload
```
✅ Backend runs at: **http://localhost:8000**

---

## 🧪 Testing Guide

### STEP 1: Insert Test Token
```bash
python add_token.py
```
This inserts token: `TEST123`

To add custom tokens, edit `add_token.py`:
```python
insert_token("CUSTOM_TOKEN_HERE")
```

---

### STEP 2: Run Full System Test

1. **Open Frontend:** http://localhost:5173
2. **Fill Form:**
   - Name: `John Doe`
   - Matric No: `12345678` (last 4 digits = seed)
   - Email: `your_test_email@gmail.com`
   - Token: `TEST123`
3. **Click:** "Run My Analysis"
4. **Watch:** Terminal animation (15 seconds)
5. **Check:** Email inbox (and spam folder!)

---

### STEP 3: Verify Output

**Email should contain a zip file with:**
- `dataset.csv` (550 rows, theme-based columns)
- `main.py` (AI-generated Python script)
- `heatmap.png` (correlation matrix)
- `scatter.png` (actual vs predicted)
- `residual.png` (residual plot)
- `defense_guide.txt` (model explanation)

---

### STEP 4: Test Token Reuse Prevention
Try submitting the same token again → Should get **401 Unauthorized** error.

---

## 🔧 How It Works (Technical Deep Dive)

### 1. Token Validation (`db_manager.py`)
```python
# Checks if token exists AND is_used = False
# Immediately marks as used (atomic operation)
# Prevents token sharing between students
```

### 2. Dataset Generation (`data_engine.py`)
```python
# Uses last 4 digits of matric_no as numpy seed
# Randomly selects 1 of 5 themes:
#   - Housing_Prices (square_feet, bedrooms, etc.)
#   - Car_Efficiency (engine_size, weight, etc.)
#   - Student_Performance (study_hours, attendance, etc.)
#   - Employee_Salary (years_experience, performance, etc.)
#   - Health_Metrics (exercise_hours, calorie_intake, etc.)
# 
# Target = Linear Combination + Noise
# Ensures R² between 0.70-0.90
```

### 3. AI Code Generation (`code_generator.py`)
```python
# Sends strict prompt to GPT-4o-mini:
#   - Use random variable names (NOT df, X, y)
#   - Use random colormap (viridis, plasma, coolwarm, etc.)
#   - NO plt.show() - ONLY plt.savefig()
#   - Add unique comments
# 
# Temperature = 0.9 (high variation)
# Strips markdown formatting from response
```

### 4. Script Execution (`main.py`)
```python
# subprocess.run(['python', 'main.py'], cwd=folder_path, timeout=20)
# Runs in isolated directory
# Captures stdout/stderr
# On failure: deletes folder, returns 500 error
```

### 5. Email Delivery (`mailer.py`)
```python
# shutil.make_archive() → creates zip
# smtplib.SMTP() → sends email with attachment
# Cleanup: deletes temp folder + zip file
```

---

## 🐛 Troubleshooting

### Frontend Issues

**Problem:** "Cannot connect to backend"
```bash
# Check if backend is running
# Verify API endpoint in App.jsx is http://localhost:8000/generate
```

**Problem:** Terminal animation stuck
```bash
# Check browser console for errors
# Verify backend returned 200 response
```

---

### Backend Issues

**Problem:** "Invalid or already used token"
```bash
# Token is single-use only
# Add new token: python add_token.py
```

**Problem:** "OpenAI API key not configured"
```bash
# Check .env file exists in cos201_backend/
# Verify OPENAI_API_KEY is set correctly
```

**Problem:** "Script execution failed"
```bash
# Check backend terminal for subprocess errors
# Common cause: Missing Python packages in generated script
# Solution: AI prompt may need adjustment
```

**Problem:** "Email not received"
```bash
# Check spam folder
# Verify SMTP credentials in .env
# Test Gmail App Password is correct
# Check backend logs for SMTP errors
```

**Problem:** "Script execution timed out"
```bash
# Dataset too large or complex
# Increase timeout in main.py (line 47): timeout=20 → timeout=30
```

---

## 📊 Database Schema

**Table:** `tokens`
```sql
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_string TEXT UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT 0
);
```

**Location:** `cos201_backend/tokens.db` (auto-created on first run)

---

## 🔐 Security Notes

1. **Token System:** Single-use tokens prevent sharing
2. **Subprocess Isolation:** Each student runs in separate directory
3. **Timeout Protection:** 20-second limit prevents infinite loops
4. **Cleanup:** Temp files deleted immediately after email
5. **CORS:** Currently allows all origins (restrict in production)

---

## 🚀 Production Deployment

### Frontend (Vercel/Netlify)
```bash
npm run build
# Deploy dist/ folder
# Update API endpoint to production URL
```

### Backend (Railway/Render/AWS)
```bash
# Set environment variables in platform dashboard
# Use PostgreSQL instead of SQLite for production
# Add rate limiting middleware
# Restrict CORS to frontend domain only
```

---

## 📝 Adding New Themes

Edit `data_engine.py`, add to `themes` list:
```python
{
    "name": "Your_Theme",
    "features": ["feature1", "feature2", "feature3", "feature4", "feature5"],
    "target": "target_variable",
    "generators": lambda: {
        "feature1": np.random.randint(min, max, 550),
        # ... define all features
    },
    "coefficients": [coef1, coef2, coef3, coef4, coef5],
    "intercept": base_value
}
```

---

## 📞 Support

**Common Questions:**

Q: Can students get the same dataset?
A: No, matric number seed ensures uniqueness.

Q: Will AI generate identical code?
A: No, temperature=0.9 + random instructions ensure variation.

Q: What if two students submit simultaneously?
A: Each runs in isolated directory (no conflicts).

Q: Can I use a different email provider?
A: Yes, update SMTP_SERVER and SMTP_PORT in .env.

---

## ✅ Final Checklist

- [ ] Node.js and Python installed
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with all 4 variables
- [ ] Gmail App Password generated
- [ ] Test token inserted (`python add_token.py`)
- [ ] Frontend running on port 5173
- [ ] Backend running on port 8000
- [ ] API endpoint updated in App.jsx
- [ ] Test submission completed successfully
- [ ] Email received with zip file

---

**🎉 System Ready for Production!**

For issues, check backend terminal logs and browser console.
