from dataclasses import dataclass

@dataclass
class ClassificationResult:
    status: str  # NOMINAL, ELEVATED, ANOMALY, EMERGENCY
    triggered_by: str | None
    triggered_value: float | None
    threshold_exceeded: float | None

PRIORITY = ["EMERGENCY", "ANOMALY", "ELEVATED", "NOMINAL"]

def _check_heart_rate(value: float) -> str:
    if value > 150 or value < 45:
        return "EMERGENCY"
    if (120 <= value <= 150) or (45 <= value < 50):
        return "ANOMALY"
    if (100 <= value < 120) or (50 <= value < 60):
        return "ELEVATED"
    return "NOMINAL"

def _check_spo2(value: float) -> str:
    if value < 88:
        return "EMERGENCY"
    if 88 <= value < 92:
        return "ANOMALY"
    if 92 <= value < 95:
        return "ELEVATED"
    return "NOMINAL"

def _check_temperature(value: float) -> str:
    if value > 40.0 or value < 35.0:
        return "EMERGENCY"
    if 38.5 <= value <= 40.0:
        return "ANOMALY"
    if 37.5 <= value < 38.5:
        return "ELEVATED"
    return "NOMINAL"

def _check_radiation(value: float) -> str:
    if value > 500:
        return "EMERGENCY"
    if 150 < value <= 500:
        return "ANOMALY"
    if 50 < value <= 150:
        return "ELEVATED"
    return "NOMINAL"

def _check_stress(value: float) -> str:
    if value > 0.8:
        return "EMERGENCY"
    if 0.6 < value <= 0.8:
        return "ANOMALY"
    if 0.4 < value <= 0.6:
        return "ELEVATED"
    return "NOMINAL"

def _check_sleep(value: float) -> str:
    if value < 5:
        return "EMERGENCY"
    if 5 <= value < 6:
        return "ANOMALY"
    if 6 <= value < 7:
        return "ELEVATED"
    return "NOMINAL"

VITAL_CHECKERS = {
    "heart_rate": (_check_heart_rate, {"EMERGENCY": 150.0, "ANOMALY": 120.0, "ELEVATED": 100.0}),
    "spo2": (_check_spo2, {"EMERGENCY": 88.0, "ANOMALY": 92.0, "ELEVATED": 95.0}),
    "temperature": (_check_temperature, {"EMERGENCY": 40.0, "ANOMALY": 38.5, "ELEVATED": 37.5}),
    "radiation_dose": (_check_radiation, {"EMERGENCY": 500.0, "ANOMALY": 150.0, "ELEVATED": 50.0}),
    "stress_index": (_check_stress, {"EMERGENCY": 0.8, "ANOMALY": 0.6, "ELEVATED": 0.4}),
    "sleep_hours": (_check_sleep, {"EMERGENCY": 5.0, "ANOMALY": 6.0, "ELEVATED": 7.0}),
}

def classify_vitals(
    heart_rate: float,
    spo2: float,
    temperature: float,
    radiation_dose: float,
    sleep_hours: float,
    stress_index: float,
) -> ClassificationResult:
    readings = {
        "heart_rate": heart_rate,
        "spo2": spo2,
        "temperature": temperature,
        "radiation_dose": radiation_dose,
        "sleep_hours": sleep_hours,
        "stress_index": stress_index,
    }

    all_results: list[tuple[str, str, float]] = []
    for vital_name, value in readings.items():
        checker, thresholds = VITAL_CHECKERS[vital_name]
        status = checker(value)
        all_results.append((status, vital_name, value))

    for priority_level in PRIORITY:
        for status, vital_name, value in all_results:
            if status == priority_level and status != "NOMINAL":
                checker, thresholds = VITAL_CHECKERS[vital_name]
                threshold = thresholds.get(status)
                return ClassificationResult(
                    status=status,
                    triggered_by=vital_name,
                    triggered_value=value,
                    threshold_exceeded=threshold,
                )

    return ClassificationResult(
        status="NOMINAL",
        triggered_by=None,
        triggered_value=None,
        threshold_exceeded=None,
    )
