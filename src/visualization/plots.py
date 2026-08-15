"""Performance plot builders for suspension analysis."""

from __future__ import annotations

from typing import Dict, List

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.kinematics.metrics import Metrics

THEME = dict(
    paper_bgcolor="#0B1220",
    plot_bgcolor="#111827",
    font=dict(color="#E5E7EB", family="Inter, system-ui, sans-serif", size=12),
    colorway=["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#A855F7", "#06B6D4"],
)

AXIS = dict(
    gridcolor="#1F2937",
    zerolinecolor="#374151",
    color="#9CA3AF",
    title_font=dict(size=12),
)


def _style(fig: go.Figure, title: str, height: int = 360) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(size=14)),
        **THEME,
        height=height,
        margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(17,24,39,0.7)", bordercolor="#374151", borderwidth=1),
    )
    fig.update_xaxes(**AXIS)
    fig.update_yaxes(**AXIS)
    return fig


def build_performance_figures(metrics: Metrics) -> Dict[str, go.Figure]:
    figs: Dict[str, go.Figure] = {}

    # --- Camber vs travel (all corners) ---
    fig = go.Figure()
    for name, df, color in [
        ("FL", metrics.front_left, "#3B82F6"),
        ("FR", metrics.front_right, "#60A5FA"),
        ("RL", metrics.rear_left, "#EF4444"),
        ("RR", metrics.rear_right, "#F87171"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df["travel_mm"],
                y=df["camber_deg"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
            )
        )
    fig.update_xaxes(title="Wheel travel (mm)  [+ bump]")
    fig.update_yaxes(title="Camber (deg)  [− top-in]")
    figs["camber"] = _style(fig, "Camber gain vs wheel travel")

    # --- Toe vs travel ---
    fig = go.Figure()
    for name, df, color in [
        ("FL", metrics.front_left, "#3B82F6"),
        ("FR", metrics.front_right, "#60A5FA"),
        ("RL", metrics.rear_left, "#EF4444"),
        ("RR", metrics.rear_right, "#F87171"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df["travel_mm"],
                y=df["toe_deg"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
            )
        )
    fig.update_xaxes(title="Wheel travel (mm)")
    fig.update_yaxes(title="Toe (deg)  [+ toe-in]")
    figs["toe"] = _style(fig, "Toe change vs wheel travel")

    # --- Motion ratio ---
    fig = go.Figure()
    for name, df, color in [
        ("FL", metrics.front_left, "#3B82F6"),
        ("FR", metrics.front_right, "#60A5FA"),
        ("RL", metrics.rear_left, "#EF4444"),
        ("RR", metrics.rear_right, "#F87171"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df["travel_mm"],
                y=df["motion_ratio"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
            )
        )
    fig.update_xaxes(title="Wheel travel (mm)  [+ jounce]")
    fig.update_yaxes(title="Motion ratio  (wheel / damper compression)")
    figs["motion_ratio"] = _style(
        fig, "Motion ratio vs wheel travel  (+ = damper compresses in jounce)"
    )

    # --- Damper travel ---
    fig = go.Figure()
    for name, df, color in [
        ("FL", metrics.front_left, "#3B82F6"),
        ("FR", metrics.front_right, "#60A5FA"),
        ("RL", metrics.rear_left, "#EF4444"),
        ("RR", metrics.rear_right, "#F87171"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df["travel_mm"],
                y=df["damper_travel_mm"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
            )
        )
    fig.update_xaxes(title="Wheel travel (mm)  [+ jounce]")
    fig.update_yaxes(title="Damper Δ length (mm)  [− compression / + extension]")
    figs["damper_travel"] = _style(
        fig, "Damper travel vs wheel travel  (jounce should compress)"
    )

    # --- Track width (heave) ---
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=metrics.front_heave["travel_mm"],
            y=metrics.front_heave["track_mm"],
            mode="lines",
            name="Front",
            line=dict(color="#3B82F6", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.rear_heave["travel_mm"],
            y=metrics.rear_heave["track_mm"],
            mode="lines",
            name="Rear",
            line=dict(color="#EF4444", width=2),
        )
    )
    fig.update_xaxes(title="Heave travel (mm)")
    fig.update_yaxes(title="Track width (mm)")
    figs["track"] = _style(fig, "Track width vs heave")

    # --- Roll center height ---
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=metrics.front_heave["travel_mm"],
            y=metrics.front_heave["roll_center_z_mm"],
            mode="lines",
            name="Front RC",
            line=dict(color="#3B82F6", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.rear_heave["travel_mm"],
            y=metrics.rear_heave["roll_center_z_mm"],
            mode="lines",
            name="Rear RC",
            line=dict(color="#EF4444", width=2),
        )
    )
    fig.update_xaxes(title="Heave travel (mm)")
    fig.update_yaxes(title="Roll center height (mm)")
    figs["roll_center"] = _style(fig, "Roll center height vs heave")

    # --- Camber in roll ---
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=metrics.front_roll["roll_deg"],
            y=metrics.front_roll["camber_L"],
            mode="lines",
            name="Front L",
            line=dict(color="#3B82F6", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.front_roll["roll_deg"],
            y=metrics.front_roll["camber_R"],
            mode="lines",
            name="Front R",
            line=dict(color="#60A5FA", width=2, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.rear_roll["roll_deg"],
            y=metrics.rear_roll["camber_L"],
            mode="lines",
            name="Rear L",
            line=dict(color="#EF4444", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.rear_roll["roll_deg"],
            y=metrics.rear_roll["camber_R"],
            mode="lines",
            name="Rear R",
            line=dict(color="#F87171", width=2, dash="dash"),
        )
    )
    fig.update_xaxes(title="Body roll (deg)  [+ right side down]")
    fig.update_yaxes(title="Camber (deg)")
    figs["camber_roll"] = _style(fig, "Camber vs body roll")

    # --- Scrub & trail (FL / RL design sweeps) ---
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Scrub radius", "Mechanical trail"))
    for name, df, color in [
        ("FL", metrics.front_left, "#3B82F6"),
        ("RL", metrics.rear_left, "#EF4444"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df["travel_mm"],
                y=df["scrub_radius_mm"],
                mode="lines",
                name=f"{name} scrub",
                line=dict(color=color, width=2),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df["travel_mm"],
                y=df["trail_mm"],
                mode="lines",
                name=f"{name} trail",
                line=dict(color=color, width=2, dash="dot"),
            ),
            row=1,
            col=2,
        )
    fig.update_xaxes(title="Wheel travel (mm)", row=1, col=1)
    fig.update_xaxes(title="Wheel travel (mm)", row=1, col=2)
    fig.update_yaxes(title="Scrub (mm)", row=1, col=1)
    fig.update_yaxes(title="Trail (mm)", row=1, col=2)
    figs["scrub_trail"] = _style(fig, "Scrub radius & mechanical trail", height=380)

    # --- Castor / KPI static ---
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=metrics.front_left["travel_mm"],
            y=metrics.front_left["castor_deg"],
            mode="lines",
            name="FL castor",
            line=dict(color="#A855F7", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.front_left["travel_mm"],
            y=metrics.front_left["kpi_deg"],
            mode="lines",
            name="FL KPI",
            line=dict(color="#F59E0B", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.rear_left["travel_mm"],
            y=metrics.rear_left["castor_deg"],
            mode="lines",
            name="RL castor",
            line=dict(color="#A855F7", width=2, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=metrics.rear_left["travel_mm"],
            y=metrics.rear_left["kpi_deg"],
            mode="lines",
            name="RL KPI",
            line=dict(color="#F59E0B", width=2, dash="dash"),
        )
    )
    fig.update_xaxes(title="Wheel travel (mm)")
    fig.update_yaxes(title="Angle (deg)")
    figs["castor_kpi"] = _style(fig, "Castor & kingpin inclination vs travel")

    return figs
