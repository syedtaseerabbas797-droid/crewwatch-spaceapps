# 07 — Deployment Guide (Render.com)

> **Goal:** Live URL for judges to test → `https://crewwatch-api.onrender.com`

---

## Why Render.com?

| Feature | Render Free Tier |
|---------|-----------------|
| Cost | Free |
| Sleep after inactivity | 15 min (wake up on request) |
| GitHub auto-deploy | ✅ Yes |
| Environment variables | ✅ Yes |
| Custom domain | ✅ Yes |
| PostgreSQL | ✅ Free (90 days) |

> [!TIP]
> Render pe **Neon DB** use karein (alag free PostgreSQL) — Render ka apna PostgreSQL 90 din baad delete ho jata hai.

---

## Step 1: GitHub se Render Connect karo

1. [render.com](https://render.com) par jao → GitHub se sign in
2. **New** → **Web Service**
3. GitHub repo select karo → `crewwatch-backend`
4. Settings:
   - **Name:** `crewwatch-api`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Step 2: Environment Variables Render mein dalo

Render dashboard mein **Environment** tab mein yeh sab add karo:

```
NASA_API_KEY          = 9QDzRJgtGhNrMpkrHBGfFfntJBpgNwkbRRRfqFLr
DATABASE_URL          = (Neon se copy karo)
REDIS_URL             = (Upstash se copy karo)
SECRET_KEY            = crewwatch-prod-secret-key-very-long
ALGORITHM             = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 60
APP_ENV               = production
SIMULATOR_TICK_SECONDS = 5
```

---

## Step 3: Dockerfile (Render ke liye)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> [!NOTE]
> Locally Docker use nahi kar rahe — yeh sirf Render ke liye hai. Render khud build karega.

---

## Step 4: Auto-Deploy

GitHub pe `main` branch mein push karte hi Render automatically:
1. Code pull karta hai
2. `pip install` karta hai
3. `alembic upgrade head` chalata hai (DB tables update)
4. `uvicorn` start karta hai

---

## Deployment Checklist

```
[ ] Neon DB URL .env mein aur Render environment mein
[ ] Upstash Redis URL dono jagah
[ ] NASA API Key dono jagah
[ ] GitHub repo public hai (judges ke liye)
[ ] alembic migrations GitHub mein committed hain
[ ] /health endpoint working hai
[ ] /docs (Swagger) accessible hai
[ ] WebSocket connection test kiya
[ ] Anomaly injection demo test kiya
```

---

## Production URLs (after deploy)

```
API Base:     https://crewwatch-api.onrender.com
Swagger Docs: https://crewwatch-api.onrender.com/docs
Health Check: https://crewwatch-api.onrender.com/health
WebSocket:    wss://crewwatch-api.onrender.com/ws/mission-feed
```

---

## Render Sleep Problem ka Hal

Free tier 15 min inactivity ke baad "sleep" ho jata hai. Judges ke liye:

**Option 1:** Hackathon ke din manually ek request bhejna — tab woh 15 min active rahega.

**Option 2:** UptimeRobot (free) se har 10 min mein health check ping karo:
1. [uptimerobot.com](https://uptimerobot.com) → free account
2. New Monitor → HTTP(s)
3. URL: `https://crewwatch-api.onrender.com/health`
4. Interval: 10 minutes

Yeh backend hamesha awake rakhega demo ke waqt.
