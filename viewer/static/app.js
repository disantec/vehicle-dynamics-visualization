import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { TransformControls } from "three/addons/controls/TransformControls.js";

const COL = {
  lower: 0x3b82f6,
  upper: 0xef4444,
  upright: 0xf59e0b,
  tierod: 0x10b981,
  rod: 0xa855f7,
  rocker: 0xec4899,
  damper: 0x06b6d4,
  tire: 0x1f2937,
  wheel: 0x9ca3af,
  point: 0xe5e7eb,
  sel: 0xfbbf24,
  ic: 0xf97316,
  rc: 0x22d3ee,
  ground: 0x374151,
};

const state = {
  params: null,
  schema: null,
  travels: { FL: 0, FR: 0, RL: 0, RR: 0 },
  poseMode: "heave",
  selected: null, // { axle: "front", name: "lower_outer" }
  busy: false,
  dirty: false,
};

let scene, camera, renderer, orbit, transform;
let carGroup = new THREE.Group();
let pickables = [];

const canvasWrap = document.getElementById("canvas-wrap");

function vehToThree(p) {
  return new THREE.Vector3(p[0], p[1], p[2]);
}

async function api(path, body) {
  const opts = body
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    : {};
  const res = await fetch(path, opts);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t);
  }
  return res.json();
}

function initScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b1220);
  scene.up.set(0, 0, 1);

  camera = new THREE.PerspectiveCamera(45, 1, 10, 20000);
  camera.up.set(0, 0, 1);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  canvasWrap.appendChild(renderer.domElement);

  orbit = new OrbitControls(camera, renderer.domElement);
  orbit.enableDamping = true;
  orbit.target.set(1670, 0, 220);

  transform = new TransformControls(camera, renderer.domElement);
  transform.setSpace("world");
  transform.addEventListener("dragging-changed", (e) => {
    orbit.enabled = !e.value;
  });
  transform.addEventListener("objectChange", onGizmo);
  scene.add(transform.getHelper());

  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 0.9);
  key.position.set(800, -1600, 2200);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x93c5fd, 0.35);
  fill.position.set(-1200, 900, 800);
  scene.add(fill);

  const grid = new THREE.GridHelper(6000, 30, 0x374151, 0x1f2937);
  grid.rotation.x = Math.PI / 2;
  scene.add(grid);
  scene.add(carGroup);

  setView("iso");
  resize();
  window.addEventListener("resize", resize);
  renderer.domElement.addEventListener("pointerdown", onPointerDown);
  animate();
}

function resize() {
  const w = canvasWrap.clientWidth;
  const h = canvasWrap.clientHeight;
  camera.aspect = w / Math.max(h, 1);
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

function setView(name) {
  const c = new THREE.Vector3(1670, 0, 200);
  const dist = 2800;
  const pos = {
    iso: new THREE.Vector3(c.x + 1600, c.y - 2000, c.z + 1400),
    front: new THREE.Vector3(c.x - dist, 0, 400),
    rear: new THREE.Vector3(c.x + dist, 0, 400),
    side: new THREE.Vector3(c.x, -dist, 350),
    top: new THREE.Vector3(c.x, 0, dist),
  }[name];
  camera.position.copy(pos);
  orbit.target.copy(c);
  orbit.update();
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === name);
  });
}

function linkMesh(a, b, radius, color) {
  const va = vehToThree(a);
  const vb = vehToThree(b);
  const dir = new THREE.Vector3().subVectors(vb, va);
  const len = dir.length();
  if (len < 1e-3) return null;
  const geom = new THREE.CylinderGeometry(radius, radius, len, 8);
  const mat = new THREE.MeshStandardMaterial({ color, metalness: 0.2, roughness: 0.45 });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.copy(va).add(vb).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  return mesh;
}

function sphere(p, r, color, userData) {
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(r, 16, 12),
    new THREE.MeshStandardMaterial({ color, metalness: 0.1, roughness: 0.4 })
  );
  mesh.position.copy(vehToThree(p));
  mesh.userData = userData || {};
  return mesh;
}

