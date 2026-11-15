from typing import Optional

GUIDANCE_TEMPLATES: dict[tuple[str, str], str] = {
    ("heart_rate", "EMERGENCY"): (
        "⚠️ CARDIAC EMERGENCY: Lie flat immediately, stop all physical activity. "
        "{responder} has been alerted. Administer emergency cardiac protocol. "
        "Do not exert yourself — await medical guidance."
    ),
    ("heart_rate", "ANOMALY"): (
        "Heart rate significantly elevated. Rest immediately, take 10 slow deep breaths. "
        "Notify {responder} if no improvement in 5 minutes."
    ),
    ("heart_rate", "ELEVATED"): (
        "Heart rate trending above normal. Reduce activity level, rest for 10 minutes. "
        "{responder} is monitoring your status."
    ),
    ("spo2", "EMERGENCY"): (
        "⚠️ OXYGEN EMERGENCY: Activate supplemental O₂ system immediately. "
        "Alert {responder} NOW. Check suit integrity and airlock seals. "
        "Do NOT remove helmet in compromised environment."
    ),
    ("spo2", "ANOMALY"): (
        "Oxygen saturation critically low. Activate supplemental O₂. "
        "Alert {responder} immediately. Check environmental systems."
    ),
    ("spo2", "ELEVATED"): (
        "SpO₂ slightly below optimal. Monitor closely, ensure proper breathing technique. "
        "{responder} has been notified."
    ),
    ("temperature", "EMERGENCY"): (
        "⚠️ TEMPERATURE EMERGENCY: Extreme body temperature detected. "
        "Seek thermal regulation system immediately. {responder} alerted. "
        "Administer antipyretic if fever — cooling protocol if hypothermia."
    ),
    ("temperature", "ANOMALY"): (
        "Body temperature significantly elevated. Increase hydration, rest in cooled area. "
        "Administer antipyretic. {responder} has been notified."
    ),
    ("temperature", "ELEVATED"): (
        "Temperature trending above normal. Increase fluid intake, reduce physical load. "
        "{responder} is aware."
    ),
    ("radiation_dose", "EMERGENCY"): (
        "⚠️ RADIATION EMERGENCY: SEEK SHIELDED COMPARTMENT IMMEDIATELY. "
        "Move to central module shielded area. {responder} and mission control ALERTED. "
        "Do NOT return to exposed area until all-clear given."
    ),
    ("radiation_dose", "ANOMALY"): (
        "Radiation levels critically elevated — possible solar storm. "
        "Move to shielded area. Alert {responder}. Minimize EVA exposure."
    ),
    ("radiation_dose", "ELEVATED"): (
        "Radiation dose above baseline — monitoring solar weather. "
        "Limit time in poorly shielded areas. {responder} notified."
    ),
    ("stress_index", "EMERGENCY"): (
        "⚠️ CRITICAL STRESS LEVELS: Psychological emergency protocol initiated. "
        "Remove from high-demand tasks immediately. {responder} alerted. "
        "Initiate crew support protocol."
    ),
    ("stress_index", "ANOMALY"): (
        "Stress markers critically elevated. Mandatory rest period required. "
        "Alert {responder}. Reduce task load — crew wellbeing takes priority."
    ),
    ("stress_index", "ELEVATED"): (
        "Stress markers elevated. Recommended: 5-minute breathing exercise. "
        "{responder} monitoring your wellbeing."
    ),
    ("sleep_hours", "EMERGENCY"): (
        "⚠️ CRITICAL SLEEP DEPRIVATION: Cognitive impairment risk HIGH. "
        "Mandatory immediate rest cycle. {responder} alerted. "
        "No critical operations until minimum 6 hours rest achieved."
    ),
    ("sleep_hours", "ANOMALY"): (
        "Severe sleep deficit detected. Schedule rest immediately. "
        "{responder} reviewing duty schedule. Cognitive performance may be impaired."
    ),
    ("sleep_hours", "ELEVATED"): (
        "Sleep hours below recommended. Prioritize rest in next scheduled window. "
        "{responder} has been informed."
    ),
}

DEFAULT_GUIDANCE = "Status change detected. {responder} has been notified. Follow standard protocol."

def get_guidance(triggered_by: str | None, status: str, responder_name: str = "Mission Control") -> str:
    if not triggered_by:
        return f"Status update: {status}. {responder_name} monitoring."
    template = GUIDANCE_TEMPLATES.get((triggered_by, status), DEFAULT_GUIDANCE)
    return template.format(responder=responder_name)
