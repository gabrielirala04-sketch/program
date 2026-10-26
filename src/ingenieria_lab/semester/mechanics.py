import numpy as np
from .types import Tool, n, choice, curve, chart, result

SUBJECT = "Resistencia de Materiales"


def beam(p):
    L, F, q = p["L"], p["F"], p["q"]
    E = p["E"] * 1e9
    b, h = p["b"] / 1000, p["h"] / 1000
    I = b * h**3 / 12
    a = p["a"]
    if a > L:
        raise ValueError("La posición de carga a debe estar dentro de la luz L")
    # Include the load point and both sides of its shear jump.
    x = np.unique(np.r_[np.linspace(0, L, 801), a, max(0, a - L * 1e-9)])
    if p["support"] == "Simplemente apoyada":
        RA = F * (L - a) / L + q * L / 2
        RB = F * a / L + q * L / 2
        V = RA - q * x - F * (x >= a)
        M = RA * x - q * x * x / 2 - F * np.maximum(x - a, 0)
        primitive = RA * x**3 / 6 - q * x**4 / 24 - F * np.maximum(x - a, 0) ** 3 / 6
        end = RA * L**3 / 6 - q * L**4 / 24 - F * (L - a) ** 3 / 6
        d = (-primitive + end * x / L) / (E * I)
        reactions = {"Reacción izquierda [N]": RA, "Reacción derecha [N]": RB}
    else:
        V = q * (L - x) + F * (x < a)
        M = -q * (L - x) ** 2 / 2 - F * np.maximum(a - x, 0)
        # Point force at arbitrary a, free section beyond the force stays linear.
        d = (
            q * (L * L * x * x / 4 - L * x**3 / 6 + x**4 / 24)
            + F * (a * x * x / 2 - x**3 / 6 + np.maximum(x - a, 0) ** 3 / 6)
        ) / (E * I)
        reactions = {
            "Reacción vertical [N]": F + q * L,
            "Momento de reacción [N·m]": F * a + q * L * L / 2,
        }
    metrics = {
        **reactions,
        "I de sección [m⁴]": I,
        "|M| máximo muestreado [N·m]": float(np.max(np.abs(M))),
        "|Flecha| máxima muestreada [mm]": float(np.max(np.abs(d))) * 1000,
        "|Tensión de flexión| máxima [MPa]": float(np.max(np.abs(M))) * h / 2 / I / 1e6,
    }
    return result(
        metrics,
        [
            chart("Cortante", "Posición [m]", "V [N]", curve("V", x, V)),
            chart("Momento", "Posición [m]", "M [N·m]", curve("M", x, M)),
            chart(
                "Deformada",
                "Posición [m]",
                "Flecha hacia abajo [mm]",
                curve("Flecha", x, d * 1000),
            ),
        ],
        note="Sección rectangular uniforme; cargas hacia abajo. V=dM/dx. Flecha positiva hacia abajo, d″=−M/EI. Euler–Bernoulli, pequeñas deformaciones; no verifica resistencia admisible ni estabilidad.",
    )


def mohr(p):
    sx, sy, t = p["sx"], p["sy"], p["tau"]
    mean = (sx + sy) / 2
    radius = np.hypot((sx - sy) / 2, t)
    theta = np.linspace(0, 2 * np.pi, 361)
    principals = [mean + radius, mean - radius, 0]
    return result(
        {
            "σ1 en plano [MPa]": mean + radius,
            "σ2 en plano [MPa]": mean - radius,
            "τ máximo en plano [MPa]": radius,
            "τ máximo 3D [MPa]": (max(principals) - min(principals)) / 2,
            "Von Mises [MPa]": np.sqrt(sx * sx + sy * sy - sx * sy + 3 * t * t),
            "Ángulo principal [°]": np.degrees(0.5 * np.arctan2(2 * t, sx - sy)),
        },
        [
            chart(
                "Círculo de Mohr",
                "σ [MPa]",
                "τ [MPa]",
                curve("Mohr", mean + radius * np.cos(theta), radius * np.sin(theta)),
            )
        ],
        note="Estado plano de tensiones: σz=τxz=τyz=0. El ángulo físico es la mitad del ángulo de Mohr.",
    )


