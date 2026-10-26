"""Referencias independientes y límites para los nuevos modelos académicos."""

import json
import math
import subprocess
import sys
import numpy as np
import pytest
from ingenieria_lab.semester.registry import TOOLS, BY_KEY, run_tool
from ingenieria_lab.semester.spice import executable


def solve(key, **overrides):
    p = {f.key: f.default for f in BY_KEY[key].inputs}
    p.update(overrides)
    return run_tool(key, p)


@pytest.mark.parametrize("key", [t.key for t in TOOLS])
def test_all_defaults_are_serializable_and_finite(key):
    data = solve(key)
    assert data["metrics"]
    json.dumps(data, allow_nan=False)
    for plot in data["charts"]:
        for c in plot["curves"]:
            assert len(c["x"]) == len(c["y"]) > 0


@pytest.mark.parametrize(
    "support,F,q,a",
    [
        ("Simplemente apoyada", 1000, 0, 1),
        ("Simplemente apoyada", 0, 500, 1),
        ("Voladizo", 1000, 0, 2),
        ("Voladizo", 0, 500, 1),
    ],
)
def test_beam_closed_form_cases(support, F, q, a):
    data = solve("beam", support=support, F=F, q=q, a=a)
    L = 2
    E = 200e9
    I = 0.05 * 0.1**3 / 12
    deflection = np.array(data["charts"][2]["curves"][0]["y"]) / 1000
    if support == "Simplemente apoyada":
        expected = F * L**3 / (48 * E * I) if F else 5 * q * L**4 / (384 * E * I)
        assert deflection[0] == pytest.approx(0, abs=1e-14)
        assert deflection[-1] == pytest.approx(0, abs=1e-14)
        assert data["metrics"]["Reacción izquierda [N]"] + data["metrics"][
            "Reacción derecha [N]"
        ] == pytest.approx(F + q * L)
    else:
        expected = F * L**3 / (3 * E * I) if F else q * L**4 / (8 * E * I)
    assert max(deflection) == pytest.approx(expected, rel=1e-10)


def test_cantilever_force_inside_span_and_force_at_support():
    d = solve("beam", support="Voladizo", F=1000, q=0, a=0.75)
    expected = (
        1000 * 0.75**2 * (3 * 2 - 0.75) / (6 * 200e9 * (0.05 * 0.1**3 / 12)) * 1000
    )
    assert d["metrics"]["|Flecha| máxima muestreada [mm]"] == pytest.approx(expected)
    d = solve("beam", support="Simplemente apoyada", F=1000, q=0, a=0)
    assert d["metrics"]["|Flecha| máxima muestreada [mm]"] == pytest.approx(
        0, abs=1e-10
    )


def test_mohr_uniaxial_and_pure_shear():
    m = solve("mohr", sx=100, sy=0, tau=0)["metrics"]
    assert m["Von Mises [MPa]"] == 100 and m["τ máximo 3D [MPa]"] == 50
    m = solve("mohr", sx=0, sy=0, tau=50)["metrics"]
    assert m["σ1 en plano [MPa]"] == 50 and m["σ2 en plano [MPa]"] == -50
    assert m["Von Mises [MPa]"] == pytest.approx(math.sqrt(3) * 50)


def test_torsion_and_buckling():
    m = solve("torsion", D=40, d=0, T=500)["metrics"]
    assert m["τ máxima [MPa]"] == pytest.approx(16 * 500 / (np.pi * 0.04**3) / 1e6)
    assert solve("buckling")["metrics"]["Carga crítica Euler [N]"] == pytest.approx(
        np.pi**2 * 200e9 * 100e-8 / 9
    )


@pytest.mark.parametrize("method", ["Bisección", "Newton", "Secante"])
def test_roots_known_solution(method):
    d = solve("roots", expr="x^2-2", method=method)
    assert d["metrics"]["Estado"] == "Convergió"
    assert d["metrics"]["Última aproximación x"] == pytest.approx(np.sqrt(2), abs=1e-8)
    assert len(d["rows"]) > 0


def test_nonconvergence_does_not_report_a_root():
    d = solve("roots", iterations=1, tol=1e-12)
    assert d["metrics"]["Estado"] == "NO convergió"
    d = solve("roots", method="Newton", expr="x^2+1", a=0, b=1)
    assert d["metrics"]["Estado"] == "NO convergió"


