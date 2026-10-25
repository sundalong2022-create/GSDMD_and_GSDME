"""Small shared statistical helpers."""

from __future__ import annotations

import numpy as np


def benjamini_hochberg(p_values: list[float] | np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values, returned in input order."""
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1:
        raise ValueError("p_values must be one-dimensional")
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("p_values must be finite and between 0 and 1")
    n = p.size
    if n == 0:
        return p.copy()
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adjusted_sorted = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.empty(n, dtype=float)
    adjusted[order] = np.minimum(adjusted_sorted, 1.0)
    return adjusted
