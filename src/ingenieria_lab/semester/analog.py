import numpy as np
from .types import Tool, n, choice, curve, chart, result

SUBJECT = "Electrónica Analógica · preparación"


def rectifier(p):
    A = np.sqrt(2) * p["vrms"]
    cycles = 12
    N = cycles * 2000
    t = np.linspace(0, cycles / p["f"], N + 1)
    source = A * np.sin(2 * np.pi * p["f"] * t)
    full = p["kind"] == "Puente completo"
    drops = 2 if full else 1
    rect = np.maximum((np.abs(source) if full else source) - drops * p["vd"], 0)
    cap = np.zeros_like(t)
    dt = t[1] - t[0]
    tau = p["R"] * p["C"] * 1e-6
    decay = np.exp(-dt / tau)
    for i in range(1, len(t)):
        cap[i] = max(rect[i], cap[i - 1] * decay)
    # Analyze the final two complete periods; discard the initial charging interval.
    start = cycles * 2000 - 4000
    steady = cap[start:]
    mean = float(np.mean(steady))
    return result(
        {
            "Salida media última ventana [V]": mean,
            "Rizado pico a pico última ventana [V]": float(np.ptp(steady)),
            "Corriente media de carga [A]": mean / p["R"],
            "Rizado pequeño aproximado I/(fr C) [V]": mean
            / p["R"]
            / ((2 if full else 1) * p["f"] * p["C"] * 1e-6),
        },
        [
            chart(
                "Rectificación y filtrado",
                "Tiempo [s]",
                "Tensión [V]",
                curve("Entrada", t[start:], source[start:]),
                curve("Rectificada sin C", t[start:], rect[start:]),
                curve("Capacitor y carga", t[start:], steady),
            )
        ],
        note="Modelo de caída de diodo constante y recarga instantánea desde fuente sin impedancia. Descarga exponencial RC entre picos. Se simulan 12 períodos y se muestran los 2 finales; no modela corriente de irrupción, resistencia del transformador ni conducción detallada.",
    )


def bjt(p):
    vth = p["vcc"] * p["r2"] / (p["r1"] + p["r2"])
    rth = p["r1"] * p["r2"] / (p["r1"] + p["r2"])
    ib = max(0, (vth - p["vbe"]) / (rth + (p["beta"] + 1) * p["re"]))
    ic = p["beta"] * ib
    ie = (p["beta"] + 1) * ib
    vce = p["vcc"] - ic * p["rc"] - ie * p["re"]
    ve = ie * p["re"]
    region = (
        "Corte"
        if ib == 0
        else (
            "Activo (modelo aproximado)"
            if vce > p["vbe"]
            else "Fuera de activo: requiere modelo de saturación"
        )
    )
    gm = ic / 0.02585
    metrics = {"V Thévenin [V]": vth, "R Thévenin [Ω]": rth, "Región estimada": region}
    if ib > 0 and vce <= p["vbe"]:
        return result(
            metrics,
            note="La hipótesis Ic=βIb predice saturación. No se presentan Ic ni VCE activos como punto Q válido. Cambiá polarización o contrastá con ngspice.",
        )
    metrics.update(
        {"Ib [µA]": ib * 1e6, "Ic [mA]": ic * 1000, "VCE [V]": vce, "VE [V]": ve}
    )
    if ic > 0:
        metrics.update(
            {
                "gm a 300 K [S]": gm,
                "rπ [Ω]": p["beta"] / gm,
                "Ganancia con RE sin bypass (aprox.)": -gm
                * p["rc"]
                / (1 + gm * p["re"]),
                "Ganancia con RE desacoplada (aprox.)": -gm * p["rc"],
            }
        )
    volt = np.linspace(0, p["vcc"], 200)
    load = (p["vcc"] - volt) / (p["rc"] + (1 + 1 / p["beta"]) * p["re"])
    return result(
        metrics,
        [
            chart(
                "Recta de carga DC",
                "VCE [V]",
                "Ic [mA]",
                curve("Recta de carga aproximada", volt, load * 1000),
                curve("Punto Q", [vce], [ic * 1000]),
            )
        ],
        note="NPN con divisor R1 desde VCC a base, R2 base-tierra, RC colector y RE emisor. VBE y β constantes; sin efecto Early ni carga externa. Ganancias aproximadas de banda media, sin ro; 25.85 mV a 300 K. No modela corte/saturación dinámicos.",
    )


