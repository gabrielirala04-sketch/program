"""Calculadoras con unidades explícitas y modelos documentados."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    default: float
    minimum: float = 0.000001
    maximum: float = 1e9


@dataclass(frozen=True)
class Calculator:
    name: str
    fields: tuple
    formula: str
    assumption: str
    solve: object


F = Field
C = Calculator
CALCULATORS = [
    C(
        "Ley de Ohm y potencia",
        (F("v", "Tensión [V]", 12, -1e6), F("r", "Resistencia [Ω]", 1000)),
        "I = V/R · P = V²/R",
        "Resistencia ideal de CC; potencia disipada.",
        lambda v, r: {"Corriente [A]": v / r, "Potencia [W]": v * v / r},
    ),
    C(
        "Divisor de tensión",
        (
            F("v", "Entrada [V]", 12, -1e6),
            F("r1", "R1 [Ω]", 10000),
            F("r2", "R2 [Ω]", 2000),
        ),
        "Vo = Vi R2/(R1 + R2)",
        "Salida sobre R2, sin carga conectada.",
        lambda v, r1, r2: {
            "Salida [V]": v * r2 / (r1 + r2),
            "R Thévenin [Ω]": r1 * r2 / (r1 + r2),
        },
    ),
    C(
        "Resistencias serie / paralelo",
        (F("r1", "R1 [Ω]", 100), F("r2", "R2 [Ω]", 200)),
        "Rs = R1 + R2 · Rp = R1R2/(R1 + R2)",
        "Dos resistencias ideales.",
        lambda r1, r2: {"Serie [Ω]": r1 + r2, "Paralelo [Ω]": r1 * r2 / (r1 + r2)},
    ),
    C(
        "Amplificador operacional",
        (
            F("v", "Entrada [V]", 0.1, -1e6),
            F("rf", "Rf [Ω]", 10000),
            F("rg", "Rg o Rin [Ω]", 1000),
        ),
        "Av+ = 1 + Rf/Rg · Av− = −Rf/Rin",
        "Operacional ideal. No modela saturación ni límites de alimentación.",
        lambda v, rf, rg: {
            "Ganancia no inversora": 1 + rf / rg,
            "Salida no inversora [V]": v * (1 + rf / rg),
            "Ganancia inversora": -rf / rg,
            "Salida inversora [V]": -v * rf / rg,
        },
    ),
    C(
        "Filtro RC",
        (F("r", "Resistencia [Ω]", 1000), F("c", "Capacitancia [µF]", 1)),
        "τ = RC · fc = 1/(2πRC)",
        "Filtro de primer orden sin carga; C se ingresa en microfaradios.",
        lambda r, c: {
            "Constante τ [s]": r * c * 1e-6,
            "Corte [Hz]": 1 / (2 * math.pi * r * c * 1e-6),
        },
    ),
    C(
        "Potencia trifásica",
        (
            F("v", "Tensión de línea RMS [V]", 380),
            F("i", "Corriente de línea RMS [A]", 10, 0),
            F("pf", "Factor de potencia", 0.85, 0, 1),
        ),
        "S = √3 VL IL · P = S cos φ · |Q| = S √(1 − cos² φ)",
        "Sistema equilibrado. Q se muestra como magnitud.",
        lambda v, i, pf: {
            "Aparente [VA]": math.sqrt(3) * v * i,
            "Activa [W]": math.sqrt(3) * v * i * pf,
            "Reactiva |Q| [var]": math.sqrt(3) * v * i * math.sqrt(1 - pf * pf),
        },
    ),
    C(
        "Motor: velocidad y deslizamiento",
        (
            F("f", "Frecuencia [Hz]", 50),
            F("p", "Número de polos (par)", 4, 2, 100),
            F("n", "Velocidad del rotor [rpm]", 1450, 0),
        ),
        "ns = 120 f/p · s = (ns − n)/ns",
        "Velocidad mecánica. Deslizamiento negativo indica régimen generador.",
        lambda f, p, n: {
            "Síncrona [rpm]": 120 * f / p,
            "Deslizamiento [%]": 100 * (120 * f / p - n) / (120 * f / p),
        },
    ),
    C(
        "Sensor de 4–20 mA",
        (
            F("i", "Corriente [mA]", 12, 4, 20),
            F("lo", "Mínimo de escala", 0, -1e9),
            F("hi", "Máximo de escala", 100, -1e9),
        ),
        "y = ymin + (I − 4)(ymax − ymin)/16",
        "Interpolación lineal dentro del rango nominal.",
        lambda i, lo, hi: {
            "Valor en unidades de escala": lo + (i - 4) * (hi - lo) / 16
        },
    ),
    C(
        "ADC ideal",
        (
            F("v", "Entrada [V]", 1.65, 0),
            F("ref", "Referencia [V]", 3.3),
            F("bits", "Resolución [bits]", 12, 1, 24),
        ),
        "LSB = Vref/2ⁿ · código = floor(Vin/LSB), limitado a 2ⁿ−1",
        "ADC unipolar ideal; Vin debe estar entre 0 y Vref.",
        lambda v, ref, bits: {
            "LSB [V]": ref / 2 ** int(bits),
            "Código": min(2 ** int(bits) - 1, math.floor(v / ref * 2 ** int(bits))),
        },
    ),
    C(
        "Esfuerzo axial",
        (
            F("force", "Fuerza [N]", 10000, -1e9),
            F("area", "Sección [mm²]", 100),
            F("young", "Módulo E [GPa]", 200),
            F("length", "Longitud [m]", 1),
        ),
        "σ = F/A · ε = σ/E · ΔL = ε L",
        "Barra uniforme, carga axial y elasticidad lineal.",
        lambda force, area, young, length: {
            "Tensión [MPa]": force / area,
            "Deformación ε": force / (area * young * 1000),
            "Alargamiento [mm]": force * length / (area * young),
        },
    ),
    C(
        "Viga simplemente apoyada",
        (
            F("force", "Carga central [N]", 1000, 0),
            F("length", "Luz [m]", 2),
            F("young", "Módulo E [GPa]", 200),
            F("inertia", "Momento de área [cm⁴]", 100),
        ),
        "Mmax = FL/4 · δmax = FL³/(48EI)",
        "Viga Euler–Bernoulli, carga puntual central, sección constante, pequeña deformación.",
        lambda force, length, young, inertia: {
            "Momento máximo [N·m]": force * length / 4,
            "Flecha máxima [mm]": force
            * length**3
            / (48 * young * 1e9 * inertia * 1e-8)
            * 1000,
        },
    ),
    C(
        "Potencia de bomba",
        (
            F("rho", "Densidad [kg/m³]", 1000),
            F("flow", "Caudal [L/s]", 10, 0),
            F("head", "Altura [m]", 20, 0),
            F("eff", "Rendimiento [%]", 75, 0.001, 100),
        ),
        "Ph = ρgQH · Peje = Ph/η",
        "Régimen estacionario, g = 9.80665 m/s². La altura debe incluir las pérdidas.",
        lambda rho, flow, head, eff: {
            "Hidráulica [W]": rho * 9.80665 * flow / 1000 * head,
            "En el eje [W]": rho * 9.80665 * flow / 1000 * head / (eff / 100),
        },
    ),
    C(
        "Continuidad en tubería",
        (F("flow", "Caudal [L/s]", 10, 0), F("diam", "Diámetro interno [mm]", 50)),
        "v = Q/A · A = πD²/4",
        "Flujo incompresible; velocidad media.",
        lambda flow, diam: {
            "Velocidad [m/s]": flow / 1000 / (math.pi * (diam / 1000) ** 2 / 4)
        },
    ),
    C(
        "Calor sensible",
        (
            F("mass", "Masa [kg]", 1),
            F("cp", "Calor específico [J/(kg·K)]", 4180),
            F("delta", "Cambio de temperatura [K]", 20, -1e6),
        ),
        "Q = m cp ΔT",
        "cp constante, sin cambio de fase.",
        lambda mass, cp, delta: {
            "Calor [J]": mass * cp * delta,
            "Calor [kJ]": mass * cp * delta / 1000,
        },
    ),
    C(
        "Rendimiento de Carnot",
        (
            F("hot", "Temperatura caliente [K]", 600),
            F("cold", "Temperatura fría [K]", 300),
        ),
        "ηmáx = 1 − Tc/Th",
        "Límite de un motor reversible entre dos focos, Th > Tc > 0.",
        lambda hot, cold: {"Rendimiento ideal [%]": 100 * (1 - cold / hot)},
    ),
    C(
        "Incertidumbre combinada",
        (
            F("a", "Incertidumbre estándar u1", 0.1, 0),
            F("b", "Incertidumbre estándar u2", 0.2, 0),
            F("k", "Factor de cobertura k", 2),
        ),
        "uc = √(u1² + u2²) · U = k uc",
        "Suma de magnitudes independientes, mismas unidades, sensibilidades unitarias.",
        lambda a, b, k: {
            "Estándar combinada": math.hypot(a, b),
            "Expandida": k * math.hypot(a, b),
        },
    ),
]


def solve_calculator(index, values):
    calc = CALCULATORS[index]
    if set(values) != {f.key for f in calc.fields}:
        raise ValueError("Faltan parámetros")
    for field in calc.fields:
        value = values[field.key]
        if not math.isfinite(value) or not field.minimum <= value <= field.maximum:
            raise ValueError(f"{field.label}: valor fuera de rango")
    if "bits" in values and values["bits"] != int(values["bits"]):
        raise ValueError("La resolución debe ser entera")
    if "p" in values and values["p"] % 2:
        raise ValueError("El número de polos debe ser par")
    if "ref" in values and values["v"] > values["ref"]:
        raise ValueError("La entrada no puede superar la referencia")
    if "hot" in values and values["cold"] >= values["hot"]:
        raise ValueError("El foco caliente debe superar al frío")
    if "hi" in values and values["hi"] <= values["lo"]:
        raise ValueError("El máximo debe superar al mínimo")
    result = calc.solve(**values)
    if not all(math.isfinite(x) for x in result.values()):
        raise ValueError("El cálculo excede el rango numérico")
    return result


UNITS = {
    "Longitud": {
        "m": (1, 0),
        "mm": (0.001, 0),
        "cm": (0.01, 0),
        "km": (1000, 0),
        "in": (0.0254, 0),
    },
    "Área": {"m²": (1, 0), "cm²": (1e-4, 0), "mm²": (1e-6, 0)},
    "Presión": {
        "Pa": (1, 0),
        "kPa": (1000, 0),
        "MPa": (1e6, 0),
        "bar": (1e5, 0),
        "atm": (101325, 0),
        "psi": (6894.757293, 0),
    },
    "Energía": {
        "J": (1, 0),
        "kJ": (1000, 0),
        "Wh": (3600, 0),
        "kWh": (3.6e6, 0),
        "cal": (4.184, 0),
    },
    "Potencia": {
        "W": (1, 0),
        "kW": (1000, 0),
        "hp mecánico": (745.699872, 0),
        "CV": (735.49875, 0),
    },
    "Temperatura": {"K": (1, 0), "°C": (1, 273.15), "°F": (5 / 9, 255.3722222222222)},
    "Ángulo": {"rad": (1, 0), "°": (math.pi / 180, 0)},
    "Frecuencia": {"Hz": (1, 0), "kHz": (1000, 0), "MHz": (1e6, 0), "rpm": (1 / 60, 0)},
    "Capacitancia": {
        "F": (1, 0),
        "mF": (0.001, 0),
        "µF": (1e-6, 0),
        "nF": (1e-9, 0),
        "pF": (1e-12, 0),
    },
    "Inductancia": {"H": (1, 0), "mH": (0.001, 0), "µH": (1e-6, 0)},
    "Caudal": {
        "m³/s": (1, 0),
        "L/s": (0.001, 0),
        "L/min": (1 / 60000, 0),
        "m³/h": (1 / 3600, 0),
    },
}


def convert(value, dimension, source, target):
    if not math.isfinite(value):
        raise ValueError("Ingresá un valor finito")
    factor, offset = UNITS[dimension][source]
    base = value * factor + offset
    if dimension == "Temperatura" and base < 0:
        raise ValueError("Temperatura inferior al cero absoluto")
    factor, offset = UNITS[dimension][target]
    return (base - offset) / factor
