import asyncio
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .schemas import StartRequest, StartResponse
from .sim_runner import SimRun, RunRegistry


app = FastAPI(title="HIVEC-CM Live API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "*"],  # tighten as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REGISTRY = RunRegistry()
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/parameters.json'))


@app.post("/api/simulations", response_model=StartResponse)
def start_sim(req: StartRequest):
    run = SimRun(
        config_path=CONFIG_PATH,
        population=req.population,
        years=req.years,
        dt=req.dt,
        start_year=req.start_year,
        seed=req.seed,
        mixing_method=req.mixing_method,
        use_numba=req.use_numba,
    )
    REGISTRY.add(run)
    run.start()
    return StartResponse(id=run.id, status=run.status)


@app.get("/api/simulations/{run_id}")
def get_status(run_id: str):
    run = REGISTRY.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"id": run.id, "status": run.status}


@app.post("/api/simulations/{run_id}/stop")
def stop_sim(run_id: str):
    run = REGISTRY.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.stop()
    return {"id": run.id, "status": run.status}


@app.websocket("/ws/simulations/{run_id}")
async def ws_updates(ws: WebSocket, run_id: str):
    await ws.accept()
    run = REGISTRY.get(run_id)
    if not run:
        await ws.send_json({"type": "error", "message": "Run not found"})
        await ws.close()
        return
    try:
        while True:
            # Drain queue cooperatively
            try:
                row = run.queue.get_nowait()
                await ws.send_json({"type": "year_update", "data": row, "id": run.id})
            except Exception:
                # No data; send heartbeat/status
                await asyncio.sleep(0.2)
                if run.status in ("completed", "error"):
                    await ws.send_json({"type": run.status, "id": run.id})
                    break
    except WebSocketDisconnect:
        return


# To launch: uvicorn ui_server.main:app --reload

