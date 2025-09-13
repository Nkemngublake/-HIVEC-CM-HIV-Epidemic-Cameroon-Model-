#!/usr/bin/env python3
"""
Benchmark the transmission routine with and without binning/Numba across populations.
"""

import os
import sys
import time
from dataclasses import asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel


def run_once(population: int, years: float, dt: float, *,
             mixing_method: str, use_numba: bool | None) -> float:
    params = load_parameters(os.path.join(os.path.dirname(__file__), '../config/parameters.json'))
    params.initial_population = population
    t0 = time.perf_counter()
    model = EnhancedHIVModel(params, start_year=1990, seed=42,
                             use_numba=use_numba, mixing_method=mixing_method)
    model.run_simulation(years=years, dt=dt)
    t1 = time.perf_counter()
    return t1 - t0


def main():
    sizes = [10_000, 25_000, 50_000]
    years = 1.0
    dt = 0.1
    print("Benchmarking transmission routine")
    print(f"Years={years}, dt={dt}")
    print()
    header = f"{'Pop':>8} | {'Scan (no numba)':>17} | {'Binned (no numba)':>18} | {'Binned (numba)':>15}"
    print(header)
    print('-' * len(header))
    for pop in sizes:
        t_scan = run_once(pop, years, dt, mixing_method='scan', use_numba=False)
        t_binned = run_once(pop, years, dt, mixing_method='binned', use_numba=False)
        try:
            t_numba = run_once(pop, years, dt, mixing_method='binned', use_numba=True)
        except Exception:
            t_numba = float('nan')
        print(f"{pop:8d} | {t_scan:17.3f} | {t_binned:18.3f} | {t_numba:15.3f}")

    print("\nNote: 'Binned (numba)' requires Numba; shows NaN if unavailable.")


if __name__ == '__main__':
    main()

