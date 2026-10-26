"""Laboratorios dirigidos al semestre, resultados trazables y notas reutilizables."""

import csv
from datetime import datetime
from itertools import zip_longest
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
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
    QTextBrowser,
    QSplitter,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QAbstractItemView,
)
from ingenieria_lab.semester.registry import TOOLS, BY_KEY, SUBJECTS
from ingenieria_lab.ui.common import label, button, spin, heading, plot_widget, error


class SemesterJob(QThread):
    result = Signal(dict)

    def __init__(self, key, params, parent):
        super().__init__(parent)
        self.key = key
        self.params = params

    def run(self):
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "ingenieria_lab.semester.worker"],
                input=json.dumps({"key": self.key, "params": self.params}),
                capture_output=True,
                text=True,
                timeout=20,
            )
            if completed.returncode:
                raise ValueError(
                    "El motor no pudo completar la operación: "
                    + completed.stderr[-600:]
                )
            payload = json.loads(completed.stdout)
        except subprocess.TimeoutExpired:
            payload = {
                "error": "Se superaron 20 segundos. Simplificá la expresión o reducí el tamaño del cálculo."
            }
        except Exception as exc:
            payload = {"error": str(exc)}
        self.result.emit(payload)


class SemesterPage(QWidget):
    changed = Signal()

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.job = None
        self.data = None
        self.fields = {}
        self.snapshot = {}
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Mi semestre",
            "3.er año · 2.º semestre · preparación para Electrónica Analógica",
        )
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)
        workspace = QWidget()
        wl = QVBoxLayout(workspace)
        split = QSplitter()
        wl.addWidget(split, 1)
        controls = QWidget()
        cl = QVBoxLayout(controls)
        self.subject = QComboBox()
        self.subject.setMinimumContentsLength(12)
        self.subject.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.subject.addItems(SUBJECTS)
        cl.addWidget(label("Materia"))
        cl.addWidget(self.subject)
        self.kind = QComboBox()
        self.kind.setMinimumContentsLength(12)
        self.kind.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.kind.addItems(["Todas las herramientas", "Laboratorio", "Calculadora"])
        cl.addWidget(self.kind)
        self.selection = QComboBox()
        self.selection.setMinimumContentsLength(20)
        self.selection.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        cl.addWidget(self.selection)
        self.description = label("")
        self.formula = label("", "muted")
        cl.addWidget(self.description)
        cl.addWidget(self.formula)
        self.form = QFormLayout()
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        cl.addLayout(self.form)
        self.compute = button("Resolver / simular", self.run, True)
        cl.addStretch()
        self.controls = controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setMinimumWidth(260)
        split.addWidget(scroll)
        right = QWidget()
        rl = QVBoxLayout(right)
        self.feedback = label("Elegí una herramienta e ingresá los datos.", "muted")
        action_header = QHBoxLayout()
        action_header.addWidget(self.feedback, 1)
        action_header.addWidget(self.compute)
        rl.addLayout(action_header)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(140)
        rl.addWidget(self.output)
        self.results = QTabWidget()
        rl.addWidget(self.results, 1)
        self.assumptions = QPlainTextEdit()
        self.assumptions.setReadOnly(True)
        self.assumptions.setFixedHeight(72)
        self.assumptions.setAccessibleName("Hipótesis y límites del modelo")
        rl.addWidget(self.assumptions)
        actions = QHBoxLayout()
        self.export_button = button("Exportar CSV", self.export_csv)
        self.note_button = button("Guardar en apuntes", self.save_note)
        self.netlist_button = button("Exportar netlist", self.export_netlist)
        for w in (self.export_button, self.note_button, self.netlist_button):
            actions.addWidget(w)
            w.setEnabled(False)
        rl.addLayout(actions)
        split.addWidget(right)
        split.setSizes([320, 700])
        tabs.addTab(workspace, "Laboratorios y cálculos")
        guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setHtml(GUIDE)
        tabs.addTab(guide, "Ruta de estudio y fuentes")
        self.subject.currentTextChanged.connect(self.filter_tools)
        self.kind.currentTextChanged.connect(self.filter_tools)
        self.selection.currentIndexChanged.connect(self.update_form)
        self.filter_tools()

    def filter_tools(self):
        self.selection.blockSignals(True)
        self.selection.clear()
        for tool in TOOLS:
            if tool.subject == self.subject.currentText() and (
                self.kind.currentIndex() == 0 or tool.kind == self.kind.currentText()
            ):
                self.selection.addItem(tool.name, tool.key)
        self.selection.blockSignals(False)
        self.update_form()

    def invalidate(self):
        self.data = None
        self.output.clear()
        self.assumptions.clear()
        while self.results.count():
            widget = self.results.widget(0)
            self.results.removeTab(0)
            widget.deleteLater()
        for w in (self.export_button, self.note_button, self.netlist_button):
            w.setEnabled(False)
        self.feedback.setText("Resultados pendientes. Presioná Resolver / simular.")

    def update_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.fields = {}
        self.invalidate()
        key = self.selection.currentData()
        self.compute.setEnabled(bool(key))
        if not key:
            self.description.setText("No hay herramientas de este tipo en la materia.")
            self.formula.clear()
            return
        tool = BY_KEY[key]
        self.description.setText(tool.description)
        self.formula.setText(tool.formula)
        for f in tool.inputs:
            if f.options:
                w = QComboBox()
                w.addItems(f.options)
                w.currentTextChanged.connect(self.invalidate)
            elif isinstance(f.default, str):
                w = QLineEdit(f.default)
                w.setMaxLength(600)
                w.textChanged.connect(self.invalidate)
            else:
                w = spin(f.default, f.minimum, f.maximum, 0 if f.integer else 12)
                w.setMinimumWidth(100)
                w.valueChanged.connect(self.invalidate)
            w.setAccessibleName(f.label)
            self.form.addRow(label(f.label), w)
            self.fields[f.key] = w

    def parameters(self):
        return {
            key: (
                w.currentText()
                if isinstance(w, QComboBox)
                else w.text()
                if isinstance(w, QLineEdit)
                else w.value()
            )
            for key, w in self.fields.items()
        }

    def run(self):
        key = self.selection.currentData()
        if not key or (self.job and self.job.isRunning()):
            return
        self.snapshot = {"key": key, "params": self.parameters()}
        self.invalidate()
        self.controls.setEnabled(False)
        self.compute.setEnabled(False)
        self.feedback.setText("Calculando en un proceso separado…")
        self.job = SemesterJob(key, self.snapshot["params"], self)
        self.job.result.connect(self.complete)
        self.job.finished.connect(self.finish)
        self.job.start()

    def finish(self):
        self.controls.setEnabled(True)
        self.compute.setEnabled(bool(self.selection.currentData()))

    def complete(self, payload):
        if "error" in payload:
            self.feedback.setText("No se pudo resolver. Revisá los parámetros.")
            self.output.setPlainText(payload["error"])
            return
        self.data = payload["result"]
        self.feedback.setText("Resultado de los parámetros ingresados.")
        self.output.setPlainText(
            "\n".join(
                f"{k}: {v:.10g}" if isinstance(v, (int, float)) else f"{k}: {v}"
                for k, v in self.data["metrics"].items()
            )
        )
        self.assumptions.setPlainText(self.data["note"])
        for plot in self.data["charts"]:
            graph = plot_widget(plot["ylabel"], plot["xlabel"], None)
            graph.setMinimumHeight(180)
            graph.addLegend()
            for i, c in enumerate(plot["curves"]):
                color = ("#168b80", "#d48548", "#6d69bb", "#3a83c2", "#be5a88")[i % 5]
                points = c["name"] in ("Nodos", "Muestras", "Punto Q")
                graph.plot(
                    c["x"],
                    c["y"],
                    name=c["name"],
                    pen=None if points else pg.mkPen(color, width=2),
                    symbol="o" if points else None,
                    symbolSize=5,
                    symbolBrush=color,
                )
            self.results.addTab(graph, plot["title"])
        if self.data["headers"]:
            table = QTableWidget(len(self.data["rows"]), len(self.data["headers"]))
            table.setHorizontalHeaderLabels(self.data["headers"])
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            for i, row in enumerate(self.data["rows"]):
                for j, value in enumerate(row):
                    table.setItem(
                        i,
                        j,
                        QTableWidgetItem(
                            f"{value:.10g}"
                            if isinstance(value, (int, float))
                            else str(value)
                        ),
                    )
            self.results.addTab(table, "Tabla de cálculo")
        self.export_button.setEnabled(bool(self.data["charts"] or self.data["headers"]))
        self.note_button.setEnabled(True)
        self.netlist_button.setEnabled("netlist" in self.data)

    def report(self):
        tool = BY_KEY[self.snapshot["key"]]
        inputs = "\n".join(
            f"- {f.label}: {self.snapshot['params'][f.key]}" for f in tool.inputs
        )
        return f"# {tool.name}\n\nMateria: {tool.subject}\nFecha: {datetime.now():%Y-%m-%d %H:%M}\n\n## Datos\n{inputs}\n\n## Modelo\n{tool.formula}\n\n## Resultados\n{self.output.toPlainText()}\n\n## Hipótesis y límites\n{tool.description}\n{self.data['note']}\n"

    def save_note(self):
        if self.data is None:
            return
        tool = BY_KEY[self.snapshot["key"]]
        mapping = {
            "Cálculo Numérico": "Cálculo numérico",
            "Mediciones Eléctricas y Electrónicas": "Mediciones Eléctricas",
            "Electrónica Analógica · preparación": "Electrónica I",
        }
        try:
            self.store.save_note(
                mapping.get(tool.subject, tool.subject),
                f"{tool.name} · {datetime.now():%d/%m %H:%M}",
                self.report(),
            )
            self.changed.emit()
            self.feedback.setText(
                "Resultado, datos e hipótesis guardados como un nuevo apunte."
            )
        except (ValueError, sqlite3.Error) as exc:
            error(self, exc)

    def export_csv(self):
        if self.data is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar pestaña de resultados visible", "calculo.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                index = self.results.currentIndex()
                if index < len(self.data["charts"]):
                    plot = self.data["charts"][index]
                    writer.writerow(
                        [
                            field
                            for c in plot["curves"]
                            for field in (
                                c["name"] + " · " + plot["xlabel"],
                                c["name"] + " · " + plot["ylabel"],
                            )
                        ]
                    )
                    columns = [
                        column for c in plot["curves"] for column in (c["x"], c["y"])
                    ]
                    writer.writerows(zip_longest(*columns, fillvalue=""))
                else:
                    writer.writerow(self.data["headers"])
                    writer.writerows(self.data["rows"])
        except OSError as exc:
            error(self, exc)

    def export_netlist(self):
        if self.data is None or "netlist" not in self.data:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar circuito ngspice", "circuito.cir", "SPICE (*.cir)"
        )
        if path:
            try:
                Path(path).write_text(self.data["netlist"], encoding="ascii")
            except OSError as exc:
                error(self, exc)