function addCorner(group, corner, tire, axle, isLeft) {
  const p = corner.points;
  const links = [
    [p.lower_front_chassis, p.lower_outer, 7, COL.lower],
    [p.lower_rear_chassis, p.lower_outer, 7, COL.lower],
    [p.lower_front_chassis, p.lower_rear_chassis, 4, COL.lower],
    [p.upper_front_chassis, p.upper_outer, 7, COL.upper],
    [p.upper_rear_chassis, p.upper_outer, 7, COL.upper],
    [p.upper_front_chassis, p.upper_rear_chassis, 4, COL.upper],
    [p.lower_outer, p.upper_outer, 8, COL.upright],
    [p.lower_outer, p.wheel_center, 4, COL.upright],
    [p.upper_outer, p.wheel_center, 3, COL.upright],
    [p.tierod_inner, p.tierod_outer, 5, COL.tierod],
    [p.rod_arm_point, p.rod_rocker_point, 5, COL.rod],
    [p.rocker_pivot, p.rod_rocker_point, 6, COL.rocker],
    [p.rocker_pivot, p.rocker_damper_point, 6, COL.rocker],
    [p.rod_rocker_point, p.rocker_damper_point, 3, COL.rocker],
    [p.rocker_damper_point, p.damper_body, 7, COL.damper],
  ];
  for (const [a, b, r, c] of links) {
    const m = linkMesh(a, b, r, c);
    if (m) group.add(m);
  }

  const tireR = tire.radius_mm;
  const tireW = tire.width_mm;
  const tireMesh = new THREE.Mesh(
    new THREE.CylinderGeometry(tireR, tireR, tireW, 28),
    new THREE.MeshStandardMaterial({ color: COL.tire, roughness: 0.9 })
  );
  tireMesh.position.copy(vehToThree(p.wheel_center));
  group.add(tireMesh);

  const ic = sphere(p.instant_center, 10, COL.ic, {});
  group.add(ic);

  if (isLeft) {
    for (const name of state.schema.editable_points) {
      const pt = p[name];
      if (!pt) continue;
      const selected =
        state.selected && state.selected.axle === axle && state.selected.name === name;
      const s = sphere(pt, selected ? 16 : 11, selected ? COL.sel : COL.point, {
        axle,
        name,
      });
      group.add(s);
      pickables.push(s);
    }
  }
}

function rebuildCar(payload) {
  while (carGroup.children.length) carGroup.remove(carGroup.children[0]);
  pickables = [];
  const corners = payload.corners;
  addCorner(carGroup, corners.FL, payload.tires.FL, "front", true);
  addCorner(carGroup, corners.FR, payload.tires.FR, "front", false);
  addCorner(carGroup, corners.RL, payload.tires.RL, "rear", true);
  addCorner(carGroup, corners.RR, payload.tires.RR, "rear", false);

  const rcF = payload.roll_centers.front_z_mm;
  const rcR = payload.roll_centers.rear_z_mm;
  const xF = payload.params.front.wheel_center[0];
  const xR = payload.params.rear.wheel_center[0];
  carGroup.add(sphere([xF, 0, rcF], 14, COL.rc, {}));
  carGroup.add(sphere([xR, 0, rcR], 14, COL.rc, {}));
  const rcLine = linkMesh([xF, 0, rcF], [xR, 0, rcR], 3, COL.rc);
  if (rcLine) carGroup.add(rcLine);

  attachGizmo();
}

function attachGizmo() {
  transform.detach();
  if (!state.selected) return;
  const hit = pickables.find(
    (m) => m.userData.axle === state.selected.axle && m.userData.name === state.selected.name
  );
  if (hit) transform.attach(hit);
}

function onGizmo() {
  if (!state.selected || !transform.object) return;
  const p = transform.object.position;
  const axle = state.selected.axle;
  const name = state.selected.name;
  state.params[axle][name] = [p.x, p.y, p.z];
  document.getElementById("ed-x").value = p.x.toFixed(1);
  document.getElementById("ed-y").value = p.y.toFixed(1);
  document.getElementById("ed-z").value = p.z.toFixed(1);
  scheduleSolve();
}

