# Product Requirements Document (PRD)
## CrewWatch — NASA Space Apps Challenge 2026
**Version:** 1.0 | **Challenge:** Create Health Monitoring Software for Astronauts  
**Status:** APPROVED | **Date:** 2026-11-15

---

## 1. Problem Statement

Astronauts on long-duration missions operate beyond the reach of immediate medical intervention. Ground-based flight surgeons face communication delays, limited visibility, and no structured early-warning system. Small physiological changes — a creeping heart rate, declining oxygen saturation, accumulating radiation dose — can escalate into mission-critical emergencies.

**There is no practical, always-available software that:**
- Continuously watches multiple health indicators simultaneously
- Flags problems early, before they become emergencies
- Tells the crew exactly what to do next
- Maintains an accountable, timestamped record of every health event

---

## 2. Vision

> *"Give every astronaut — and every person far from care — a system that makes their health status visible, their warnings actionable, and every event accountable."*

---

## 3. Target Users

### Primary Users
| User | Context | Need |
|------|---------|------|
| **Crew Member** | Aboard spacecraft, limited medical training | Simple, immediate understanding of own status + clear action |
| **Flight Surgeon** | Earth-based, monitoring 3–6 crew remotely | Early warning, all crew overview, event log access |
| **Mission Controller** | Earth-based, coordinating response | Alert routing, acknowledgement system, report access |

### Secondary Users (Real-World Extension)
- Rural clinic nurses monitoring remote patients
- Disaster response coordinators
- Field research teams in isolated environments

---

## 4. User Stories

### Crew Member
```
As a crew member,
I want to open the app on my phone and immediately see my health status in plain language,
So that I know if I need to take action — without interpreting raw numbers.

As a crew member,
I want to receive specific step-by-step guidance when my status changes,
So that I know exactly what to do without waiting for ground communication.
```

### Flight Surgeon
```
As a flight surgeon,
I want to see all crew members' statuses on a single screen,
So that I can identify who needs attention at a glance.

As a flight surgeon,
I want to receive an immediate alert when any crew member reaches ANOMALY or EMERGENCY,
So that I can intervene before the situation escalates.

As a flight surgeon,
I want to download a mission health report at the end of each day,
So that I have an accountable, timestamped record for medical review.
```

### Mission Controller
```
As a mission controller,
I want to acknowledge alerts so the system knows they've been seen,
So that nothing falls through the cracks during high-pressure situations.
```

---

## 5. Core Feature Requirements

### F-01: Real-Time Vitals Monitoring
- **MUST:** Display 6 vital signs per crew member: Heart Rate, SpO₂, Body Temperature, Radiation Dose, Sleep Hours, Stress Index
- **MUST:** Update every 5 seconds
- **MUST:** Show current value + status indicator per vital

### F-02: 4-Level Status Classification
- **MUST:** Classify each crew member into: NOMINAL → ELEVATED → ANOMALY → EMERGENCY
- **MUST:** Use defined thresholds (see SystemDesign.md)
- **MUST:** Display status in color-coded plain language
- **MUST:** Identify which vital triggered the status change

### F-03: Early Warning Alert System
- **MUST:** Generate alert immediately on any ELEVATED, ANOMALY, or EMERGENCY classification
- **MUST:** Route alert to named responder
- **MUST:** Include specific, actionable guidance text in alert
- **MUST:** Support acknowledgement of alerts
- **SHOULD:** Show unacknowledged alert count in UI

### F-04: Event Logging
- **MUST:** Log every status change with timestamp, trigger, and guidance given
- **MUST:** Log every acknowledgement with timestamp and who acknowledged
- **MUST:** Persist all events in database

### F-05: Automated Mission Health Report
- **MUST:** Generate a report covering: crew status summary, all events, emergency/anomaly count
- **MUST:** Export as downloadable PDF
- **SHOULD:** Report auto-generates every 24 hours
- **COULD:** Include NASA space weather context (DONKI data)

### F-06: NASA Data Integration
- **MUST:** Integrate at least 3 NASA APIs
- **MUST:** Use DONKI data to adjust simulated radiation environment
- **SHOULD:** Display EPIC Earth image on mission dashboard
- **SHOULD:** Display APOD on mission home screen

### F-07: Vitals Simulator
- **MUST:** Generate realistic vitals for 3 crew members continuously
- **MUST:** Support anomaly injection for demo (8 scenarios minimum)
- **SHOULD:** Reflect real NASA space weather in radiation simulation

### F-08: Progressive Web App
- **MUST:** Work on mobile (phone/tablet) and desktop
- **MUST:** Responsive layout
- **SHOULD:** Offline-capable for last-known status

---

## 6. Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| **Performance** | WebSocket latency < 500ms from ingest to client display |
| **Availability** | Demo window: 100% uptime (Render keep-alive via UptimeRobot) |
| **Usability** | Status change understandable in < 3 seconds by any observer |
| **Compatibility** | Chrome, Firefox, Safari — desktop + mobile |
| **Data** | All vitals simulated — no real patient data |

---

## 7. Out of Scope

- Real biometric sensor hardware integration
- Native mobile apps (iOS/Android)
- Multi-language support
- Payment / subscription model
- HIPAA/medical compliance (simulated data only)

---

## 8. Success Metrics (Hackathon Judging)

| Criterion | Target |
|-----------|--------|
| Judge can understand crew status in < 5 seconds | ✅ |
| Live demo: anomaly injection → alert in < 10s | ✅ |
| At least 3 NASA APIs demonstrably integrated | ✅ |
| PDF report downloadable during demo | ✅ |
| Public GitHub repo with working code | ✅ |
| Live URL accessible to judges | ✅ |

---

## 9. Release Plan

| Phase | Deliverables | Target |
|-------|-------------|--------|
| **v0.1 — Foundation** | FastAPI + DB + Auth + Crew CRUD | Day 1 AM |
| **v0.2 — Core Engine** | Simulator + Classification + WebSocket | Day 1 PM |
| **v0.3 — Alerts + NASA** | Alert router + DONKI/EPIC/APOD | Day 2 AM |
| **v1.0 — Demo Ready** | Reports + Render deploy + UptimeRobot | Day 2 PM |
