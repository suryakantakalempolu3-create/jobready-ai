# JobReady AI — Resume Builder & Interview Preparation Platform

Flask + **MySQL** (Flask-SQLAlchemy / PyMySQL) + vanilla HTML/CSS/JS, with an LLM (Anthropic Claude) for resume analysis and interview coaching.
Every AI feature has an **offline fallback**, so the whole app works even before you add an API key.

## Features
| Feature | Where |
|---|---|
| Signup / login (salted password hashes, CSRF protection, sessions) | `/register`, `/login` |
| Dashboard: resume score, interview performance, skills progress, career recommendations | `/dashboard` |
| Resume builder (education, skills, experience, projects, certifications), live preview, **PDF download**, AI summary + bullet rewriting | `/resume` |
| Resume analyzer: upload PDF → ATS score, breakdown, missing skills, improvements | `/analyzer` |
| Interview prep: technical / HR questions by role with sample answers | `/prep` |
| Mock interview: one question at a time, scored feedback per answer, final score | `/mock` |
| Job recommendations ranked by skills, target role and degree; save jobs | `/jobs` |
| Profile (skills + target role drive recommendations) | `/profile` |

## Folder structure
```
jobready-ai/
├── run.py                 # start the server
├── seed.py                # load demo account + sample jobs into MySQL
├── schema.sql             # MySQL database + all 10 tables
├── config.py              # settings read from .env (MySQL connection URL)
├── requirements.txt
├── .env.example           # copy to .env
├── app/
│   ├── __init__.py        # app factory, MySQL connection, CSRF, error handlers
│   ├── models.py          # SQLAlchemy models (mirror schema.sql)
│   ├── auth.py            # register / login / profile API
│   ├── pages.py           # HTML page routes
│   ├── resume.py          # resume CRUD, AI improve, PDF download
│   ├── analyzer.py        # PDF upload + ATS analysis
│   ├── interview.py       # prep questions + mock interview API
│   ├── jobs.py            # job matching + save
│   ├── dashboard.py       # aggregated dashboard data
│   ├── seed_data.py       # sample jobs + demo user
│   ├── utils.py
│   ├── services/          # ai.py, scoring.py, questions.py, pdfgen.py
│   ├── templates/         # Jinja HTML pages
│   └── static/css, js     # style.css + one JS file per page
└── tests/test_app.py      # end-to-end tests against a real MySQL test database
```

## Database design (MySQL 8.0+, InnoDB, utf8mb4)
```
users ──1:1── student_profiles
  │──1:1── resumes ──1:N── resume_analysis (resume_id optional)
  │──1:N── resume_analysis
  │──1:N── interviews ──1:N── interview_questions ──1:1── interview_feedback
  │──1:N── job_recommendations ──N:1── jobs
  └──1:N── student_progress
```
| Table | Purpose |
|---|---|
| `users` | name, unique email, **password_hash** (salted scrypt hash, never plain text) |
| `student_profiles` | phone, location, college, degree, target role, headline, skills (JSON) |
| `resumes` | the resume built in the Resume Builder (JSON data) |
| `resume_analysis` | every ATS analysis: score, breakdown, skills found/missing, strengths, improvements |
| `interviews` | mock interview sessions: role, type, status, average score |
| `interview_questions` | the questions of each interview, in order, with sample answers |
| `interview_feedback` | the student's answer + score and feedback for each question |
| `jobs` | job listings (sample data) |
| `job_recommendations` | match % and matched/missing skills per student and job, plus the "saved" flag |
| `student_progress` | timeline of resume scores, interview scores and resume completeness (dashboard charts) |

All child tables use foreign keys with `ON DELETE CASCADE` (deleting a user removes all of their data;
deleting a resume only clears `resume_analysis.resume_id`).

## 1. Install
Requires **Python 3.10+** and **MySQL 8.0+** (MariaDB 10.5+ also works).