function onPointerDown(ev) {
  if (transform.dragging) return;
  const rect = renderer.domElement.getBoundingClientRect();
  const mouse = new THREE.Vector2(
    ((ev.clientX - rect.left) / rect.width) * 2 - 1,
    -((ev.clientY - rect.top) / rect.height) * 2 + 1
  );
  const ray = new THREE.Raycaster();
  ray.setFromCamera(mouse, camera);
  const hits = ray.intersectObjects(pickables, false);
  if (hits.length) {
    const { axle, name } = hits[0].object.userData;
    selectPoint(axle, name);
  }
}

function selectPoint(axle, name) {
  state.selected = { axle, name };
  const xyz = state.params[axle][name];
  document.getElementById("editor").classList.remove("hidden");
  document.getElementById("editor-title").textContent =
    `${axle} · ${state.schema.point_labels[name] || name}`;
  document.getElementById("ed-x").value = Number(xyz[0]).toFixed(1);
  document.getElementById("ed-y").value = Number(xyz[1]).toFixed(1);
  document.getElementById("ed-z").value = Number(xyz[2]).toFixed(1);
  document.querySelectorAll(".pt").forEach((b) => {
    b.classList.toggle("sel", b.dataset.axle === axle && b.dataset.name === name);
  });
  attachGizmo();
}

function applyEditor() {
  if (!state.selected) return;
  const x = parseFloat(document.getElementById("ed-x").value);
  const y = parseFloat(document.getElementById("ed-y").value);
  const z = parseFloat(document.getElementById("ed-z").value);
  if ([x, y, z].some((v) => Number.isNaN(v))) return;
  state.params[state.selected.axle][state.selected.name] = [x, y, z];
  scheduleSolve();
}

function poseFromUi() {
  const mode = state.poseMode;
  const v = state.params.vehicle;
  const t = { FL: 0, FR: 0, RL: 0, RR: 0 };
  if (mode === "heave") {
    const h = parseFloat(document.getElementById("heave").value);
    document.getElementById("heave-val").textContent = h;
    t.FL = t.FR = t.RL = t.RR = h;
  } else if (mode === "roll") {
    const r = parseFloat(document.getElementById("roll").value);
    document.getElementById("roll-val").textContent = r.toFixed(1);
    const dzF = (v.track_front_mm / 2) * Math.sin((r * Math.PI) / 180);
    const dzR = (v.track_rear_mm / 2) * Math.sin((r * Math.PI) / 180);
    t.FL = dzF;
    t.FR = -dzF;
    t.RL = dzR;
    t.RR = -dzR;
  } else if (mode === "pitch") {
    const p = parseFloat(document.getElementById("pitch").value);
    document.getElementById("pitch-val").textContent = p.toFixed(1);
    const dz = (v.wheelbase_mm / 2) * Math.sin((p * Math.PI) / 180);
    t.FL = t.FR = -dz;
    t.RL = t.RR = dz;
  } else {
    for (const k of ["FL", "FR", "RL", "RR"]) {
      t[k] = parseFloat(document.getElementById(`tr-${k}`).value);
    }
    document.getElementById("fl-val").textContent = t.FL;
    document.getElementById("fr-val").textContent = t.FR;
    document.getElementById("rl-val").textContent = t.RL;
    document.getElementById("rr-val").textContent = t.RR;
  }
  state.travels = t;
}

let solveTimer = null;
function scheduleSolve() {
  state.dirty = true;
  if (solveTimer) return;
  solveTimer = setTimeout(async () => {
    solveTimer = null;
    await solveNow();
  }, 40);
}

async function solveNow() {
  if (state.busy) {
    state.dirty = true;
    return;
  }
  state.busy = true;
  state.dirty = false;
  poseFromUi();
  document.getElementById("status").textContent = "solving…";
  try {
    const payload = await api("/api/solve", {
      params: state.params,
      travels: state.travels,
    });
    state.params = payload.params;
    rebuildCar(payload);
    renderLive(payload);
    document.getElementById("status").textContent = "";
    schedulePlots();
  } catch (err) {
    document.getElementById("status").textContent = String(err);
  } finally {
    state.busy = false;
    if (state.dirty) scheduleSolve();
  }
}

