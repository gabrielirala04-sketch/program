import numpy as np
from CoolProp.CoolProp import PropsSI, PhaseSI
from .types import Tool, n, choice, curve, chart, result

SUBJECT = "Termodinámica"


def state(p):
    if p["mode"] == "Presión y temperatura":
        args = ("P", p["P"] * 1000, "T", p["T"] + 273.15, p["fluid"])
    else:
        args = ("P", p["P"] * 1000, "Q", p["quality"], p["fluid"])
    values = {key: PropsSI(key, *args) for key in ("T", "P", "D", "H", "S", "U")}
    return result(
        {
            "Temperatura [°C]": values["T"] - 273.15,
            "Presión [kPa]": values["P"] / 1000,
            "Densidad [kg/m³]": values["D"],
            "Volumen específico [m³/kg]": 1 / values["D"],
            "Entalpía [kJ/kg]": values["H"] / 1000,
            "Entropía [kJ/(kg·K)]": values["S"] / 1000,
            "Energía interna [kJ/kg]": values["U"] / 1000,
            "Fase CoolProp": PhaseSI(*args),
        },
        note="Propiedades calculadas con CoolProp. En saturación usá P y calidad, porque P y T no definen la mezcla. Temperatura se ignora en modo P,Q y calidad se ignora en modo P,T. h y s dependen de una referencia; compará diferencias coherentes.",
    )


def rankine(p):
    low, high = p["low"] * 1000, p["high"] * 1000
    temp = p["temp"] + 273.15
    if low >= high:
        raise ValueError("La presión de caldera debe superar la del condensador")
    if temp <= PropsSI("T", "P", high, "Q", 1, "Water"):
        raise ValueError(
            "Elegí temperatura de entrada a turbina por encima de saturación"
        )
    h1 = PropsSI("H", "P", low, "Q", 0, "Water")
    s1 = PropsSI("S", "P", low, "Q", 0, "Water")
    h2 = PropsSI("H", "P", high, "S", s1, "Water")
    s2 = s1
    h3 = PropsSI("H", "P", high, "T", temp, "Water")
    s3 = PropsSI("S", "P", high, "T", temp, "Water")
    h4 = PropsSI("H", "P", low, "S", s3, "Water")
    s4 = s3
    qin = h3 - h2
    wt = h3 - h4
    wp = h2 - h1
    wnet = wt - wp
    qout = h4 - h1
    if qin <= 0 or wnet <= 0:
        raise ValueError("Los parámetros no producen un ciclo motor Rankine válido")
    states = [(low, h1, s1), (high, h2, s2), (high, h3, s3), (low, h4, s4)]
    rows = [
        [
            i + 1,
            P / 1000,
            PropsSI("T", "P", P, "H", h, "Water") - 273.15,
            h / 1000,
            s / 1000,
        ]
        for i, (P, h, s) in enumerate(states)
    ]
    quality = PropsSI("Q", "P", low, "H", h4, "Water")
    # Build actual isentropic/isobaric paths, not straight joins between state points.
    Ps = [
        np.geomspace(low, high, 80),
        np.full(160, high),
        np.geomspace(high, low, 80),
        np.full(160, low),
    ]
    Ss = [
        np.full(80, s1),
        np.linspace(s2, s3, 160),
        np.full(80, s3),
        np.linspace(s4, s1, 160),
    ]
    curves = []
    for name, press, entropy in zip(
        (
            "Bomba isentrópica",
            "Caldera isobárica",
            "Turbina isentrópica",
            "Condensador isobárico",
        ),
        Ps,
        Ss,
    ):
        T = PropsSI("T", "P", press, "S", entropy, "Water")
        curves.append(curve(name, entropy / 1000, T - 273.15))
    return result(
        {
            "Trabajo turbina [kJ/kg]": wt / 1000,
            "Trabajo bomba [kJ/kg]": wp / 1000,
            "Trabajo neto [kJ/kg]": wnet / 1000,
            "Calor aportado [kJ/kg]": qin / 1000,
            "Calor rechazado [kJ/kg]": qout / 1000,
            "Rendimiento [%]": 100 * wnet / qin,
            "Calidad salida turbina": quality
            if 0 <= quality <= 1
            else "Fuera de mezcla saturada",
        },
        [chart("Ciclo T–s", "s [kJ/(kg·K)]", "T [°C]", *curves)],
        ["Estado", "P [kPa]", "T [°C]", "h [kJ/kg]", "s [kJ/(kg·K)]"],
        rows,
        note="Rankine ideal con agua: bomba y turbina isentrópicas, sin pérdidas de presión; salida condensador líquido saturado. Propiedades reales mediante CoolProp; equipos ideales.",
    )


