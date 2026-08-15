"""Full-car 3D Plotly visualization of double-wishbone suspension."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go

from src.geometry.hardpoints import TireParams, VehicleParams
from src.kinematics.wishbone import CornerState, solve_full_car

# Color palette
COL = {
    "lower": "#3B82F6",
    "upper": "#EF4444",
    "upright": "#F59E0B",
    "tierod": "#10B981",
    "rod": "#A855F7",
    "rocker": "#EC4899",
    "damper": "#06B6D4",
    "tire": "#374151",
    "wheel": "#9CA3AF",
    "chassis": "#6B7280",
    "ic": "#F97316",
    "ground": "#D1D5DB",
    "cg": "#DC2626",
}


def _line(a, b, color, width=5, name=None, showlegend=False) -> go.Scatter3d:
    a, b = np.asarray(a), np.asarray(b)
    return go.Scatter3d(
        x=[a[0], b[0]],
        y=[a[1], b[1]],
        z=[a[2], b[2]],
        mode="lines",
        line=dict(color=color, width=width),
        name=name or "",
        showlegend=showlegend,
        hoverinfo="skip",
    )


def _points(pts, color, size=4, name="", symbol="circle") -> go.Scatter3d:
    pts = np.asarray(pts)
    if pts.ndim == 1:
        pts = pts.reshape(1, 3)
    return go.Scatter3d(
        x=pts[:, 0],
        y=pts[:, 1],
        z=pts[:, 2],
        mode="markers",
        marker=dict(size=size, color=color, symbol=symbol),
        name=name,
        showlegend=bool(name),
    )


def _tire_mesh(
    center: np.ndarray,
    radius: float,
    width: float,
    side: float,
    n_u: int = 24,
    n_v: int = 12,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Simple torus-like tire as parametric surface (approximate cylinder + walls)."""
    # Wheel axis ≈ lateral Y
    thetas = np.linspace(0, 2 * np.pi, n_u)
    # Across width
    ys = np.linspace(-width / 2, width / 2, n_v)
    # Local frame: X' long, Y' lateral (axis), Z' up — ignore camber for mesh simplicity
    # Rotate slightly later if needed
    xs, ys_g, zs = [], [], []
    for th in thetas:
        for w in ys:
            # circle in XZ
            x = center[0] + radius * np.sin(th)
            y = center[1] + side * w  # width along lateral from center
            # For right side positive Y is outboard; width centered on wheel center
            y = center[1] + w * (1 if side >= 0 else 1)
            # Actually center width on wheel center along pure Y
            y = center[1] + w
            z = center[2] + radius * np.cos(th)
            xs.append(x)
            ys_g.append(y)
            zs.append(z)
    # Return as grid for Surface
    X = np.array(xs).reshape(n_u, n_v)
    Y = np.array(ys_g).reshape(n_u, n_v)
    Z = np.array(zs).reshape(n_u, n_v)
    return X, Y, Z