def opamp(p):
    if p["lo"] >= p["hi"]:
        raise ValueError("El límite inferior de salida debe ser menor que el superior")
    gain = -p["rf"] / p["rin"] if p["kind"] == "Inversor" else 1 + p["rf"] / p["rin"]
    t = np.linspace(0, 3 / p["f"], 2000)
    vin = p["offset"] + p["A"] * np.sin(2 * np.pi * p["f"] * t)
    ideal = gain * vin
    out = np.clip(ideal, p["lo"], p["hi"])
    return result(
        {
            "Ganancia ideal": gain,
            "Salida mínima [V]": float(np.min(out)),
            "Salida máxima [V]": float(np.max(out)),
            "Recorte": "Sí" if np.any(ideal != out) else "No",
        },
        [
            chart(
                "Operacional con límites de salida",
                "Tiempo [s]",
                "Tensión [V]",
                curve("Entrada", t, vin),
                curve("Salida", t, out),
            )
        ],
        note="Operacional ideal con recorte estático en límites de salida dados; esos límites no necesariamente coinciden con los rieles. No modela GBW, slew rate, modo común ni corrientes de salida.",
    )


def bode(p):
    tau = p["r"] * p["c"] * 1e-9
    fc = 1 / (2 * np.pi * tau)
    f = np.geomspace(fc / 1000, fc * 1000, 800)
    s = 1j * 2 * np.pi * f * tau
    transfer = 1 / (1 + s) if p["kind"] == "Pasa bajos" else s / (1 + s)
    return result(
        {"Frecuencia de corte [Hz]": fc, "Constante de tiempo [s]": tau},
        [
            chart(
                "Bode: magnitud",
                "log10(f / Hz)",
                "Ganancia [dB]",
                curve("Magnitud", np.log10(f), 20 * np.log10(abs(transfer))),
            ),
            chart(
                "Bode: fase",
                "log10(f / Hz)",
                "Fase [°]",
                curve("Fase", np.log10(f), np.angle(transfer, deg=True)),
            ),
        ],
        note="Filtro RC pasivo sin carga. El eje horizontal representa log10 de la frecuencia en Hz (3 significa 1000 Hz). Ganancia en corte −3.0103 dB.",
    )


def diode(p):
    vt = 8.617333262e-5 * p["temp"]
    v = np.linspace(p["lo"], p["hi"], 500)
    exp = v / (p["ideality"] * vt)
    if np.max(exp) > 100:
        raise ValueError(
            "Rango fuera de la validez práctica del modelo; reducí tensión directa"
        )
    current = p["Is"] * 1e-12 * np.expm1(exp)
    return result(
        {"Tensión térmica VT [mV]": vt * 1000},
        [
            chart(
                "Curva I–V ideal",
                "Tensión diodo [V]",
                "Corriente [mA]",
                curve("Shockley", v, current * 1000),
            )
        ],
        note="Modelo Shockley sin resistencia serie, ruptura inversa ni autocalentamiento; las corrientes altas no representan un dispositivo físico real.",
    )


def zener(p):
    if p["vin"] <= p["vz"]:
        raise ValueError("La entrada debe superar VZ para regulación ideal")
    ir = (p["vin"] - p["vz"]) / p["r"]
    il = p["vz"] / p["load"]
    iz = ir - il
    if iz < p["izmin"] * 0.001:
        raise ValueError(
            "No alcanza la corriente Zener mínima: este diseño no regula según el modelo"
        )
    return result(
        {
            "Corriente Zener [mA]": iz * 1000,
            "Potencia Zener [W]": p["vz"] * iz,
            "Potencia resistencia serie [W]": ir * ir * p["r"],
            "Corriente carga [mA]": il * 1000,
        },
        note="Zener ideal con VZ constante. Evaluar extremos de tensión, carga, tolerancia y temperatura antes de elegir componentes físicos.",
    )


