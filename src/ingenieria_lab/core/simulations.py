"""Modelos lineales ideales para exploración académica."""

from dataclasses import dataclass
import math
import numpy as np
from scipy import signal
from ingenieria_lab.core.engineering import Field as F


@dataclass(frozen=True)
class Model:
    name: str
    fields: tuple
    description: str


MODELS = [
    Model(
        "RC · carga de capacitor",
        (
            F("r", "Resistencia [Ω]", 1000, 0.01, 1e7),
            F("c", "Capacitancia [µF]", 100, 0.001, 1e6),
            F("v", "Escalón [V]", 5, -1000, 1000),
        ),
        "Fuente ─ R ─ C ─ tierra · salida sobre C\nVc(t) = V(1 − exp(−t/RC)); capacitor inicialmente descargado.",
    ),
    Model(
        "RLC · respuesta al escalón",
        (
            F("r", "Resistencia [Ω]", 20, 0.01, 1e6),
            F("l", "Inductancia [mH]", 100, 0.001, 1e6),
            F("c", "Capacitancia [µF]", 10, 0.001, 1e6),
            F("v", "Escalón [V]", 5, -1000, 1000),
        ),
        "R, L y C en serie · salida sobre C\nH(s) = 1/(LCs² + RCs + 1). Energía inicial nula; componentes ideales.",
    ),
    Model(
        "RLC · análisis de CA",
        (
            F("r", "Resistencia [Ω]", 100, 0.01, 1e6),
            F("l", "Inductancia [mH]", 100, 0.001, 1e6),
            F("c", "Capacitancia [µF]", 10, 0.001, 1e6),
            F("v", "Fuente RMS [V]", 12, 0, 1000),
            F("f", "Frecuencia [Hz]", 50, 0.001, 1e6),
        ),
        "R, L y C en serie; régimen sinusoidal permanente.\nZ = R + j(ωL − 1/ωC). Las curvas muestran valores instantáneos.",
    ),
    Model(
        "Masa · resorte · amortiguador",
        (
            F("m", "Masa [kg]", 1, 0.001, 1e5),
            F("k", "Rigidez [N/m]", 100, 0.001, 1e7),
            F("b", "Amortiguamiento [N·s/m]", 2, 0, 1e5),
            F("x0", "Posición inicial [m]", 0.1, -100, 100),
        ),
        "m x″ + b x′ + k x = 0\nVibración libre, velocidad inicial nula. Resorte y amortiguador lineales.",
    ),
    Model(
        "Control · segundo orden",
        (
            F("wn", "Frecuencia natural [rad/s]", 10, 0.001, 1e5),
            F("zeta", "Amortiguamiento ζ", 0.3, 0.001, 20),
            F("gain", "Ganancia estática", 1, -1000, 1000),
        ),
        "G(s) = Kωn² / (s² + 2ζωns + ωn²)\nRespuesta a escalón unitario; condiciones iniciales nulas.",
    ),
]


def simulate(index, p):
    model = MODELS[index]
    if set(p) != {f.key for f in model.fields}:
        raise ValueError("Faltan parámetros")
    for f in model.fields:
        if not math.isfinite(p[f.key]) or not f.minimum <= p[f.key] <= f.maximum:
            raise ValueError(f"{f.label}: valor fuera de rango")
    if index == 0:
        tau = p["r"] * p["c"] * 1e-6
        t = np.linspace(0, 6 * tau, 1800)
        return (
            t,
            {"Vc [V]": p["v"] * (-np.expm1(-t / tau))},
            "Tensión [V]",
            {
                "τ [s]": tau,
                "fc [Hz]": 1 / (2 * np.pi * tau),
                "Valor final ideal [V]": p["v"],
            },
        )
    if index == 2:
        omega = 2 * np.pi * p["f"]
        z = complex(p["r"], omega * p["l"] * 0.001 - 1 / (omega * p["c"] * 1e-6))
        current = p["v"] / z
        t = np.linspace(0, 4 / p["f"], 2000)
        # Corriente en gráfico separado por selector; cada curva conserva su unidad.
        return (
            t,
            {
                "Fuente [V]": np.sqrt(2) * p["v"] * np.sin(omega * t),
                "Corriente [A]": np.sqrt(2)
                * abs(current)
                * np.sin(omega * t + np.angle(current)),
            },
            "Amplitud (unidad en leyenda)",
            {
                "|Z| [Ω]": abs(z),
                "Fase Z [°]": np.angle(z, deg=True),
                "I RMS [A]": abs(current),
                "P [W]": abs(current) ** 2 * p["r"],
                "Q [var]": abs(current) ** 2 * z.imag,
                "Resonancia [Hz]": 1
                / (2 * np.pi * np.sqrt(p["l"] * 0.001 * p["c"] * 1e-6)),
            },
        )
    if index == 1:
        l, c = p["l"] * 0.001, p["c"] * 1e-6
        wn = 1 / np.sqrt(l * c)
        zeta = p["r"] / 2 * np.sqrt(c / l)
        gain = p["v"]
    elif index == 3:
        wn = np.sqrt(p["k"] / p["m"])
        zeta = p["b"] / (2 * np.sqrt(p["k"] * p["m"]))
        gain = None
    else:
        wn, zeta, gain = p["wn"], p["zeta"], p["gain"]
    # Horizonte adaptativo: seis constantes del polo lento o seis períodos.
    decay = wn * zeta if zeta <= 1 else wn / (zeta + np.sqrt(zeta * zeta - 1))
    duration = max(6 / max(decay, wn * 0.03), 6 * 2 * np.pi / wn)
    cycles = duration * wn / (2 * np.pi)
    if cycles > 500:
        raise ValueError(
            "Escalas demasiado separadas; ajustá el amortiguamiento para una simulación resuelta"
        )
    count = min(30000, max(2000, int(cycles * 60)))
    t = np.linspace(0, duration, count)
    if index == 3:
        system = signal.StateSpace(
            [[0, 1], [-p["k"] / p["m"], -p["b"] / p["m"]]],
            [[0], [1 / p["m"]]],
            [[1, 0]],
            [[0]],
        )
        _, y, _ = signal.lsim(system, np.zeros_like(t), t, X0=[p["x0"], 0])
        label, unit = "Posición [m]", "Posición [m]"
    else:
        _, y = signal.step(
            signal.TransferFunction([gain * wn**2], [1, 2 * zeta * wn, wn**2]), T=t
        )
        label, unit = (
            ("Vc [V]", "Tensión [V]")
            if index == 1
            else ("Salida", "Salida / entrada unitaria")
        )
    if not np.all(np.isfinite(y)):
        raise ValueError("El modelo excede el rango numérico")
    metrics = {
        "ωn [rad/s]": wn,
        "Amortiguamiento ζ": zeta,
        "Máximo en ventana": float(np.max(y)),
    }
    if gain is not None:
        metrics["Valor final ideal"] = gain
    return t, {label: y}, unit, metrics
