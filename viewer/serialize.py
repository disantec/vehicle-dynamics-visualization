"""JSON helpers for the interactive viewer API."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from src.geometry.hardpoints import VehicleParams, params_from_dict, params_to_dict
from src.kinematics.metrics import compute_metrics
from src.kinematics.wishbone import CornerState, roll_center_height, solve_full_car

POINT_LABELS = {
    "lower_front_chassis": "Lower front chassis",
    "lower_rear_chassis": "Lower rear chassis",
    "lower_outer": "Lower outer (LBJ)",
    "upper_front_chassis": "Upper front chassis",
    "upper_rear_chassis": "Upper rear chassis",
    "upper_outer": "Upper outer (UBJ)",
    "wheel_center": "Wheel center",
    "tierod_inner": "Tierod inner",
    "tierod_outer": "Tierod outer",
    "rod_arm_point": "Rod ↔ wishbone",
    "rod_rocker_point": "Rod ↔ rocker",
    "rocker_pivot": "Rocker pivot",
    "rocker_damper_point": "Rocker ↔ damper",
    "damper_body": "Damper body",
}

POINT_GROUPS = {
    "Lower A-arm": ["lower_front_chassis", "lower_rear_chassis", "lower_outer"],
    "Upper A-arm": ["upper_front_chassis", "upper_rear_chassis", "upper_outer"],
    "Wheel / spindle": ["wheel_center"],
    "Steering": ["tierod_inner", "tierod_outer"],
    "Pushrod": ["rod_arm_point", "rod_rocker_point"],
    "Rocker / damper": ["rocker_pivot", "rocker_damper_point", "damper_body"],
}

EDITABLE_POINTS = list(POINT_LABELS.keys())


def _xyz(v) -> List[float]:
    arr = np.asarray(v, dtype=float).reshape(-1)
    return [float(arr[0]), float(arr[1]), float(arr[2])]


def corner_state_to_dict(s: CornerState) -> Dict[str, Any]:
    return {
        "label": s.label,
        "travel_mm": float(s.travel_mm),
        "points": {
            "lower_front_chassis": _xyz(s.lower_front_chassis),
            "lower_rear_chassis": _xyz(s.lower_rear_chassis),
            "lower_outer": _xyz(s.lower_outer),
            "upper_front_chassis": _xyz(s.upper_front_chassis),
            "upper_rear_chassis": _xyz(s.upper_rear_chassis),
            "upper_outer": _xyz(s.upper_outer),
            "wheel_center": _xyz(s.wheel_center),
            "contact_patch": _xyz(s.contact_patch),
            "tierod_inner": _xyz(s.tierod_inner),
            "tierod_outer": _xyz(s.tierod_outer),
            "rod_arm_point": _xyz(s.rod_arm_point),
            "rod_rocker_point": _xyz(s.rod_rocker_point),
            "rocker_pivot": _xyz(s.rocker_pivot),
            "rocker_damper_point": _xyz(s.rocker_damper_point),
            "damper_eye": _xyz(s.damper_eye),
            "damper_body": _xyz(s.damper_body),
            "instant_center": _xyz(s.instant_center),
        },
        "camber_deg": float(s.camber_deg),
        "toe_deg": float(s.toe_deg),
        "castor_deg": float(s.castor_deg),
        "kpi_deg": float(s.kpi_deg),
        "scrub_radius_mm": float(s.scrub_radius_mm),
        "trail_mm": float(s.trail_mm),
        "damper_length_mm": float(s.damper_length_mm),
        "damper_travel_mm": float(s.damper_travel_mm),
        "motion_ratio": float(s.motion_ratio),
        "side": float(s.side),
    }


def solve_payload(params_dict: Dict[str, Any], travels: Dict[str, float]) -> Dict[str, Any]:
    params = params_from_dict(params_dict)
    states = solve_full_car(params, travels)
    front_rc = roll_center_height(states["FL"], states["FR"])
    rear_rc = roll_center_height(states["RL"], states["RR"])
    return {
        "params": params_to_dict(params),
        "travels": {k: float(travels.get(k, 0.0)) for k in ("FL", "FR", "RL", "RR")},
        "corners": {name: corner_state_to_dict(st) for name, st in states.items()},
        "tires": {
            "FL": {**params.tire_front.__dict__, "width_mm": params.tire_front.width_mm},
            "FR": {**params.tire_front.__dict__, "width_mm": params.tire_front.width_mm},
            "RL": {**params.tire_rear.__dict__, "width_mm": params.tire_rear.width_mm},
            "RR": {**params.tire_rear.__dict__, "width_mm": params.tire_rear.width_mm},
        },
        "roll_centers": {
            "front_z_mm": float(front_rc),
            "rear_z_mm": float(rear_rc),
        },
        "vehicle": params_to_dict(params)["vehicle"],
    }


def metrics_payload(params_dict: Dict[str, Any]) -> Dict[str, Any]:
    params = params_from_dict(params_dict)
    m = compute_metrics(params)

    def series(df, cols: List[str]) -> Dict[str, List[float]]:
        out = {}
        for c in cols:
            out[c] = [float(v) for v in df[c].tolist()]
        return out

    cols = [
        "travel_mm",
        "camber_deg",
        "toe_deg",
        "motion_ratio",
        "damper_travel_mm",
        "scrub_radius_mm",
        "trail_mm",
        "castor_deg",
        "kpi_deg",
    ]
    return {
        "summary": {k: float(v) for k, v in m.summary.items()},
        "FL": series(m.front_left, cols),
        "FR": series(m.front_right, cols),
        "RL": series(m.rear_left, cols),
        "RR": series(m.rear_right, cols),
        "front_heave": series(m.front_heave, ["travel_mm", "track_mm", "roll_center_z_mm"]),
        "rear_heave": series(m.rear_heave, ["travel_mm", "track_mm", "roll_center_z_mm"]),
    }


def schema() -> Dict[str, Any]:
    return {
        "point_labels": POINT_LABELS,
        "point_groups": POINT_GROUPS,
        "editable_points": EDITABLE_POINTS,
    }
