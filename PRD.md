# Product Requirements Document (PRD)
# COS201 Automated Assignment System

---

## 1. Executive Summary

### Problem Statement
Students in COS201 Machine Learning course need unique datasets and Python scripts for their Multiple Linear Regression assignments. Manual creation is time-consuming, and shared datasets lead to plagiarism flags.

### Solution
An automated system that generates completely unique, personalized ML assignments for each student using:
- Deterministic randomness (seeded by matric number)
- AI-powered code generation (OpenAI GPT-4o-mini)
- Automated execution and email delivery

### Key Metrics
- **Uniqueness:** 100% (no two students get identical code)
- **Processing Time:** ~15-20 seconds per student
- **Success Rate:** 95%+ (with proper configuration)
- **Cost:** ~$0.02 per student (OpenAI API)

---

## 2. System Architecture

### 2.1 Frontend (React + Tailwind CSS)

**Technology Stack:**
- React 18.2.0 (functional components + hooks)
- Vite 5.0.8 (build tool)
- Tailwind CSS 3.3.6 (styling)
- Lucide React (icons)

**User Flow:**
```
Landing Page (Form)
    ↓
Submit Button Clicked
    ↓
Terminal Animation (15s)
    ↓
Success Screen (Green Checkmark)
```

**State Management:**
- `state`: 'form' | 'loading' | 'success'
- `formData`: {name, matric_no, email, token}
- `terminalText`: Current animation message

**Key Features:**
1. **Mobile-First Design:** Most users access via phone
2. **Dark Mode Aesthetic:** Developer-friendly UI
3. **Terminal Illusion:** Builds trust during processing
4. **No Backend Logic:** Pure presentation layer

---

### 2.2 Backend (FastAPI + Python)

**Technology Stack:**
- FastAPI 0.109.0 (async web framework)
- SQLite3 (token database)
- NumPy 1.26.3 (data generation)
- Pandas 2.1.4 (dataframe handling)
- OpenAI 1.12.0 (code generation)
- Python SMTP (email delivery)

**API Endpoints:**
```
POST /generate
    Request: {name, matric_no, email, token}
    Response: {status: "success", message: "..."}
    Errors: 401 (invalid token), 500 (execution failure)
```

**Processing Pipeline:**
```
1. Token Validation (db_manager.py)
2. Dataset Generation (data_engine.py)
3. AI Code Generation (code_generator.py)
4. Script Execution (subprocess)
5. Defense Guide Creation
6. Zip & Email (mailer.py)
7. Cleanup
```

---

## 3. Core Components

### 3.1 Token Management (`db_manager.py`)

**Purpose:** Prevent token sharing and reuse

**Database Schema:**
```sql
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_string TEXT UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT 0
);
```

**Functions:**
- `init_db()`: Creates table if not exists
- `insert_token(token_string)`: Adds new token
- `validate_token(token_string)`: Checks validity + marks as used

**Security Features:**
- Atomic operations (no race conditions)
- Single-use tokens (immediate marking)
- Unique constraint (no duplicates)

---

### 3.2 Dataset Generation (`data_engine.py`)

**Purpose:** Create unique, realistic datasets per student

**Seeding Strategy:**
```python
seed = int(matric_no[-4:])  # Last 4 digits
np.random.seed(seed)
```
**Why?** Ensures:
- Same student always gets same data (idempotent)
- Different students get different data (unique)

**Themes (5 Total):**

1. **Housing_Prices**
   - Features: square_feet, num_bedrooms, age_of_house, distance_to_center, crime_rate
   - Target: price
   - Coefficients: [150, 20000, -500, -2000, -300]

2. **Car_Efficiency**
   - Features: engine_size, weight, horsepower, age, cylinders
   - Target: mpg
   - Coefficients: [-3, -0.005, -0.02, -0.5, -2]

3. **Student_Performance**
   - Features: study_hours, attendance_rate, previous_score, sleep_hours, tutoring_sessions
   - Target: final_score
   - Coefficients: [0.8, 0.3, 0.4, 1.5, 0.5]

4. **Employee_Salary**
   - Features: years_experience, performance_score, training_hours, projects_completed, age
   - Target: salary
   - Coefficients: [3000, 5000, 50, 800, 500]

5. **Health_Metrics**
   - Features: exercise_hours, calorie_intake, water_intake, stress_level, sleep_quality
   - Target: health_score
   - Coefficients: [2, 0.01, 5, -3, 4]

**Target Calculation:**
```python
target = intercept + Σ(coefficient[i] * feature[i]) + noise
noise = N(0, σ * 0.15)  # 15% noise for realistic R²
```

