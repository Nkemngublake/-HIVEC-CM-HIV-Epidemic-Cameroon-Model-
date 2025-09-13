import os
import threading
import uuid
from queue import Queue
from typing import Dict, Optional

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel


class SimRun:
    def __init__(self, *, config_path: str, population: int, years: int, dt: float,
                 start_year: int, seed: Optional[int], mixing_method: str, use_numba: bool):
        self.id = str(uuid.uuid4())
        self.queue: Queue = Queue()
        self.updates = []
        self.status = 'pending'
        self.thread: Optional[threading.Thread] = None
        self.model: Optional[EnhancedHIVModel] = None

        params = load_parameters(config_path)
        params.initial_population = population

        def on_year_result(row: dict):
            self.queue.put(row)

        self.model = EnhancedHIVModel(
            params,
            start_year=start_year,
            seed=seed,
            mixing_method=mixing_method,
            use_numba=use_numba,
            on_year_result=on_year_result,
        )

        def target():
            self.status = 'running'
            try:
                self.model.run_simulation(years=years, dt=dt)
                self.status = 'completed'
            except Exception:
                self.status = 'error'

        self.thread = threading.Thread(target=target, daemon=True)

    def start(self):
        if self.thread and not self.thread.is_alive():
            self.thread.start()

    def stop(self):
        if self.model:
            self.model.request_stop()


class RunRegistry:
    def __init__(self):
        self.runs: Dict[str, SimRun] = {}

    def add(self, run: SimRun):
        self.runs[run.id] = run

    def get(self, run_id: str) -> Optional[SimRun]:
        return self.runs.get(run_id)

