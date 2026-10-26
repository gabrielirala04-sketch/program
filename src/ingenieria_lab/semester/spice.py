"""Ngspice opcional, con netlists propios y sin cargar archivos de inicio externos."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import numpy as np
from .types import Tool, n, curve, chart, result

SUBJECT = "Electrónica Analógica · preparación"


def executable():
    configured = os.environ.get("INGENIERIA_LAB_NGSPICE")
    if configured:
        p = Path(configured)
        return str(p) if p.is_file() and os.access(p, os.X_OK) else None
    return shutil.which("ngspice")


def run(netlist, files):
    binary = executable()
    if not binary:
        return None
    with tempfile.TemporaryDirectory(prefix="ingenieria-spice-") as directory:
        root = Path(directory)
        (root / "circuito.cir").write_text(netlist, encoding="ascii")
        try:
            completed = subprocess.run(
                [binary, "-n", "-b", "circuito.cir"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Ngspice superó 10 segundos") from exc
        if completed.returncode != 0 or any(not (root / f).is_file() for f in files):
            raise ValueError(
                "Ngspice no completó el circuito: "
                + (completed.stderr + completed.stdout)[-1600:]
            )
        values = [np.atleast_2d(np.loadtxt(root / f, skiprows=1)) for f in files]
        if any(not np.all(np.isfinite(a)) for a in values):
            raise ValueError("Ngspice produjo datos no finitos")
        return values


def absent(netlist):
    data = result(
        {"Estado": "Ngspice no instalado: simulación NO ejecutada"},
        note="En Linux Mint: sudo apt install ngspice. También podés exportar este netlist y abrirlo con ngspice. No hay resultados simulados hasta instalar el motor.",
    )
    data["netlist"] = netlist
    return data


def rc(p):
    period = 1 / p["f"]
    netlist = f"""RC low-pass - Ingenieria Lab
.options reltol=1e-8 abstol=1e-12 vntol=1e-9
Vin in 0 SIN(0 {p["A"]:.12g} {p["f"]:.12g})
R1 in out {p["R"]:.12g}
C1 out 0 {p["C"] * 1e-6:.12g}
.control
set wr_singlescale
set wr_vecnames
tran {period / 300:.12g} {8 * period:.12g}
wrdata transient.txt v(in) v(out)
quit
.endc
.end
"""
    data = run(netlist, ["transient.txt"])
    if data is None:
        return absent(netlist)
    values = data[0]
    t = values[:, 0]
    mask = t >= 6 * period
    output = result(
        {
            "Motor": "ngspice",
            "Corte analítico [Hz]": 1 / (2 * np.pi * p["R"] * p["C"] * 1e-6),
        },
        [
            chart(
                "RC transitorio SPICE",
                "Tiempo [s]",
                "Tensión [V]",
                curve("Entrada", t[mask], values[mask, 1]),
                curve("Salida ngspice", t[mask], values[mask, 2]),
            )
        ],
        note="Netlist original exportable; fuente y componentes ideales. Se muestran los dos últimos períodos de ocho simulados. Para RC muy lento puede no alcanzarse aún régimen permanente.",
    )
    output["netlist"] = netlist
    return output


def common_emitter(p):
    netlist = f"""BJT common emitter - Ingenieria Lab
.options reltol=1e-8 abstol=1e-12 vntol=1e-9
VCC supply 0 {p["vcc"]:.12g}
VS src 0 DC 0 AC 1
RS src input 600
CIN input base 10u
R1 supply base {p["r1"]:.12g}
R2 base 0 {p["r2"]:.12g}
RC supply collector {p["rc"]:.12g}
RE emitter 0 {p["re"]:.12g}
CE emitter 0 100u
Q1 collector base emitter NPNLAB
COUT collector out 10u
RL out 0 10k
.model NPNLAB NPN(IS=1e-14 BF={p["beta"]:.12g} VAF=100 CJE=10p CJC=4p TF=0.3n)
.control
set wr_singlescale
set wr_vecnames
op
wrdata operating.txt v(base) v(emitter) v(collector) @q1[ic] @q1[ib]
ac dec 60 1 1Meg
let gain_real = real(v(out))
let gain_imag = imag(v(out))
wrdata ac.txt gain_real gain_imag
quit
.endc
.end
"""
    data = run(netlist, ["operating.txt", "ac.txt"])
    if data is None:
        return absent(netlist)
    op, ac = data
    vb, ve, vc, ic, ib = op[0, 1:6]
    h = ac[:, 1] + 1j * ac[:, 2]
    output = result(
        {
            "Motor": "ngspice",
            "VB [V]": vb,
            "VE [V]": ve,
            "VC [V]": vc,
            "VCE [V]": vc - ve,
            "IC [mA]": ic * 1000,
            "IB [µA]": ib * 1e6,
            "Estado de unión BC": "Polarización inversa"
            if vc > vb
            else "No inversa: revisar saturación",
        },
        [
            chart(
                "BJT AC: magnitud",
                "log10(f / Hz)",
                "Ganancia [dB]",
                curve(
                    "Vo/Vs",
                    np.log10(ac[:, 0]),
                    20 * np.log10(np.maximum(abs(h), 1e-300)),
                ),
            ),
            chart(
                "BJT AC: fase",
                "log10(f / Hz)",
                "Fase [°]",
                curve("Fase", np.log10(ac[:, 0]), np.unwrap(np.angle(h)) * 180 / np.pi),
            ),
        ],
        note="Modelo NPN genérico, no un transistor comercial particular. RS=600 Ω, carga=10 kΩ, acoples=10 µF y bypass emisor=100 µF. AC es pequeña señal alrededor del punto DC, no una prueba de amplitud o recorte. Para dispositivos reales usá sus modelos de fabricante en una herramienta SPICE completa.",
    )
    output["netlist"] = netlist
    return output


TOOLS = [
    Tool(
        "spice_rc",
        "Ngspice: filtro RC transitorio",
        SUBJECT,
        "Laboratorio",
        (
            n("R", "R [Ω]", 1000, 1, 1e7),
            n("C", "C [µF]", 1, 0.001, 1e5),
            n("A", "Amplitud fuente [V]", 1, 0.001, 100),
            n("f", "Frecuencia fuente [Hz]", 100, 1, 1e6),
        ),
        "Motor SPICE real, ejecución local y netlist exportable. Instalar ngspice en Mint.",
        "R y C resueltos por ngspice, no una gráfica precalculada",
        rc,
    ),
    Tool(
        "spice_bjt",
        "Ngspice: emisor común DC y AC",
        SUBJECT,
        "Laboratorio",
        (
            n("vcc", "VCC [V]", 12, 1, 100),
            n("r1", "R1 [Ω]", 47000, 1, 1e8),
            n("r2", "R2 [Ω]", 10000, 1, 1e8),
            n("rc", "RC [Ω]", 2200, 1, 1e7),
            n("re", "RE [Ω]", 1000, 1, 1e7),
            n("beta", "BF del modelo", 100, 1, 1000),
        ),
        "Punto de operación y respuesta en frecuencia con un NPN genérico y capacitores de acoplamiento.",
        "Análisis .op y .ac de ngspice",
        common_emitter,
    ),
]