function renderLive(payload) {
  const live = document.getElementById("live");
  live.innerHTML = "";
  for (const name of ["FL", "FR", "RL", "RR"]) {
    const c = payload.corners[name];
    const damp =
      c.damper_travel_mm < -0.05
        ? "compression"
        : c.damper_travel_mm > 0.05
          ? "extension"
          : "design";
    const cls = c.damper_travel_mm < -0.05 ? "ok" : c.damper_travel_mm > 0.05 ? "bad" : "";
    const el = document.createElement("div");
    el.className = "live-card";
    el.innerHTML = `<strong>${name}</strong>
      camber ${c.camber_deg.toFixed(2)}° · toe ${c.toe_deg.toFixed(2)}°<br>
      castor ${c.castor_deg.toFixed(2)}° · KPI ${c.kpi_deg.toFixed(2)}°<br>
      damper Δ ${c.damper_travel_mm.toFixed(1)} mm <span class="${cls}">${damp}</span>`;
    live.appendChild(el);
  }
  const rc = payload.roll_centers;
  document.getElementById("rc").innerHTML = `
    Front RC ${rc.front_z_mm.toFixed(1)} mm<br>
    Rear RC ${rc.rear_z_mm.toFixed(1)} mm
    <p class="hint">${rc.front_z_mm >= rc.rear_z_mm - 1 ? "Front ≥ rear (stable split)" : "Rear above front (oversteer-leaning)"}</p>`;
}

function buildPointList() {
  const root = document.getElementById("point-list");
  root.innerHTML = "";
  const groups = state.schema.point_groups;
  for (const axle of ["front", "rear"]) {
    const h = document.createElement("div");
    h.className = "group-title";
    h.textContent = axle.toUpperCase();
    root.appendChild(h);
    for (const [gname, keys] of Object.entries(groups)) {
      const wrap = document.createElement("div");
      wrap.className = "group";
      wrap.innerHTML = `<div class="group-title">${gname}</div>`;
      for (const key of keys) {
        const b = document.createElement("button");
        b.className = "pt";
        b.dataset.axle = axle;
        b.dataset.name = key;
        b.textContent = state.schema.point_labels[key];
        b.addEventListener("click", () => selectPoint(axle, key));
        wrap.appendChild(b);
      }
      root.appendChild(wrap);
    }
  }
}

function bindUi() {
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.addEventListener("click", () => setView(b.dataset.view));
  });
  document.querySelectorAll("[data-mode]").forEach((b) => {
    b.addEventListener("click", () => {
      state.poseMode = b.dataset.mode;
      document.querySelectorAll("[data-mode]").forEach((x) => x.classList.toggle("active", x === b));
      document.getElementById("pose-heave").classList.toggle("hidden", state.poseMode !== "heave");
      document.getElementById("pose-roll").classList.toggle("hidden", state.poseMode !== "roll");
      document.getElementById("pose-pitch").classList.toggle("hidden", state.poseMode !== "pitch");
      document.getElementById("pose-corners").classList.toggle("hidden", state.poseMode !== "corners");
      scheduleSolve();
    });
  });
  for (const id of ["heave", "roll", "pitch", "tr-FL", "tr-FR", "tr-RL", "tr-RR"]) {
    document.getElementById(id).addEventListener("input", scheduleSolve);
  }
  for (const id of ["ed-x", "ed-y", "ed-z"]) {
    document.getElementById(id).addEventListener("change", applyEditor);
  }
  document.getElementById("btn-reset").addEventListener("click", async () => {
    const payload = await api("/api/defaults");
    applyPayload(payload);
    await refreshPlots();
  });
  document.getElementById("btn-yaml").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(state.params, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "suspension_params.json";
    a.click();
  });
  for (const [id, axle, field] of [
    ["front-camber", "front", "static_camber_deg"],
    ["front-toe", "front", "static_toe_deg"],
    ["rear-camber", "rear", "static_camber_deg"],
    ["rear-toe", "rear", "static_toe_deg"],
  ]) {
    document.getElementById(id).addEventListener("change", (e) => {
      state.params[axle][field] = parseFloat(e.target.value);
      scheduleSolve();
      refreshPlots();
    });
  }
}

