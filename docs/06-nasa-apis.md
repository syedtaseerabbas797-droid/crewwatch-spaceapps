# 06 — NASA API Integrations

> [!IMPORTANT]
> NASA Space Apps Challenge mein **NASA open data ka use MANDATORY** hai judges ke liye.

---

## API Key Setup

```env
NASA_API_KEY=9QDzRJgtGhNrMpkrHBGfFfntJBpgNwkbRRRfqFLr
```

**Rate Limits:**
- Personal key: **1,000 requests/hour**
- DEMO_KEY (avoid karo): 30 requests/hour

---

## APIs We Use

---

### 1. DONKI — Space Weather (Sabse Important!)
**URL:** `https://api.nasa.gov/DONKI/`

**Kyun use karte hain:**
Real NASA solar flare + radiation storm data → humara simulator is data ko use karke radiation levels adjust karta hai. Yeh sabse strong NASA integration hai.

**Endpoints:**
| Endpoint | Kya milta hai |
|----------|--------------|
| `/FLR` | Solar Flares list |
| `/CME` | Coronal Mass Ejections |
| `/GST` | Geomagnetic Storms |
| `/SEP` | Solar Energetic Particles (radiation) |

**Sample Request:**
```
GET https://api.nasa.gov/DONKI/FLR?startDate=2026-11-14&endDate=2026-11-15&api_key=YOUR_KEY
```

**Sample Response:**
```json
[
  {
    "flrID": "2026-11-15T12:00:00-FLR-001",
    "classType": "M2.5",
    "peakTime": "2026-11-15T14:30:00Z",
    "sourceLocation": "N15W30"
  }
]
```

**CrewWatch mein kaise use hoga:**
```
M-class flare  → radiation simulator +40%
X-class flare  → radiation simulator +150% (EMERGENCY territory)
Quiet sun      → radiation simulator baseline
```

---

### 2. EPIC — Earth Polychromatic Imaging Camera
**URL:** `https://api.nasa.gov/EPIC/`

**Kyun use karte hain:**
DSCOVR satellite se Earth ki full-disk daily images. Mission dashboard pe dikhayenge — crew Earth ko dekhti hai, emotional connection + morale.

**Endpoints:**
| Endpoint | Kya milta hai |
|----------|--------------|
| `/api/natural` | Latest natural color images list |
| `/api/natural/date/YYYY-MM-DD` | Specific date ki images |

**Image URL Format:**
```
https://epic.gsfc.nasa.gov/archive/natural/{YYYY}/{MM}/{DD}/png/{image_name}.png
```

**Sample Request:**
```
GET https://api.nasa.gov/EPIC/api/natural?api_key=YOUR_KEY
```

---

### 3. APOD — Astronomy Picture of the Day
**URL:** `https://api.nasa.gov/planetary/apod`

**Kyun use karte hain:**
Mission home screen pe daily space image + description. Crew ko connected rakhta hai cosmos ke saath. Judges ke liye bhi visually impressive.

**Sample Request:**
```
GET https://api.nasa.gov/planetary/apod?api_key=YOUR_KEY
```

**Sample Response:**
```json
{
  "title": "Nebula NGC 604",
  "explanation": "...",
  "url": "https://apod.nasa.gov/apod/image/...",
  "hdurl": "https://apod.nasa.gov/...",
  "media_type": "image",
  "date": "2026-11-15"
}
```

---

### 4. NeoWs — Near Earth Object Web Service
**URL:** `https://api.nasa.gov/neo/rest/v1/`

**Kyun use karte hain:**
Near-Earth asteroid data → space environment risk indicator. Dashboard pe "Space Environment" section mein dikhayenge.

**Sample Request:**
```
GET https://api.nasa.gov/neo/rest/v1/feed?start_date=2026-11-15&end_date=2026-11-15&api_key=YOUR_KEY
```

---

## Caching Strategy (Important!)

NASA APIs pe har second call nahi karna — rate limit hit ho jayegi.

| API | Cache Duration | Reason |
|-----|---------------|--------|
| DONKI | 15 minutes | Solar events frequently nahi badalte |
| EPIC | 1 hour | Daily images hain |
| APOD | 24 hours | Roz ek hi image |
| NeoWs | 1 hour | Asteroid data slow-moving |

Redis mein cache karenge:
```
redis.set("nasa:donki:latest", json_data, ex=900)   # 15 min
redis.set("nasa:epic:latest", json_data, ex=3600)   # 1 hour
redis.set("nasa:apod:today", json_data, ex=86400)   # 24 hours
```

---

## NASA Data → Simulator Integration

Yeh CrewWatch ki **unique selling point** hai judges ke liye:

```
Real NASA Data (DONKI)  →  CrewWatch Simulator
─────────────────────────────────────────────
No flares detected     →  radiation: 20-50 μSv/hr (normal)
C-class flare          →  radiation: 50-100 μSv/hr (ELEVATED)
M-class flare          →  radiation: 100-300 μSv/hr (ANOMALY)
X-class flare          →  radiation: 300-600 μSv/hr (EMERGENCY)
```

**Story for judges:**
> "When NASA detects a real solar flare, CrewWatch automatically adjusts the simulated radiation environment, triggering real alerts for the crew — exactly as it would on a real mission."