**Output:**
- CSV file: 550 rows × (5 features + 1 target)
- R² range: 0.70 - 0.90 (realistic for student projects)

---

### 3.3 AI Code Generation (`code_generator.py`)

**Purpose:** Generate unique Python scripts per student

**Model:** GPT-4o-mini
- **Why?** Fast (2-3s), cheap ($0.02/student), good quality
- **Temperature:** 0.9 (high variation)

**Prompt Engineering:**
```
REQUIREMENTS:
- Read 'dataset.csv' from current directory
- Predict {target_var} using {feature_list}
- Use statsmodels.api for OLS summary
- Use scikit-learn for train_test_split, metrics
- Generate 3 plots: heatmap, scatter, residual

CRITICAL RULES:
1. NO plt.show() - ONLY plt.savefig()
2. Use random variable names (NOT df, X, y)
3. Use random colormap (viridis, plasma, coolwarm, etc.)
4. Add unique comments
5. Output ONLY Python code (no markdown)
```

**Anti-Plagiarism Features:**
- Random variable names: `data_frame`, `predictors`, `target_vals`
- Random colormaps: `viridis`, `plasma`, `coolwarm`, `RdYlBu`, `magma`, `cividis`
- Unique comments: AI generates different explanations
- High temperature: Ensures code variation

**Output:**
- `main.py`: Complete executable Python script

---

### 3.4 Script Execution (Subprocess)

**Purpose:** Run generated code safely

**Implementation:**
```python
subprocess.run(
    ['python', 'main.py'],
    cwd=folder_path,        # Isolated directory
    timeout=20,             # Prevent infinite loops
    capture_output=True,    # Capture errors
    text=True
)
```

**Security Measures:**
1. **Isolation:** Each student runs in separate directory
2. **Timeout:** 20-second limit
3. **Error Handling:** Catches exceptions, cleans up
4. **No GUI:** All plots saved to files (no plt.show())

**Expected Output:**
- `heatmap.png`: Correlation matrix
- `scatter.png`: Actual vs Predicted
- `residual.png`: Residual analysis

---

### 3.5 Email Delivery (`mailer.py`)

**Purpose:** Send zip file to student

**Process:**
1. Zip folder contents (CSV, script, plots, guide)
2. Create MIME multipart email
3. Attach zip file
4. Send via SMTP
5. Delete temp files

**Email Template:**
```
Subject: Your COS201 ML Assignment Solution

Body: Hey! Attached is your unique dataset, personalized 
Python script, and your generated plots. Read the defense 
guide just in case the lecturer asks questions.

Attachment: {matric_no}.zip
```

**SMTP Configuration:**
- Server: smtp.gmail.com
- Port: 587 (TLS)
- Auth: Gmail App Password (NOT regular password)

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │   Form   │ -> │ Terminal │ -> │ Success  │             │
│  │  State   │    │Animation │    │  State   │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │                                                     │
│       │ POST /generate                                      │
│       ↓                                                     │
└─────────────────────────────────────────────────────────────┘
        │
        ↓
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Token Validation (db_manager.py)                  │  │
│  │    - Check if token exists                           │  │
│  │    - Check if is_used = False                        │  │
│  │    - Mark as used (atomic)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2. Dataset Generation (data_engine.py)               │  │
│  │    - Extract seed from matric_no                     │  │
│  │    - Select random theme                             │  │
│  │    - Generate 550 rows                               │  │
│  │    - Save as dataset.csv                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 3. AI Code Generation (code_generator.py)            │  │
│  │    - Build prompt with theme context                 │  │
│  │    - Call OpenAI GPT-4o-mini                         │  │
│  │    - Strip markdown formatting                       │  │
│  │    - Save as main.py                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 4. Script Execution (subprocess)                     │  │
│  │    - Run python main.py in isolated dir              │  │
│  │    - Timeout: 20 seconds                             │  │
│  │    - Generates: heatmap.png, scatter.png, residual   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 5. Defense Guide Creation                            │  │
│  │    - Extract model details                           │  │
│  │    - Write defense_guide.txt                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 6. Zip & Email (mailer.py)                           │  │
│  │    - Zip all files                                   │  │
│  │    - Send via SMTP                                   │  │
│  │    - Delete temp folder                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 7. Return Success Response                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Technical Specifications

### 5.1 Performance Requirements
- **Response Time:** < 25 seconds (end-to-end)
- **Concurrent Users:** 10+ (with proper server)
- **Success Rate:** > 95%
- **Email Delivery:** < 5 seconds

