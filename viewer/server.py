"""FastAPI app: kinematics API + static Three.js viewer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.geometry.hardpoints import load_params, params_from_dict, params_to_dict
from viewer.serialize import metrics_payload, schema, solve_payload

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Suspension kinematics viewer", version="0.1.0")


class SolveRequest(BaseModel):
    params: Optional[Dict[str, Any]] = None
    travels: Dict[str, float] = Field(
        default_factory=lambda: {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}
    )


class MetricsRequest(BaseModel):
    params: Optional[Dict[str, Any]] = None


def _params_dict(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if raw is None:
        return params_to_dict(load_params())
    try:
        return params_to_dict(params_from_dict(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid params: {exc}") from exc


@app.get("/api/schema")
def get_schema() -> Dict[str, Any]:
    return schema()


@app.get("/api/defaults")
def get_defaults() -> Dict[str, Any]:
    params = params_to_dict(load_params())
    travels = {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}
    return solve_payload(params, travels)


@app.post("/api/solve")
def post_solve(req: SolveRequest) -> Dict[str, Any]:
    params = _params_dict(req.params)
    travels = {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}
    travels.update({k: float(v) for k, v in (req.travels or {}).items() if k in travels})
    try:
        return solve_payload(params, travels)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Solve failed: {exc}") from exc


@app.post("/api/metrics")
def post_metrics(req: MetricsRequest) -> Dict[str, Any]:
    params = _params_dict(req.params)
    try:
        return metrics_payload(params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Metrics failed: {exc}") from exc


@app.get("/api/params.yaml")
def get_params_yaml() -> PlainTextResponse:
    text = yaml.safe_dump(params_to_dict(load_params()), sort_keys=False)
    return PlainTextResponse(text, media_type="text/yaml")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")


def main() -> None:
    import uvicorn

    uvicorn.run(
        "viewer.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT)],
    )


if __name__ == "__main__":
    main()
