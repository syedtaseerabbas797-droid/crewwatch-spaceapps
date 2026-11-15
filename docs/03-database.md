# 03 — Database Schema (PostgreSQL on Neon.tech)

## Database: Should we use it?

**HAAN, zaroor use karni hai.** Yeh cheezain bina DB ke possible nahi:
- Vitals history store karna (report ke liye)
- Health events log karna (kab kya hua)
- Alert acknowledgement track karna
- Mission report generate karna

**Neon.tech** perfect hai — free, cloud, no Docker, hackathon-ready.

---

## Neon Setup Steps

1. [neon.tech](https://neon.tech) par jao → GitHub se sign in
2. **New Project** → Name: `crewwatch` → Create
3. **Connection Details** tab mein connection string copy karo
4. `backend/.env` mein `DATABASE_URL` mein paste karo

---

## Tables (4 total)

---

### Table 1: `crew_members`
Har astronaut ka record.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique ID |
| `name` | VARCHAR(100) | Astronaut ka naam |
| `role` | VARCHAR(50) | Commander / Pilot / Mission Specialist |
| `responder_name` | VARCHAR(100) | Jis insaan ko alert jayega |
| `created_at` | TIMESTAMP | Record banane ka waqt |

**Sample Data:**
```
id: "a1b2c3..."  name: "Dr. Sarah Chen"   role: "Commander"      responder: "Dr. James Liu"
id: "d4e5f6..."  name: "Maj. Alex Odhiambo" role: "Pilot"        responder: "Dr. James Liu"
id: "g7h8i9..."  name: "Dr. Priya Sharma"  role: "Mission Spec."  responder: "Dr. James Liu"
```

---

### Table 2: `vitals_readings`
Har 5 second ka vitals snapshot.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto ID |
| `crew_member_id` | UUID (FK) | Kaun sa crew member |
| `timestamp` | TIMESTAMP | Kab liya gaya |
| `heart_rate` | FLOAT | BPM (beats per minute) |
| `spo2` | FLOAT | % oxygen saturation |
| `temperature` | FLOAT | Body temp °C |
| `radiation_dose` | FLOAT | μSv/hr |
| `sleep_hours` | FLOAT | Last sleep duration |
| `stress_index` | FLOAT | 0.0 to 1.0 |
| `status` | VARCHAR(20) | NOMINAL/ELEVATED/ANOMALY/EMERGENCY |
| `triggered_by` | VARCHAR(50) | Kaun sa vital ne status change kiya |

> [!NOTE]
> Yeh table sabse zyada grow karegi — har crew member ka har 5 second ka data. Neon free tier (0.5 GB) mein 72 hours ke data ke liye kaafi hai.

---

### Table 3: `health_events`
Status change hone par ya alert fire hone par ek event log hota hai.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto ID |
| `crew_member_id` | UUID (FK) | Kaun sa crew member |
| `event_type` | VARCHAR(30) | STATUS_CHANGE / ALERT_SENT / RECOVERY / ACKNOWLEDGED |
| `from_status` | VARCHAR(20) | Pehle kya tha |
| `to_status` | VARCHAR(20) | Ab kya hai |
| `triggered_by` | VARCHAR(50) | Kaun sa vital |
| `guidance_text` | TEXT | Exact instructions jo crew ko dikhaye |
| `responder_name` | VARCHAR(100) | Jise alert gaya |
| `acknowledged` | BOOLEAN | Kya acknowledge kiya gaya? |
| `acknowledged_by` | VARCHAR(100) | Kisne acknowledge kiya |
| `acknowledged_at` | TIMESTAMP | Kab acknowledge kiya |
| `created_at` | TIMESTAMP | Event kab hua |

---

### Table 4: `mission_reports`
Auto-generated PDF reports.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto ID |
| `generated_at` | TIMESTAMP | Kab generate hua |
| `mission_day` | INTEGER | Mission ka kaunsa din |
| `total_events` | INTEGER | Is period mein kitne events hue |
| `emergency_count` | INTEGER | Kitni emergencies |
| `anomaly_count` | INTEGER | Kitni anomalies |
| `summary_text` | TEXT | Auto-written summary |
| `pdf_filename` | VARCHAR(255) | PDF file ka naam |
| `report_data` | JSONB | Full report ka structured data |

---

## Relationships Diagram

```
crew_members (1)
    │
    ├──── vitals_readings (many)   → ek crew member ke hazaaron readings
    │
    ├──── health_events (many)     → ek crew member ke events log
    │
mission_reports → independent table, aggregate data
```

---

## Migration Commands

```bash
# Tables create karo (Neon mein)
alembic upgrade head

# Seed data daal do (3 crew members banao)
python -m app.scripts.seed_data

# Check karo
alembic current
```
