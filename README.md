# 🤖 AI Mentoring Bot (v2.0) - HIMSI Information Systems UNAIR

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://aiogram.dev)
[![Groq AI](https://img.shields.io/badge/LLM-Qwen--27B%20on%20Groq-F55036?style=flat&logo=groq&logoColor=white)](https://groq.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Render](https://img.shields.io/badge/Render-Singapore%20Region-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com)

A production-ready Telegram-based digital assistant designed to facilitate competition mentoring, automated deadline reminders, and an interactive FAQ hub for Information Systems students at Universitas Airlangga.

Version 2.0 represents a complete architectural overhaul—migrating from a monolithic polling script to an asynchronous **FastAPI Webhook backend**, co-locating both server and database in **Singapore (`ap-southeast-1`)** for ultra-low latency, and upgrading the AI Gatekeeper to **`qwen/qwen3.8-27b`**.

---

## 🚀 What's New in Version 2.0?

| Feature / Metric | Version 1.0 (Legacy) | Version 2.0 (Current) | Impact |
| :--- | :--- | :--- | :--- |
| **Backend Architecture** | Standalone Aiogram Script (Long Polling) | **FastAPI + Aiogram 3.x (Webhooks)** | High concurrency, zero dropped updates, RESTful APIs |
| **Server Region** | Koyeb (Frankfurt, Germany) | **Render (Singapore)** | Latency dropped from ~250ms to **~10–30ms** |
| **Database Region** | Supabase (Tokyo, Japan) | **Supabase (Singapore)** | Sub-millisecond database queries co-located with server |
| **AI LLM Model** | Llama 3.1 8B Instant | **Qwen 27B (`qwen/qwen3.8-27b`)** | Richer semantic evaluation & smarter request reasoning |
| **NIM Verification** | Single regex pattern | **Multi-cohort support** (`1872[3-6]xxxx` & `626108112xxx`) | Seamless onboarding for newly formatted 2026 students |
| **Data Sync Engine** | Hard delete (`DELETE ALL`) | **Soft Delete (`is_active` flag)** | Preserves historical mentoring logs when sheets change |
| **Database Resilience**| Default connection pool | **`pool_pre_ping=True` & `pool_recycle`** | Prevents SSL connection drops from idle cloud poolers |

---

## ✨ Key Features

- 🔐 **Dual-Format Student Verification (NIM)**
  Restricts bot access strictly to verified Information Systems students. Supports both historical cohorts (`18723xxxx`–`18726xxxx`, 9 digits) and the new 2026 cohort format (`626108112xxx`, 12 digits).
- 🧠 **AI Gatekeeper (`qwen/qwen3.8-27b` via Groq)**
  Evaluates mentoring proposals dynamically. Ensures students demonstrate at least 50% initial preparation (team readiness, target competition, concept/draft) before granting access to senior mentors.
- ⏰ **Automated Competition Deadline Alerts**
  An asynchronous background job (`APScheduler`) checks for active competitions expiring within 3 days and dispatches proactive notification blasts to all verified students every morning at 08:00 WIB.
- 🔄 **Zero-Code Synchronization via Google Sheets**
  Staff members manage competitions, mentors, and FAQs directly from Google Sheets. Admins can invoke `/sync` or call `/api/sync` to instantly pull fresh data without restarting the server.
- 🛡️ **Soft Delete & Data Preservation**
  Items removed from Google Sheets are deactivated (`is_active = False`) rather than deleted, keeping foreign-key relationships and past consultation audit trails intact.

---

## 🧩 System Architecture

```
                    ┌─────────────────────────┐
                    │    Student (Telegram)   │
                    └────────────┬────────────┘
                                 │ Webhook (HTTPS)
                                 ▼
                    ┌─────────────────────────┐
                    │    FastAPI Web Server   │  ◄── Keep-Alive Ping (13m)
                    │   (Render - Singapore)  │      [cron-job.org]
                    └──────┬───────────┬──────┘
                           │           │
        Mentoring Requests │           │ Data Sync & Reads
                           ▼           ▼
             ┌────────────────┐     ┌─────────────────────────────────┐
             │ Groq Cloud API │     │   Supabase PostgreSQL Pooler    │
             │ Qwen 3.8 (27B) │     │     (Singapore - Port 6543)     │
             └────────────────┘     └────────────────┬────────────────┘
                                                     ▲
                                        Fetch Sheets │ (/sync)
                                    ┌────────────────┴────────────────┐
                                    │    Google Sheets Data Source    │
                                    │      (Service Account API)      │
                                    └─────────────────────────────────┘
```

---

## 💬 Bot Commands

| Command | Role | Description |
| :--- | :---: | :--- |
| `/start` | Public | Initiates NIM verification flow or opens the main interactive menu. |
| `/faq` | Student | Browses dynamic FAQs retrieved from the database. |
| `/list_lomba` | Student | Lists currently active competitions with upcoming deadlines. |
| `/detail_lomba` | Student | Shows detailed descriptions and official registration links. |
| `/req_mentor` | Student | Submits an application for mentor matching evaluated by AI. |
| `/sync` | Admin | Synchronizes Lomba, Mentor, and FAQ records from Google Sheets. |

---

## 🛠️ Tech Stack

* **Language:** Python 3.11
* **Web Framework:** FastAPI, Uvicorn
* **Telegram Framework:** Aiogram 3.x
* **AI Provider:** Groq Cloud (`qwen/qwen3.8-27b`)
* **Database & ORM:** PostgreSQL (Supabase Singapore), SQLAlchemy 2.0+
* **Drivers:** `psycopg2-binary`, `psycopg`
* **Spreadsheet Integration:** `gspread`, `google-auth`
* **Task Scheduling:** APScheduler (AsyncIO)
* **Deployment & Containerization:** Docker, Render (Singapore Web Service)

---

## 📁 Directory Structure

```text
bot-mentoring-si-fastapi/
├── app/
│   ├── bot/
│   │   ├── handlers/          # Modular telegram routers
│   │   │   ├── admin.py       # Admin commands (/sync)
│   │   │   ├── base.py        # /start and NIM verification
│   │   │   ├── faq.py         # FAQ navigation and answers
│   │   │   └── mentoring.py   # AI mentoring request submission
│   │   ├── bot_instance.py    # Bot and Dispatcher initialization
│   │   ├── keyboards.py       # Inline & Reply keyboards
│   │   ├── scheduler.py       # APScheduler deadline check cron
│   │   └── states.py          # Aiogram FSM state classes
│   ├── services/
│   │   ├── ai_service.py      # Groq Qwen 27B client & prompt logic
│   │   └── sheet_service.py   # Google Sheets pull & soft-delete engine
│   ├── config.py              # Pydantic BaseSettings & env sanitizer
│   ├── database.py            # SQLAlchemy engine with pool resilience
│   ├── main.py                # FastAPI lifecycle, webhooks & endpoints
│   └── models.py              # Declarative database tables
├── Dockerfile                 # Container definition for Render
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Protects secrets & database files
└── .dockerignore              # Excludes secrets from Docker builds
```

---

## ⚙️ Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/farhanAkbar91/bot-mentoring-si-fastapi.git
cd bot-mentoring-si-fastapi
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_id
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3.8-27b
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
WEBHOOK_HOST=https://your-domain-or-ngrok-tunnel.com
PORT=8080
API_SYNC_KEY=default_sync_key
```

### 5. Google Sheets Credentials
Either place your `credentials.json` in the root folder, or set the `GOOGLE_CREDS_JSON` environment variable with the minified JSON string.

### 6. Run the Application
```bash
python -m app.main
```

---

## ☁️ Cloud Deployment (Render & Supabase)

1. **Supabase (Singapore Region):**
   * Create a PostgreSQL database located in **Southeast Asia (Singapore - `ap-southeast-1`)**.
   * Retrieve the transaction pooler connection URI on port `6543`.
2. **Render (Singapore Region):**
   * Connect your GitHub repository to a new **Web Service** with the **Docker** runtime.
   * Region: **Singapore**.
   * Set Environment Variables as outlined in `.env.example`. Paste the raw JSON text of your Google credentials into `GOOGLE_CREDS_JSON`.
3. **Keep-Alive Cron:**
   * Configure an HTTP `GET` request every 13 minutes pointing to `https://<your-service>.onrender.com/` on [cron-job.org](https://cron-job.org) to prevent container cold starts.

---

## 👥 Authors & Maintainers

* **Farhan Akbar** - *System Architecture & Development*
* Developed for **HIMA Sistem Informasi (HIMSI) - Universitas Airlangga**.
