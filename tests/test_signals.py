"""Pruebas científicas del generador y las mediciones."""

import numpy as np
import pytest
from ingenieria_lab.core.models import SignalConfig
from ingenieria_lab.signals.generator import generate
from ingenieria_lab.signals.measurements import measure
from ingenieria_lab.storage.csv_export import export_csv


def test_sine_rms_full_cycles():
    t, v = generate(SignalConfig(amplitude_v=5, frequency_hz=50, duration_s=0.2))
    assert len(t) == len(v) == 2000
    assert measure(v)["rms_v"] == pytest.approx(5 / np.sqrt(2), rel=1e-12)
    assert measure(v)["mean_v"] == pytest.approx(0, abs=1e-12)


def test_offset_rms():
    _, v = generate(SignalConfig(amplitude_v=4, offset_v=3, duration_s=0.2))
    assert measure(v)["rms_v"] == pytest.approx(np.sqrt(3**2 + 4**2 / 2), rel=1e-12)


def test_phase_and_amplitude():
    _, v = generate(SignalConfig(amplitude_v=2, phase_deg=90))
    assert v[0] == pytest.approx(2)


def test_square_levels():
    _, v = generate(SignalConfig(waveform="square", amplitude_v=3, offset_v=1))
    assert set(np.unique(v)).issubset({-2.0, 4.0})


def test_invalid_nyquist():
    with pytest.raises(ValueError):
        generate(SignalConfig(frequency_hz=100, sample_rate_hz=200))


def test_csv_export(tmp_path):
    t, v = generate(SignalConfig())
    path = tmp_path / "test.csv"
    export_csv(path, t, v)
    loaded = np.loadtxt(path, delimiter=",", skiprows=1)
    assert loaded.shape == (len(t), 2)
    assert loaded[0, 0] == pytest.approx(0)
