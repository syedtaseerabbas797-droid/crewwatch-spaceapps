# 01 — Environment Setup (No Docker Required)

> [!IMPORTANT]
> Docker ki zaroorat NAHI hai. Database aur Redis dono cloud pe hain (Neon + Upstash — free tier).

---

## Step 1: Python Environment

```bash
# Python 3.11+ required
python --version

# Virtual environment banao
cd d:\Nasa_2026\backend
python -m venv venv

# Activate karo (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Neon.tech (Free Cloud PostgreSQL)

1. **https://neon.tech** par jao → "Sign Up" (GitHub se sign in karo)
2. "New Project" banao → Name: `crewwatch`
3. Region: **AWS us-east-1** (ya jo bhi nearest ho)
4. Project banane ke baad **Connection String** copy karo — kuch aisa dikhega:
   ```
   postgresql://crewwatch_user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
5. Yeh string `.env` mein `DATABASE_URL` mein paste karo

> [!TIP]
> Neon free tier mein 0.5 GB storage + automatic suspend (cost zero when idle) — hackathon ke liye perfect hai.

---

## Step 3: Upstash (Free Cloud Redis)

1. **https://upstash.com** par jao → "Sign Up" (GitHub se)
2. "Create Database" → Name: `crewwatch-redis`
3. Region: **US-East-1**
4. **REST URL** aur **REST Token** copy karo
5. `.env` mein `UPSTASH_REDIS_REST_URL` aur `UPSTASH_REDIS_REST_TOKEN` mein paste karo

> [!NOTE]
> Upstash mein standard Redis URL bhi milta hai (`rediss://...`) — woh `REDIS_URL` mein daal dena.

---

## Step 4: Environment File

```bash
# .env.example ko copy karo
cp .env.example .env
```

`.env` file mein yeh fill karo:
```env
# App Settings
APP_ENV=development
SECRET_KEY=crewwatch-super-secret-jwt-key-change-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# NASA APIs (REQUIRED)
NASA_API_KEY=9QDzRJgtGhNrMpkrHBGfFfntJBpgNwkbRRRfqFLr

# Database (Neon.tech se copy karo)
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?ssl=require

# Redis (Upstash se copy karo)
REDIS_URL=rediss://default:token@hostname:6379

# Simulator Settings
SIMULATOR_TICK_SECONDS=5
DEMO_MODE=false
```

---

## Step 5: Database Migration (Tables banana)

```bash
# Alembic se tables create karo
cd backend
alembic upgrade head
```

Yeh automatically saari tables bana dega Neon database mein.

---

## Step 6: Run the Backend

```bash
# Development server
uvicorn app.main:app --reload --port 8000

# Check karo:
# API Docs:    http://localhost:8000/docs
# Health:      http://localhost:8000/health
# WebSocket:   ws://localhost:8000/ws/mission-feed
```

---

## Required Python Packages (`requirements.txt`)

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pydantic==2.10.0
pydantic-settings==2.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.28.0
redis==5.2.0
python-multipart==0.0.12
reportlab==4.2.5
jinja2==3.1.4
numpy==2.2.0
python-dotenv==1.0.1
websockets==14.1
```

---

## Folder Structure (Backend)

```
backend/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings from .env
│   ├── database.py             # Neon DB connection
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── crew.py
│   │   │   ├── vitals.py
│   │   │   ├── alerts.py
│   │   │   ├── reports.py
│   │   │   ├── nasa.py
│   │   │   └── websocket.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── classification.py   # THE BRAIN — vital sign classifier
│   │   ├── alert_router.py     # Alert dispatch + guidance text
│   │   ├── simulator.py        # Vitals data simulator
│   │   └── report_generator.py # PDF report builder
│   │
│   ├── integrations/
│   │   ├── nasa_client.py      # DONKI, EPIC, APOD clients
│   │   └── redis_client.py     # Upstash Redis client
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic schemas
│   └── tasks/                  # Background tasks
│
├── alembic/                    # DB migrations
├── tests/
├── .env
├── .env.example
├── requirements.txt
└── Dockerfile                  # For Render deployment only
```
