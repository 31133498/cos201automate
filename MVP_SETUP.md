# 🚀 MVP Setup Guide - For Developers

## ✅ Current Working Features
- Dataset generation (5 themes, 550 rows per student)
- AI-powered Python script generation (OpenAI GPT-4o-mini)
- Automated script execution with plot generation
- Zip file saved directly to Downloads folder

## 🔧 What's NOT Working Yet (Your Job!)
- ❌ Email delivery (SMTP timeout issues)
- ❌ Token authentication (currently disabled for testing)

---

## 📦 Quick Setup (5 Minutes)

### 1. Clone Repository
```bash
git clone https://github.com/31133498/cos201automate.git
cd cos201automate
```

### 2. Frontend Setup
```bash
npm install
npm run dev
```
Frontend runs at: **http://localhost:5173**

### 3. Backend Setup
```bash
cd cos201_backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 4. Install ML Libraries (IMPORTANT!)
```bash
pip install statsmodels scikit-learn matplotlib seaborn
```

### 5. Create .env File
Create `cos201_backend/.env`:
```env
OPENAI_API_KEY=your_openai_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Get OpenAI Key:** https://platform.openai.com/api-keys

### 6. Start Backend
```bash
uvicorn main:app --reload
```
Backend runs at: **http://localhost:8000**

---

## 🧪 Testing the MVP

### Test Flow:
1. Open http://localhost:5173
2. Fill form:
   - Name: `Test Student`
   - Matric No: `12345678`
   - Email: `test@example.com` (not used yet)
   - Token: `anything` (validation disabled)
3. Click "Run My Analysis"
4. Wait ~20 seconds
5. Check your **Downloads folder** for `COS201_Assignment_12345678.zip`

### What's in the Zip:
- `dataset.csv` - 550 rows of unique data
- `main.py` - AI-generated Python script
- `heatmap.png` - Correlation matrix
- `scatter.png` - Actual vs Predicted plot
- `residual.png` - Residual analysis
- `defense_guide.txt` - Model explanation

---

## 🛠️ Your Development Tasks

### Task 1: Fix Email Delivery
**Problem:** SMTP connection times out

**File:** `cos201_backend/mailer.py`

**Current Status:** Email logic exists but is commented out in `main.py` (line 7)

**What to do:**
1. Test SMTP connection separately:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
   server.starttls()
   server.login('your_email@gmail.com', 'your_app_password')
   print("✅ SMTP works!")
   ```
2. If Gmail blocks you, try:
   - Use Gmail App Password (not regular password)
   - Enable "Less secure app access"
   - Try different SMTP provider (SendGrid, Mailgun)
3. Once working, uncomment line 7 in `main.py`:
   ```python
   from mailer import zip_and_email
   ```
4. Replace lines 88-95 in `main.py` with:
   ```python
   zip_and_email(folder_path, request.email)
   return {"status": "success", "message": "Emailed successfully!"}
   ```

---

### Task 2: Re-enable Token Authentication
**Problem:** Token validation is disabled for testing

**File:** `cos201_backend/main.py` (lines 32-34)

**Current Status:**
```python
# Token validation disabled for testing
# if not validate_token(request.token):
#     raise HTTPException(status_code=401, detail="Invalid or already used token")
```

**What to do:**
1. Uncomment lines 33-34
2. Test token system:
   ```bash
   python add_token.py  # Creates token in database
   ```
3. Update `add_token.py` to generate multiple tokens:
   ```python
   tokens = ["TOKEN001", "TOKEN002", "TOKEN003"]
   for token in tokens:
       insert_token(token)
   ```
4. Test in frontend - should reject used tokens

---

### Task 3: Build Admin Dashboard (Optional)
**Goal:** Web UI to manage tokens

**Features needed:**
- View all tokens (used/unused)
- Generate new tokens
- Delete tokens
- View usage statistics

**Tech Stack:** React + FastAPI endpoints

**New Endpoints to Create:**
```python
@app.get("/admin/tokens")
def list_tokens():
    # Return all tokens from database

@app.post("/admin/tokens/generate")
def generate_tokens(count: int):
    # Generate N random tokens

@app.delete("/admin/tokens/{token_id}")
def delete_token(token_id: int):
    # Delete specific token
```

---

## 🐛 Common Issues

### "ModuleNotFoundError: No module named 'statsmodels'"
```bash
pip install statsmodels scikit-learn matplotlib seaborn
```

### "OpenAI API key not configured"
Check `.env` file exists in `cos201_backend/` folder

### "No space left on device"
Free up disk space or install packages globally:
```bash
deactivate
pip install statsmodels scikit-learn matplotlib seaborn
```

### Zip file not in Downloads
Check backend terminal for errors. Folder path: `C:\Users\{YourName}\Downloads`

---

## 📁 Project Structure

```
cos201automate/
├── src/
│   └── App.jsx              # Frontend (React)
├── cos201_backend/
│   ├── main.py              # API endpoint (line 88-95 = Downloads save)
│   ├── data_engine.py       # Dataset generation
│   ├── code_generator.py    # OpenAI integration
│   ├── mailer.py            # Email logic (needs fixing)
│   ├── db_manager.py        # Token management
│   └── add_token.py         # Token insertion helper
└── README.md
```

---

## 🔑 Key Code Locations

### Where Downloads Save Happens:
`main.py` lines 88-95:
```python
downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
zip_name = f"COS201_Assignment_{request.matric_no}"
zip_path = shutil.make_archive(os.path.join(downloads_path, zip_name), 'zip', folder_path)
```

### Where Email Should Happen:
`main.py` line 7 (currently commented):
```python
# from mailer import zip_and_email
```

### Where Token Validation Happens:
`main.py` lines 32-34 (currently commented):
```python
# if not validate_token(request.token):
#     raise HTTPException(status_code=401, detail="Invalid or already used token")
```

---

## 🎯 Success Criteria

### MVP is Working When:
- ✅ Frontend loads without errors
- ✅ Backend accepts form submission
- ✅ Zip file appears in Downloads folder
- ✅ Zip contains all 6 files (CSV, script, 3 PNGs, guide)

### Production Ready When:
- ✅ Email delivery works
- ✅ Token system prevents reuse
- ✅ Admin can generate tokens easily
- ✅ Error handling is robust
- ✅ Deployed to cloud (Railway/Render)

---

## 📞 Need Help?

**Check logs:**
- Frontend: Browser console (F12)
- Backend: Terminal where uvicorn is running

**Test individual components:**
```bash
# Test dataset generation
python -c "from data_engine import generate_student_dataset; print(generate_student_dataset('12345678'))"

# Test OpenAI
python -c "from code_generator import generate_ml_script_with_ai; import asyncio; asyncio.run(generate_ml_script_with_ai('./test', 'price', ['sqft'], 'Housing', 'your_key'))"
```

---

## 🚀 Next Steps

1. **Fix email delivery** (Task 1)
2. **Re-enable tokens** (Task 2)
3. **Test end-to-end** with real students
4. **Deploy to production** (Vercel + Railway)
5. **Build admin dashboard** (Task 3)

---

**Current Status:** MVP working locally, saves to Downloads folder
**Your Mission:** Fix email + tokens, then deploy to production

Good luck! 🎉
