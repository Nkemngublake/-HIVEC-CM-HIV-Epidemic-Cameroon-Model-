"""
Optional numeric accelerators using Numba.

Provides jitted kernels when Numba is available; falls back to NumPy otherwise.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from numba import njit  # type: ignore

    NUMBA_AVAILABLE = True

    @njit(cache=True)
    def poisson_counts_numba(lams: np.ndarray, seed: int) -> np.ndarray:  # pragma: no cover - numba
        np.random.seed(seed)
        n = lams.shape[0]
        out = np.empty(n, dtype=np.int64)
        for i in range(n):
            lam = lams[i]
            if lam <= 0.0:
                out[i] = 0
            else:
                out[i] = np.random.poisson(lam)
        return out

except Exception:  # Numba not present or incompatible
    NUMBA_AVAILABLE = False

    def poisson_counts_numba(lams: np.ndarray, seed: int) -> np.ndarray:
        raise RuntimeError("Numba is not available")
