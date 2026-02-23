# 🚀 QUICK START GUIDE - COS201 Assignment System

## ⚡ 5-Minute Setup

### 1. Install Dependencies

**Frontend:**
```bash
cd "c:\Users\HP\Desktop\Shazily Projects\cos201automate"
npm install
```

**Backend:**
```bash
cd cos201_backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

### 2. Configure Environment

Create `cos201_backend/.env`:
```env
OPENAI_API_KEY=sk-proj-your_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASSWORD=your_app_password
```

---

### 3. Update API Endpoint

Edit `src/App.jsx` line 32:
```javascript
fetch('http://localhost:8000/generate', {
```

---

### 4. Add Test Token

```bash
cd cos201_backend
python add_token.py
```
Token: `TEST123`

---

### 5. Start Servers

**Terminal 1 (Frontend):**
```bash
npm run dev
```

**Terminal 2 (Backend):**
```bash
cd cos201_backend
venv\Scripts\activate
uvicorn main:app --reload
```

---

### 6. Test

1. Open: http://localhost:5173
2. Fill form with token `TEST123`
3. Wait 15 seconds
4. Check email!

---

## 🎯 What You Built

### Frontend Features
✅ Dark mode UI with Tailwind CSS
✅ Mobile-responsive design
✅ Terminal-style loading animation
✅ 3-state flow (form → loading → success)

### Backend Features
✅ Token-based authentication (single-use)
✅ 5 unique dataset themes (Housing, Cars, Students, Employees, Health)
✅ AI-powered code generation (GPT-4o-mini)
✅ Secure subprocess execution
✅ Automated email delivery with zip attachment
✅ Automatic cleanup

### Anti-Plagiarism Features
✅ Seeded randomness (unique per matric number)
✅ AI generates different variable names
✅ Random colormaps for plots
✅ Unique comments in code
✅ Different themes per student

---

## 📊 System Flow

```
Student Submits Form
    ↓
Token Validated (marked as used)
    ↓
Dataset Generated (550 rows, theme-based)
    ↓
AI Writes Python Script (unique code)
    ↓
Script Executed (generates 3 plots)
    ↓
Defense Guide Created
    ↓
Everything Zipped
    ↓
Email Sent
    ↓
Temp Files Deleted
    ↓
Success Response
```

---

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `src/App.jsx` | React UI (3 states) |
| `main.py` | FastAPI endpoint |
| `db_manager.py` | Token validation |
| `data_engine.py` | Dataset generation |
| `code_generator.py` | OpenAI integration |
| `mailer.py` | Email delivery |
| `add_token.py` | Token insertion helper |

---

## 🐛 Quick Fixes

**Backend won't start:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Email not sending:**
- Check spam folder
- Verify Gmail App Password (not regular password)
- Test SMTP credentials

**Token already used:**
```bash
python add_token.py  # Add new token
```

**Frontend can't connect:**
- Check backend is running on port 8000
- Verify API endpoint in App.jsx

---

## 📝 Adding More Tokens

Edit `add_token.py`:
```python
from db_manager import init_db, insert_token

init_db()
insert_token("TOKEN1")
insert_token("TOKEN2")
insert_token("TOKEN3")
print("✅ Tokens added!")
```

Run:
```bash
python add_token.py
```

---

## 🎓 For Students

Each student receives:
1. **dataset.csv** - 550 rows of unique data
2. **main.py** - Complete Python script
3. **heatmap.png** - Correlation matrix
4. **scatter.png** - Actual vs Predicted plot
5. **residual.png** - Residual analysis
6. **defense_guide.txt** - Model explanation

All files are zipped and emailed automatically.

---

## 🚀 Production Checklist

- [ ] Change API endpoint to production URL
- [ ] Restrict CORS to frontend domain only
- [ ] Use PostgreSQL instead of SQLite
- [ ] Add rate limiting
- [ ] Set up monitoring/logging
- [ ] Configure production SMTP
- [ ] Add error tracking (Sentry)
- [ ] Set up automated backups

---

## 📞 Need Help?

Check `DEVELOPER_GUIDE.md` for detailed documentation.

**Common Issues:**
- Token errors → Add new token
- Email issues → Check SMTP config
- Timeout errors → Increase timeout in main.py
- API errors → Check OpenAI key

---

**✅ System is ready to use!**
