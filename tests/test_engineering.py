import math
import numpy as np
import pytest
from ingenieria_lab.core.engineering import CALCULATORS, solve_calculator, convert
from ingenieria_lab.core.simulations import MODELS, simulate


def solve(name, **overrides):
    index = next(i for i, c in enumerate(CALCULATORS) if c.name == name)
    values = {f.key: f.default for f in CALCULATORS[index].fields}
    values.update(overrides)
    return solve_calculator(index, values)


@pytest.mark.parametrize("index", range(len(CALCULATORS)))
def test_all_calculator_defaults_finite(index):
    values = {f.key: f.default for f in CALCULATORS[index].fields}
    assert all(math.isfinite(v) for v in solve_calculator(index, values).values())


def test_ohm_divider_and_three_phase_reference():
    assert solve("Ley de Ohm y potencia", v=12, r=1000)[
        "Corriente [A]"
    ] == pytest.approx(0.012)
    assert solve("Divisor de tensión", v=12, r1=10000, r2=2000)[
        "Salida [V]"
    ] == pytest.approx(2)
    result = solve("Potencia trifásica", v=400, i=10, pf=0.8)
    assert result["Activa [W]"] == pytest.approx(math.sqrt(3) * 400 * 10 * 0.8)
    assert result["Aparente [VA]"] ** 2 == pytest.approx(
        result["Activa [W]"] ** 2 + result["Reactiva |Q| [var]"] ** 2
    )


def test_mechanical_units_reference():
    result = solve("Esfuerzo axial")
    assert result["Tensión [MPa]"] == pytest.approx(100)
    assert result["Alargamiento [mm]"] == pytest.approx(0.5)
    assert solve("Viga simplemente apoyada")["Flecha máxima [mm]"] == pytest.approx(
        0.8333333333
    )
    assert solve("Potencia de bomba")["En el eje [W]"] == pytest.approx(2615.1066666667)


@pytest.mark.parametrize(
    "name,values",
    [
        ("Ley de Ohm y potencia", {"r": 0}),
        ("Motor: velocidad y deslizamiento", {"p": 3}),
        ("ADC ideal", {"bits": 12.5}),
        ("ADC ideal", {"v": 4}),
        ("Rendimiento de Carnot", {"cold": 800}),
        ("Sensor de 4–20 mA", {"hi": -1}),
        ("Potencia de bomba", {"eff": 101}),
        ("Filtro RC", {"c": float("nan")}),
    ],
)
def test_reject_nonphysical_inputs(name, values):
    with pytest.raises(ValueError):
        solve(name, **values)


def test_adc_and_sensor_endpoints():
    assert solve("ADC ideal", v=3.3)["Código"] == 4095
    assert solve("ADC ideal", v=0)["Código"] == 0
    assert solve("Sensor de 4–20 mA", i=4)["Valor en unidades de escala"] == 0
    assert solve("Sensor de 4–20 mA", i=20)["Valor en unidades de escala"] == 100


@pytest.mark.parametrize(
    "value,dimension,source,target,expected",
    [
        (0, "Temperatura", "°C", "K", 273.15),
        (32, "Temperatura", "°F", "°C", 0),
        (100, "Temperatura", "°C", "°F", 212),
        (1, "Energía", "kWh", "J", 3600000),
        (60, "Frecuencia", "rpm", "Hz", 1),
        (1, "Caudal", "L/s", "m³/h", 3.6),
        (1, "Capacitancia", "µF", "nF", 1000),
        (1, "Área", "cm²", "mm²", 100),
    ],
)
def test_unit_conversion(value, dimension, source, target, expected):
    assert convert(value, dimension, source, target) == pytest.approx(
        expected, abs=1e-10
    )


def test_below_absolute_zero():
    with pytest.raises(ValueError):
        convert(-274, "Temperatura", "°C", "K")


def model(index, **overrides):
    params = {f.key: f.default for f in MODELS[index].fields}
    params.update(overrides)
    return simulate(index, params)


def test_rc_charges_to_source():
    t, curves, _, metrics = model(0)
    y = curves["Vc [V]"]
    assert y[0] == 0
    assert y[-1] == pytest.approx(5 * (1 - math.exp(-6)))
    assert metrics["τ [s]"] == pytest.approx(0.1)
    assert np.all(np.diff(y) >= 0)


def test_rlc_at_resonance_has_unity_power_factor():
    f = 1 / (2 * np.pi * np.sqrt(0.1 * 10e-6))
    _, _, _, metrics = model(2, f=f)
    assert metrics["|Z| [Ω]"] == pytest.approx(100)
    assert metrics["Q [var]"] == pytest.approx(0, abs=1e-12)
    assert metrics["I RMS [A]"] == pytest.approx(0.12)


def test_undamped_mechanical_matches_analytic():
    t, curves, _, _ = model(3, b=0)
    np.testing.assert_allclose(curves["Posición [m]"], 0.1 * np.cos(10 * t), atol=1e-11)


@pytest.mark.parametrize("index", [1, 4])
def test_stable_step_reaches_final_value(index):
    _, curves, _, metrics = model(index)
    y = next(iter(curves.values()))
    assert y[0] == pytest.approx(0, abs=1e-12)
    assert y[-1] == pytest.approx(metrics["Valor final ideal"], rel=0.003)