def test_simpson_cubic_exact_and_errors_reduce():
    m = solve("integration", expr="x^3", a=0, b=1, N=10)["metrics"]
    assert m["Simpson 1/3 compuesto"] == pytest.approx(0.25, abs=1e-14)
    high = solve("integration", expr="x^3", a=0, b=1, N=20)["metrics"]
    assert high["Error absoluto trapecios"] == pytest.approx(
        m["Error absoluto trapecios"] / 4, rel=1e-10
    )


def test_interpolation_and_ode_accuracy():
    m = solve("interpolation")["metrics"]
    assert m["Polinomio en x elegido"] == pytest.approx(2.25)
    m = solve("ode", N=40)["metrics"]
    expected = np.exp(-4)
    assert m["RK4 final"] == pytest.approx(expected, abs=1e-7)
    assert m["Error final RK4"] < m["Error final Euler"] / 1000
    finer = solve("ode", N=80)["metrics"]
    assert finer["Error final Euler"] < m["Error final Euler"]


def test_cable_resistive_and_three_phase_reference():
    m = solve(
        "cable", system="Monofásico", I=20, L=30, S=4, pf=1, temp=20, reactance=0
    )["metrics"]
    assert m["Caída de tensión [V]"] == pytest.approx(2 * 20 * 30 * 0.017241 / 4)
    tri = solve(
        "cable", system="Trifásico", I=20, L=30, S=4, pf=1, temp=20, reactance=0
    )["metrics"]
    assert tri["Caída de tensión [V]"] == pytest.approx(
        m["Caída de tensión [V]"] * np.sqrt(3) / 2
    )
    assert solve("cable", I=0)["metrics"]["Caída de tensión [V]"] == 0


def test_measurement_accuracy_loading_and_correlation():
    m = solve("meter")["metrics"]
    assert m["Límite de error ± [unidad de lectura]"] == pytest.approx(0.08)
    assert m["u tipo B rectangular"] == pytest.approx(0.08 / np.sqrt(3))
    assert solve("loading", rs=1000, rv=1000)["metrics"]["Tensión medida [V]"] == 5
    m = solve("propagation", x=10, y=2, ux=0.1, uy=0.02, rho=1)["metrics"]
    assert m["Incertidumbre estándar u(x·y)"] == pytest.approx(0.4)
    m = solve("propagation", x=10, y=2, ux=0.1, uy=0.02, rho=-1)["metrics"]
    assert m["Incertidumbre estándar u(x·y)"] == pytest.approx(0, abs=1e-8)


def test_sampling_alias_and_bridge_balance():
    d = solve("sampling", f=70, fs=100)
    assert d["metrics"]["Frecuencia alias aparente [Hz]"] == 30
    samples = d["charts"][0]["curves"][1]
    t = np.array(samples["x"])
    np.testing.assert_allclose(samples["y"], np.sin(-2 * np.pi * 30 * t), atol=1e-12)
    d = solve("bridge")
    c = d["charts"][0]["curves"][0]
    assert c["y"][250] == pytest.approx(0)


def test_water_boiling_and_rankine_energy_balance():
    m = solve("fluid", mode="Presión y calidad", P=101.325, quality=0)["metrics"]
    assert m["Temperatura [°C]"] == pytest.approx(100, abs=0.1)
    d = solve("rankine")
    m = d["metrics"]
    assert m["Calor aportado [kJ/kg]"] - m["Calor rechazado [kJ/kg]"] == pytest.approx(
        m["Trabajo neto [kJ/kg]"]
    )
    assert 20 < m["Rendimiento [%]"] < 50
    assert len(d["rows"]) == 4 and 0 < m["Calidad salida turbina"] < 1
    assert d["rows"][0][4] == pytest.approx(d["rows"][1][4])
    assert d["rows"][2][4] == pytest.approx(d["rows"][3][4])


def test_otto_and_polytropic_limits():
    m = solve("otto")["metrics"]
    assert m["Rendimiento [%]"] == pytest.approx(100 * (1 - 8 ** (-0.4)))
    assert m["Trabajo neto [kJ/kg]"] == pytest.approx(
        m["Calor entrante [kJ/kg]"] - m["Calor saliente [kJ/kg]"]
    )
    m = solve("polytropic", n=1)["metrics"]
    assert m["Trabajo del gas [kJ]"] == pytest.approx(100 * np.log(2))
    m = solve("polytropic", n=0)["metrics"]
    assert m["Trabajo del gas [kJ]"] == pytest.approx(100)
    assert solve("balance")["metrics"]["u final [kJ/kg]"] == 235


