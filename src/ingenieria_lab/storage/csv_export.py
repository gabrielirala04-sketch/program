"""Exportación sencilla de señales a CSV."""

from __future__ import annotations
from pathlib import Path
import numpy as np
from numpy.typing import NDArray


def export_csv(
    path: str | Path, t: NDArray[np.float64], v: NDArray[np.float64]
) -> None:
    """Guarda dos columnas con unidades en el encabezado."""
    if t.shape != v.shape:
        raise ValueError("Tiempo y tensión deben tener igual forma")
    np.savetxt(
        path,
        np.column_stack((t, v)),
        delimiter=",",
        header="time_s,voltage_v",
        comments="",
        fmt="%.12g",
    )