def otto(p):
    r, gamma = p["ratio"], p["gamma"]
    T1 = p["T1"]
    T3 = p["T3"]
    P1 = p["P1"]
    R = p["R"]
    cv = R / (gamma - 1)
    T2 = T1 * r ** (gamma - 1)
    T4 = T3 / r ** (gamma - 1)
    if T3 <= T2:
        raise ValueError("T3 debe superar T2 para aportar calor en un ciclo motor")
    v1 = R * T1 / (P1 * 1000)
    v2 = v1 / r
    P2 = P1 * r**gamma
    P3 = P2 * T3 / T2
    P4 = P1 * T4 / T1
    compression = np.linspace(v1, v2, 180)
    expansion = np.linspace(v2, v1, 180)
    qin = cv * (T3 - T2)
    qout = cv * (T4 - T1)
    return result(
        {
            "Rendimiento [%]": 100 * (1 - r ** (1 - gamma)),
            "Calor entrante [kJ/kg]": qin / 1000,
            "Calor saliente [kJ/kg]": qout / 1000,
            "Trabajo neto [kJ/kg]": (qin - qout) / 1000,
        },
        [
            chart(
                "Ciclo Otto P–v",
                "v [m³/kg]",
                "P [kPa]",
                curve("1→2 isentrópica", compression, P1 * (v1 / compression) ** gamma),
                curve("2→3 isócora", [v2, v2], [P2, P3]),
                curve("3→4 isentrópica", expansion, P3 * (v2 / expansion) ** gamma),
                curve("4→1 isócora", [v1, v1], [P4, P1]),
            )
        ],
        ["Estado", "T [K]", "P [kPa]", "v [m³/kg]"],
        [[1, T1, P1, v1], [2, T2, P2, v2], [3, T3, P3, v2], [4, T4, P4, v1]],
        note="Modelo aire estándar, gas ideal y calores específicos constantes. No representa combustión, fricción ni pérdidas reales.",
    )


def polytropic(p):
    P1, V1, V2, exponent = p["P1"], p["V1"], p["V2"], p["n"]
    P2 = P1 * (V1 / V2) ** exponent
    work = (
        P1 * V1 * np.log(V2 / V1)
        if abs(exponent - 1) < 1e-10
        else (P2 * V2 - P1 * V1) / (1 - exponent)
    )
    V = np.linspace(V1, V2, 200)
    return result(
        {
            "P final [kPa]": P2,
            "Trabajo del gas [kJ]": work,
            "T2/T1 (gas ideal)": (V1 / V2) ** (exponent - 1),
        },
        [
            chart(
                "Proceso P–V",
                "Volumen [m³]",
                "P [kPa]",
                curve("PVⁿ constante", V, P1 * (V1 / V) ** exponent),
            )
        ],
        note="Proceso cuasiestático PVⁿ constante. Trabajo positivo en expansión; volumen total, no específico. No calcula calor sin propiedades calóricas adicionales.",
    )


def balance(p):
    return result(
        {
            "ΔU [kJ]": p["Q"] - p["W"],
            "u final [kJ/kg]": p["u1"] + (p["Q"] - p["W"]) / p["m"],
        },
        note="Sistema cerrado, sin variación de energía cinética o potencial. Q positivo hacia el sistema y W positivo realizado por el sistema.",
    )


TOOLS = [
    Tool(
        "fluid",
        "Agua y refrigerante: propiedades",
        SUBJECT,
        "Calculadora",
        (
            choice("fluid", "Fluido", ["Water", "R134a"]),
            choice(
                "mode",
                "Par de propiedades",
                ["Presión y temperatura", "Presión y calidad"],
            ),
            n("P", "Presión absoluta [kPa]", 101.325, 1, 100000),
            n("T", "Temperatura [°C], modo P,T", 25, -100, 1000),
            n("quality", "Calidad x, modo P,x", 0.5, 0, 1),
        ),
        "Tabla de propiedades reales y fase, usando la biblioteca CoolProp.",
        "Estado definido por P,T o P,x; calidad = fracción másica de vapor",
        state,
    ),
    Tool(
        "rankine",
        "Ciclo Rankine ideal con agua",
        SUBJECT,
        "Laboratorio",
        (
            n("low", "Presión condensador [kPa]", 10, 0.7, 1000),
            n("high", "Presión caldera [kPa]", 8000, 100, 22000),
            n("temp", "Temperatura entrada turbina [°C]", 480, 100, 700),
        ),
        "Estados, balance energético, calidad de escape y diagrama T–s con trayectorias termodinámicas.",
        "η=(wt−wp)/qin · s2=s1 · s4=s3",
        rankine,
    ),
    Tool(
        "otto",
        "Ciclo Otto aire estándar",
        SUBJECT,
        "Laboratorio",
        (
            n("ratio", "Relación de compresión r", 8, 1.01, 30),
            n("gamma", "γ=cp/cv", 1.4, 1.01, 2),
            n("T1", "Temperatura inicial [K]", 300, 1, 2000),
            n("T3", "Temperatura máxima [K]", 1800, 10, 6000),
            n("P1", "Presión inicial [kPa]", 100, 0.1, 10000),
            n("R", "R específica [J/(kg·K)]", 287, 1, 5000),
        ),
        "Cuatro estados y diagrama P–v; comparar calor y trabajo.",
        "ηOtto=1−1/r^(γ−1)",
        otto,
    ),
    Tool(
        "polytropic",
        "Proceso politrópico P–V",
        SUBJECT,
        "Laboratorio",
        (
            n("P1", "Presión inicial absoluta [kPa]", 100, 0.001),
            n("V1", "Volumen inicial [m³]", 1, 0.000001),
            n("V2", "Volumen final [m³]", 2, 0.000001),
            n("n", "Exponente politrópico n", 1, 0, 3),
        ),
        "Incluye n=0 isobárico y n=1 isotérmico de gas ideal.",
        "W=(P2V2−P1V1)/(1−n); n=1: W=P1V1 ln(V2/V1)",
        polytropic,
    ),
    Tool(
        "balance",
        "Primera ley: sistema cerrado",
        SUBJECT,
        "Calculadora",
        (
            n("Q", "Calor hacia el sistema [kJ]", 100, -1e9),
            n("W", "Trabajo del sistema [kJ]", 30, -1e9),
            n("m", "Masa [kg]", 2, 0.000001),
            n("u1", "Energía interna específica inicial [kJ/kg]", 200, -1e9),
        ),
        "Balance con convenio de signos explícito.",
        "ΔU=Q−W",
        balance,
    ),
]