def _add_corner_traces(
    fig: go.Figure,
    state: CornerState,
    tire: TireParams,
    show_legend: bool = False,
) -> None:
    s = state
    # Lower wishbone A-arm
    fig.add_trace(
        _line(s.lower_front_chassis, s.lower_outer, COL["lower"], 6, "Lower A-arm", show_legend)
    )
    fig.add_trace(_line(s.lower_rear_chassis, s.lower_outer, COL["lower"], 6))
    fig.add_trace(
        _line(s.lower_front_chassis, s.lower_rear_chassis, COL["lower"], 3)
    )

    # Upper wishbone
    fig.add_trace(
        _line(s.upper_front_chassis, s.upper_outer, COL["upper"], 6, "Upper A-arm", show_legend)
    )
    fig.add_trace(_line(s.upper_rear_chassis, s.upper_outer, COL["upper"], 6))
    fig.add_trace(
        _line(s.upper_front_chassis, s.upper_rear_chassis, COL["upper"], 3)
    )

    # Upright
    fig.add_trace(_line(s.lower_outer, s.upper_outer, COL["upright"], 7, "Upright", show_legend))
    fig.add_trace(_line(s.lower_outer, s.wheel_center, COL["upright"], 4))
    fig.add_trace(_line(s.upper_outer, s.wheel_center, COL["upright"], 3))

    # Tierod
    fig.add_trace(
        _line(s.tierod_inner, s.tierod_outer, COL["tierod"], 5, "Tierod", show_legend)
    )

    # Push/pull rod
    fig.add_trace(
        _line(s.rod_arm_point, s.rod_rocker_point, COL["rod"], 5, "Push/Pull rod", show_legend)
    )

    # Rocker bellcrank: two lever arms about chassis pivot + web between rod/damper eyes
    fig.add_trace(
        _line(s.rocker_pivot, s.rod_rocker_point, COL["rocker"], 7, "Rocker", show_legend)
    )
    fig.add_trace(_line(s.rocker_pivot, s.rocker_damper_point, COL["rocker"], 7))
    fig.add_trace(_line(s.rod_rocker_point, s.rocker_damper_point, COL["rocker"], 4))
    # Closed triangle outline for the rocker plate
    rp, rr, rd = s.rocker_pivot, s.rod_rocker_point, s.rocker_damper_point
    fig.add_trace(
        go.Scatter3d(
            x=[rp[0], rr[0], rd[0], rp[0]],
            y=[rp[1], rr[1], rd[1], rp[1]],
            z=[rp[2], rr[2], rd[2], rp[2]],
            mode="lines",
            line=dict(color=COL["rocker"], width=3),
            name="",
            showlegend=False,
            hoverinfo="skip",
            opacity=0.9,
        )
    )

    # Rocker pivot — distinct chassis joint (axis stub + marker)
    axis_dir = np.array([1.0, 0.0, 0.0], dtype=float)
    # Approximate axis from rocker plane normal of the three points
    n = np.cross(rr - rp, rd - rp)
    n_norm = np.linalg.norm(n)
    if n_norm > 1e-9:
        axis_dir = n / n_norm
    half = 35.0  # mm half-length of visible pivot pin
    pin_a = rp - half * axis_dir
    pin_b = rp + half * axis_dir
    fig.add_trace(
        go.Scatter3d(
            x=[pin_a[0], pin_b[0]],
            y=[pin_a[1], pin_b[1]],
            z=[pin_a[2], pin_b[2]],
            mode="lines",
            line=dict(color="#FDE68A", width=10),
            name="Rocker pivot" if show_legend else "",
            showlegend=show_legend,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=[rp[0]],
            y=[rp[1]],
            z=[rp[2]],
            mode="markers+text",
            marker=dict(size=8, color="#FDE68A", symbol="diamond", line=dict(color="#EC4899", width=2)),
            text=["pivot"] if show_legend else [""],
            textposition="top center",
            textfont=dict(size=10, color="#FDE68A"),
            name="",
            showlegend=False,
            hovertemplate=f"Rocker pivot<br>X={rp[0]:.0f} Y={rp[1]:.0f} Z={rp[2]:.0f}<extra></extra>",
        )
    )
    # Rod / damper eyes on rocker
    fig.add_trace(
        _points([s.rod_rocker_point, s.rocker_damper_point], COL["rocker"], size=5)
    )

    # Damper (body mount → rocker eye)
    fig.add_trace(
        _line(s.damper_body, s.damper_eye, COL["damper"], 8, "Damper", show_legend)
    )
    fig.add_trace(_points([s.damper_body, s.damper_eye], COL["damper"], size=4))

    # Chassis hardpoints
    fig.add_trace(
        _points(
            [
                s.lower_front_chassis,
                s.lower_rear_chassis,
                s.upper_front_chassis,
                s.upper_rear_chassis,
                s.damper_body,
                s.tierod_inner,
            ],
            COL["chassis"],
            size=3,
        )
    )
    fig.add_trace(
        _points(
            [s.lower_outer, s.upper_outer, s.tierod_outer, s.wheel_center],
            COL["upright"],
            size=4,
        )
    )

    # Instant center marker
    fig.add_trace(
        _points([s.instant_center], COL["ic"], size=5, name="Instant center" if show_legend else "")
    )

    # Tire surface
    X, Y, Z = _tire_mesh(s.wheel_center, tire.radius_mm, tire.width_mm, s.side)
    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale=[[0, COL["tire"]], [1, "#4B5563"]],
            showscale=False,
            opacity=0.85,
            name="Tire" if show_legend else "",
            showlegend=show_legend,
            hoverinfo="skip",
        )
    )

    # Wheel center hub
    fig.add_trace(_points([s.wheel_center], COL["wheel"], size=6))
    # Contact patch
    fig.add_trace(_points([s.contact_patch], "#FBBF24", size=3))


