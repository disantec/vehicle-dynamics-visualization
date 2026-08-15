"""Double-wishbone suspension kinematics solver.

Coordinate system (right-hand):
  X rearward, Y rightward, Z upward. Units: mm.

Approach
--------
At design position the hardpoints define fixed link lengths. For a vertical
wheel-center travel `dz` we solve for lower/upper arm rotations about their
chassis hinge axes and upright orientation such that:
  - lower outer ball joint stays at lower-arm length
  - upper outer ball joint stays at upper-arm length
  - upright length (UBJ–LBJ) is preserved
  - wheel center remains at fixed offset in upright frame
  - toe is controlled by the tierod length constraint

Rocker / pushrod / damper are then evaluated from the solved arm pose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import least_squares

from src.geometry.hardpoints import CornerHardpoints, TireParams, VehicleParams, v3

Vec3 = np.ndarray


def _unit(v: Vec3) -> Vec3:
    n = np.linalg.norm(v)
    if n < 1e-12:
        return np.zeros(3)
    return v / n


def _rot_about_axis(axis: Vec3, angle: float) -> np.ndarray:
    """Rodrigues rotation matrix."""
    k = _unit(axis)
    K = np.array(
        [
            [0, -k[2], k[1]],
            [k[2], 0, -k[0]],
            [-k[1], k[0], 0],
        ]
    )
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)


def _project_point_to_axis(p: Vec3, origin: Vec3, axis: Vec3) -> Vec3:
    a = _unit(axis)
    return origin + np.dot(p - origin, a) * a


def _arm_axis(front: Vec3, rear: Vec3) -> Tuple[Vec3, Vec3]:
    """Return (origin mid-hinge, axis direction front→rear)."""
    origin = 0.5 * (front + rear)
    axis = rear - front
    return origin, _unit(axis)


def _rotate_point_about_arm(
    point: Vec3, front: Vec3, rear: Vec3, angle: float
) -> Vec3:
    origin, axis = _arm_axis(front, rear)
    foot = _project_point_to_axis(point, origin, axis)
    R = _rot_about_axis(axis, angle)
    return foot + R @ (point - foot)


@dataclass
class CornerState:
    """Solved pose for one suspension corner."""

    label: str
    travel_mm: float
    lower_outer: Vec3
    upper_outer: Vec3
    wheel_center: Vec3
    contact_patch: Vec3
    tierod_outer: Vec3
    rod_arm_point: Vec3
    rod_rocker_point: Vec3
    rocker_damper_point: Vec3
    damper_eye: Vec3
    # Chassis fixed references (for drawing)
    lower_front_chassis: Vec3
    lower_rear_chassis: Vec3
    upper_front_chassis: Vec3
    upper_rear_chassis: Vec3
    tierod_inner: Vec3
    rocker_pivot: Vec3
    damper_body: Vec3
    # Metrics at this pose
    camber_deg: float
    toe_deg: float
    castor_deg: float
    kpi_deg: float
    scrub_radius_mm: float
    trail_mm: float
    damper_length_mm: float
    damper_travel_mm: float
    motion_ratio: float
    instant_center: Vec3
    side: float  # +1 right, -1 left (sign of design Y)


@dataclass
class DesignLengths:
    lower_len: float
    upper_len: float
    upright_len: float
    tierod_len: float
    rod_len: float
    # Upright-local offsets expressed in design upright frame
    wc_offset: Vec3  # wheel center relative to lower outer, in upright basis
    to_offset: Vec3  # tierod outer relative to lower outer
    spindle_local: Vec3  # hub axis in upright basis (design)
    basis0: np.ndarray  # design upright basis (3x3)
    rod_frac: float  # fraction of arm length for rod pickup (0 chassis → 1 outer)
    rod_on_lower: bool
    # Rocker geometry in local plane (+ axial offset along pivot axis)
    rocker_rod_radius: float
    rocker_damper_radius: float
    rocker_rod_angle0: float
    rocker_damper_angle0: float
    rocker_rod_axial: float
    rocker_damper_axial: float
    design_damper_len: float
    # Design positions
    design_wc: Vec3
    design_lo: Vec3
    design_uo: Vec3
    side: float


def _upright_basis(lo: Vec3, uo: Vec3, ref_outboard: Vec3, side: float) -> np.ndarray:
    """Orthonormal upright frame from kingpin + outboard reference point.

    e1: kingpin (lo → uo)
    e2: roughly outboard (toward ref, ⊥ kingpin)
    e3: e1 × e2 (completes right-handed frame)
    """
    e1 = _unit(uo - lo)
    to_ref = ref_outboard - lo
    lat = to_ref - np.dot(to_ref, e1) * e1
    if np.linalg.norm(lat) < 1e-6:
        lat = np.array([0.0, side, 0.0])
    e2 = _unit(lat)
    if e2[1] * side < 0:
        e2 = -e2
    e3 = _unit(np.cross(e1, e2))
    e2 = _unit(np.cross(e3, e1))
    return np.column_stack([e1, e2, e3])


def _design_spindle(side: float, camber_deg: float = -1.5, toe_deg: float = 0.1) -> Vec3:
    """Hub/spindle axis at design (points outboard). Independent of kingpin (KPI ≠ camber)."""
    c = np.deg2rad(camber_deg)
    t = np.deg2rad(toe_deg)
    # X aft, Y outboard*side, Z up. +toe-in, −camber (top-in) ⇒ small +Z on outboard axis.
    return _unit(
        np.array(
            [
                side * np.sin(t),
                side * np.cos(t) * np.cos(c),
                -np.sin(c),
            ]
        )
    )


def build_design_lengths(hp: CornerHardpoints) -> DesignLengths:
    side = 1.0 if hp.wheel_center[1] >= 0 else -1.0
    lo, uo, wc = hp.lower_outer, hp.upper_outer, hp.wheel_center
    # Distance from outer ball joints to arm hinge axes
    l_origin, l_axis = _arm_axis(hp.lower_front_chassis, hp.lower_rear_chassis)
    lower_len = np.linalg.norm(lo - _project_point_to_axis(lo, l_origin, l_axis))
    u_origin, u_axis = _arm_axis(hp.upper_front_chassis, hp.upper_rear_chassis)
    upper_len = np.linalg.norm(uo - _project_point_to_axis(uo, u_origin, u_axis))
    upright_len = np.linalg.norm(uo - lo)
    tierod_len = np.linalg.norm(hp.tierod_outer - hp.tierod_inner)
    rod_len = np.linalg.norm(hp.rod_rocker_point - hp.rod_arm_point)

    basis = _upright_basis(lo, uo, wc, side)
    wc_offset = basis.T @ (wc - lo)
    to_offset = basis.T @ (hp.tierod_outer - lo)
    spindle0 = _design_spindle(
        side,
        camber_deg=float(getattr(hp, "static_camber_deg", -1.0)),
        toe_deg=float(getattr(hp, "static_toe_deg", 0.10)),
    )
    spindle_local = basis.T @ spindle0

    # Rod pickup as fraction along arm from chassis mid to outer
    if hp.rod_wishbone.lower() == "upper":
        arm_outer = uo
        arm_front, arm_rear = hp.upper_front_chassis, hp.upper_rear_chassis
        rod_on_lower = False
    else:
        arm_outer = lo
        arm_front, arm_rear = hp.lower_front_chassis, hp.lower_rear_chassis
        rod_on_lower = True
    a_origin, a_axis = _arm_axis(arm_front, arm_rear)
    arm_mid = a_origin
    arm_vec = arm_outer - arm_mid
    arm_len = np.linalg.norm(arm_vec)
    rod_vec = hp.rod_arm_point - arm_mid
    rod_frac = float(np.clip(np.dot(rod_vec, arm_vec) / (arm_len**2 + 1e-12), 0.05, 0.98))

    # Rocker polar coordinates about pivot, axis = rocker_axis
    pivot = hp.rocker_pivot
    axis = _unit(hp.rocker_axis)
    ref = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 0.0, 1.0])
    r1 = _unit(np.cross(axis, ref))
    r2 = _unit(np.cross(axis, r1))

    def polar(p: Vec3) -> Tuple[float, float, float]:
        d = p - pivot
        axial = float(np.dot(d, axis))
        d_plane = d - axial * axis
        x, y = float(np.dot(d_plane, r1)), float(np.dot(d_plane, r2))
        return float(np.hypot(x, y)), float(np.arctan2(y, x)), axial

    rod_r, rod_a, rod_ax = polar(hp.rod_rocker_point)
    dam_r, dam_a, dam_ax = polar(hp.rocker_damper_point)
    design_damper = np.linalg.norm(hp.rocker_damper_point - hp.damper_body)

    return DesignLengths(
        lower_len=lower_len,
        upper_len=upper_len,
        upright_len=upright_len,
        tierod_len=tierod_len,
        rod_len=rod_len,
        wc_offset=wc_offset,
        to_offset=to_offset,
        spindle_local=spindle_local,
        basis0=basis,
        rod_frac=rod_frac,
        rod_on_lower=rod_on_lower,
        rocker_rod_radius=rod_r,
        rocker_damper_radius=dam_r,
        rocker_rod_angle0=rod_a,
        rocker_damper_angle0=dam_a,
        rocker_rod_axial=rod_ax,
        rocker_damper_axial=dam_ax,
        design_damper_len=design_damper,
        design_wc=wc.copy(),
        design_lo=lo.copy(),
        design_uo=uo.copy(),
        side=side,
    )


def _angles_from_pose(
    lo: Vec3,
    uo: Vec3,
    hp: CornerHardpoints,
) -> Tuple[float, float]:
    """Estimate arm rotation angles from current outer positions vs design."""
    # Use signed angle of radial vector about arm axis
    def ang(front, rear, design_outer, outer):
        origin, axis = _arm_axis(front, rear)
        d0 = design_outer - _project_point_to_axis(design_outer, origin, axis)
        d1 = outer - _project_point_to_axis(outer, origin, axis)
        d0u, d1u = _unit(d0), _unit(d1)
        c = np.clip(np.dot(d0u, d1u), -1, 1)
        s = np.dot(axis, np.cross(d0u, d1u))
        return float(np.arctan2(s, c))

    la = ang(hp.lower_front_chassis, hp.lower_rear_chassis, hp.lower_outer, lo)
    ua = ang(hp.upper_front_chassis, hp.upper_rear_chassis, hp.upper_outer, uo)
    return la, ua


def solve_corner(
    hp: CornerHardpoints,
    tire: TireParams,
    travel_mm: float = 0.0,
    lengths: Optional[DesignLengths] = None,
    label: str = "",
    rocker_theta_seed: float = 0.0,
) -> CornerState:
    """Solve corner pose for a given vertical wheel-center travel."""
    if lengths is None:
        lengths = build_design_lengths(hp)

    side = lengths.side
    design_wc = lengths.design_wc
    target_wc_z = design_wc[2] + travel_mm

    # Free variables: lower_angle, upper_angle, upright_twist (about kingpin)

    def pose_from_x(x: np.ndarray):
        la, ua, twist = x
        lo = _rotate_point_about_arm(
            hp.lower_outer, hp.lower_front_chassis, hp.lower_rear_chassis, la
        )
        uo = _rotate_point_about_arm(
            hp.upper_outer, hp.upper_front_chassis, hp.upper_rear_chassis, ua
        )
        # Seed outboard ref from design wheel center (translated by travel for stability)
        ref = design_wc + np.array([0.0, 0.0, travel_mm])
        basis = _upright_basis(lo, uo, ref, side)
        R_twist = _rot_about_axis(basis[:, 0], twist)
        basis_t = R_twist @ basis
        wc = lo + basis_t @ lengths.wc_offset
        to = lo + basis_t @ lengths.to_offset
        spindle = basis_t @ lengths.spindle_local
        return lo, uo, wc, to, spindle, basis_t

    def residual(x: np.ndarray) -> np.ndarray:
        lo, uo, wc, to, _, _ = pose_from_x(x)
        r = np.zeros(5)
        r[0] = np.linalg.norm(uo - lo) - lengths.upright_len
        r[1] = wc[2] - target_wc_z
        r[2] = 0.05 * (wc[0] - design_wc[0])
        r[3] = np.linalg.norm(to - hp.tierod_inner) - lengths.tierod_len
        r[4] = 0.01 * x[2]
        return r

    x0 = np.array([0.0, 0.0, 0.0])
    if abs(travel_mm) > 1e-6:
        l_origin, l_axis = _arm_axis(hp.lower_front_chassis, hp.lower_rear_chassis)
        rad = np.linalg.norm(
            hp.lower_outer - _project_point_to_axis(hp.lower_outer, l_origin, l_axis)
        )
        # Arm angle sign: positive rotation that lifts outer on +Y side
        x0[0] = travel_mm / max(rad, 1.0) * 0.8
        x0[1] = x0[0] * 0.85

    sol = least_squares(residual, x0, bounds=([-1.2, -1.2, -0.6], [1.2, 1.2, 0.6]))
    lo, uo, wc, to, spindle, basis_t = pose_from_x(sol.x)
    la, ua, twist = sol.x

    camber, toe, castor, kpi, scrub, trail = _alignment_metrics(
        lo, uo, wc, spindle, tire, side
    )
    camber_rad = np.deg2rad(camber)
    contact = wc.copy()
    contact[2] = wc[2] - tire.radius_mm * np.cos(camber_rad)
    contact[1] = wc[1] - side * tire.radius_mm * np.sin(camber_rad)

    # Rod arm pickup
    if lengths.rod_on_lower:
        arm_outer = lo
        arm_front, arm_rear = hp.lower_front_chassis, hp.lower_rear_chassis
        design_outer = hp.lower_outer
    else:
        arm_outer = uo
        arm_front, arm_rear = hp.upper_front_chassis, hp.upper_rear_chassis
        design_outer = hp.upper_outer
    a_origin, a_axis = _arm_axis(arm_front, arm_rear)
    # rotate design rod point with same arm angle
    arm_angle = la if lengths.rod_on_lower else ua
    rod_arm = _rotate_point_about_arm(
        hp.rod_arm_point, arm_front, arm_rear, arm_angle
    )

    # Solve rocker angle so rod length is preserved
    rocker_angle, rod_rocker, damper_eye = _solve_rocker(
        hp, lengths, rod_arm, theta_seed=rocker_theta_seed
    )
    damper_len = float(np.linalg.norm(damper_eye - hp.damper_body))
    damper_travel = damper_len - lengths.design_damper_len

    # Motion ratio filled during sweep via gradient; single-pose placeholder
    motion_ratio = 0.0

    ic = compute_instant_center(hp, lo, uo)

    return CornerState(
        label=label,
        travel_mm=travel_mm,
        lower_outer=lo,
        upper_outer=uo,
        wheel_center=wc,
        contact_patch=contact,
        tierod_outer=to,
        rod_arm_point=rod_arm,
        rod_rocker_point=rod_rocker,
        rocker_damper_point=damper_eye,
        damper_eye=damper_eye,
        lower_front_chassis=hp.lower_front_chassis,
        lower_rear_chassis=hp.lower_rear_chassis,
        upper_front_chassis=hp.upper_front_chassis,
        upper_rear_chassis=hp.upper_rear_chassis,
        tierod_inner=hp.tierod_inner,
        rocker_pivot=hp.rocker_pivot,
        damper_body=hp.damper_body,
        camber_deg=camber,
        toe_deg=toe,
        castor_deg=castor,
        kpi_deg=kpi,
        scrub_radius_mm=scrub,
        trail_mm=trail,
        damper_length_mm=damper_len,
        damper_travel_mm=damper_travel,
        motion_ratio=motion_ratio,
        instant_center=ic,
        side=side,
    )


def _rocker_frame(hp: CornerHardpoints) -> Tuple[Vec3, Vec3, Vec3, Vec3]:
    """Return pivot, unit axis, and in-plane basis (r1, r2)."""
    pivot = hp.rocker_pivot
    axis = _unit(hp.rocker_axis)
    ref = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 0.0, 1.0])
    r1 = _unit(np.cross(axis, ref))
    r2 = _unit(np.cross(axis, r1))
    return pivot, axis, r1, r2


def _rocker_points_at(
    hp: CornerHardpoints,
    lengths: DesignLengths,
    theta: float,
) -> Tuple[Vec3, Vec3]:
    pivot, axis, r1, r2 = _rocker_frame(hp)
    a_rod = lengths.rocker_rod_angle0 + theta
    a_dam = lengths.rocker_damper_angle0 + theta
    rod_pt = (
        pivot
        + lengths.rocker_rod_axial * axis
        + lengths.rocker_rod_radius * (np.cos(a_rod) * r1 + np.sin(a_rod) * r2)
    )
    dam_pt = (
        pivot
        + lengths.rocker_damper_axial * axis
        + lengths.rocker_damper_radius * (np.cos(a_dam) * r1 + np.sin(a_dam) * r2)
    )
    return rod_pt, dam_pt


def _solve_rocker(
    hp: CornerHardpoints,
    lengths: DesignLengths,
    rod_arm: Vec3,
    theta_seed: float = 0.0,
) -> Tuple[float, Vec3, Vec3]:
    """Solve rocker angle for fixed push/pull-rod length.

    Analytic circle–sphere intersection in the rocker plane (up to two roots);
    the root closest to ``theta_seed`` is chosen for branch continuity. If the
    sphere misses the circle (packaging limit), the nearest reachable angle is
    used so the model degrades gracefully instead of jumping.
    """
    pivot, axis, r1, r2 = _rocker_frame(hp)
    R = lengths.rocker_rod_radius
    Lrod = lengths.rod_len
    # Circle centre in 3D
    c = pivot + lengths.rocker_rod_axial * axis
    # Vector from circle centre to rod arm end
    d = rod_arm - c
    d_axial = float(np.dot(d, axis))
    d_plane = d - d_axial * axis
    # Effective 2D sphere: remaining radial distance after axial offset
    r_eff_sq = Lrod**2 - d_axial**2
    if r_eff_sq < 0:
        # Impossible axial reach — aim toward rod_arm projection
        target = d_plane
        if np.linalg.norm(target) < 1e-9:
            theta = theta_seed
        else:
            ang = float(np.arctan2(np.dot(target, r2), np.dot(target, r1)))
            theta = ang - lengths.rocker_rod_angle0
        return theta, *_rocker_points_at(hp, lengths, theta)

    rho = float(np.linalg.norm(d_plane))
    r_eff = np.sqrt(r_eff_sq)
    # Distance from circle centre to projected rod_arm in plane
    # Law of cosines on triangle (circle radius R, r_eff, rho)
    if rho < 1e-9:
        # Rod arm projects to centre — any angle if R≈r_eff
        theta = theta_seed
        return theta, *_rocker_points_at(hp, lengths, theta)

    # Angle of plane projection of rod_arm
    phi = float(np.arctan2(np.dot(d_plane, r2), np.dot(d_plane, r1)))
    # Half-angle between the two intersection solutions
    cos_alpha = (R**2 + rho**2 - r_eff**2) / (2.0 * R * rho + 1e-12)
    if cos_alpha > 1.0 or cos_alpha < -1.0:
        # No intersection — clamp to line-of-centres angle (nearest point on circle)
        theta = phi - lengths.rocker_rod_angle0
        # unwrap near seed
        while theta - theta_seed > np.pi:
            theta -= 2 * np.pi
        while theta - theta_seed < -np.pi:
            theta += 2 * np.pi
        return theta, *_rocker_points_at(hp, lengths, theta)

    alpha = float(np.arccos(np.clip(cos_alpha, -1.0, 1.0)))
    cand_plane = [phi + alpha, phi - alpha]
    cand_theta = []
    for a in cand_plane:
        th = a - lengths.rocker_rod_angle0
        while th - theta_seed > np.pi:
            th -= 2 * np.pi
        while th - theta_seed < -np.pi:
            th += 2 * np.pi
        cand_theta.append(th)

    theta = min(cand_theta, key=lambda t: abs(t - theta_seed))
    return theta, *_rocker_points_at(hp, lengths, theta)


def _alignment_metrics(
    lo: Vec3,
    uo: Vec3,
    wc: Vec3,
    spindle: Vec3,
    tire: TireParams,
    side: float,
) -> Tuple[float, float, float, float, float, float]:
    """Camber, toe, castor, KPI, scrub radius, mechanical trail.

    Sign conventions (same for left and right):
      camber > 0  → top of tire outward
      toe    > 0  → toe-in
      castor > 0  → kingpin top rearward (+X)
      KPI    > 0  → kingpin top inward
      scrub  > 0  → contact outboard of kingpin ground intersection
      trail  > 0  → contact aft of kingpin ground intersection
    """
    kingpin = _unit(uo - lo)
    wheel_axis = _unit(spindle)
    if wheel_axis[1] * side < 0:
        wheel_axis = -wheel_axis

    # Camber from spindle pitch (axis outboard)
    camber = -np.degrees(np.arcsin(np.clip(wheel_axis[2], -1.0, 1.0)))
    # Toe from plan view of spindle
    toe = np.degrees(np.arctan2(side * wheel_axis[0], abs(wheel_axis[1]) + 1e-12))

    # KPI: top of kingpin inward
    kpi = np.degrees(np.arctan2(-side * kingpin[1], abs(kingpin[2]) + 1e-12))
    castor = np.degrees(np.arctan2(kingpin[0], abs(kingpin[2]) + 1e-12))

    if abs(kingpin[2]) > 1e-9:
        t = -lo[2] / kingpin[2]
        kp_ground = lo + t * kingpin
    else:
        kp_ground = lo.copy()
        kp_ground[2] = 0.0

    contact = wc.copy()
    contact[2] = 0.0
    scrub = float(side * (contact[1] - kp_ground[1]))
    trail = float(kp_ground[0] - contact[0])

    return camber, toe, castor, kpi, scrub, trail


def compute_instant_center(hp: CornerHardpoints, lo: Vec3, uo: Vec3) -> Vec3:
    """2D front-view instant center from upper/lower arm lines (YZ plane)."""
    # Project arm hinge midpoints and outers into YZ
    lf = 0.5 * (hp.lower_front_chassis + hp.lower_rear_chassis)
    uf = 0.5 * (hp.upper_front_chassis + hp.upper_rear_chassis)

    def line_yz(p0, p1):
        return p0[1:], p1[1:]  # (y,z)

    # Intersection of lines lf-lo and uf-uo in YZ
    a, b = line_yz(lf, lo)
    c, d = line_yz(uf, uo)
    # Parametric: a + t (b-a) = c + s (d-c)
    A = np.column_stack([b - a, c - d])
    try:
        ts = np.linalg.lstsq(A, c - a, rcond=None)[0]
        yz = a + ts[0] * (b - a)
        # X at average of arm mid X
        x = 0.5 * (lf[0] + uf[0])
        return np.array([x, yz[0], yz[1]])
    except Exception:
        return np.array([lf[0], 0.0, 0.0])


def sweep_vertical_travel(
    hp: CornerHardpoints,
    tire: TireParams,
    z_min: float,
    z_max: float,
    steps: int,
    label: str = "",
) -> List[CornerState]:
    lengths = build_design_lengths(hp)
    zs = np.linspace(z_min, z_max, steps)
    # Always march through design (z=0) first for rocker branch continuity
    order = list(range(len(zs)))
    if z_min < 0 < z_max and steps > 1:
        z0 = int(np.argmin(np.abs(zs)))
        order = list(range(z0, len(zs))) + list(range(z0 - 1, -1, -1))

    states: List[Optional[CornerState]] = [None] * len(zs)
    theta = 0.0
    # Forward from design to bump
    prev_theta = 0.0
    for i in range(len(zs)):
        if zs[i] < 0:
            continue
        st = solve_corner(
            hp, tire, float(zs[i]), lengths=lengths, label=label, rocker_theta_seed=prev_theta
        )
        # Recover theta from rocker pose approximately via damper length path
        prev_theta = _estimate_theta(hp, lengths, st.rod_rocker_point, prev_theta)
        states[i] = st
    # Backward from design to droop
    prev_theta = 0.0
    for i in range(len(zs) - 1, -1, -1):
        if zs[i] > 0:
            continue
        if states[i] is not None and zs[i] == 0:
            prev_theta = _estimate_theta(hp, lengths, states[i].rod_rocker_point, 0.0)
            continue
        st = solve_corner(
            hp, tire, float(zs[i]), lengths=lengths, label=label, rocker_theta_seed=prev_theta
        )
        prev_theta = _estimate_theta(hp, lengths, st.rod_rocker_point, prev_theta)
        states[i] = st

    # Fill any gaps
    for i, st in enumerate(states):
        if st is None:
            states[i] = solve_corner(hp, tire, float(zs[i]), lengths=lengths, label=label)

    states_list = [s for s in states if s is not None]

    # Motion ratio: wheel travel per unit damper compression.
    # Positive when jounce shortens the damper (correct coilover packaging).
    # MR = dz_wheel / d(compression) = dz / (-dL) = -1 / (dL/dz)
    if len(states_list) >= 3:
        damps = np.array([s.damper_length_mm for s in states_list])
        travels = np.array([s.travel_mm for s in states_list])
        dL_dz = np.gradient(damps, travels)
        for i, s in enumerate(states_list):
            if abs(dL_dz[i]) > 1e-6:
                s.motion_ratio = float(-1.0 / dL_dz[i])
            else:
                s.motion_ratio = 0.0
    return states_list


def _estimate_theta(
    hp: CornerHardpoints,
    lengths: DesignLengths,
    rod_rocker: Vec3,
    fallback: float,
) -> float:
    """Estimate rocker angle from a known rod-rocker point."""
    pivot, axis, r1, r2 = _rocker_frame(hp)
    d = rod_rocker - pivot - lengths.rocker_rod_axial * axis
    x, y = float(np.dot(d, r1)), float(np.dot(d, r2))
    ang = float(np.arctan2(y, x))
    return ang - lengths.rocker_rod_angle0



def solve_full_car(
    params: VehicleParams,
    travels: Optional[Dict[str, float]] = None,
) -> Dict[str, CornerState]:
    """Solve all four corners. travels maps FL/FR/RL/RR → vertical travel mm."""
    travels = travels or {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}
    out = {}
    for label, hp in params.all_corners().items():
        out[label] = solve_corner(
            hp, params.tire_for(label), travels.get(label, 0.0), label=label
        )
    return out


def roll_center_height(left: CornerState, right: CornerState) -> float:
    """Front-view roll center height from left/right instant centers + contact patches."""
    # Line from left IC to left contact, right IC to right contact; RC = intersection with vehicle center
    # Classic: IC_L and IC_R connected; RC is where IC line crosses vehicle centerline,
    # more precisely intersection of lines (contact_L → IC_L) and (contact_R → IC_R).
    cl = left.contact_patch
    cr = right.contact_patch
    il = left.instant_center
    ir = right.instant_center

    def yz(p):
        return np.array([p[1], p[2]], dtype=float)

    a, b = yz(cl), yz(il)
    c, d = yz(cr), yz(ir)
    A = np.column_stack([b - a, c - d])
    try:
        ts = np.linalg.lstsq(A, c - a, rcond=None)[0]
        yz_rc = a + ts[0] * (b - a)
        return float(yz_rc[1])
    except Exception:
        return 0.0