GUIDE = """
<h1>Tu semestre, convertido en prácticas</h1>
<p><b>Entorno principal: Linux Mint Cinnamon.</b> Datos y apuntes locales; se conservan los respaldos de la versión 0.2.</p>
<h2>Ahora: 3.er año, 2.º semestre</h2>
<ul>
<li><b>Resistencia:</b> empezá por equilibrio de la viga; después revisá V, M, flecha y tensión. Compará apoyos y sección. Seguí con torsión, Mohr y Euler.</li>
<li><b>Cálculo numérico:</b> compará bisección, Newton y secante usando el mismo problema; observá residuo y convergencia. Estudiá integración, interpolación y EDO variando N.</li>
<li><b>Instalaciones:</b> calculá corriente, caída de tensión y pérdidas. Contrastá cobre/aluminio y mono/trifásico. Las verificaciones normativas requieren la norma y condiciones de instalación de tu curso.</li>
<li><b>Mediciones:</b> ingresá la especificación real de tu multímetro, compará errores de carga y propagación. Observá aliasing y respuesta de una galga en puente.</li>
<li><b>Termodinámica:</b> practicá convenios de signos, procesos P–V y propiedades de agua. Compará el modelo ideal Otto con Rankine usando propiedades reales.</li>
</ul>
<h2>Próximo semestre: electrónica analógica</h2>
<ol>
<li>Diodo: curva I–V, temperatura, rectificación y rizado.</li>
<li>BJT: polarización, región de operación, recta de carga y pequeña señal.</li>
<li>Operacionales: ganancia, offset y límites de salida.</li>
<li>Respuesta en frecuencia: filtro RC, corte, magnitud y fase.</li>
<li>Contraste SPICE: resolvé un RC y un emisor común DC/AC con ngspice. Exportá el netlist y exploralo en una herramienta especializada.</li>
</ol>
<p>Guardá cada resultado como apunte: el programa agrega los parámetros, fórmulas e hipótesis. Los CSV exportan la pestaña de resultados visible.</p>
<h2>Referencias investigadas</h2>
<ul>
<li><a href="https://github.com/ra3xdh/qucs_s">Qucs-S</a>: esquemas y visualización sobre motores como ngspice; alternativa completa para Linux.</li>
<li><a href="https://github.com/ngspice/ngspice">ngspice</a>: simulación SPICE. Aquí se integra como proceso opcional, con circuitos propios.</li>
<li><a href="https://github.com/sharpie7/circuitjs1">CircuitJS</a>: simulación interactiva en navegador, referencia didáctica.</li>
<li><a href="https://github.com/KiCad/kicad-doc">KiCad</a>: simulación mediante ngspice y preparación de circuitos más completos.</li>
<li><a href="https://github.com/gnu-octave/octave">GNU Octave</a> y <a href="https://github.com/scipy/scipy">SciPy</a>: herramientas de cálculo numérico y validación.</li>
<li><a href="https://github.com/sympy/sympy">SymPy</a>: cálculo simbólico y mecánica de vigas.</li>
<li><a href="https://github.com/CoolProp/CoolProp">CoolProp</a>: propiedades termodinámicas, integrado directamente.</li>
</ul>
<p>El informe completo, fuentes, decisiones y límites están en <b>docs/INVESTIGACION-v0.3.md</b> del repositorio. Los modelos educativos y la interfaz son implementaciones propias; no se copian interfaces ni código de los simuladores comparados.</p>
"""