def test_analog_reference_and_saturation_detection():
    m = solve("bjt")["metrics"]
    ib = m["Ib [µA]"] * 1e-6
    ic = m["Ic [mA]"] * 1e-3
    vb = m["VE [V]"] + 0.7
    assert (12 - vb) / 47000 == pytest.approx(vb / 10000 + ib)
    assert m["VE [V]"] / 1000 == pytest.approx(ic + ib)
    assert m["VCE [V]"] + m["VE [V]"] + ic * 2200 == pytest.approx(12)
    saturated = solve("bjt", rc=100000)["metrics"]
    assert (
        "Ic [mA]" not in saturated and "Fuera de activo" in saturated["Región estimada"]
    )
    m = solve("opamp")["metrics"]
    assert m["Recorte"] == "Sí"
    assert m["Salida máxima [V]"] == 10 and m["Salida mínima [V]"] == -10
    assert solve("bode")["metrics"]["Frecuencia de corte [Hz]"] == pytest.approx(
        1591.5494309
    )


def test_rectifier_filter_and_zener():
    d = solve("rectifier")
    m = d["metrics"]
    assert 14 < m["Salida media última ventana [V]"] < 12 * np.sqrt(2) - 1.4
    more = solve("rectifier", C=940)["metrics"]
    assert (
        more["Rizado pico a pico última ventana [V]"]
        < m["Rizado pico a pico última ventana [V]"]
    )
    assert solve("zener")["metrics"]["Corriente Zener [mA]"] == pytest.approx(
        ((12 - 5.1) / 330 - 5.1 / 1000) * 1000
    )


@pytest.mark.parametrize(
    "key,override",
    [
        ("beam", {"a": 3}),
        ("torsion", {"d": 50}),
        ("roots", {"expr": '__import__("os").system("id")'}),
        ("roots", {"method": "Bisección", "expr": "x^2+1"}),
        ("roots", {"iterations": 2.5}),
        ("integration", {"N": 3}),
        ("interpolation", {"xs": "0 0", "ys": "1 2"}),
        ("interpolation", {"at": 4}),
        ("ode", {"a": 3, "b": 1}),
        ("compensation", {"pf2": 0.2}),
        ("short", {"R": 0, "X": 0}),
        ("rankine", {"high": 5}),
        ("otto", {"T3": 310}),
        ("opamp", {"lo": 10, "hi": -10}),
        ("diode", {"lo": 1, "hi": 0}),
        ("zener", {"load": 1}),
        ("meter", {"reading": float("nan")}),
    ],
)
def test_invalid_inputs_raise(key, override):
    with pytest.raises((ValueError, KeyError)):
        solve(key, **override)


def test_ngspice_missing_is_explicit_and_netlist_still_exportable(monkeypatch):
    monkeypatch.setenv("INGENIERIA_LAB_NGSPICE", "/does/not/exist")
    d = solve("spice_rc")
    assert d["charts"] == [] and "NO ejecutada" in d["metrics"]["Estado"]
    assert ".control" in d["netlist"]


@pytest.mark.skipif(executable() is None, reason="Motor ngspice no instalado")
def test_real_ngspice_against_rc_transfer_and_bjt_kcl():
    d = solve("spice_rc", R=1000, C=1, f=100)
    c = d["charts"][0]["curves"][1]
    amplitude = np.ptp(c["y"]) / 2
    expected = 1 / np.sqrt(1 + (2 * np.pi * 100 * 0.001) ** 2)
    assert amplitude == pytest.approx(expected, rel=0.003)
    m = solve("spice_bjt")["metrics"]
    ic = m["IC [mA]"] / 1000
    ib = m["IB [µA]"] / 1e6
    assert m["VE [V]"] / 1000 == pytest.approx(ic + ib, rel=1e-6)
    assert (12 - m["VC [V]"]) / 2200 == pytest.approx(ic, rel=1e-6)


def test_worker_serialization_protocol():
    request = {
        "key": "meter",
        "params": {f.key: f.default for f in BY_KEY["meter"].inputs},
    }
    completed = subprocess.run(
        [sys.executable, "-m", "ingenieria_lab.semester.worker"],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(completed.stdout)["result"]["metrics"][
        "Límite de error ± [unidad de lectura]"
    ] == pytest.approx(0.08)


def test_sampling_plot_is_resolved_and_extreme_window_rejected():
    d = solve("sampling", f=200, fs=500, duration=0.2)
    t = np.asarray(d["charts"][0]["curves"][0]["x"])
    assert 1 / (t[1] - t[0]) >= 50 * 200
    with pytest.raises(ValueError):
        solve("sampling", f=100000, duration=10)