```bash
cd jobready-ai
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

## 2. Create the MySQL database
Start your MySQL server, then run the schema (creates the `jobready_ai` database and all tables; safe to re-run):

```bash
mysql -u root -p < schema.sql
```

Create a dedicated user for the app (recommended instead of using root). In the MySQL shell (`mysql -u root -p`):

```sql
CREATE USER 'jobready'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON jobready_ai.* TO 'jobready'@'localhost';
-- only needed if you want to run the tests (they use a separate database, jobready_ai_test):
GRANT ALL PRIVILEGES ON jobready_ai_test.* TO 'jobready'@'localhost';
FLUSH PRIVILEGES;
```

> Prefer a GUI? Open `schema.sql` in MySQL Workbench / phpMyAdmin and run it.
> No command line access? Skip `schema.sql`: with `AUTO_CREATE_TABLES=1` the app creates the tables itself, but you must still create the empty database: `CREATE DATABASE jobready_ai CHARACTER SET utf8mb4;`

## 3. Configure `.env`
| Variable | Meaning |
|---|---|
| `SECRET_KEY` | Long random string. Generate: `python -c "import secrets;print(secrets.token_hex(32))"` |
| `DB_HOST`, `DB_PORT` | MySQL server (default `localhost`, `3306`) |
| `DB_USER`, `DB_PASSWORD` | The MySQL user/password from step 2 |
| `DB_NAME` | `jobready_ai` |
| `AUTO_CREATE_TABLES` | `1` = create missing tables on start (no effect if `schema.sql` was already run). `0` = never touch the schema |
| `ANTHROPIC_API_KEY` | **Your own key** from https://console.anthropic.com/ → API Keys. Leave empty for offline mode |
| `ANTHROPIC_MODEL` | Model name (default `claude-sonnet-5-5`; change if your account uses another) |

No API key is included. Without one, the app shows an **“Offline mode”** badge and uses built-in question banks and rule-based scoring.
With a key you get **“AI online”**: the LLM generates questions, evaluates answers and reviews resumes.
To use another LLM provider, only `complete_json()` in `app/services/ai.py` needs changing.

## 4. Run
```bash
python seed.py          # optional: demo account + 16 sample jobs (jobs also auto-seed on first start)
python run.py           # open http://127.0.0.1:5000
```
**Demo login:** `demo@jobready.ai` / `Demo@1234` (pre-filled resume, score history and interview history).
`python seed.py --reset` empties all tables first.

## 5. Run the tests
```bash
python -m pytest -q
```
The tests connect with your `.env` settings, drop/recreate a separate database `jobready_ai_test` **from `schema.sql`**
(so they also prove the schema works) and cover registration, login/CSRF, resume save + PDF, analyzer, prep, mock interview,
jobs, dashboard and cascading deletes. They never touch your `jobready_ai` data. Change the name with `TEST_DB_NAME`.

## Troubleshooting
| Problem | Fix |
|---|---|
| `Could not connect to MySQL` | Server not running, or wrong `DB_HOST/PORT/USER/PASSWORD` in `.env` |
| `Unknown database 'jobready_ai'` | Run `mysql -u root -p < schema.sql` (step 2) |
| `Access denied for user` | Re-check the `CREATE USER` / `GRANT` statements and the password in `.env` |
| `cryptography package is required` | `pip install -r requirements.txt` (needed for MySQL 8 logins) |
| Special characters in the password | Fine — the connection URL is escaped automatically |

## Security notes
- Passwords hashed with Werkzeug (salted scrypt); the session is reset on login.
- All database access goes through SQLAlchemy with bound parameters (no string-built SQL → no SQL injection).
- CSRF token required on every state-changing `/api/*` request.
- Inputs validated and length-limited server-side; uploads limited to 5 MB and verified as real PDFs.
- Resume/answer text is passed to the LLM as clearly delimited, untrusted data (prompt-injection mitigation).
- Users can only read their own interviews, resumes and analyses.
- For production: strong `SECRET_KEY`, HTTPS, `SESSION_COOKIE_SECURE=True`, run with gunicorn (`gunicorn run:app`), never commit `.env`.

## Notes
- Job listings are **sample data**; “Apply” opens a live LinkedIn search for that job title and city.
- Scanned (image-only) PDFs can't be analyzed; export a text-based PDF from Word/Google Docs.
