"""Generación de señales periódicas ideales."""

from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from ingenieria_lab.core.models import SignalConfig


def generate(config: SignalConfig) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Devuelve tiempo [s] y tensión [V], sin incluir el extremo final."""
    config.validate()
    n = int(config.sample_rate_hz * config.duration_s)
    t = np.arange(n, dtype=np.float64) / config.sample_rate_hz
    cycles = config.frequency_hz * t + config.phase_deg / 360.0
    phase = 2 * np.pi * cycles
    if config.waveform == "sine":
        base = np.sin(phase)
    elif config.waveform == "square":
        base = np.where(np.sin(phase) >= 0, 1.0, -1.0)
    elif config.waveform == "triangle":
        base = 2 / np.pi * np.arcsin(np.sin(phase))
    else:
        base = 2 * np.mod(cycles, 1.0) - 1.0
    voltage = config.offset_v + config.amplitude_v * base
    return t, voltage