TOOLS = [
    Tool(
        "rectifier",
        "Rectificador y filtro capacitivo",
        SUBJECT,
        "Laboratorio",
        (
            choice("kind", "Topología", ["Puente completo", "Media onda"]),
            n("vrms", "Entrada senoidal RMS [V]", 12, 0.01, 1000),
            n("f", "Frecuencia [Hz]", 50, 1, 100000),
            n("vd", "Caída por diodo [V]", 0.7, 0, 10),
            n("R", "Carga [Ω]", 1000, 0.1, 1e7),
            n("C", "Capacitor [µF]", 470, 0.01, 1e6),
        ),
        "Comparación de entrada, rectificación y descarga RC.",
        "ΔV≈I/(fr C) para rizado pequeño",
        rectifier,
    ),
    Tool(
        "bjt",
        "BJT: polarización y pequeña señal",
        SUBJECT,
        "Laboratorio",
        (
            n("vcc", "VCC [V]", 12, 0.1, 100),
            n("r1", "R1 divisor superior [Ω]", 47000, 1, 1e8),
            n("r2", "R2 divisor inferior [Ω]", 10000, 1, 1e8),
            n("rc", "RC [Ω]", 2200, 1, 1e7),
            n("re", "RE [Ω]", 1000, 1, 1e7),
            n("beta", "β", 100, 1, 1000),
            n("vbe", "VBE aproximado [V]", 0.7, 0.1, 1.5),
        ),
        "Punto Q, recta de carga y estimaciones de banda media.",
        "Ib=(Vth−VBE)/(Rth+(β+1)RE) · Ic=βIb",
        bjt,
    ),
    Tool(
        "opamp",
        "Operacional: ganancia y saturación",
        SUBJECT,
        "Laboratorio",
        (
            choice("kind", "Configuración", ["Inversor", "No inversor"]),
            n("rf", "Rf [Ω]", 10000, 1),
            n("rin", "Rin o Rg [Ω]", 1000, 1),
            n("A", "Entrada amplitud pico [V]", 1.5, 0, 100),
            n("offset", "Offset entrada [V]", 0, -100, 100),
            n("f", "Frecuencia [Hz]", 100, 1, 100000),
            n("lo", "Límite inferior salida [V]", -10, -100, 100),
            n("hi", "Límite superior salida [V]", 10, -100, 100),
        ),
        "Explorá el efecto de ganancia, offset y límites de salida.",
        "Av−=−Rf/Rin · Av+=1+Rf/Rg",
        opamp,
    ),
    Tool(
        "bode",
        "Filtros RC: diagramas de Bode",
        SUBJECT,
        "Laboratorio",
        (
            choice("kind", "Filtro", ["Pasa bajos", "Pasa altos"]),
            n("r", "R [Ω]", 10000, 1, 1e8),
            n("c", "C [nF]", 10, 0.001, 1e8),
        ),
        "Magnitud y fase sobre seis décadas alrededor de fc.",
        "Hpb=1/(1+jωRC) · Hpa=jωRC/(1+jωRC)",
        bode,
    ),
    Tool(
        "diode",
        "Diodo: característica de Shockley",
        SUBJECT,
        "Laboratorio",
        (
            n("Is", "Corriente saturación Is [pA]", 1, 0.0001, 1e9),
            n("ideality", "Factor de idealidad n", 1.5, 0.5, 3),
            n("temp", "Temperatura [K]", 300, 100, 600),
            n("lo", "Tensión inicial [V]", -0.1, -10, 2),
            n("hi", "Tensión final [V]", 0.7, -10, 2),
        ),
        "Dependencia de la curva I–V con temperatura e idealidad.",
        "I=Is(exp(V/(nVT))−1) · VT=kT/q",
        diode,
    ),
    Tool(
        "zener",
        "Regulador Zener con carga",
        SUBJECT,
        "Calculadora",
        (
            n("vin", "Entrada [V]", 12, 0.1, 1000),
            n("vz", "Tensión Zener [V]", 5.1, 0.1, 1000),
            n("r", "Resistencia serie [Ω]", 330, 0.1, 1e8),
            n("load", "Carga [Ω]", 1000, 0.1, 1e8),
            n("izmin", "Corriente mínima Zener [mA]", 1, 0, 1000),
        ),
        "Corrientes y potencias, verificando la condición de regulación ideal.",
        "Iz=(Vin−Vz)/R−Vz/RL",
        zener,
    ),
]
