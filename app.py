"""
Double Wishbone Suspension Visualization Tool
=============================================
Interactive full-car kinematics explorer with adjustable hardpoints,
push/pull rod & rocker layout, tire geometry, and performance plots.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import yaml

from src.geometry.hardpoints import (
    CornerHardpoints,
    VehicleParams,
    load_params,
    params_from_dict,
    params_to_dict,
    v3,
)
from src.kinematics.metrics import compute_metrics
from src.kinematics.wishbone import solve_full_car
from src.visualization.car_3d import build_car_figure
from src.visualization.plots import build_performance_figures

st.set_page_config(
    page_title="Double Wishbone Visualizer",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #0B1220; }
    section[data-testid="stSidebar"] { background-color: #111827; }
    h1, h2, h3 { color: #F3F4F6 !important; }
    div[data-testid="stMetricValue"] { color: #E5E7EB; }
    .block-container { padding-top: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _migrate_tire_keys(d: dict) -> None:
    """Older sessions/YAML had a single ``tire`` used on all four corners."""
    if "tire_front" not in d or "tire_rear" not in d:
        legacy = d.get("tire") or {}
        d.setdefault("tire_front", dict(legacy))
        d.setdefault("tire_rear", dict(legacy))


def _init_state():
    if "params_dict" not in st.session_state:
        params = load_params()
        st.session_state.params_dict = params_to_dict(params)
    _migrate_tire_keys(st.session_state.params_dict)
    if "travels" not in st.session_state:
        st.session_state.travels = {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}


_init_state()


def get_params() -> VehicleParams:
    return params_from_dict(st.session_state.params_dict)


def set_params(p: VehicleParams) -> None:
    st.session_state.params_dict = params_to_dict(p)


# ---------------------------------------------------------------------------
# Sidebar helpers
# ---------------------------------------------------------------------------
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
    "rod_arm_point": "Rod ↔ wishbone pickup",
    "rod_rocker_point": "Rod ↔ rocker",
    "rocker_pivot": "Rocker pivot",
    "rocker_damper_point": "Rocker ↔ damper",
    "damper_body": "Damper body (chassis)",
    "arb_drop_link": "ARB drop link",
}


def xyz_inputs(key_prefix: str, label: str, values, step: float = 5.0):
    c1, c2, c3 = st.columns(3)
    x = c1.number_input(f"{label} X", value=float(values[0]), step=step, key=f"{key_prefix}_x")
    y = c2.number_input(f"{label} Y", value=float(values[1]), step=step, key=f"{key_prefix}_y")
    z = c3.number_input(f"{label} Z", value=float(values[2]), step=step, key=f"{key_prefix}_z")
    return [x, y, z]


def edit_corner_sidebar(axle: str) -> None:
    """Edit front or rear left-side hardpoints (right is mirrored)."""
    d = st.session_state.params_dict[axle]
    st.caption("Edit **left** side hardpoints. Right side is mirrored about vehicle centerline.")

    d["rod_mode"] = st.selectbox(
        "Rod mode",
        ["pushrod", "pullrod"],
        index=0 if d.get("rod_mode", "pushrod") == "pushrod" else 1,
        key=f"{axle}_rod_mode",
    )
    d["rod_wishbone"] = st.selectbox(
        "Rod attaches to",
        ["lower", "upper"],
        index=0 if d.get("rod_wishbone", "lower") == "lower" else 1,
        key=f"{axle}_rod_arm",
    )
    d["damper_length_mm"] = st.number_input(
        "Design damper length (mm)",
        value=float(d.get("damper_length_mm", 220)),
        step=1.0,
        key=f"{axle}_damper_len",
    )
    d["static_camber_deg"] = st.number_input(
        "Static camber (deg, − top-in)",
        value=float(d.get("static_camber_deg", -1.0)),
        step=0.05,
        format="%.2f",
        key=f"{axle}_static_camber",
    )
    d["static_toe_deg"] = st.number_input(
        "Static toe (deg, + toe-in)",
        value=float(d.get("static_toe_deg", 0.10)),
        step=0.05,
        format="%.2f",
        key=f"{axle}_static_toe",
    )

    groups = {
        "Lower A-arm": [
            "lower_front_chassis",
            "lower_rear_chassis",
            "lower_outer",
        ],
        "Upper A-arm": [
            "upper_front_chassis",
            "upper_rear_chassis",
            "upper_outer",
        ],
        "Wheel / spindle": ["wheel_center"],
        "Steering (tierod)": ["tierod_inner", "tierod_outer"],
        "Push/Pull rod": ["rod_arm_point", "rod_rocker_point"],
        "Rocker": ["rocker_pivot", "rocker_damper_point"],
        "Damper": ["damper_body"],
    }

    for group, keys in groups.items():
        with st.expander(group, expanded=(group in ("Lower A-arm", "Wheel / spindle"))):
            for k in keys:
                d[k] = xyz_inputs(f"{axle}_{k}", POINT_LABELS[k], d[k])


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🏎️ Suspension Lab")
    st.caption("Double wishbone · full car · kinematics")

    if st.button("Reset to defaults", width="stretch"):
        set_params(load_params())
        st.session_state.travels = {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}
        st.rerun()

    tab_v, tab_t, tab_f, tab_r, tab_a = st.tabs(
        ["Vehicle", "Tire", "Front", "Rear", "Analysis"]
    )

    with tab_v:
        v = st.session_state.params_dict["vehicle"]
        v["wheelbase_mm"] = st.number_input("Wheelbase (mm)", value=float(v["wheelbase_mm"]), step=10.0)
        v["track_front_mm"] = st.number_input("Front track (mm)", value=float(v["track_front_mm"]), step=5.0)
        v["track_rear_mm"] = st.number_input("Rear track (mm)", value=float(v["track_rear_mm"]), step=5.0)
        v["ride_height_mm"] = st.number_input("Ride height (mm)", value=float(v["ride_height_mm"]), step=1.0)
        v["cg_height_mm"] = st.number_input("CG height (mm)", value=float(v["cg_height_mm"]), step=5.0)
        v["mass_kg"] = st.number_input("Mass (kg)", value=float(v["mass_kg"]), step=5.0)
        v["front_weight_bias"] = st.slider(
            "Front weight bias", 0.30, 0.70, float(v["front_weight_bias"]), 0.01
        )

    with tab_t:
        def _edit_tire(key: str, heading: str) -> None:
            t = st.session_state.params_dict[key]
            st.subheader(heading)
            t["size"] = st.text_input(
                "Size", value=str(t.get("size", "")), key=f"{key}_size"
            )
            t["radius_mm"] = st.number_input(
                "Tire radius (mm)", value=float(t["radius_mm"]), step=1.0, key=f"{key}_radius"
            )
            t["width_mm"] = st.number_input(
                "Tire width (mm)", value=float(t["width_mm"]), step=5.0, key=f"{key}_width"
            )
            t["wheel_diameter_in"] = st.number_input(
                "Wheel diameter (in)",
                value=float(t["wheel_diameter_in"]),
                step=0.5,
                key=f"{key}_wdia",
            )
            t["wheel_width_mm"] = st.number_input(
                "Wheel width (mm)",
                value=float(t["wheel_width_mm"]),
                step=5.0,
                key=f"{key}_wwidth",
            )
            t["offset_mm"] = st.number_input(
                "Wheel offset (mm)", value=float(t["offset_mm"]), step=1.0, key=f"{key}_off"
            )
            t["sidewall_mm"] = st.number_input(
                "Sidewall (mm)", value=float(t["sidewall_mm"]), step=1.0, key=f"{key}_side"
            )

        _edit_tire("tire_front", "Front")
        st.markdown("---")
        _edit_tire("tire_rear", "Rear")

    with tab_f:
        edit_corner_sidebar("front")

    with tab_r:
        edit_corner_sidebar("rear")

    with tab_a:
        a = st.session_state.params_dict["analysis"]
        a["travel_min_mm"] = st.number_input("Travel min (mm)", value=float(a["travel_min_mm"]), step=5.0)
        a["travel_max_mm"] = st.number_input("Travel max (mm)", value=float(a["travel_max_mm"]), step=5.0)
        a["travel_steps"] = st.number_input("Travel steps", value=int(a["travel_steps"]), step=2, min_value=5)
        a["roll_max_deg"] = st.number_input("Roll max (deg)", value=float(a["roll_max_deg"]), step=0.5)
        a["roll_steps"] = st.number_input("Roll steps", value=int(a["roll_steps"]), step=2, min_value=5)

        st.markdown("---")
        st.markdown("**Pose for 3D view**")
        mode = st.radio("Pose mode", ["Independent corners", "Heave", "Roll", "Pitch"], horizontal=False)
        tr = st.session_state.travels
        if mode == "Independent corners":
            tr["FL"] = st.slider("FL travel (mm)", -50.0, 50.0, float(tr["FL"]), 1.0)
            tr["FR"] = st.slider("FR travel (mm)", -50.0, 50.0, float(tr["FR"]), 1.0)
            tr["RL"] = st.slider("RL travel (mm)", -50.0, 50.0, float(tr["RL"]), 1.0)
            tr["RR"] = st.slider("RR travel (mm)", -50.0, 50.0, float(tr["RR"]), 1.0)
        elif mode == "Heave":
            h = st.slider("Heave (mm)", -50.0, 50.0, 0.0, 1.0)
            tr.update({"FL": h, "FR": h, "RL": h, "RR": h})
        elif mode == "Roll":
            r = st.slider("Roll (deg, + R down)", -5.0, 5.0, 0.0, 0.1)
            params = get_params()
            dz_f = (params.track_front_mm / 2) * __import__("math").sin(__import__("math").radians(r))
            dz_r = (params.track_rear_mm / 2) * __import__("math").sin(__import__("math").radians(r))
            tr.update({"FL": dz_f, "FR": -dz_f, "RL": dz_r, "RR": -dz_r})
        else:  # Pitch
            p = st.slider("Pitch (deg, + nose up)", -3.0, 3.0, 0.0, 0.1)
            params = get_params()
            # Approximate: front/rear opposite travel from pitch about mid-wheelbase
            half_wb = params.wheelbase_mm / 2
            dz = half_wb * __import__("math").sin(__import__("math").radians(p))
            tr.update({"FL": -dz, "FR": -dz, "RL": dz, "RR": dz})

    st.markdown("---")
    # Export / import
    export = yaml.dump(st.session_state.params_dict, default_flow_style=False, sort_keys=False)
    st.download_button(
        "Download params YAML",
        data=export,
        file_name="suspension_params.yaml",
        mime="text/yaml",
        width="stretch",
    )
    up = st.file_uploader("Load params YAML", type=["yaml", "yml"])
    if up is not None:
        loaded = yaml.safe_load(up.read())
        _migrate_tire_keys(loaded)
        st.session_state.params_dict = loaded
        st.success("Loaded parameters.")
        st.rerun()


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("Double Wishbone Suspension Visualizer")
st.caption(
    "Ariel Atom 3 starting point · full car (FL / FR / RL / RR) · "
    "adjustable hardpoints · pushrod & rocker · camber / toe / roll center / MR plots"
)

params = get_params()
travels = dict(st.session_state.travels)

main_tab_3d, main_tab_plots, main_tab_kpi, main_tab_help = st.tabs(
    ["3D Vehicle", "Performance Plots", "KPI Table", "About / Coordinates"]
)

with main_tab_3d:
    col_view, col_info = st.columns([3.2, 1])
    with col_view:
        with st.spinner("Solving kinematics…"):
            fig3d = build_car_figure(params, travels)
        st.plotly_chart(fig3d, use_container_width=True)

    with col_info:
        st.subheader("Live pose")
        try:
            states = solve_full_car(params, travels)
            for label in ("FL", "FR", "RL", "RR"):
                s = states[label]
                st.markdown(f"**{label}**  ·  travel `{s.travel_mm:.1f}` mm")
                damp_state = (
                    "compression" if s.damper_travel_mm < -0.05
                    else ("extension" if s.damper_travel_mm > 0.05 else "design")
                )
                st.write(
                    f"Camber `{s.camber_deg:+.2f}°` · Toe `{s.toe_deg:+.2f}°`  \n"
                    f"MR `{s.motion_ratio:.3f}` · Damper Δ `{s.damper_travel_mm:+.1f}` mm ({damp_state})  \n"
                    f"Castor `{s.castor_deg:.2f}°` · KPI `{s.kpi_deg:.2f}°`"
                )
                st.markdown("---")
        except Exception as e:
            st.error(f"Solve failed: {e}")

        st.markdown(
            """
            **Legend**
            - 🔵 Lower A-arm  
            - 🔴 Upper A-arm  
            - 🟡 Upright  
            - 🟢 Tierod  
            - 🟣 Push/Pull rod  
            - 🩷 Rocker (arms about chassis pivot)  
            - 💛 Rocker pivot pin  
            - 🩵 Damper (shortens in jounce)  
            """
        )

with main_tab_plots:
    with st.spinner("Running travel / roll sweeps…"):
        metrics = compute_metrics(params)
        figs = build_performance_figures(metrics)

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.plotly_chart(figs["camber"], use_container_width=True)
    with r1c2:
        st.plotly_chart(figs["toe"], use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.plotly_chart(figs["motion_ratio"], use_container_width=True)
    with r2c2:
        st.plotly_chart(figs["damper_travel"], use_container_width=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.plotly_chart(figs["track"], use_container_width=True)
    with r3c2:
        st.plotly_chart(figs["roll_center"], use_container_width=True)

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        st.plotly_chart(figs["camber_roll"], use_container_width=True)
    with r4c2:
        st.plotly_chart(figs["scrub_trail"], use_container_width=True)

    st.plotly_chart(figs["castor_kpi"], use_container_width=True)

with main_tab_kpi:
    with st.spinner("Computing KPIs…"):
        if "metrics" not in dir() or metrics is None:
            metrics = compute_metrics(params)
    st.subheader("Design-position summary")
    # Display as two-column metrics
    items = list(metrics.summary.items())
    cols = st.columns(4)
    for i, (k, v) in enumerate(items):
        cols[i % 4].metric(k, f"{v:.3f}" if abs(v) < 10 else f"{v:.2f}")

    st.subheader("Front-left travel sweep data")
    st.dataframe(metrics.front_left.style.format("{:.3f}"), width="stretch")

    st.subheader("Front heave / roll-center data")
    st.dataframe(metrics.front_heave.style.format("{:.3f}"), width="stretch")

    st.download_button(
        "Download FL sweep CSV",
        data=metrics.front_left.to_csv(index=False),
        file_name="fl_travel_sweep.csv",
        mime="text/csv",
    )

with main_tab_help:
    st.markdown(
        """
        ## Coordinate system
        Right-handed, vehicle-fixed at design ride height:

        | Axis | Direction |
        |------|-----------|
        | **+X** | Rearward (aft) |
        | **+Y** | Right |
        | **+Z** | Up |

        Origin is mid-track at ground level. The default setup is an
        **Ariel Atom 3** starting point: front axle X = 500 mm, rear
        X = 2845 mm (published wheelbase 2345 mm). Wishbone, rack, and
        rocker coordinates are estimated — see the comments in
        `data/default_params.yaml` for what is published vs fitted.

        ## What is modeled
        - **Double wishbone** (unequal A-arms) with fixed chassis hinges  
        - **Upright** length constraint between UBJ / LBJ  
        - **Tierod** length → toe curve  
        - **Pushrod or pullrod** from arm pickup to rocker  
        - **Rocker (bellcrank)** rotating about a chassis pivot  
        - **Damper** eye-to-eye from rocker to chassis mount  
        - **Full car** — front/rear, left/right (right mirrored from left)

        ## Performance outputs
        | Plot | Use |
        |------|-----|
        | Camber vs travel | Camber gain in bump / droop |
        | Toe vs travel | Bump steer |
        | Motion ratio | Spring/damper rate at wheel |
        | Damper travel | Packaging & stroke check |
        | Track vs heave | Jacking / scrub |
        | Roll center vs heave | Lateral load transfer sensitivity |
        | Camber vs roll | Outside-wheel camber in cornering |
        | Scrub / trail | Steering feedback & torque |
        | Castor / KPI | Self-aligning & scrub geometry |

        ## Tips
        1. Edit **Front** / **Rear** left hardpoints in the sidebar; right side mirrors.  
        2. Use **Analysis → Pose** sliders to animate heave, roll, pitch, or corners.  
        3. Export YAML to save a setup; re-upload to restore.  
        4. Motion ratio is
           \( \\mathrm{MR} = \\mathrm{d}z_\\mathrm{wheel} / \\mathrm{d}(\\mathrm{compression}) \),
           positive when the damper shortens in jounce.  
        5. The **rocker pivot** is a chassis hardpoint (gold pin in 3D); both the
           push/pull-rod eye and the damper eye lever about it.  
        6. Geometry is kinematic only (no compliance, no tire deflection model beyond radius).  
        7. What we optimize for, and what each plot should look like:
           `docs/design-guide.md`.
        """
    )
