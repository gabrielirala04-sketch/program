"""Mediciones discretas de señales."""

from __future__ import annotations
import numpy as np
from numpy.typing import NDArray


def measure(voltage: NDArray[np.float64]) -> dict[str, float]:
    """Calcula magnitudes sobre la ventana muestreada, no valores ideales."""
    if voltage.size == 0 or not np.all(np.isfinite(voltage)):
        raise ValueError("La señal debe contener muestras finitas")
    return {
        "mean_v": float(np.mean(voltage)),
        "rms_v": float(np.sqrt(np.mean(np.square(voltage)))),
        "min_v": float(np.min(voltage)),
        "max_v": float(np.max(voltage)),
        "peak_to_peak_v": float(np.ptp(voltage)),
    }
