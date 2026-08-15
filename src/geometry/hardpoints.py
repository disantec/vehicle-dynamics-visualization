"""Vehicle and corner hardpoint parameter models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import yaml

Vec3 = np.ndarray


def v3(x, y, z) -> Vec3:
    return np.array([float(x), float(y), float(z)], dtype=float)


def mirror_y(p: Vec3) -> Vec3:
    """Mirror a point across the vehicle centerline (XZ plane)."""
    return np.array([p[0], -p[1], p[2]], dtype=float)


def _as_v3(value) -> Vec3:
    return v3(*value)


@dataclass
class TireParams:
    radius_mm: float = 280.0
    width_mm: float = 200.0
    sidewall_mm: float = 80.0
    wheel_diameter_in: float = 13.0
    wheel_width_mm: float = 200.0
    offset_mm: float = 25.0
    size: str = ""

    @property
    def wheel_radius_mm(self) -> float:
        return self.wheel_diameter_in * 25.4 / 2.0


def _tire_from_raw(d: Optional[Dict[str, Any]]) -> TireParams:
    if not d:
        return TireParams()
    kwargs: Dict[str, Any] = {}
    for k, v in d.items():
        if k == "size":
            kwargs[k] = str(v)
        else:
            kwargs[k] = float(v)
    return TireParams(**kwargs)


@dataclass
class CornerHardpoints:
    """Left-side design hardpoints for one axle end."""

    lower_front_chassis: Vec3
    lower_rear_chassis: Vec3
    lower_outer: Vec3
    upper_front_chassis: Vec3
    upper_rear_chassis: Vec3
    upper_outer: Vec3
    wheel_center: Vec3
    tierod_inner: Vec3
    tierod_outer: Vec3
    rod_mode: str = "pushrod"  # pushrod | pullrod
    rod_wishbone: str = "lower"  # lower | upper
    rod_arm_point: Vec3 = field(default_factory=lambda: v3(0, 0, 0))
    rod_rocker_point: Vec3 = field(default_factory=lambda: v3(0, 0, 0))
    rocker_pivot: Vec3 = field(default_factory=lambda: v3(0, 0, 0))
    rocker_damper_point: Vec3 = field(default_factory=lambda: v3(0, 0, 0))
    rocker_axis: Vec3 = field(default_factory=lambda: v3(0, 1, 0))
    damper_body: Vec3 = field(default_factory=lambda: v3(0, 0, 0))
    damper_length_mm: float = 220.0
    arb_drop_link: Vec3 = field(default_factory=lambda: v3(0, 0, 0))
    # Design-position alignment (spindle axis). Camber − = top-in; toe + = toe-in.
    static_camber_deg: float = -1.0
    static_toe_deg: float = 0.10

    def mirrored(self) -> "CornerHardpoints":
        """Return right-side hardpoints by mirroring Y."""
        fields = {}
        for name, value in asdict(self).items():
            if isinstance(value, (list, tuple)) or (
                isinstance(value, np.ndarray) and value.shape == (3,)
            ):
                arr = np.asarray(value, dtype=float)
                if arr.shape == (3,):
                    fields[name] = mirror_y(arr)
                else:
                    fields[name] = value
            else:
                fields[name] = value
        # Rebuild with proper Vec3 types
        return CornerHardpoints(
            lower_front_chassis=mirror_y(self.lower_front_chassis),
            lower_rear_chassis=mirror_y(self.lower_rear_chassis),
            lower_outer=mirror_y(self.lower_outer),
            upper_front_chassis=mirror_y(self.upper_front_chassis),
            upper_rear_chassis=mirror_y(self.upper_rear_chassis),
            upper_outer=mirror_y(self.upper_outer),
            wheel_center=mirror_y(self.wheel_center),
            tierod_inner=mirror_y(self.tierod_inner),
            tierod_outer=mirror_y(self.tierod_outer),
            rod_mode=self.rod_mode,
            rod_wishbone=self.rod_wishbone,
            rod_arm_point=mirror_y(self.rod_arm_point),
            rod_rocker_point=mirror_y(self.rod_rocker_point),
            rocker_pivot=mirror_y(self.rocker_pivot),
            rocker_damper_point=mirror_y(self.rocker_damper_point),
            rocker_axis=mirror_y(self.rocker_axis),
            damper_body=mirror_y(self.damper_body),
            damper_length_mm=self.damper_length_mm,
            arb_drop_link=mirror_y(self.arb_drop_link),
            static_camber_deg=self.static_camber_deg,
            static_toe_deg=self.static_toe_deg,
        )

    def point_dict(self) -> Dict[str, Vec3]:
        return {
            "lower_front_chassis": self.lower_front_chassis,
            "lower_rear_chassis": self.lower_rear_chassis,
            "lower_outer": self.lower_outer,
            "upper_front_chassis": self.upper_front_chassis,
            "upper_rear_chassis": self.upper_rear_chassis,
            "upper_outer": self.upper_outer,
            "wheel_center": self.wheel_center,
            "tierod_inner": self.tierod_inner,
            "tierod_outer": self.tierod_outer,
            "rod_arm_point": self.rod_arm_point,
            "rod_rocker_point": self.rod_rocker_point,
            "rocker_pivot": self.rocker_pivot,
            "rocker_damper_point": self.rocker_damper_point,
            "damper_body": self.damper_body,
            "arb_drop_link": self.arb_drop_link,
        }


@dataclass
class VehicleParams:
    wheelbase_mm: float = 2600.0
    track_front_mm: float = 1600.0
    track_rear_mm: float = 1580.0
    ride_height_mm: float = 50.0
    cg_height_mm: float = 320.0
    mass_kg: float = 280.0
    front_weight_bias: float = 0.45
    tire_front: TireParams = field(default_factory=TireParams)
    tire_rear: TireParams = field(default_factory=TireParams)
    front: CornerHardpoints = field(default=None)  # type: ignore
    rear: CornerHardpoints = field(default=None)  # type: ignore
    travel_min_mm: float = -40.0
    travel_max_mm: float = 40.0
    travel_steps: int = 41
    roll_max_deg: float = 3.0
    roll_steps: int = 21

    def front_left(self) -> CornerHardpoints:
        return self.front

    def front_right(self) -> CornerHardpoints:
        return self.front.mirrored()

    def rear_left(self) -> CornerHardpoints:
        return self.rear

    def rear_right(self) -> CornerHardpoints:
        return self.rear.mirrored()

    def all_corners(self) -> Dict[str, CornerHardpoints]:
        return {
            "FL": self.front_left(),
            "FR": self.front_right(),
            "RL": self.rear_left(),
            "RR": self.rear_right(),
        }

    @property
    def tire(self) -> TireParams:
        """Front tire. Prefer ``tire_for(label)`` for staggered setups."""
        return self.tire_front

    def tire_for(self, label: str) -> TireParams:
        return self.tire_rear if str(label).upper().startswith("R") else self.tire_front


def _corner_from_dict(d: Dict[str, Any]) -> CornerHardpoints:
    return CornerHardpoints(
        lower_front_chassis=_as_v3(d["lower_front_chassis"]),
        lower_rear_chassis=_as_v3(d["lower_rear_chassis"]),
        lower_outer=_as_v3(d["lower_outer"]),
        upper_front_chassis=_as_v3(d["upper_front_chassis"]),
        upper_rear_chassis=_as_v3(d["upper_rear_chassis"]),
        upper_outer=_as_v3(d["upper_outer"]),
        wheel_center=_as_v3(d["wheel_center"]),
        tierod_inner=_as_v3(d["tierod_inner"]),
        tierod_outer=_as_v3(d["tierod_outer"]),
        rod_mode=d.get("rod_mode", "pushrod"),
        rod_wishbone=d.get("rod_wishbone", "lower"),
        rod_arm_point=_as_v3(d.get("rod_arm_point", d["lower_outer"])),
        rod_rocker_point=_as_v3(d.get("rod_rocker_point", [0, 0, 0])),
        rocker_pivot=_as_v3(d.get("rocker_pivot", [0, 0, 0])),
        rocker_damper_point=_as_v3(d.get("rocker_damper_point", [0, 0, 0])),
        rocker_axis=_as_v3(d.get("rocker_axis", [0, 1, 0])),
        damper_body=_as_v3(d.get("damper_body", [0, 0, 0])),
        damper_length_mm=float(d.get("damper_length_mm", 220)),
        arb_drop_link=_as_v3(d.get("arb_drop_link", [0, 0, 0])),
        static_camber_deg=float(d.get("static_camber_deg", -1.0)),
        static_toe_deg=float(d.get("static_toe_deg", 0.10)),
    )


def load_params(path: Optional[str | Path] = None) -> VehicleParams:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "data" / "default_params.yaml"
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    vehicle = raw.get("vehicle", {})
    legacy_tire = raw.get("tire", {})
    analysis = raw.get("analysis", {})

    return VehicleParams(
        wheelbase_mm=float(vehicle.get("wheelbase_mm", 2600)),
        track_front_mm=float(vehicle.get("track_front_mm", 1600)),
        track_rear_mm=float(vehicle.get("track_rear_mm", 1580)),
        ride_height_mm=float(vehicle.get("ride_height_mm", 50)),
        cg_height_mm=float(vehicle.get("cg_height_mm", 320)),
        mass_kg=float(vehicle.get("mass_kg", 280)),
        front_weight_bias=float(vehicle.get("front_weight_bias", 0.45)),
        tire_front=_tire_from_raw(raw.get("tire_front", legacy_tire)),
        tire_rear=_tire_from_raw(raw.get("tire_rear", legacy_tire)),
        front=_corner_from_dict(raw["front"]),
        rear=_corner_from_dict(raw["rear"]),
        travel_min_mm=float(analysis.get("travel_min_mm", -40)),
        travel_max_mm=float(analysis.get("travel_max_mm", 40)),
        travel_steps=int(analysis.get("travel_steps", 41)),
        roll_max_deg=float(analysis.get("roll_max_deg", 3.0)),
        roll_steps=int(analysis.get("roll_steps", 21)),
    )


def update_corner_point(
    corner: CornerHardpoints, name: str, value: List[float]
) -> CornerHardpoints:
    """Return a new corner with one point updated."""
    data = asdict(corner)
    data[name] = v3(*value)
    # asdict converts ndarray to list; rebuild carefully
    return _corner_from_dict(
        {
            **{
                k: (list(v) if isinstance(v, (list, tuple, np.ndarray)) else v)
                for k, v in data.items()
            }
        }
    )


def params_to_dict(params: VehicleParams) -> Dict[str, Any]:
    """Serialize params for session state / export."""

    def pt(p: Vec3) -> List[float]:
        return [float(p[0]), float(p[1]), float(p[2])]

    def corner_dict(c: CornerHardpoints) -> Dict[str, Any]:
        return {
            "lower_front_chassis": pt(c.lower_front_chassis),
            "lower_rear_chassis": pt(c.lower_rear_chassis),
            "lower_outer": pt(c.lower_outer),
            "upper_front_chassis": pt(c.upper_front_chassis),
            "upper_rear_chassis": pt(c.upper_rear_chassis),
            "upper_outer": pt(c.upper_outer),
            "wheel_center": pt(c.wheel_center),
            "tierod_inner": pt(c.tierod_inner),
            "tierod_outer": pt(c.tierod_outer),
            "rod_mode": c.rod_mode,
            "rod_wishbone": c.rod_wishbone,
            "rod_arm_point": pt(c.rod_arm_point),
            "rod_rocker_point": pt(c.rod_rocker_point),
            "rocker_pivot": pt(c.rocker_pivot),
            "rocker_damper_point": pt(c.rocker_damper_point),
            "rocker_axis": pt(c.rocker_axis),
            "damper_body": pt(c.damper_body),
            "damper_length_mm": c.damper_length_mm,
            "arb_drop_link": pt(c.arb_drop_link),
            "static_camber_deg": c.static_camber_deg,
            "static_toe_deg": c.static_toe_deg,
        }

    return {
        "vehicle": {
            "wheelbase_mm": params.wheelbase_mm,
            "track_front_mm": params.track_front_mm,
            "track_rear_mm": params.track_rear_mm,
            "ride_height_mm": params.ride_height_mm,
            "cg_height_mm": params.cg_height_mm,
            "mass_kg": params.mass_kg,
            "front_weight_bias": params.front_weight_bias,
        },
        "tire_front": asdict(params.tire_front),
        "tire_rear": asdict(params.tire_rear),
        "front": corner_dict(params.front),
        "rear": corner_dict(params.rear),
        "analysis": {
            "travel_min_mm": params.travel_min_mm,
            "travel_max_mm": params.travel_max_mm,
            "travel_steps": params.travel_steps,
            "roll_max_deg": params.roll_max_deg,
            "roll_steps": params.roll_steps,
        },
    }


def params_from_dict(d: Dict[str, Any]) -> VehicleParams:
    vehicle = d.get("vehicle", {})
    legacy_tire = d.get("tire", {})
    analysis = d.get("analysis", {})
    return VehicleParams(
        wheelbase_mm=float(vehicle.get("wheelbase_mm", 2600)),
        track_front_mm=float(vehicle.get("track_front_mm", 1600)),
        track_rear_mm=float(vehicle.get("track_rear_mm", 1580)),
        ride_height_mm=float(vehicle.get("ride_height_mm", 50)),
        cg_height_mm=float(vehicle.get("cg_height_mm", 320)),
        mass_kg=float(vehicle.get("mass_kg", 280)),
        front_weight_bias=float(vehicle.get("front_weight_bias", 0.45)),
        tire_front=_tire_from_raw(d.get("tire_front", legacy_tire)),
        tire_rear=_tire_from_raw(d.get("tire_rear", legacy_tire)),
        front=_corner_from_dict(d["front"]),
        rear=_corner_from_dict(d["rear"]),
        travel_min_mm=float(analysis.get("travel_min_mm", -40)),
        travel_max_mm=float(analysis.get("travel_max_mm", 40)),
        travel_steps=int(analysis.get("travel_steps", 41)),
        roll_max_deg=float(analysis.get("roll_max_deg", 3.0)),
        roll_steps=int(analysis.get("roll_steps", 21)),
    )
