import numpy as np
from .types import Tool, n, choice, curve, chart, result

INSTALL = "Instalaciones Eléctricas"
MEASURE = "Mediciones Eléctricas y Electrónicas"


def cable(p):
    rho20 = 0.017241 if p["material"] == "Cobre" else 0.028264
    alpha = 0.00393 if p["material"] == "Cobre" else 0.00403
    rho = rho20 * (1 + alpha * (p["temp"] - 20))
    factor = 2 if p["system"] == "Monofásico" else np.sqrt(3)
    pf = p["pf"]
    sin = np.sqrt(1 - pf * pf)

    def drop(length, section):
        return (
            factor
            * p["I"]
            * length
            * (rho / section * pf + p["reactance"] / 1000 * sin)
        )

    dv = drop(p["L"], p["S"])
    options = np.array(
        [
            1.5,
            2.5,
            4,
            6,
            10,
            16,
            25,
            35,
            50,
            70,
            95,
            120,
            150,
            185,
            240,
            300,
            400,
            500,
            630,
        ]
    )
    passing = options[drop(p["L"], options) <= p["V"] * p["limit"] / 100]
    lengths = np.linspace(0, p["L"], 200)
    ncond = 2 if p["system"] == "Monofásico" else 3
    return result(
        {
            "Caída de tensión [V]": dv,
            "Caída [%]": 100 * dv / p["V"],
            "Tensión final aproximada [V]": p["V"] - dv,
            "Pérdida resistiva [W]": ncond * p["I"] ** 2 * rho * p["L"] / p["S"],
            "Sección de tabla por caída únicamente [mm²]": float(passing[0])
            if len(passing)
            else "Ninguna hasta 630 mm²",
        },
        [
            chart(
                "Caída frente a longitud",
                "Longitud de ida [m]",
                "Caída [%]",
                curve(
                    "Sección ingresada", lengths, 100 * drop(lengths, p["S"]) / p["V"]
                ),
            )
        ],
        note="Longitud de ida; trifásico equilibrado, tensión de línea, carga inductiva. Modelo aproximado R cosφ + X sinφ. El límite es un dato del ejercicio, no una norma universal. La sección mostrada NO verifica ampacidad, cortocircuito, protección, instalación ni temperatura admisible. Si la caída es grande, la aproximación pierde validez.",
    )


def compensation(p):
    if p["pf2"] < p["pf1"]:
        raise ValueError("El factor objetivo debe ser al menos el inicial")
    Q = p["P"] * 1000 * (np.tan(np.arccos(p["pf1"])) - np.tan(np.arccos(p["pf2"])))
    w = 2 * np.pi * p["f"]
    return result(
        {
            "Compensación [kvar]": Q / 1000,
            "C por rama delta [µF]": Q / (3 * w * p["V"] ** 2) * 1e6,
            "C por rama estrella [µF]": Q / (w * p["V"] ** 2) * 1e6,
        },
        note="Banco trifásico equilibrado ideal. P activa y V de línea. No analiza armónicos, resonancia, maniobra ni tensión nominal del capacitor.",
    )


def protection(p):
    factor = 1 if p["system"] == "Monofásico" else np.sqrt(3)
    ib = p["P"] * 1000 / (factor * p["V"] * p["pf"] * p["eta"])
    return result(
        {
            "Corriente de diseño Ib [A]": ib,
            "Condición Ib ≤ In ≤ Iz": "Cumple esta desigualdad"
            if ib <= p["In"] <= p["Iz"]
            else "No cumple esta desigualdad",
        },
        note="Iz debe ser la ampacidad YA corregida por la norma, método, temperatura y agrupamiento del ejercicio. Esta única desigualdad no valida una instalación ni verifica I²t, desconexión, I2 o poder de corte.",
    )


def short_circuit(p):
    z = np.hypot(p["R"], p["X"])
    if z == 0:
        raise ValueError("La impedancia no puede ser nula")
    return result(
        {
            "Corriente de cortocircuito simétrica [A]": p["V"]
            / ((1 if p["system"] == "Monofásico" else np.sqrt(3)) * z),
            "|Z equivalente| [Ω]": z,
        },
        note="Impedancia TOTAL equivalente conocida hasta la falla. En monofásico incluye ida, retorno y fuente; en trifásico es la impedancia por fase. No calcula pico asimétrico ni poder de corte requerido.",
    )


def meter(p):
    error = abs(p["reading"]) * p["pct"] / 100 + p["digits"] * p["resolution"]
    return result(
        {
            "Límite de error ± [unidad de lectura]": error,
            "Lectura mínima": p["reading"] - error,
            "Lectura máxima": p["reading"] + error,
            "u tipo B rectangular": error / np.sqrt(3),
        },
        note="Especificación ±(% de lectura + dígitos). La incertidumbre estándar supone distribución rectangular de ese límite; no es automáticamente la incertidumbre total de la medición.",
    )


