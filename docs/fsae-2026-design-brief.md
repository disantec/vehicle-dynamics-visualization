# 2026 FSAE Electric — design brief

**Status:** paused. Comparison and decisions are recorded here. Hardpoints were
not retuned. The running car is still the Atom 3 baseline.

**Sources** (folder `Documents/2026 Electric Cars`):

| Car | School | Files used |
|-----|--------|------------|
| #1 | Oregon State / GFR | DSS + Design Brief |
| #8 | RIT | DSS + Design Brief |
| #38 | Wisconsin–Madison | DSS + Design Brief |
| #99 | ÉTS (Formule ETS) | DSS + Design Brief |

These are 2026 Formula SAE / Formula Student **electric** design packets. The common thread is not “a nicer street Atom.” It is a 160–200 kg autocross car with 4WD hub motors, a full aero package, and ±25–30 mm of suspension travel.

Our current model is an Ariel Atom 3 starting point (2345 mm wheelbase, 1600 mm track, 520 kg, 15"/17" street tires). The deltas below are what would have to change if we want this tool to represent a **high-performance FSAE EV** instead.

---

## 1. What these cars are optimizing for

Every brief says some version of the same mission:

1. **Autocross lap time** on a tight, low-speed course (lots of 1–1.5 g corners, frequent direction changes).
2. **Endurance efficiency** with the same car (DRS / low-drag modes, regen, power limits).
3. **4WD traction** off the line and out of slow corners (torque vectoring + traction control).
4. **Aero platform** — keep the floor and wings at a known ride height and pitch.
5. **Serviceability** — camber, toe, ride height, ARB, and dampers changeable at the track in minutes.
6. **Mass** — every kilogram is fought for because the cars are already in the 160–205 kg band.

That mission produces a car that is **small, stiff, low, and busy in yaw**. It is the opposite of a road-going Atom that must feel honest at 120 mm ride height on a 195-section tire.

---

## 2. Comparison (from the Design Spec Sheets)

### Vehicle

| | OSU #1 | RIT #8 | Wisconsin #38 | ÉTS #99 | **Cluster** |
|---|---|---|---|---|---|
| Length / width / height mm | 2879 / 1438 / 1124 | 2941 / 1410 / 1176 | 2878 / 1397 / 1102 | 2878 / 1363 / 1196 | ~2.88 m × 1.40 m × 1.14 m |
| Wheelbase mm | 1535 | 1575 | 1549 | 1530 | **1530–1575** |
| Track F / R mm | 1230 / 1230 | 1219 / 1219 | 1189 / 1189 | 1143 / 1143 | **Equal tracks, 1140–1230** |
| WB / track | 1.25 | 1.29 | 1.30 | 1.34 | **~1.25–1.34** (square, yaw-eager) |
| Mass w/o driver kg | 205 | 186 | 162 | 178 | **160–205** |
| Front / rear mass kg | 92 / 113 | 82 / 104 | 72 / 90 | 82 / 96 | ~45 / 55 unladen |
| % front with 68 kg driver | 48 | 50.5 | 49 | 49.6 | **~49–50%** |
| CG height mm | 245 | 272 | 245 | 270 | **245–270** |

Our Atom baseline: WB 2345, track 1600, mass 520, CG 300, 40% front. Completely different car.

### Powertrain (why the corners look the way they do)

| | OSU | RIT | Wisconsin | ÉTS |
|---|---|---|---|---|
| Driven wheels | 4× hub motors | 4× hub (AMK kit) | 4× hub (Fischer) | 4× hub (Fischer) |
| Gearbox | 2-stage planetary in upright | 1.5-stage compound star in-wheel | compound planetary in upright | planetary in upright |
| Final drive | 15:1 | 12.97:1 | 10.22:1 | 13.93:1 |
| Peak motor | 28 kW / 24 Nm | ~AMK kit | 35.4 kW / 29.1 Nm | 35.4 kW / 29.1 Nm |
| Pack | 578 V | 587 V, 6.8 kWh | 515 V nom, ~6 kWh | 600 V, 6.0 kWh |
| Controls | TC + TV + regen | TC + TV | feed-forward TV + TC | TV + TC + torque split |
| Diff | none | none | none | none |

**Every car is 4WD in-hub.** No differential, no halfshafts. The upright **is** the gearbox housing. That forces:

