import asyncio
import random
import logging
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class CrewBaseline:
    heart_rate: float
    spo2: float
    temperature: float
    radiation_dose: float
    sleep_hours: float
    stress_index: float

CREW_BASELINES: list[CrewBaseline] = [
    CrewBaseline(heart_rate=70.0, spo2=98.5, temperature=36.6, radiation_dose=35.0, sleep_hours=7.5, stress_index=0.25),
    CrewBaseline(heart_rate=65.0, spo2=97.8, temperature=36.4, radiation_dose=38.0, sleep_hours=7.0, stress_index=0.30),
    CrewBaseline(heart_rate=72.0, spo2=98.0, temperature=36.8, radiation_dose=40.0, sleep_hours=8.0, stress_index=0.22),
]

@dataclass
class VitalsState:
    crew_id: str
    baseline: CrewBaseline
    current: dict = field(default_factory=dict)
    scenario: str | None = None
    scenario_tick: int = 0

    def __post_init__(self):
        self.current = {
            "heart_rate": self.baseline.heart_rate + random.uniform(-2, 2),
            "spo2": self.baseline.spo2 + random.uniform(-0.5, 0.5),
            "temperature": self.baseline.temperature + random.uniform(-0.1, 0.1),
            "radiation_dose": self.baseline.radiation_dose + random.uniform(-2, 2),
            "sleep_hours": self.baseline.sleep_hours,
            "stress_index": self.baseline.stress_index + random.uniform(-0.02, 0.02),
        }

SCENARIOS = {
    "radiation_spike": [
        {"radiation_dose": 210.0}, {"radiation_dose": 360.0}, {"radiation_dose": 540.0},
        {"radiation_dose": 490.0}, {"radiation_dose": 410.0}, {"radiation_dose": 310.0},
    ],
    "low_oxygen": [
        {"spo2": 93.5}, {"spo2": 91.0}, {"spo2": 88.5}, {"spo2": 86.0},
        {"spo2": 89.0}, {"spo2": 92.5},
    ],
    "cardiac_event": [
        {"heart_rate": 115.0}, {"heart_rate": 138.0}, {"heart_rate": 162.0},
        {"heart_rate": 148.0}, {"heart_rate": 122.0}, {"heart_rate": 102.0},
    ],
    "high_fever": [
        {"temperature": 37.8}, {"temperature": 38.4}, {"temperature": 39.1},
        {"temperature": 39.6}, {"temperature": 39.0}, {"temperature": 38.3},
        {"temperature": 37.7}, {"temperature": 37.2},
    ],
    "fatigue_accumulation": [
        {"sleep_hours": 6.5, "stress_index": 0.45},
        {"sleep_hours": 5.8, "stress_index": 0.58},
        {"sleep_hours": 5.2, "stress_index": 0.68},
        {"sleep_hours": 4.8, "stress_index": 0.78},
        {"sleep_hours": 4.4, "stress_index": 0.85},
    ],
    "full_recovery": [],
}

_crew_states: dict[str, VitalsState] = {}

def initialize_crew_states(crew_members: list[dict]) -> None:
    global _crew_states
    for i, crew in enumerate(crew_members):
        baseline = CREW_BASELINES[i % len(CREW_BASELINES)]
        _crew_states[str(crew["id"])] = VitalsState(
            crew_id=str(crew["id"]),
            baseline=baseline,
        )

def inject_scenario(crew_id: str, scenario: str) -> bool:
    if crew_id not in _crew_states:
        return False
    if scenario == "full_recovery":
        state = _crew_states[crew_id]
        state.current = {
            "heart_rate": state.baseline.heart_rate,
            "spo2": state.baseline.spo2,
            "temperature": state.baseline.temperature,
            "radiation_dose": state.baseline.radiation_dose,
            "sleep_hours": state.baseline.sleep_hours,
            "stress_index": state.baseline.stress_index,
        }
        state.scenario = None
        state.scenario_tick = 0
        return True
    _crew_states[crew_id].scenario = scenario
    _crew_states[crew_id].scenario_tick = 0
    return True

def generate_tick(crew_id: str, radiation_multiplier: float = 1.0) -> dict:
    if crew_id not in _crew_states:
        return {}

    state = _crew_states[crew_id]
    curr = state.current.copy()

    if state.scenario and state.scenario in SCENARIOS:
        ticks = SCENARIOS[state.scenario]
        if state.scenario_tick < len(ticks):
            overrides = ticks[state.scenario_tick]
            curr.update(overrides)
            state.scenario_tick += 1
        else:
            state.scenario = None
            state.scenario_tick = 0
    else:
        curr["heart_rate"] = float(round(np.clip(
            curr["heart_rate"] + np.random.normal(0, 0.5), 50, 180
        ), 1))
        curr["spo2"] = float(round(np.clip(
            curr["spo2"] + np.random.normal(0, 0.1), 85, 100
        ), 1))
        curr["temperature"] = float(round(np.clip(
            curr["temperature"] + np.random.normal(0, 0.04), 35.0, 42.0
        ), 2))
        curr["radiation_dose"] = float(round(np.clip(
            (curr["radiation_dose"] + np.random.normal(0, 0.8)) * radiation_multiplier,
            10, 1500
        ), 1))
        curr["sleep_hours"] = float(round(np.clip(
            curr["sleep_hours"] + np.random.normal(0, 0.02), 0, 12
        ), 1))
        curr["stress_index"] = float(round(np.clip(
            curr["stress_index"] + np.random.normal(0, 0.01), 0.0, 1.0
        ), 2))

    state.current = curr
    return {**curr, "crew_member_id": crew_id}

def get_all_states() -> dict[str, VitalsState]:
    return _crew_states