def loading(p):
    value = p["v"] * p["rv"] / (p["rs"] + p["rv"])
    return result(
        {"Tensión medida [V]": value, "Error de carga [%]": 100 * (value / p["v"] - 1)},
        note="Fuente de Thévenin, impedancias puramente resistivas; voltímetro conectado en paralelo a la salida.",
    )


def propagation(p):
    product = p["x"] * p["y"]
    variance = (
        (p["y"] * p["ux"]) ** 2
        + (p["x"] * p["uy"]) ** 2
        + 2 * p["x"] * p["y"] * p["rho"] * p["ux"] * p["uy"]
    )
    u = np.sqrt(max(0, variance))
    return result(
        {
            "Producto x·y": product,
            "Incertidumbre estándar u(x·y)": u,
            "Incertidumbre expandida U": p["k"] * u,
        },
        note="Propagación lineal de primer orden; ux, uy son incertidumbres estándar absolutas. ρ es correlación. No sustituye evaluación no lineal para incertidumbres grandes.",
    )


def bridge(p):
    eps = np.linspace(-p["span"], p["span"], 501) * 1e-6
    R = p["R"]
    changed = R * (1 + p["gf"] * eps)
    if np.any(changed <= 0):
        raise ValueError("La deformación genera resistencia no positiva")
    output = p["v"] * (R / (changed + R) - 0.5)
    return result(
        {"Sensibilidad cerca de cero [mV/µε]": -p["v"] * p["gf"] / 4 * 0.001},
        [
            chart(
                "Cuarto de puente",
                "Deformación [µε]",
                "Salida [mV]",
                curve("Vo", eps * 1e6, output * 1000),
            )
        ],
        note="Tres resistencias R iguales y una galga R1=R(1+GF ε). Vo es punto medio izquierdo menos derecho. Sin compensación térmica ni resistencia de cables.",
    )


def sampling(p):
    dense_count = max(2000, int(50 * p["f"] * p["duration"]) + 1)
    if dense_count > 100000 or p["fs"] * p["duration"] > 50000:
        raise ValueError(
            "Reducí la ventana o las frecuencias para resolver la señal sin submuestrear el gráfico"
        )
    t = np.linspace(0, p["duration"], dense_count)
    ts = np.arange(0, p["duration"], 1 / p["fs"])
    if len(ts) > 50000:
        raise ValueError("Demasiadas muestras: reducí duración o muestreo")
    alias = (p["f"] + p["fs"] / 2) % p["fs"] - p["fs"] / 2
    return result(
        {
            "Frecuencia alias aparente [Hz]": abs(alias),
            "Nyquist [Hz]": p["fs"] / 2,
            "Muestreo de fundamental": "Adecuado (fs > 2f)"
            if p["fs"] > 2 * p["f"]
            else "No cumple fs > 2f",
        },
        [
            chart(
                "Muestreo y alias",
                "Tiempo [s]",
                "Tensión [V]",
                curve("Señal original", t, p["A"] * np.sin(2 * np.pi * p["f"] * t)),
                curve("Muestras", ts, p["A"] * np.sin(2 * np.pi * p["f"] * ts)),
                curve("Alias compatible", t, p["A"] * np.sin(2 * np.pi * alias * t)),
            )
        ],
        note="Senoide pura, fase cero y muestreo ideal. Las muestras se muestran como puntos. La coincidencia de muestras no permite identificar la frecuencia original por sí sola.",
    )


