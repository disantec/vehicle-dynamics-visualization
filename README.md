# Double Wishbone Suspension Visualizer

Interactive full-car visualization and kinematics tool for double-wishbone
suspension with pushrod/pullrod, rocker, and damper packaging.

Default geometry is an **Ariel Atom 3** starting point: published vehicle,
tyre, and street-alignment figures, with wishbone / pushrod / rocker
coordinates estimated so the kinematic plots stay driveable (see
`data/default_params.yaml` for sources).

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B)

## Features

- **Full car** — front & rear, left & right (right side mirrored from left hardpoints)
- **Adjustable hardpoints** — upper/lower A-arms, upright/wheel center, tierod
- **Tire / wheel** — staggered front/rear size, radius, width, offset, wheel diameter
- **Pushrod or pullrod** — arm pickup, rocker attachment
- **Rocker + damper** — pivot, lever points, chassis damper mount
- **3D view** — pose via heave, roll, pitch, or per-corner travel
- **Performance plots**
  - Camber & toe vs wheel travel
  - Motion ratio & damper travel
  - Track width & roll-center height vs heave
  - Camber vs body roll
  - Scrub radius, mechanical trail, castor, KPI
- **Import / export** — YAML setups and CSV sweep data

## Coordinate system

| Axis | Direction |
|------|-----------|
| +X   | Rearward (aft) |
| +Y   | Right |
| +Z   | Up |

Units: millimeters, degrees.

## Quick start

```bash
# from repo root
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Project layout

```
app.py                      # Streamlit UI
data/default_params.yaml    # Default vehicle & hardpoints
docs/design-guide.md        # What we optimize for, and what each plot should look like
src/
  geometry/hardpoints.py    # Parameter models, load/save
  kinematics/
    wishbone.py             # DW kinematics + rocker/damper
    metrics.py              # Travel/roll sweeps & KPIs
  visualization/
    car_3d.py               # Plotly 3D full-car figure
    plots.py                # Performance charts
```

## Workflow

1. Open **Vehicle / Tire / Front / Rear** sidebar tabs to set packaging.
2. Use **Analysis** to set sweep ranges and 3D pose (heave/roll/pitch).
3. Inspect **3D Vehicle** for packaging and instant centers.
4. Review **Performance Plots** and **KPI Table** for camber gain, bump steer,
   motion ratio, roll center, etc.
5. Download YAML to version a setup.

## Notes

- Kinematic model only — no bushing compliance or force-based tire model.
- Motion ratio is wheel travel over damper length change
  \(\mathrm{MR} = dz_\mathrm{wheel}/dL_\mathrm{damper}\).
- Roll center is the front-view geometric construction from left/right
  instant centers and contact patches.
- Default geometry is an Ariel Atom 3 **starting point**, not a scanned car.
  Wheelbase, track, tyres, ride height, and street camber/toe are published;
  ball joints, rack, and rocker points are estimated. Reset to defaults after
  changing them.
- Why the plots are shaped the way they are:
  [docs/design-guide.md](docs/design-guide.md).

## License

MIT