- fat, machined 7075 uprights
- short steering arms packaged around a motor
- no pullrod/pushrod pickup that fights the motor can
- toe-link compliance treated as a stability item (Wisconsin: front toe compliance cut 33%)

### Tires and wheels

| | OSU | RIT | Wisconsin | ÉTS |
|---|---|---|---|---|
| Tire | Hoosier 7.5/16-10 LC0 | Hoosier 16×7.5-10 R20 | Hoosier 16×7.5-10 R20 | Hoosier 16×7.5-10 R20 |
| Wheel | 10×7.25 Al Keizer | 10×7.5 custom CFRP | 10×7.0 CFRP | 10×8 two-piece Al |

**Common:** 10-inch diameter, ~7.5" wide Hoosier, same size all around. Three of four on R20. No stagger.

Geometric radius of a 16.0×7.5-10 is about **203 mm** (much shorter than our 293 / 314 mm street tires). Ride height and RC numbers only make sense at that radius.

### Suspension architecture

| | OSU | RIT | Wisconsin | ÉTS |
|---|---|---|---|---|
| Type | unequal non-parallel A-arms | unequal A-arms | dual unequal A-arms | unequal A-arms |
| Front actuation | **direct** damper | **pushrod** + U-bar | **pushrod** + DSSV | **pullrod**, decoupled |
| Rear actuation | **roll-heave** (trunnion roll damper) | **pushrod** + U-bar | **pushrod** + DSSV | **pushrod**, decoupled |
| Travel jounce/rebound mm | 25 / 25 | 30.5 / 25.4 | 25.4 / 25.4 | 30 / 30 |
| Motion ratio | 0.60 F / 0.68 R linear | 0.95 / 0.95 linear | 1.08 / 1.08 linear | 1.30 F / 1.23 R quasi-linear |
| Wheel rate N/mm | 34.7 / 33.4 | 25.4 / 33.9 | 33.7 / 39.6 | 98.4 / 87.1 (heave springs; decoupled) |
| Ride freq Hz | 4.0 / 3.14 | 4.31 / 5.15 | 4.23 / 4.23 | 5.08 / 4.79 |
| Roll rate Nm/deg | 460 / **750** | 478 / **971** | **914** / 677 | 1268 / **1468** |
| Damping % crit | 62 / 62 | 69 / 65 | 51 / 51 | 71 jounce / 80 rebound |

**Common:** unequal-length double wishbone, short travel, linear-ish MR near 1:1 (OSU is the outlier at 0.6 because the front damper is direct-acting), ride frequencies **4–5 Hz**. Rear roll stiffness is usually **higher** than front (Wisconsin flipped that).

ÉTS wheel rates look huge because the heave and roll springs are **decoupled** — the heave spring is not doing all the roll work. Do not copy 98 N/mm as a conventional corner rate.

### Kinematics (the plots we care about)

| | OSU | RIT | Wisconsin | ÉTS | **Cluster** |
|---|---|---|---|---|---|
| Static camber deg | −2.0 / −1.0 | −1.5 / −1.5 | −1.0 / −1.0 | −0.25 / −0.25 | **−1.0 to −1.5** typical |
| Static sum toe deg | 0 / 0 | +0.5 / +0.5 | 0 / 0 | 0 / 0 | **0 to slight toe-in** |
| Ride camber deg/m | 36.5 / 41.5 | 24.8* / 25.6* | 43.4 / 50 | 48.8 / 77 | **~35–50 front** |
| Roll camber deg/deg | 0.55 / 0.55 | 0.57* / 0.73* | 0.57 / 0.50 | 0.57 / **0.26** | **~0.55 front** |
| Anti-dive / anti-squat % | 25 / 15 | 45 / 25 | 8 / 3.8 | 40 / **−23** | front anti-dive common; rear varies |
| Static RC height mm | **32 / 75** | **52 / 94** | **51 / 89** | **87 / 105** | **rear always higher** |
| RC @ 1 g, height mm | 7 / 76 | 52 / 93 | 51 / 89 | 87 / 105 | want **little migration** |
| RC @ 1 g, lateral mm | 4 / 70 | 38 / 38 | 0.7 / 1.2 | 1.7 / 7.2 | Wisconsin / ÉTS almost on centerline |
| Caster deg | 7.9 | 3.5 | 3.8 | 4.2 | **3.5–8** |
| Mechanical trail mm | 8.8 | 9.2 | 3.8 | 12 | **small, 4–12** |
| Scrub mm | 5.4 | 21.8 | 12.7 | 15.2 | **5–22** |
| KPI deg | 8.5 | 4.7 | 5.8 | 14.1 | 5–8 typical; ÉTS high on purpose |
| Ackermann % | 2.5 | **96** | 2 | 0 (they call it pro-Ackermann in the brief) | mixed |
| Steer ratio | 3.63 | 3.5 | 3.9 | 4.9 | **~3.5–5 : 1** |