TOOLS = [
    Tool(
        "cable",
        "Caída de tensión y sección por caída",
        INSTALL,
        "Laboratorio",
        (
            choice("system", "Sistema", ["Monofásico", "Trifásico"]),
            choice("material", "Conductor", ["Cobre", "Aluminio"]),
            n("V", "Tensión de alimentación [V]", 220, 1, 10000),
            n("I", "Corriente [A]", 20, 0, 10000),
            n("L", "Longitud de ida [m]", 30, 0.01, 10000),
            n("S", "Sección [mm²]", 4, 0.01, 1000),
            n("pf", "cos φ inductivo", 0.9, 0.01, 1),
            n("temp", "Temperatura conductor [°C]", 70, -50, 200),
            n("reactance", "Reactancia por conductor [Ω/km]", 0.08, 0, 10),
            n("limit", "Límite del ejercicio [%]", 3, 0.01, 20),
        ),
        "R(T) y reactancia, longitudes de ida y valores RMS. Datos por defecto editables.",
        "ΔV=k I L (ρ(T) cosφ/S + X sinφ)",
        cable,
    ),
    Tool(
        "compensation",
        "Compensación de factor de potencia",
        INSTALL,
        "Calculadora",
        (
            n("P", "Potencia activa [kW]", 10, 0.001),
            n("pf1", "cos φ inicial", 0.7, 0.01, 1),
            n("pf2", "cos φ objetivo", 0.95, 0.01, 1),
            n("V", "Tensión de línea [V]", 380, 1),
            n("f", "Frecuencia [Hz]", 50, 1),
        ),
        "Banco capacitivo ideal trifásico: estrella y delta.",
        "Qc=P(tanφ1−tanφ2)",
        compensation,
    ),
    Tool(
        "protection",
        "Corriente y coordinación básica",
        INSTALL,
        "Calculadora",
        (
            choice("system", "Sistema", ["Monofásico", "Trifásico"]),
            n("P", "Potencia útil [kW]", 3, 0.001),
            n("V", "Tensión [V]", 220, 1),
            n("pf", "Factor de potencia", 0.9, 0.01, 1),
            n("eta", "Rendimiento", 0.9, 0.01, 1),
            n("In", "Corriente nominal protección [A]", 20, 0.01),
            n("Iz", "Ampacidad corregida dada Iz [A]", 25, 0.01),
        ),
        "Cálculo de Ib y comprobación de una condición necesaria; no es dimensionamiento normativo completo.",
        "Ib=P/(k V cosφ η) · Ib≤In≤Iz",
        protection,
    ),
    Tool(
        "short",
        "Cortocircuito con impedancia dada",
        INSTALL,
        "Calculadora",
        (
            choice("system", "Sistema", ["Monofásico", "Trifásico"]),
            n("V", "Tensión [V]", 220, 1),
            n("R", "R total equivalente [Ω]", 0.1, 0),
            n("X", "X total equivalente [Ω]", 0.05, 0),
        ),
        "Corriente prospectiva simétrica con impedancia del ejercicio conocida.",
        "Icc=V/(k |Z|)",
        short_circuit,
    ),
    Tool(
        "meter",
        "Exactitud del multímetro",
        MEASURE,
        "Calculadora",
        (
            n("reading", "Lectura (misma unidad)", 12, -1e9),
            n("pct", "Exactitud [% de lectura]", 0.5, 0, 100),
            n("digits", "Dígitos", 2, 0, 1000, True),
            n("resolution", "Resolución del rango", 0.01, 1e-9),
        ),
        "Usá resolución y especificación del rango elegido del instrumento.",
        "e=|lectura|·%/100 + dígitos·resolución",
        meter,
    ),
    Tool(
        "loading",
        "Efecto de carga del voltímetro",
        MEASURE,
        "Calculadora",
        (
            n("v", "Tensión en vacío [V]", 10, 0.000001),
            n("rs", "Resistencia de fuente [Ω]", 100000, 0),
            n("rv", "Resistencia de entrada voltímetro [Ω]", 10000000, 0.001),
        ),
        "Comparación de lectura y tensión en vacío.",
        "Vm=Vth Rv/(Rs+Rv)",
        loading,
    ),
    Tool(
        "propagation",
        "Propagación: producto y correlación",
        MEASURE,
        "Calculadora",
        (
            n("x", "Valor x", 10, -1e9),
            n("ux", "Incertidumbre estándar ux", 0.1),
            n("y", "Valor y", 2, -1e9),
            n("uy", "Incertidumbre estándar uy", 0.02),
            n("rho", "Correlación ρ", 0, -1, 1),
            n("k", "Factor de cobertura k", 2, 0.01, 10),
        ),
        "Útil para P=VI y otras magnitudes producto; unidades coherentes.",
        "u²=y²ux²+x²uy²+2xyρuxuy",
        propagation,
    ),
    Tool(
        "bridge",
        "Galga y puente de Wheatstone",
        MEASURE,
        "Laboratorio",
        (
            n("R", "Resistencia nominal [Ω]", 120, 0.001),
            n("gf", "Factor de galga GF", 2, 0.001, 100),
            n("v", "Excitación [V]", 5, 0.001, 100),
            n("span", "Rango ± de deformación [µε]", 2000, 1, 50000),
        ),
        "Modelo de cuarto de puente con una galga activa.",
        "ΔR/R=GF ε · Vo=V(R2/(R1+R2)−R4/(R3+R4))",
        bridge,
    ),
    Tool(
        "sampling",
        "Muestreo: observar el aliasing",
        MEASURE,
        "Laboratorio",
        (
            n("f", "Frecuencia real [Hz]", 70, 0.001, 100000),
            n("fs", "Muestreo [Hz]", 100, 0.001, 100000),
            n("A", "Amplitud pico [V]", 1, 0, 1000),
            n("duration", "Ventana [s]", 0.1, 0.00001, 10),
        ),
        "Contrastá señal, puntos de adquisición y una frecuencia alias compatible.",
        "falias=|((f+fs/2) mod fs)−fs/2|",
        sampling,
    ),
]