def torsion(p):
    D, d = p["D"] / 1000, p["d"] / 1000
    if d >= D:
        raise ValueError("El diámetro interior debe ser menor que el exterior")
    J = np.pi * (D**4 - d**4) / 32
    return result(
        {
            "Momento polar J [m⁴]": J,
            "τ máxima [MPa]": abs(p["T"]) * D / 2 / J / 1e6,
            "Giro [°]": np.degrees(p["T"] * p["L"] / (p["G"] * 1e9 * J)),
        }
    )


def buckling(p):
    I = p["I"] * 1e-8
    A = p["A"] * 1e-6
    effective = p["K"] * p["L"]
    return result(
        {
            "Carga crítica Euler [N]": np.pi**2 * p["E"] * 1e9 * I / effective**2,
            "Esbeltez KL/r": effective / np.sqrt(I / A),
            "Radio de giro [mm]": 1000 * np.sqrt(I / A),
        },
        note="Euler solo para columnas esbeltas, rectas, elásticas y carga axial centrada. K depende de los apoyos; no evalúa pandeo inelástico.",
    )


TOOLS = [
    Tool(
        "beam",
        "Vigas: cargas y diagramas",
        SUBJECT,
        "Laboratorio",
        (
            choice("support", "Apoyos", ["Simplemente apoyada", "Voladizo"]),
            n("L", "Luz L [m]", 2, 0.01, 100),
            n("F", "Carga puntual F [N]", 1000, 0, 1e7),
            n("a", "Posición de F desde izquierda [m]", 1, 0, 100),
            n("q", "Carga distribuida q [N/m]", 500, 0, 1e7),
            n("b", "Ancho de sección [mm]", 50, 0.1, 10000),
            n("h", "Alto de sección [mm]", 100, 0.1, 10000),
            n("E", "Módulo E [GPa]", 200, 0.01, 1000),
        ),
        "Carga puntual en a y carga uniforme sobre toda la luz. Voladizo empotrado a la izquierda.",
        "I=bh³/12 · σ=Mc/I · EI d″=−M",
        beam,
    ),
    Tool(
        "mohr",
        "Tensiones y círculo de Mohr",
        SUBJECT,
        "Laboratorio",
        (
            n("sx", "σx [MPa]", 80, -1e6, 1e6),
            n("sy", "σy [MPa]", 20, -1e6, 1e6),
            n("tau", "τxy [MPa]", 30, -1e6, 1e6),
        ),
        "Estado plano; principales, cortante y tensión equivalente.",
        "σ1,2=(σx+σy)/2 ± √[((σx−σy)/2)²+τ²]",
        mohr,
    ),
    Tool(
        "torsion",
        "Torsión de eje macizo o hueco",
        SUBJECT,
        "Calculadora",
        (
            n("T", "Par [N·m]", 500, -1e9),
            n("D", "Diámetro exterior [mm]", 40, 0.001),
            n("d", "Diámetro interior [mm]", 0),
            n("L", "Longitud [m]", 1, 0.0001),
            n("G", "Módulo G [GPa]", 80, 0.001),
        ),
        "Eje circular uniforme, material elástico; d=0 para macizo.",
        "J=π(D⁴−d⁴)/32 · τ=Tr/J · θ=TL/GJ",
        torsion,
    ),
    Tool(
        "buckling",
        "Pandeo de Euler",
        SUBJECT,
        "Calculadora",
        (
            n("E", "Módulo E [GPa]", 200, 0.001),
            n("I", "I mínimo [cm⁴]", 100, 0.001),
            n("A", "Área [mm²]", 1000, 0.001),
            n("L", "Longitud [m]", 3, 0.001),
            n("K", "Factor K (articulada-articulada: 1)", 1, 0.1, 5),
        ),
        "Usar el menor momento de área y el factor de longitud efectiva correspondiente.",
        "Pcr=π²EI/(KL)²",
        buckling,
    ),
]