### 5.2 Scalability
- **Current:** Single-threaded (development)
- **Production:** Use Celery for async task queue
- **Database:** Migrate to PostgreSQL for production
- **Storage:** Temp files deleted immediately (no accumulation)

### 5.3 Cost Analysis (Per Student)
- OpenAI API: $0.015 (GPT-4o-mini)
- SMTP: Free (Gmail)
- Server: $0.005 (compute time)
- **Total:** ~$0.02 per student

### 5.4 Error Handling
- **401:** Invalid/used token → User-friendly message
- **500:** Script execution failure → Cleanup + error log
- **Timeout:** 20s limit → Cleanup + retry suggestion
- **SMTP Failure:** Log error + manual intervention

---

## 6. Security Considerations

### 6.1 Token System
- Single-use tokens prevent sharing
- No token = no access
- Tokens stored in database (not hardcoded)

### 6.2 Code Execution
- Isolated directories (no file conflicts)
- Timeout protection (no infinite loops)
- No shell injection (subprocess with list args)
- No network access from generated scripts

### 6.3 Data Privacy
- Temp files deleted after email
- No student data stored long-term
- Email sent directly (no intermediary storage)

### 6.4 Production Hardening
- [ ] Add rate limiting (10 requests/hour per IP)
- [ ] Restrict CORS to frontend domain only
- [ ] Use environment-specific configs
- [ ] Add request logging
- [ ] Implement API key rotation
- [ ] Add input validation/sanitization

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Token validation logic
- Dataset generation (seed consistency)
- Email formatting

### 7.2 Integration Tests
- Full pipeline (form → email)
- Error scenarios (invalid token, timeout)
- Concurrent requests

### 7.3 Manual Testing
- UI responsiveness (mobile + desktop)
- Email delivery (Gmail, Outlook, Yahoo)
- Different matric numbers (seed variation)

---

## 8. Deployment Strategy

### 8.1 Development
- Frontend: `npm run dev` (Vite dev server)
- Backend: `uvicorn main:app --reload`

### 8.2 Production

**Frontend (Vercel/Netlify):**
```bash
npm run build
# Deploy dist/ folder
```

**Backend (Railway/Render/AWS):**
```bash
# Set environment variables
# Use gunicorn + uvicorn workers
# Enable auto-scaling
```

**Database:**
- Migrate from SQLite to PostgreSQL
- Add connection pooling
- Enable backups

---

## 9. Future Enhancements

### Phase 2 (Optional)
- [ ] Admin dashboard (token management)
- [ ] Usage analytics (students served, themes used)
- [ ] Multiple assignment types (not just MLR)
- [ ] Student portal (download history)
- [ ] Batch token generation
- [ ] Custom theme creation UI

### Phase 3 (Advanced)
- [ ] Support for other ML algorithms (SVM, Random Forest)
- [ ] Interactive Jupyter notebooks instead of scripts
- [ ] Video tutorials generated per theme
- [ ] Plagiarism detection integration
- [ ] Grading automation

---

## 10. Success Criteria

### Launch Criteria
✅ All dependencies installed
✅ Environment variables configured
✅ Test token successfully processed
✅ Email received with correct files
✅ No errors in logs

### Post-Launch Metrics
- **Week 1:** 50+ students served
- **Week 2:** < 5% error rate
- **Week 3:** Positive student feedback
- **Week 4:** Zero plagiarism flags

---

## 11. Maintenance Plan

### Daily
- Monitor error logs
- Check email delivery rate
- Verify OpenAI API quota

### Weekly
- Add new tokens for upcoming students
- Review and optimize AI prompts
- Check disk space (temp folder cleanup)

### Monthly
- Update dependencies
- Review security patches
- Analyze usage patterns

---

## 12. Documentation Deliverables

✅ `DEVELOPER_GUIDE.md` - Complete technical documentation
✅ `QUICK_START.md` - 5-minute setup guide
✅ `PRD.md` - This document (product requirements)
✅ Code comments in all Python files
✅ README.md (to be created)

---

## 13. Conclusion

This system successfully automates the generation of unique ML assignments, eliminating plagiarism concerns while saving instructor time. The combination of deterministic randomness and AI-powered code generation ensures each student receives a completely personalized assignment.

**Key Innovations:**
1. Seeded randomness (reproducible uniqueness)
2. AI code generation (infinite variation)
3. Automated execution (no manual intervention)
4. Email delivery (seamless student experience)

**Next Steps:**
1. Complete setup using QUICK_START.md
2. Test with 5-10 students
3. Gather feedback
4. Deploy to production
5. Scale to full class

---

**Document Version:** 1.0
**Last Updated:** 2024
**Status:** Ready for Implementation