function applyPayload(payload) {
  state.params = payload.params;
  document.getElementById("front-camber").value = payload.params.front.static_camber_deg;
  document.getElementById("front-toe").value = payload.params.front.static_toe_deg;
  document.getElementById("rear-camber").value = payload.params.rear.static_camber_deg;
  document.getElementById("rear-toe").value = payload.params.rear.static_toe_deg;
  rebuildCar(payload);
  renderLive(payload);
}

function drawPlot(canvas, title, xs, series) {
  const ctx = canvas.getContext("2d");
  const w = (canvas.width = canvas.clientWidth * 2);
  const h = (canvas.height = canvas.clientHeight * 2);
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#9ca3af";
  ctx.font = "20px ui-sans-serif";
  ctx.fillText(title, 8, 22);
  let ymin = Infinity;
  let ymax = -Infinity;
  for (const s of series) {
    for (const y of s.y) {
      if (y < ymin) ymin = y;
      if (y > ymax) ymax = y;
    }
  }
  if (!isFinite(ymin)) return;
  if (ymax === ymin) {
    ymax += 1;
    ymin -= 1;
  }
  const pad = { l: 8, r: 8, t: 28, b: 8 };
  const xmin = xs[0];
  const xmax = xs[xs.length - 1];
  const sx = (x) => pad.l + ((x - xmin) / (xmax - xmin)) * (w - pad.l - pad.r);
  const sy = (y) => h - pad.b - ((y - ymin) / (ymax - ymin)) * (h - pad.t - pad.b);
  ctx.strokeStyle = "#374151";
  ctx.beginPath();
  ctx.moveTo(sx(xmin), sy(0));
  ctx.lineTo(sx(xmax), sy(0));
  ctx.stroke();
  for (const s of series) {
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    s.y.forEach((y, i) => {
      const x = sx(xs[i]);
      const yy = sy(y);
      if (i === 0) ctx.moveTo(x, yy);
      else ctx.lineTo(x, yy);
    });
    ctx.stroke();
  }
}

let plotTimer = null;
function schedulePlots() {
  if (plotTimer) clearTimeout(plotTimer);
  plotTimer = setTimeout(() => {
    plotTimer = null;
    refreshPlots();
  }, 400);
}

async function refreshPlots() {
  try {
    const m = await api("/api/metrics", { params: state.params });
    const xs = m.FL.travel_mm;
    drawPlot(document.getElementById("plot-camber"), "Camber vs travel", xs, [
      { y: m.FL.camber_deg, color: "#3b82f6" },
      { y: m.RL.camber_deg, color: "#ef4444" },
    ]);
    drawPlot(document.getElementById("plot-toe"), "Toe vs travel", xs, [
      { y: m.FL.toe_deg, color: "#3b82f6" },
      { y: m.RL.toe_deg, color: "#ef4444" },
    ]);
    drawPlot(document.getElementById("plot-rc"), "Roll centre vs heave", m.front_heave.travel_mm, [
      { y: m.front_heave.roll_center_z_mm, color: "#3b82f6" },
      { y: m.rear_heave.roll_center_z_mm, color: "#ef4444" },
    ]);
  } catch (err) {
    document.getElementById("status").textContent = String(err);
  }
}

function animate() {
  requestAnimationFrame(animate);
  orbit.update();
  renderer.render(scene, camera);
}

async function boot() {
  initScene();
  bindUi();
  state.schema = await api("/api/schema");
  buildPointList();
  const payload = await api("/api/defaults");
  applyPayload(payload);
  await refreshPlots();
}

boot().catch((err) => {
  document.getElementById("status").textContent = String(err);
});
