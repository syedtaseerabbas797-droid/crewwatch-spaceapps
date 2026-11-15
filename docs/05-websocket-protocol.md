# 05 — WebSocket Protocol (Frontend Team ke liye)

> [!IMPORTANT]
> Yeh document **Frontend Team** ke liye hai. Backend se real-time data kaisa aayega — exact format yahan hai.

---

## Connection

```
WebSocket URL (Local):       ws://localhost:8000/ws/mission-feed
WebSocket URL (Production):  wss://crewwatch-api.onrender.com/ws/mission-feed
```

**Connect kaise karein (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/mission-feed');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data handle karo
};

ws.onopen = () => console.log('Connected to CrewWatch feed');
ws.onclose = () => console.log('Disconnected — reconnecting...');
```

---

## Message Types

Backend 3 tarah ke messages bhejta hai:

---

### Type 1: `VITALS_UPDATE`
Har 5 second mein aata hai — sab crew ki latest vitals.

```json
{
  "type": "VITALS_UPDATE",
  "timestamp": "2026-11-15T19:00:00Z",
  "crew": [
    {
      "crew_id": "uuid-1",
      "name": "Dr. Sarah Chen",
      "role": "Commander",
      "status": "NOMINAL",
      "status_color": "#22c55e",
      "heart_rate": 72.4,
      "spo2": 97.8,
      "temperature": 36.6,
      "radiation_dose": 42.1,
      "sleep_hours": 7.5,
      "stress_index": 0.28
    },
    {
      "crew_id": "uuid-2",
      "name": "Maj. Alex Odhiambo",
      "role": "Pilot",
      "status": "ELEVATED",
      "status_color": "#eab308",
      "heart_rate": 108.0,
      "spo2": 96.1,
      "temperature": 37.2,
      "radiation_dose": 44.0,
      "sleep_hours": 6.2,
      "stress_index": 0.52
    }
  ]
}
```

---

### Type 2: `ALERT`
Jab kisi crew member ka status change ho ya ANOMALY/EMERGENCY ho.

```json
{
  "type": "ALERT",
  "timestamp": "2026-11-15T19:05:33Z",
  "alert_id": "uuid-alert",
  "crew_id": "uuid-2",
  "crew_name": "Maj. Alex Odhiambo",
  "from_status": "ELEVATED",
  "to_status": "EMERGENCY",
  "triggered_by": "radiation_dose",
  "triggered_value": 520.0,
  "threshold_exceeded": 500.0,
  "guidance_text": "RADIATION ALERT: Seek shielded area immediately. Mission control has been notified.",
  "responder_name": "Dr. James Liu",
  "severity": "critical",
  "action_required": true
}
```

---

### Type 3: `ALERT_ACKNOWLEDGED`
Jab koi alert acknowledge kare.

```json
{
  "type": "ALERT_ACKNOWLEDGED",
  "timestamp": "2026-11-15T19:06:10Z",
  "alert_id": "uuid-alert",
  "crew_id": "uuid-2",
  "crew_name": "Maj. Alex Odhiambo",
  "acknowledged_by": "Dr. James Liu",
  "new_status": "ANOMALY"
}
```

---

## Status Colors Reference

| Status | Color Hex | Tailwind Class |
|--------|-----------|----------------|
| NOMINAL | `#22c55e` | `text-green-500` |
| ELEVATED | `#eab308` | `text-yellow-500` |
| ANOMALY | `#f97316` | `text-orange-500` |
| EMERGENCY | `#ef4444` | `text-red-500` |

---

## Frontend ko kya dikhana hai

### Crew Card (Har crew member ka card)
```
┌─────────────────────────────┐
│ 🟢 NOMINAL                  │
│ Dr. Sarah Chen              │
│ Commander                   │
│                             │
│ ❤️  72 bpm                  │
│ 🫁  97.8% SpO₂              │
│ 🌡️  36.6°C                  │
│ ☢️  42 μSv/hr               │
│ 😰  Stress: Low             │
│ 💤  Sleep: 7.5 hrs          │
└─────────────────────────────┘
```

### Alert Banner (EMERGENCY pe)
```
┌─────────────────────────────────────────────────────┐
│ 🔴 EMERGENCY — Maj. Alex Odhiambo                   │
│ Radiation: 520 μSv/hr (threshold: 500)              │
│                                                     │
│ "RADIATION ALERT: Seek shielded area immediately."  │
│                                                     │
│ Responder: Dr. James Liu                            │
│                            [ACKNOWLEDGE]            │
└─────────────────────────────────────────────────────┘
```

---

## Reconnection Logic (Frontend mein implement karo)

```javascript
function connectWebSocket() {
  const ws = new WebSocket('wss://crewwatch-api.onrender.com/ws/mission-feed');
  
  ws.onclose = () => {
    // 3 second baad reconnect karo
    setTimeout(connectWebSocket, 3000);
  };
  
  return ws;
}
```