\*RIT reports ride/roll camber with the opposite sign from the other three; magnitudes are shown.

RIT’s written kinematic targets (Design Brief p.18) are the clearest “what good looks like” statement in the set:

- Bump steer **≤ 0.25° over full travel** (keep lateral-force change from toe under 10% of peak).
- Camber change **< 2° from static** through the travel they use (they claim the R20 is insensitive from 0 to −4°).
- Heave MR **≈ 1.05** so damper range is usable and normal-load variation stays small.
- Unequal A-arms + pushrod because that is how they hit camber, toe, and MR together.

ÉTS’s kinematic goals (Design Brief p.18):

- **Higher roll centre** to cut geometric roll and make the car respond faster.
- Less caster (6.5° → 4.2°) so dynamic camber stays near zero, more KPI (7° → 14°) instead.
- Lower steering torque from driver feedback.

OSU’s kinematic story (Design Brief p.18):

- Added **23% front anti-dive / 15% rear anti-squat** so they can run softer springs for aero without the car pitching.
- Shifted the whole axle 25 mm aft to move CG and grow the undertray.

Wisconsin **carried kinematics over** and spent the year on springs, ARBs, 4-post damper work, and carbon links. That is itself a finding: once the hardpoints are close, these teams stop chasing RC and start chasing **compliance, mass, and rates**.

### Chassis and aero (the environment the suspension lives in)

| | OSU | RIT | Wisconsin | ÉTS |
|---|---|---|---|---|
| Structure | CFRP / Al honeycomb monocoque | full CF monocoque | full CF monocoque | single-piece CF monocoque |
| Bare frame kg | 36.6 | — | 28.6 | 23.6 |
| Torsional target Nm/deg | 3100 | — | 2500 (hub-to-hub they cite 1500 as “enough for LLTD”) | 2600 |
| Tested Nm/deg | TBD | — | 2488 | 2293 |
| Downforce @ 80 kph N | 1460 | 1012 | 1157 | 970 |
| Aero % front | 48 | 40 | 44–53 adjustable | 53 |
| DRS / modes | rear-wing DRS | active rear AOA | 5 aero modes + endurance | rear DRS, adj. wing height |

**Common:** carbon monocoque in the mid-20s to mid-30s kg, chassis torsion **~2300–3300 Nm/deg**, a full wing + undertray package making **~1 kN of downforce at 80 kph**, CoP near 45–50% front and **adjustable**.

Wisconsin’s chassis note is the useful one for us: they **lowered** the torsion target on purpose. Past a point, extra chassis stiffness does not change lateral load transfer distribution, it only adds mass. 1500 Nm/deg hub-to-hub was “enough.” The others still carry 2500–3100 as a design number.

---

## 3. Common denominators

These showed up on **all four** cars, or on three with a documented reason for the exception.

### Architecture

1. **4WD in-hub motors, no differential.** Yaw is a software problem. The upright is a gearbox.
2. **Equal-length tracks, short wheelbase.** WB/track ≈ 1.3. The car is meant to rotate.
3. **Same tire all around**, 10" Hoosier ~16×7.5. No stagger.
4. **Unequal-length, non-parallel double wishbones** at every corner.
5. **Inboard actuation or a documented packaging reason not to.** Pushrod is the default. OSU direct-front and ÉTS pullrod-front are packaging/aero choices, not a different linkage type.
6. **Carbon (or carbon-tube) control arms**, machined 7075 uprights, spherical bearings.
7. **Carbon monocoque** with hardpoint inserts designed from link loads, not guesswork.
8. **Full aero + DRS or multi-mode CoP.** Suspension exists to hold that platform still.

### Kinematic personality

