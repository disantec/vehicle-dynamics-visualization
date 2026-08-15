# Suspension design guide

What we are optimizing for in this visualizer, and what each change *feels*
like. Open this next to the **Performance Plots** tab.

The car is a street-legal track toy in the Ariel Atom 3 mould: light,
mid-engine, double wishbone, pushrod both ends. The driver is competent but
not a professional. Fast is the goal. Predictable is the constraint.

This is a **kinematic** model only — no springs, dampers, ARBs, bushings, or
tire force. Geometry sets the *shape* of the responses. Rates and bars come
later.

---

## Sign conventions (this app)

| Quantity | + means |
|----------|---------|
| X | rearward (aft) |
| Y | right (left-side hardpoints are written with +Y, then mirrored) |
| Z | up |
| Wheel travel | bump / jounce (wheel toward the body) |
| Camber | top of the tire *outward*. Negative = top-in |
| Toe | toe-in |
| Castor | kingpin top rearward |
| KPI | kingpin top inward |
| Scrub | contact outboard of the kingpin/ground intersection |
| Trail (solver) | `kp_ground.x − contact.x`. Conventional trail (contact aft of the steer axis) is **negative** because +X is aft |
| Damper ΔL | longer than design. Compression in jounce is **negative** |
| Motion ratio | \(dz_\text{wheel} / d(\text{compression})\). Positive = damper shortens in jounce |
| Roll | right side down |

---

## Ranked goals

1. **No surprises.** Curves are smooth. No sign flips, no hooks, no roll
   centre exploding to metres.
2. **The front talks first.** If someone asks too much, the car understeers
   a little more, not less. The rear does not “come alive.”
3. **The wheel does not steer itself.** Bump steer is the #1 driveability
   killer on a light open-wheeler.
4. **The damper is a damper.** Jounce shortens it. The rocker never goes
   over-centre.
5. **The tire stays in its window.** Enough camber in roll that the outside
   front still works; not so much rear camber gain that a curb unloads it.
6. **Steering has a centre.** Small scrub, conventional trail, mid-range
   castor. Kickback is optional; self-return is not.
7. **Lap time is allowed to lose to honesty.** A slightly slower, linear
   car is the target. Pro-darty comes later, on purpose.

---

## Cause → feel → what we do

These are the thoughts behind the hardpoint choices. Read them as
tradeoffs, not commandments.

### Roll centre height

- **Higher RC at one axle** → more of that axle’s lateral load goes through
  the links, less through the springs. More jacking. That end of the car
  works harder and gives up first.
- **Raise the front RC** → more front load transfer → **understeer**.
- **Raise the rear RC** → more rear load transfer → **oversteer**,
  especially over a curb where jacking is a vertical punch.
- **Front RC a little above the rear, or equal** is the safe split for this
  car. Do **not** put the rear clearly above the front.
- **Both RCs modest and above ground** (front ~25–40 mm, rear ~20–30 mm).
  Below ground is not automatically fatal, but it usually means more roll
  and a vaguer platform. Through the floor with a steep slope is bad.
- **Low rear RC** (lots of rear roll) → the rear takes longer to take a
  set. The platform feels **vague**: you are not sure where the rear is,
  and a mid-corner bump changes the attitude more than you wanted. That is
  why we raised the rear RC after the 17" tire dropped it into single
  digits — not to put it *above* the front, but to give the rear a firmer
  geometric seat.
- **High rear RC** → the rear is “in” immediately, then it can let go at
  once. Snap, not vague.
- **RC that migrates a lot over heave or roll** → the balance you felt at
  turn-in is not the balance at mid-corner. The plot should look boring.

### Instant centres / jacking

- Nearly parallel A-arms → IC at infinity → RC construction is numerically
  wild (the plot shoots to ±metres). That is a packaging red flag, not a
  setup.
- A well-inboard IC with a sensible height is how you get a quiet RC and
  some camber gain at the same time.

### Camber vs travel

- Static: enough negative that a cold street/track tire still works in a
  straight line. Atom street figures are about **−1.0° front / −1.25° rear**.
- Gentle negative slope in bump. Rear **calmer than front**.
- Too little gain → outside tire leans with the body and washes.
- Too much rear gain → outside rear goes very negative on a curb and the
  car swaps ends.
- A U-shape or a reversal through ride height is a hard no.

### Camber vs body roll

- This is the on-track grip plot. As the body rolls onto a wheel, **that**
  wheel should go more negative.
- At ~2° of body roll, outside front still around −2° to −3°; outside rear
  less so.
