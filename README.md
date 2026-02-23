# COS201 Automated Assignment System

Automated ML assignment generator with unique datasets and AI-generated Python scripts for each student.

## 🚀 Quick Start

See [QUICK_START.md](QUICK_START.md) for 5-minute setup.

## 📚 Documentation

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Complete technical documentation
- **[QUICK_START.md](QUICK_START.md)** - Fast setup guide
- **[PRD.md](PRD.md)** - Product requirements document

## ✨ Features

- 🎨 Dark mode React UI with terminal animation
- 🔐 Token-based authentication (single-use)
- 🎲 5 unique dataset themes per student
- 🤖 AI-powered code generation (GPT-4o-mini)
- 📊 Automated plot generation
- 📧 Email delivery with zip attachment
- 🛡️ Anti-plagiarism protection

## 🛠️ Tech Stack

**Frontend:** React, Vite, Tailwind CSS
**Backend:** FastAPI, Python, OpenAI API, SQLite

## 📦 Installation

```bash
# Frontend
npm install
npm run dev

# Backend
cd cos201_backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 🔑 Environment Variables

Create `cos201_backend/.env`:
```env
OPENAI_API_KEY=your_key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 📝 License

MIT