9. **Rear roll centre above the front**, by 20–45 mm, both well above ground (front 30–90 mm, rear 75–105 mm). Every car. This is the FSAE pattern, not the street-Atom pattern.
10. **RC that does not run away in roll.** Best-in-set (Wisconsin, ÉTS) barely moves height or laterally at 1 g. OSU’s front collapsing 32 → 7 mm is the example of what they are still iterating away from.
11. **Short travel**, ±25–30 mm. The plots we care about live in a small window.
12. **Aggressive camber gain vs a street car.** Ride camber ~0.4–0.8° per 20 mm. Roll camber ~0.55°/° at the front so the outside front stays in the R20’s window. Rear is allowed to be similar or calmer (ÉTS deliberately 0.26).
13. **Almost no static toe, almost no bump steer.** RIT wrote the spec: ≤ 0.25° toe change over travel.
14. **Small trail, moderate caster, small-to-moderate scrub.** Steering must be light and quick on a 10" tire. ÉTS cut caster and raised KPI to keep dynamic camber near zero without heavy steering.
15. **Some front anti-dive.** Rear anti-squat is a free variable (ÉTS even runs anti-lift / negative).
16. **Motion ratio near 1 and linear**, unless the damper is direct-acting. Rising-rate is not the headline; usable damper stroke is.

### Rates and the platform

17. **Ride frequencies 4–5 Hz.** These are not 1.5 Hz road cars. Aero and 10" sidewalls set that.
18. **Rear roll stiffer than front** on 3 of 4 (Wisconsin is the exception, and they said they were retuning bars for the R20).
19. **Trackside adjustability is a design requirement:** shims or jackscrews for camber/toe/ride, ARB lever or a roll damper, 2- to 4-way dampers.
20. **Torque vectoring is part of the handling concept.** Geometry does not have to do all of the yaw work.

### How they work

21. **Tire data first, then OptimumK / IPG / a wireframe, then CAD.** ÉTS and RIT say this explicitly.
22. **Once kinematics are close, stop.** Wisconsin carried 2025 hardpoints and spent the year on carbon links, 4-post damping, and TV.
23. **Compliance is treated as kinematics.** Toe-link stiffness under braking is a stability spec, not a “make it strong enough” afterthought.

---

## 4. Where they disagree (do not average these blindly)

- **Front RC height:** 32 mm (OSU) vs 87 mm (ÉTS). ÉTS wants a high RC for response; OSU is still migrating a lot and may be living with a lower effective RC in roll.
- **Ackermann:** RIT 96% vs everyone else ~0–2.5%. RIT sized it for a minimum-radius slalom. Copy only if we care about that corner.
- **Actuation:** direct vs pushrod vs pullrod vs fully decoupled heave/roll. Pick from packaging (aero floor, damper access, hub motor) not from fashion.
- **Static camber:** −0.25° (ÉTS, they use KPI/steer for camber) vs −2° (OSU). Depends on the tire curve.
- **Rear anti-squat:** +25% (RIT) vs −23% (ÉTS). Driven by aero pitch and regen, not a universal truth.
- **Who owns roll stiffness:** ARB (RIT, Wisconsin), roll-heave damper (OSU), or decoupled roll spring (ÉTS).

---

## 5. Proposed brief for *our* FSAE-EV variant

This is the part to mark up. Numbers are the cluster, not a copy of one car.

### Vehicle

| Item | Proposed target | Why |
|---|---|---|
| Wheelbase | **1540 mm** | middle of the set; keeps WB/track ~1.28 on a 1200 mm track |
| Track F / R | **1200 / 1200 mm** | equal tracks; 3 of 4 sit at 1190–1230 |
| Mass (model) | **185 kg** + 68 kg driver | mid-pack |
| Front weight (with driver) | **49–50%** | all four cars |
| CG height | **255 mm** | between the two pairs (245 and 270) |
| Tires | **Hoosier 16×7.5-10**, same all around | three cars on R20; radius ≈ 203 mm |
| Wheels | **10×7.5** | cluster |
| Drive | **4WD in-hub, no diff** (even if we only model the kinematics) | universal in this set |
| Ride height | **~40–50 mm** chassis, not 120 mm | 10" tire + aero floor |

### Suspension