- Left and right should be mirrors. If they are not, the model or the
  hardpoints are asymmetric.

### Toe vs travel (bump steer)

- **The most important driveability plot.** Front should look like a ruler.
- Front toe-out in bump = pointy (a pro can use it; a non-pro gets a car
  that steers itself over every ridge).
- Rear toe-out in bump = the car steers out of the corner when the inside
  rear drops. Never.
- A little **rear toe-in in bump** is the amateur safety net under braking
  and on curbs.
- Static: tiny front toe-in or zero; rear a bit more toe-in (Atom street
  is ~2 mm front / 3 mm rear total).

### Motion ratio and damper travel

- MR must stay **positive**. Jounce must **shorten** the damper. A sign
  flip is the rocker going over-centre — the spring starts working
  backwards.
- Slightly **rising** MR in bump is good: supple at ride, firmer on a
  curb. A falling rate is the car going soft just when you need it.
- A huge MR (wheel moves a lot, damper barely moves) means you cannot
  control the wheel with any reasonable spring. A tiny MR packs the
  damper in a few millimetres of heave.
- The damper plot should be a clean diagonal down-and-right. Flattening
  or turning back up is lock / over-centre.

### Track width vs heave

- Almost flat. Track change is lateral scrub at the contact patch.
- Big front track change → the wheel fights you on every bump (kickback).
- A few millimetres over ±30 mm is normal. Tens of millimetres is a handful.

### Scrub radius

- The lever bumps use to rip the wheel out of your hands.
- Small positive (0–20 mm) is the most honest. Huge scrub (50–80 mm) is
  kickback. Large negative is torque-steer / dead feel on a driven axle
  (less of an issue on this RWD car at the front, still ugly).
- Keep it **flat vs travel**. Diving through zero mid-stroke changes the
  sign of the kickback.

### Mechanical trail and castor

- Trail (with castor) is **self-centring and feel**. It tells a non-pro
  where straight-ahead is, and that the front is starting to let go.
- In this solver, conventional trail shows as **negative** (about −15 to
  −30 mm is a good band).
- Losing trail in bump → light, darty mid-corner. Keep it.
- Castor 5–8° front, nearly flat vs travel. More than a pro car; we are
  buying feel and a straight-line centre.
- KPI 8–13°, paired with *small* scrub. High KPI + high scrub = heavy
  lock and lift-on-steer.

### Front vs rear personality

- Front is allowed to be the busy end (a bit more camber gain, a bit
  higher RC, the steering).
- Rear is the reference. Calmer camber, flatter toe, RC near the front
  not above it.
- Mid-engine + 40/60 weight already wants to rotate. Geometry should not
  help it.

---

## Plot-by-plot targets

Use these as the “does this still look like the car we meant?” checklist
after any hardpoint edit.

| Plot | Driveable-track look |
|------|----------------------|
| Camber vs travel | Gentle straight down-slope. Rear shallower than front. No hook. |
| Toe vs travel | Front dead flat (±0.05° over ±25 mm). Rear flat or slight toe-in in bump. |
| Motion ratio | Positive everywhere, gently rising in bump. No spike, no sign change. |
| Damper travel | Monotonic compression in jounce. No plateau, no reversal. |
| Track vs heave | Almost flat (a few mm over ±30 mm). |
| Roll centre vs heave | Two boring lines above ground. Front ≈ rear or front a little higher. Shallow slope. |
| Camber vs roll | Outside wheel more negative; rear less than front. Mirrors L/R. |
| Scrub / trail | Flat. Small +scrub. Conventional trail (negative in this app). |
| Castor / KPI | Flat, mid-range. |

---

## What we are not optimizing (yet)

- Spring and bar rates, damper valving, bump rubbers.
- Anti-dive / anti-squat in braking and drive (needs force, not just heave).
- Compliance (Atom chassis bushes are rubber/metal on purpose).
- Tire load sensitivity, temperature, pressure.
- Aero (the Atom has almost none in stock form).

Kinematics that look right can still drive badly if the rates are wrong.
Kinematics that look wrong will not be saved by rates.

---

## How to change something

1. Change one family of points (one arm, or the rack, or the rocker) — not
   all three at once.
2. **Reset to defaults** first if the Streamlit session is stale.
3. Check the plot that *should* move, then the ones that should *not*
   (toe after an RC change, damper after a camber change, etc.).
4. If RC shoots to huge numbers, the front-view arms are nearly parallel.
   Add slope; do not chase the number with tiny clicks.
5. Write down what you were optimizing for. This file is that list.
