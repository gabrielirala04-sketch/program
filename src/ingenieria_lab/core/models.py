"""Modelos compartidos para simulaciones."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Waveform = Literal["sine", "square", "triangle", "sawtooth"]


@dataclass(frozen=True)
class SignalConfig:
    """Parámetros de una señal periódica ideal."""

    waveform: Waveform = "sine"
    amplitude_v: float = 5.0
    frequency_hz: float = 50.0
    phase_deg: float = 0.0
    offset_v: float = 0.0
    duration_s: float = 0.1
    sample_rate_hz: float = 10_000.0

    def validate(self) -> None:
        """Rechaza configuraciones no físicas o no soportadas."""
        import math

        values = (
            self.amplitude_v,
            self.frequency_hz,
            self.phase_deg,
            self.offset_v,
            self.duration_s,
            self.sample_rate_hz,
        )
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Todos los parámetros deben ser finitos")
        if self.waveform not in ("sine", "square", "triangle", "sawtooth"):
            raise ValueError("Forma de onda desconocida")
        if self.amplitude_v < 0 or self.frequency_hz <= 0 or self.duration_s <= 0:
            raise ValueError("Amplitud no negativa; frecuencia y duración positivas")
        if self.sample_rate_hz <= 2 * self.frequency_hz:
            raise ValueError(
                "La frecuencia de muestreo debe superar 2 veces la frecuencia"
            )
        if self.sample_rate_hz * self.duration_s > 2_000_000:
            raise ValueError("Demasiadas muestras; límite: 2 millones")
        if int(self.sample_rate_hz * self.duration_s) < 2:
            raise ValueError("Se requieren al menos dos muestras")