| Item | Proposed target | Why |
|---|---|---|
| Linkage | unequal non-parallel SLA, both ends | universal |
| Actuation | **pushrod both ends**, MR **1.00–1.10**, linear | RIT/Wisconsin default; damper access |
| Travel | **±28 mm** | 25–30 mm cluster |
| Static camber | **−1.5° F / −1.2° R** | middle of the useful band |
| Static toe | **0 to +0.2°** per side (slight rear toe-in ok) | mostly zero; RIT +0.25/side |
| Bump steer | **≤ 0.25° over ±28 mm** | RIT written spec |
| Ride camber | **~40 deg/m front, ~45 deg/m rear** | ≈ −0.8° / −0.9° at +20 mm |
| Roll camber | **~0.55 deg/deg front, 0.40–0.55 rear** | three cars agree on 0.55 front |
| Static RC | **front 45–55 mm, rear 80–95 mm** | rear **above** front by ~35–40 mm |
| RC in 1 g roll | height change **< 10 mm**, lateral **< 15 mm** | Wisconsin / ÉTS quality bar |
| Caster / trail / scrub | **4–6° / 8–12 mm / 8–15 mm** | cluster without ÉTS’s high-KPI experiment |
| KPI | **6–9°** | unless we adopt ÉTS’s “caster down, KPI up” idea |
| Anti-dive / anti-squat | **~20% / ~15%** | OSU’s stated aero-pitch reason |
| Ride freq (later, with springs) | **4.2 Hz both** | Wisconsin’s matched pair |
| Roll stiffness (later) | **rear > front**, about 1.3–1.6× | 3 of 4 |

### What this means versus our current Atom 3 model

| | Atom 3 baseline now | FSAE-EV brief |
|---|---|---|
| Wheelbase / track | 2345 / 1600 | 1540 / 1200 |
| Tire radius | 293 F / 314 R | ~203 all around |
| Mass / CG / % front | 520 / 300 / 40% | 185 / 255 / 50% |
| Travel window | ±40 mm | ±28 mm |
| Front RC / rear RC | 29 / 25 mm | **50 / 90 mm** |
| Camber gain | mild | 2–3× steeper |
| Bump steer budget | we were proud of 0.14°/30 mm | still valid; FSAE wants ≤ 0.25° |
| Rear RC vs front | front slightly higher (street-stable) | **rear higher** (FSAE cluster) |
| MR | ~3.3 (packaging leftover) | **~1.05** |
| Drive | RWD street | 4WD in-hub |

The rear-higher RC is **not** a contradiction of the street-Atom design guide. These cars have a CG at ~250 mm, 1 kN of aero, 4–5 Hz springs, and software yaw control. Geometric load transfer is a smaller, more intentional knob. On a 520 kg Atom with no aero and a 300 mm CG, rear-high RC is still the oversteer layout. **Pick the car, then pick the RC split.**

---

## 6. Decisions (accepted, not implemented)

Recorded before the project was paused:

1. **Keep Atom packaging** — 2345 mm wheelbase, 1600 mm tracks, 205/50R15 front /
   245/40R17 rear, ~520 kg, mid-engine RWD, 120 mm ride height.
2. **Apply FSAE kinematic practice on that package** — unequal SLA, short useful
   travel window, bump-steer budget, camber-gain and RC quality from §3.
3. **Pushrod both ends.** OSU’s 0.6 MR is from a direct-acting front damper, so
   it does not win the actuation tie. Target MR ≈ 1.05 (RIT / Wisconsin).
4. **Oregon State is the remaining tie-breaker** — static camber −2.0° / −1.0°,
   toe 0 / 0, anti-dive ~25%, anti-squat ~15%, RC 32 / 75 mm (rear above front),
   caster / KPI / scrub / trail from the OSU spec sheet.

Implementation stopped before a new YAML preset was written. Resume from this
list, not from the FSAE-sized vehicle table in §5.

---

## 7. Open questions for you

Mark these up in the file or answer in chat:

1. Are we designing an **FSAE EV** from here, or a **hybrid** that keeps Atom packaging with FSAE kinematics?
2. **R20 all around**, or keep a street stagger?
3. Accept **rear RC above front** for the FSAE preset (recommended), or keep the street-stable split?
4. **Pushrod both ends**, or do you want ÉTS-style pullrod front / decoupled heave-roll as a second variant?
5. Model **in-hub gearbox uprights** as packaging constraints (motor can, caliper, stub), or only the linkage?
6. Which car is the closest “spirit animal” if we have to break a tie — OSU (simple, anti-geometry, roll-heave), RIT (written kinematic specs, pushrod+ARB), Wisconsin (carry kinematics, obsess rates), or ÉTS (high RC, decoupled, high KPI)?
