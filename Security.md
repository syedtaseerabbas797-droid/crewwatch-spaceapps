# Security Document
## CrewWatch — NASA Space Apps Challenge 2026
**Version:** 1.0 | **Date:** 2026-11-15

> [!NOTE]
> CrewWatch is a **hackathon prototype** using **100% simulated data**. No real patient data, no real credentials beyond the team's API keys. Security measures are proportionate to that context — robust enough to be credible to judges, not over-engineered.

---

## 1. Threat Model

| Asset | Threat | Likelihood (Hackathon) | Mitigation |
|-------|--------|----------------------|------------|
| NASA API Key | Exposed in code/GitHub | HIGH if careless | `.env` + `.gitignore` |
| JWT tokens | Forged tokens | LOW | HS256 + strong secret |
| Neon DB | Direct public access | LOW (Neon firewall) | SSL + no public IP |
| Upstash Redis | Unauthorized reads | LOW (token auth) | REST token in .env |
| Simulated data | Leakage | ZERO risk | Not real data |
| Render URL | DDoS / spam | LOW | Rate limiting |

---

## 2. Authentication & Authorization

### JWT Implementation

```python
# Token structure
{
  "sub": "user_id",          # UUID of crew member or staff
  "role": "mission_control", # crew | mission_control | admin
  "name": "Dr. James Liu",
  "exp": 1234567890          # expiry timestamp
}

# Secret: stored only in .env → never hardcoded
SECRET_KEY = settings.SECRET_KEY  # min 32 chars
ALGORITHM = "HS256"
```

### Role Permissions Matrix

| Endpoint | `crew` | `mission_control` | `admin` |
|----------|--------|-------------------|---------|
| `GET /api/crew/{own_id}` | ✅ | ✅ | ✅ |
| `GET /api/crew` (all) | ❌ | ✅ | ✅ |
| `GET /api/vitals/live` | ❌ | ✅ | ✅ |
| `GET /api/crew/{id}/vitals` | own only | ✅ | ✅ |
| `GET /api/alerts` | ❌ | ✅ | ✅ |
| `POST /api/alerts/{id}/acknowledge` | ❌ | ✅ | ✅ |
| `GET /api/reports` | ❌ | ✅ | ✅ |
| `POST /api/simulator/inject` | ❌ | ❌ | ✅ |
| `POST /api/simulator/start` | ❌ | ❌ | ✅ |
| `GET /api/nasa/*` | ✅ | ✅ | ✅ |
| `GET /health` | ✅ (public) | ✅ | ✅ |

---

## 3. Secret Management

### What goes in `.env` (NEVER in code or GitHub)

```env
# High sensitivity — treat like passwords
NASA_API_KEY=...            # api.nasa.gov key
DATABASE_URL=...            # Neon connection string (has credentials)
REDIS_URL=...               # Upstash URL (has auth token)
SECRET_KEY=...              # JWT signing secret
```

### `.gitignore` — MUST include

```gitignore
# Environment files — NEVER commit
.env
.env.local
.env.production
*.env

# Python
__pycache__/
*.pyc
venv/
.venv/

# Reports (may contain sensitive sim data)
/tmp/reports/
*.pdf

# IDE
.vscode/
.idea/
```

> [!CAUTION]
> Run `git status` before every commit. If `.env` appears as "new file" — STOP. Add it to `.gitignore` immediately. Never push API keys to GitHub — even in a private repo, treat them as compromised.

---

## 4. API Security

### 4.1 Input Validation
All request bodies validated by Pydantic v2:
```python
class VitalsIngest(BaseModel):
    heart_rate: float = Field(ge=0, le=300)       # 0–300 bpm max
    spo2: float = Field(ge=0, le=100)              # 0–100%
    temperature: float = Field(ge=30, le=50)       # physiological range
    radiation_dose: float = Field(ge=0, le=10000)  # reasonable max
    stress_index: float = Field(ge=0.0, le=1.0)   # normalized
```
Invalid values → `422 Unprocessable Entity` — never reaches DB.

### 4.2 SQL Injection Prevention
Using SQLAlchemy ORM — all queries are parameterized automatically.
```python
# SAFE — ORM handles parameterization
result = await session.execute(
    select(CrewMember).where(CrewMember.id == crew_id)
)
# NEVER use raw string concatenation in queries
```

### 4.3 CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Hackathon: allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Production: restrict to known frontend domains only
```

### 4.4 Rate Limiting (Basic)
```python
# Simple in-memory rate limiter for NASA proxy routes
# Prevents frontend from burning through 1000 req/hr limit
# Max 1 request per 30 seconds per NASA endpoint per client IP
```

---

## 5. Database Security

### Neon.tech Security Features (Automatic)
- ✅ **TLS/SSL enforced** on all connections (`?ssl=require` in URL)
- ✅ **No public IP** — connections only via Neon proxy
- ✅ **Automatic backups** — Neon handles this
- ✅ **Credentials isolated** — each project has separate DB user

### Application-Level
```python
# Always use parameterized queries via ORM
# Never log DATABASE_URL (contains credentials)
# Connection string in .env only — not in Dockerfile or render.yaml
```

---

## 6. Data Privacy

| Data Type | Sensitivity | Storage | Retention |
|-----------|------------|---------|-----------|
| Simulated vitals | None (not real) | Neon DB | Demo window only |
| Crew names (fictional) | None | Neon DB | Demo window only |
| NASA API key | HIGH | `.env` only | Rotate after hackathon |
| JWT tokens | Medium | Client memory | 60 min expiry |
| PDF reports | None (simulated) | /tmp | Deleted on restart |

> [!IMPORTANT]
> After the hackathon, **rotate the NASA API key** at api.nasa.gov — it was shared in this planning document. Generate a new one and update `.env`.

---

## 7. Render.com Security

### Environment Variables
- Set all secrets in Render dashboard → **Environment** tab
- Never set them in `Dockerfile` or `render.yaml`
- Render encrypts env vars at rest

### HTTPS
- Render provides free TLS certificate automatically
- All traffic is HTTPS — no configuration needed
- WebSocket automatically becomes WSS on Render

---

## 8. Pre-Demo Security Checklist

```
[ ] .env is in .gitignore and NOT committed to GitHub
[ ] GitHub repo scanned: no API keys visible in any file
[ ] NASA_API_KEY in Render dashboard environment variables
[ ] DATABASE_URL in Render dashboard (not in any file)
[ ] REDIS_URL in Render dashboard (not in any file)
[ ] SECRET_KEY is at least 32 characters
[ ] JWT token expiry set to 60 minutes
[ ] /api/simulator/inject requires admin role
[ ] Health endpoint returns no sensitive config data
[ ] Neon: confirm SSL=require in connection string
```

---

## 9. Post-Hackathon Actions

```
1. Rotate NASA API Key  → api.nasa.gov → My Account → Regenerate
2. Rotate Neon DB password → Neon dashboard
3. Rotate Upstash token → Upstash dashboard
4. Archive GitHub repo (make private or delete)
5. Delete Neon project (or let it auto-suspend)
6. Remove Render service
```