def _chassis_box(params: VehicleParams) -> List[go.Scatter3d]:
    """Simple chassis silhouette for spatial reference."""
    wb = params.wheelbase_mm
    # Approximate from hardpoints
    y_half = min(params.track_front_mm, params.track_rear_mm) * 0.22
    z0, z1 = 80, 420
    x0, x1 = 350, wb + 200
    corners = [
        [x0, -y_half, z0],
        [x1, -y_half, z0],
        [x1, y_half, z0],
        [x0, y_half, z0],
        [x0, -y_half, z0],
        [x0, -y_half, z1],
        [x1, -y_half, z1],
        [x1, y_half, z1],
        [x0, y_half, z1],
        [x0, -y_half, z1],
    ]
    c = np.array(corners)
    traces = [
        go.Scatter3d(
            x=c[:, 0],
            y=c[:, 1],
            z=c[:, 2],
            mode="lines",
            line=dict(color=COL["chassis"], width=2, dash="dot"),
            name="Chassis",
            showlegend=True,
            hoverinfo="skip",
            opacity=0.5,
        )
    ]
    # CG marker
    cg_x = params.wheelbase_mm * (1.0 - params.front_weight_bias)
    # design uses X from front axle ~550 mid; place CG between axles
    front_x = params.front.wheel_center[0]
    rear_x = params.rear.wheel_center[0]
    cg = np.array(
        [
            front_x + params.front_weight_bias * 0 + (1 - params.front_weight_bias) * (rear_x - front_x) * 0
            + (rear_x - front_x) * (1 - params.front_weight_bias),
            0.0,
            params.cg_height_mm,
        ]
    )
    # cleaner:
    cg = np.array(
        [
            front_x + (rear_x - front_x) * (1.0 - params.front_weight_bias),
            0.0,
            params.cg_height_mm,
        ]
    )
    traces.append(
        go.Scatter3d(
            x=[cg[0]],
            y=[cg[1]],
            z=[cg[2]],
            mode="markers+text",
            marker=dict(size=8, color=COL["cg"], symbol="diamond"),
            text=["CG"],
            textposition="top center",
            name="CG",
            showlegend=True,
        )
    )
    # Ground plane outline
    gx = np.array([0, wb + 400, wb + 400, 0, 0])
    gy = np.array([-params.track_front_mm, -params.track_front_mm, params.track_front_mm, params.track_front_mm, -params.track_front_mm]) * 0.7
    gz = np.zeros(5)
    traces.append(
        go.Scatter3d(
            x=gx,
            y=gy,
            z=gz,
            mode="lines",
            line=dict(color=COL["ground"], width=2),
            name="Ground",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    return traces


def build_car_figure(
    params: VehicleParams,
    travels: Optional[Dict[str, float]] = None,
    show_instant_centers: bool = True,
) -> go.Figure:
    travels = travels or {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}
    states = solve_full_car(params, travels)

    fig = go.Figure()
    for tr in _chassis_box(params):
        fig.add_trace(tr)

    first = True
    for label, state in states.items():
        _add_corner_traces(fig, state, params.tire_for(label), show_legend=first)
        first = False

    # Axis styling — automotive view
    fig.update_layout(
        title=dict(
            text="Double Wishbone — Full Car",
            x=0.02,
            font=dict(size=16, color="#E5E7EB"),
        ),
        scene=dict(
            xaxis=dict(
                title="X aft (mm)",
                backgroundcolor="#111827",
                gridcolor="#1F2937",
                zerolinecolor="#374151",
                color="#9CA3AF",
            ),
            yaxis=dict(
                title="Y right (mm)",
                backgroundcolor="#111827",
                gridcolor="#1F2937",
                zerolinecolor="#374151",
                color="#9CA3AF",
            ),
            zaxis=dict(
                title="Z up (mm)",
                backgroundcolor="#111827",
                gridcolor="#1F2937",
                zerolinecolor="#374151",
                color="#9CA3AF",
            ),
            aspectmode="data",
            bgcolor="#0B1220",
            camera=dict(
                eye=dict(x=1.6, y=1.4, z=0.9),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        paper_bgcolor="#0B1220",
        plot_bgcolor="#0B1220",
        font=dict(color="#E5E7EB", family="Inter, system-ui, sans-serif"),
        legend=dict(
            bgcolor="rgba(17,24,39,0.8)",
            bordercolor="#374151",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=700,
    )
    return fig
