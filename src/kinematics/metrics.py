"""Performance metrics aggregation for plots and tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.geometry.hardpoints import VehicleParams
from src.kinematics.wishbone import (
    CornerState,
    roll_center_height,
    solve_full_car,
    sweep_vertical_travel,
)


@dataclass
class Metrics:
    """Container for sweep tables and scalar KPIs."""

    front_left: pd.DataFrame
    front_right: pd.DataFrame
    rear_left: pd.DataFrame
    rear_right: pd.DataFrame
    front_heave: pd.DataFrame
    rear_heave: pd.DataFrame
    front_roll: pd.DataFrame
    rear_roll: pd.DataFrame
    summary: Dict[str, float] = field(default_factory=dict)


def _states_to_df(states: List[CornerState]) -> pd.DataFrame:
    rows = []
    for s in states:
        rows.append(
            {
                "travel_mm": s.travel_mm,
                "camber_deg": s.camber_deg,
                "toe_deg": s.toe_deg,
                "castor_deg": s.castor_deg,
                "kpi_deg": s.kpi_deg,
                "scrub_radius_mm": s.scrub_radius_mm,
                "trail_mm": s.trail_mm,
                "damper_length_mm": s.damper_length_mm,
                "damper_travel_mm": s.damper_travel_mm,
                "motion_ratio": s.motion_ratio,
                "wheel_y_mm": s.wheel_center[1],
                "wheel_z_mm": s.wheel_center[2],
                "contact_y_mm": s.contact_patch[1],
                "ic_y_mm": s.instant_center[1],
                "ic_z_mm": s.instant_center[2],
                "track_half_mm": abs(s.contact_patch[1]),
            }
        )
    return pd.DataFrame(rows)


def compute_metrics(params: VehicleParams) -> Metrics:
    tf, tr = params.tire_front, params.tire_rear
    z0, z1, n = params.travel_min_mm, params.travel_max_mm, params.travel_steps

    fl = sweep_vertical_travel(params.front_left(), tf, z0, z1, n, "FL")
    fr = sweep_vertical_travel(params.front_right(), tf, z0, z1, n, "FR")
    rl = sweep_vertical_travel(params.rear_left(), tr, z0, z1, n, "RL")
    rr = sweep_vertical_travel(params.rear_right(), tr, z0, z1, n, "RR")

    fl_df, fr_df = _states_to_df(fl), _states_to_df(fr)
    rl_df, rr_df = _states_to_df(rl), _states_to_df(rr)

    # Heave: both sides same travel — track + roll center
    front_heave = _axle_heave_table(fl, fr)
    rear_heave = _axle_heave_table(rl, rr)

    # Roll sweep at design heave: opposite wheel travels
    front_roll = _axle_roll_table(params, "front")
    rear_roll = _axle_roll_table(params, "rear")

    # Summary KPIs at design (travel=0)
    def at0(df: pd.DataFrame) -> pd.Series:
        return df.iloc[(df["travel_mm"]).abs().argmin()]

    fl0, fr0, rl0, rr0 = at0(fl_df), at0(fr_df), at0(rl_df), at0(rr_df)
    fh0 = front_heave.iloc[(front_heave["travel_mm"]).abs().argmin()]
    rh0 = rear_heave.iloc[(rear_heave["travel_mm"]).abs().argmin()]

    summary = {
        "FL camber (deg)": float(fl0["camber_deg"]),
        "FL toe (deg)": float(fl0["toe_deg"]),
        "FL castor (deg)": float(fl0["castor_deg"]),
        "FL KPI (deg)": float(fl0["kpi_deg"]),
        "FL scrub (mm)": float(fl0["scrub_radius_mm"]),
        "FL trail (mm)": float(fl0["trail_mm"]),
        "FL motion ratio": float(fl0["motion_ratio"]),
        "FR camber (deg)": float(fr0["camber_deg"]),
        "RL camber (deg)": float(rl0["camber_deg"]),
        "RR camber (deg)": float(rr0["camber_deg"]),
        "Front track (mm)": float(fh0["track_mm"]),
        "Rear track (mm)": float(rh0["track_mm"]),
        "Front roll center Z (mm)": float(fh0["roll_center_z_mm"]),
        "Rear roll center Z (mm)": float(rh0["roll_center_z_mm"]),
        "Front MR (avg L/R)": float(0.5 * (fl0["motion_ratio"] + fr0["motion_ratio"])),
        "Rear MR (avg L/R)": float(0.5 * (rl0["motion_ratio"] + rr0["motion_ratio"])),
    }

    return Metrics(
        front_left=fl_df,
        front_right=fr_df,
        rear_left=rl_df,
        rear_right=rr_df,
        front_heave=front_heave,
        rear_heave=rear_heave,
        front_roll=front_roll,
        rear_roll=rear_roll,
        summary=summary,
    )


def _axle_heave_table(
    left_states: List[CornerState], right_states: List[CornerState]
) -> pd.DataFrame:
    rows = []
    for L, R in zip(left_states, right_states):
        track = abs(R.contact_patch[1] - L.contact_patch[1])
        rc_z = roll_center_height(L, R)
        rows.append(
            {
                "travel_mm": L.travel_mm,
                "track_mm": track,
                "roll_center_z_mm": rc_z,
                "camber_L": L.camber_deg,
                "camber_R": R.camber_deg,
                "toe_L": L.toe_deg,
                "toe_R": R.toe_deg,
                "MR_L": L.motion_ratio,
                "MR_R": R.motion_ratio,
            }
        )
    return pd.DataFrame(rows)


def _axle_roll_table(params: VehicleParams, axle: str) -> pd.DataFrame:
    """Opposite travel ≈ pure roll about ground for small angles."""
    track = params.track_front_mm if axle == "front" else params.track_rear_mm
    half = track / 2.0
    rolls = np.linspace(-params.roll_max_deg, params.roll_max_deg, params.roll_steps)
    rows = []
    for roll_deg in rolls:
        # Wheel travel ≈ ± half_track * sin(roll)
        dz = half * np.sin(np.deg2rad(roll_deg))
        if axle == "front":
            L = sweep_vertical_travel(
                params.front_left(), params.tire_front, dz, dz, 1, "FL"
            )[0]
            R = sweep_vertical_travel(
                params.front_right(), params.tire_front, -dz, -dz, 1, "FR"
            )[0]
        else:
            L = sweep_vertical_travel(
                params.rear_left(), params.tire_rear, dz, dz, 1, "RL"
            )[0]
            R = sweep_vertical_travel(
                params.rear_right(), params.tire_rear, -dz, -dz, 1, "RR"
            )[0]
        rows.append(
            {
                "roll_deg": roll_deg,
                "travel_L_mm": dz,
                "travel_R_mm": -dz,
                "camber_L": L.camber_deg,
                "camber_R": R.camber_deg,
                "toe_L": L.toe_deg,
                "toe_R": R.toe_deg,
                "roll_center_z_mm": roll_center_height(L, R),
                "track_mm": abs(R.contact_patch[1] - L.contact_patch[1]),
            }
        )
    return pd.DataFrame(rows)
