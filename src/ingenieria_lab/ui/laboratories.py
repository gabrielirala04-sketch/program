import csv
import json
import subprocess
import sys
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTabWidget,
    QFileDialog,
    QSplitter,
    QScrollArea,
)
from ingenieria_lab.ui.common import label, button, spin, heading, plot_widget, error
from ingenieria_lab.core.mathematics import matrix_analysis, statistics
from ingenieria_lab.core.engineering import (
    CALCULATORS,
    UNITS,
    solve_calculator,
    convert,
)
from ingenieria_lab.core.simulations import MODELS, simulate
from ingenieria_lab.core.models import SignalConfig
from ingenieria_lab.signals.generator import generate
from ingenieria_lab.signals.measurements import measure
from ingenieria_lab.storage.csv_export import export_csv


class MathJob(QThread):
    result = Signal(dict)

    def __init__(self, request, parent):
        super().__init__(parent)
        self.request = request

    def run(self):
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "ingenieria_lab.core.math_worker"],
                input=json.dumps(self.request),
                capture_output=True,
                text=True,
                timeout=8,
            )
            if proc.returncode:
                raise ValueError("No se pudo completar el cálculo matemático")
            result = json.loads(proc.stdout)
        except subprocess.TimeoutExpired:
            result = {
                "error": "El cálculo superó 8 segundos. Simplificá la expresión o usá integración numérica."
            }
        except Exception as exc:
            result = {"error": str(exc)}
        self.result.emit(result)


class MathPage(QWidget):
    def __init__(self):
        super().__init__()
        self.job = None
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Calculadora matemática",
            "Cálculo simbólico y numérico · álgebra lineal · estadística",
        )
        tabs = QTabWidget()
        layout.addWidget(tabs)
        calc = QWidget()
        body = QVBoxLayout(calc)
        self.expr = QLineEdit("sin(x) + x^2")
        self.expr.setAccessibleName("Expresión matemática")
        body.addWidget(label("f(x) — multiplicación explícita con * y punto decimal"))
        body.addWidget(self.expr)
        body.addWidget(
            label(
                "Funciones: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, log, sqrt, abs. Constantes: pi, e, I. Ángulos en radianes.",
                "muted",
            )
        )
        row = QHBoxLayout()
        self.operation = QComboBox()
        self.operation.addItems(
            [
                "Evaluar en x = a",
                "Derivada",
                "Primitiva",
                "Integral numérica [a, b]",
                "Raíz en [a, b]",
                "Graficar",
            ]
        )
        self.a = spin(-3)
        self.b = spin(3)
        row.addWidget(self.operation, 2)
        row.addWidget(label("a"))
        row.addWidget(self.a)
        row.addWidget(label("b"))
        row.addWidget(self.b)
        body.addLayout(row)
        self.run_button = button("Calcular", self.run, True)
        body.addWidget(self.run_button)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(150)
        self.output.setPlaceholderText(
            "El resultado aparecerá aquí. Podés seleccionarlo y copiarlo a tus apuntes."
        )
        body.addWidget(self.output)
        self.plot = plot_widget("f(x)", "x", None)
        body.addWidget(self.plot, 1)
        body.addWidget(
            label(
                "Raíces: función continua y cambio de signo en [a,b]. Los gráficos requieren valores reales y finitos en todo el intervalo.",
                "muted",
            )
        )
        tabs.addTab(calc, "Funciones")
        matrix = QWidget()
        ml = QVBoxLayout(matrix)
        ml.addWidget(label("Resolver Ax = b", "section"))
        ml.addWidget(
            label(
                "Matriz cuadrada de hasta 8 × 8. Separá columnas con espacios y filas con Enter."
            )
        )
        self.matrix = QPlainTextEdit("2 1\n1 3")
        self.vector = QLineEdit("5 7")
        ml.addWidget(self.matrix)
        ml.addWidget(label("Vector b"))
        ml.addWidget(self.vector)
        ml.addWidget(button("Resolver sistema y analizar A", self.solve_matrix, True))
        self.matrix_output = QPlainTextEdit()
        self.matrix_output.setReadOnly(True)
        ml.addWidget(self.matrix_output)
        tabs.addTab(matrix, "Matrices")
        stats = QWidget()
        sl = QVBoxLayout(stats)
        sl.addWidget(label("Mediciones o datos experimentales", "section"))
        sl.addWidget(
            label(
                "Valores separados por espacios o comas; usá punto decimal. Desvío y varianza muestrales (n−1)."
            )
        )
        self.data = QPlainTextEdit("10.2 10.1 10.4 10.3 10.0")
        sl.addWidget(self.data)
        sl.addWidget(button("Analizar datos", self.solve_stats, True))
        self.stats_output = QPlainTextEdit()
        self.stats_output.setReadOnly(True)
        sl.addWidget(self.stats_output)
        tabs.addTab(stats, "Estadística")

    def run(self):
        self.run_button.setEnabled(False)
        self.output.setPlainText("Calculando…")
        self.job = MathJob(
            {
                "text": self.expr.text(),
                "operation": self.operation.currentText(),
                "a": self.a.value(),
                "b": self.b.value(),
            },
            self,
        )
        self.job.result.connect(self.complete)
        self.job.finished.connect(lambda: self.run_button.setEnabled(True))
        self.job.start()

    def complete(self, data):
        if "error" in data:
            self.output.setPlainText(data["error"])
            return
        result = data["result"]
        if "x" in result:
            self.plot.clear()
            self.plot.plot(result["x"], result["y"], pen=pg.mkPen("#117d75", width=2))
            self.output.setPlainText(
                "Gráfico calculado en el intervalo indicado. Rueda: zoom; arrastrar: desplazar; clic derecho: opciones."
            )
        else:
            self.output.setPlainText(result["text"])

    def solve_matrix(self):
        try:
            self.matrix_output.setPlainText(
                matrix_analysis(self.matrix.toPlainText(), self.vector.text())
            )
        except (ValueError, np.linalg.LinAlgError) as exc:
            self.matrix_output.setPlainText(str(exc))

    def solve_stats(self):
        try:
            self.stats_output.setPlainText(statistics(self.data.toPlainText()))
        except ValueError as exc:
            self.stats_output.setPlainText(str(exc))


class ToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Herramientas de ingeniería",
            "16 calculadoras con unidades, fórmulas y condiciones de aplicación",
        )
        tabs = QTabWidget()
        layout.addWidget(tabs)
        calc = QWidget()
        cl = QVBoxLayout(calc)
        self.choice = QComboBox()
        self.choice.addItems([c.name for c in CALCULATORS])
        cl.addWidget(self.choice)
        self.formula = label("", "section")
        cl.addWidget(self.formula)
        self.assumption = label("", "muted")
        cl.addWidget(self.assumption)
        self.form = QFormLayout()
        cl.addLayout(self.form)
        cl.addWidget(button("Calcular resultado", self.run, True))
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        cl.addWidget(self.output, 1)
        tabs.addTab(calc, "Calculadoras")
        converter = QWidget()
        ul = QVBoxLayout(converter)
        ul.addWidget(label("Conversor de unidades", "section"))
        form = QFormLayout()
        ul.addLayout(form)
        self.dimension = QComboBox()
        self.dimension.addItems(UNITS)
        self.value = spin(1, decimals=9)
        self.source = QComboBox()
        self.target = QComboBox()
        form.addRow("Magnitud", self.dimension)
        form.addRow("Valor", self.value)
        form.addRow("Desde", self.source)
        form.addRow("Hacia", self.target)
        ul.addWidget(button("Convertir", self.convert, True))
        self.converted = label("", "metric")
        ul.addWidget(self.converted)
        ul.addStretch()
        tabs.addTab(converter, "Unidades")
        self.dimension.currentTextChanged.connect(self.update_units)
        self.choice.currentIndexChanged.connect(self.update_form)
        self.update_form()
        self.update_units()

    def update_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        calc = CALCULATORS[self.choice.currentIndex()]
        self.formula.setText(calc.formula)
        self.assumption.setText(calc.assumption)
        self.fields = {}
        for spec in calc.fields:
            widget = spin(spec.default, spec.minimum, spec.maximum)
            if spec.key in ("bits", "p"):
                widget.setDecimals(0)
            self.fields[spec.key] = widget
            self.form.addRow(spec.label, widget)
        self.run()

    def run(self):
        try:
            result = solve_calculator(
                self.choice.currentIndex(),
                {k: w.value() for k, w in self.fields.items()},
            )
            self.output.setPlainText(
                "\n\n".join(f"{key}  =  {value:.10g}" for key, value in result.items())
            )
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            self.output.setPlainText(str(exc))

    def update_units(self):
        self.source.clear()
        self.target.clear()
        self.source.addItems(UNITS[self.dimension.currentText()])
        self.target.addItems(UNITS[self.dimension.currentText()])
        self.target.setCurrentIndex(1)
        self.convert()

    def convert(self):
        try:
            result = convert(
                self.value.value(),
                self.dimension.currentText(),
                self.source.currentText(),
                self.target.currentText(),
            )
            self.converted.setText(f"{result:.10g} {self.target.currentText()}")
        except ValueError as exc:
            self.converted.setText(str(exc))


class SimulationsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Simuladores",
            "Explorá cómo cambian las respuestas al modificar los parámetros",
        )
        split = QSplitter()
        layout.addWidget(split, 1)
        controls = QWidget()
        cl = QVBoxLayout(controls)
        self.choice = QComboBox()
        self.choice.addItems([m.name for m in MODELS])
        cl.addWidget(self.choice)
        self.description = label("")
        cl.addWidget(self.description)
        self.form = QFormLayout()
        cl.addLayout(self.form)
        cl.addWidget(button("Simular", self.run, True))
        cl.addWidget(button("Exportar curvas CSV", self.save))
        self.summary = label("")
        cl.addWidget(self.summary)
        cl.addStretch()
        cl.addWidget(
            label(
                "Modelos educativos ideales. Revisá sus hipótesis antes de interpretar resultados.",
                "muted",
            )
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setMinimumWidth(300)
        split.addWidget(scroll)
        right = QWidget()
        rl = QVBoxLayout(right)
        self.plot = plot_widget()
        self.plot.addLegend()
        rl.addWidget(self.plot, 1)
        rl.addWidget(
            label(
                "Zoom con la rueda · desplazá con el mouse · cada curva indica su unidad",
                "muted",
            )
        )
        split.addWidget(right)
        split.setSizes([320, 700])
        self.data = None
        self.choice.currentIndexChanged.connect(self.update_form)
        self.update_form()

    def update_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        model = MODELS[self.choice.currentIndex()]
        self.description.setText(model.description)
        self.fields = {}
        for f in model.fields:
            widget = spin(f.default, f.minimum, f.maximum)
            self.form.addRow(f.label, widget)
            self.fields[f.key] = widget
        self.run()

    def run(self):
        try:
            t, curves, unit, metrics = simulate(
                self.choice.currentIndex(),
                {key: w.value() for key, w in self.fields.items()},
            )
            self.data = t, curves
            self.plot.clear()
            self.plot.setLabel("left", unit)
            for (name, values), color in zip(curves.items(), ("#128b80", "#db8550")):
                self.plot.plot(t, values, name=name, pen=pg.mkPen(color, width=2))
            self.summary.setText(
                "\n\n".join(f"{key}: {value:.7g}" for key, value in metrics.items())
            )
        except (ValueError, OverflowError) as exc:
            self.data = None
            self.plot.clear()
            self.summary.setText(str(exc))

    def save(self):
        if self.data is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar última simulación", "simulacion.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            t, curves = self.data
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["tiempo_s", *curves])
                writer.writerows(zip(t, *curves.values()))
        except OSError as exc:
            error(self, exc)


class SignalsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Laboratorio de señales",
            "Generador ideal · osciloscopio · espectro de amplitud",
        )
        split = QSplitter()
        layout.addWidget(split, 1)
        controls = QWidget()
        cl = QVBoxLayout(controls)
        self.wave = QComboBox()
        for name, value in [
            ("Senoidal", "sine"),
            ("Cuadrada", "square"),
            ("Triangular", "triangle"),
            ("Diente de sierra", "sawtooth"),
        ]:
            self.wave.addItem(name, value)
        form = QFormLayout()
        form.addRow("Forma de onda", self.wave)
        self.fields = {}
        for key, title, lo, hi, initial, dec in [
            ("amplitude_v", "Amplitud pico [V]", 0, 1000, 5, 3),
            ("frequency_hz", "Frecuencia [Hz]", 0.01, 100000, 50, 2),
            ("phase_deg", "Fase [°]", -360, 360, 0, 2),
            ("offset_v", "Offset [V]", -1000, 1000, 0, 3),
            ("duration_s", "Duración [s]", 0.001, 30, 0.1, 3),
            ("sample_rate_hz", "Muestreo [Hz]", 1, 1000000, 10000, 0),
        ]:
            w = spin(initial, lo, hi, dec)
            self.fields[key] = w
            form.addRow(title, w)
        cl.addLayout(form)
        cl.addWidget(button("Generar señal", self.refresh, True))
        cl.addWidget(button("Exportar muestras CSV", self.save))
        self.results = label("")
        cl.addWidget(self.results)
        cl.addWidget(
            label(
                "Espectro FFT unilateral, ventana rectangular. La fuga espectral depende de la ventana temporal. Para ondas no senoidales, aumentá mucho el muestreo respecto de la fundamental.",
                "muted",
            )
        )
        cl.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setMinimumWidth(300)
        split.addWidget(scroll)
        tabs = QTabWidget()
        self.plot = plot_widget("Tensión [V]")
        self.spectrum = plot_widget("Amplitud pico [V]", "Frecuencia", "Hz")
        tabs.addTab(self.plot, "Osciloscopio")
        tabs.addTab(self.spectrum, "Espectro FFT")
        split.addWidget(tabs)
        split.setSizes([320, 700])
        self.t = self.v = None
        self.refresh()

    def refresh(self):
        try:
            config = SignalConfig(
                waveform=self.wave.currentData(),
                **{key: w.value() for key, w in self.fields.items()},
            )
            t, v = generate(config)
            stats = measure(v)
            self.t, self.v = t, v
            self.plot.clear()
            curve = self.plot.plot(t, v, pen=pg.mkPen("#128b80", width=2))
            curve.setDownsampling(auto=True, method="peak")
            freq = np.fft.rfftfreq(len(v), d=1 / config.sample_rate_hz)
            magnitude = np.abs(np.fft.rfft(v)) / len(v)
            magnitude[
                1 : len(magnitude) - 1 if len(v) % 2 == 0 else len(magnitude)
            ] *= 2
            self.spectrum.clear()
            self.spectrum.plot(freq, magnitude, pen=pg.mkPen("#6c65bf", width=2))
            self.spectrum.setXRange(
                0, min(config.sample_rate_hz / 2, 10 * config.frequency_hz)
            )
            self.results.setText(
                f"RMS: {stats['rms_v']:.6g} V\n\nMedia: {stats['mean_v']:.6g} V\n\nPico a pico: {stats['peak_to_peak_v']:.6g} V\n\nMín: {stats['min_v']:.6g} V · Máx: {stats['max_v']:.6g} V\n\n{len(t):,} muestras"
            )
        except (ValueError, MemoryError) as exc:
            self.t = self.v = None
            self.plot.clear()
            self.spectrum.clear()
            self.results.setText(str(exc))

    def save(self):
        if self.t is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar señal", "senal.csv", "CSV (*.csv)"
        )
        if path:
            try:
                export_csv(path, self.t, self.v)
            except OSError as exc:
                error(self, exc)
