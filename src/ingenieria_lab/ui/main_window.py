"""Centro de estudio de Ingeniería Lab."""

from datetime import datetime
import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QFileDialog,
    QMessageBox,
    QScrollArea,
)
from ingenieria_lab.storage.workspace import Workspace
from ingenieria_lab.ui.common import STYLE, label, button, heading, panel, error
from ingenieria_lab.ui.study import Dashboard, SubjectsPage, NotesPage, AgendaPage
from ingenieria_lab.ui.semester import SemesterPage
from ingenieria_lab.ui.laboratories import (
    MathPage,
    ToolsPage,
    SignalsPage,
    SimulationsPage,
)


class MainWindow(QMainWindow):
    def __init__(self, store=None):
        super().__init__()
        self.store = store if store is not None else Workspace()
        self.setWindowTitle("Ingeniería Lab — Mi semestre · v0.3")
        self.setMinimumSize(1020, 700)
        available = self.screen().availableGeometry()
        self.resize(
            min(1320, max(1020, available.width() - 64)),
            min(850, max(700, available.height() - 64)),
        )
        self.setStyleSheet(STYLE)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(218)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(18, 30, 18, 20)
        sl.addWidget(label("INGENIERÍA\nLAB", "brand"))
        sl.addWidget(label("Tu compañero de carrera"))
        sl.addSpacing(26)
        self.names = [
            "Inicio",
            "Mi semestre",
            "Mi carrera",
            "Calculadora",
            "Herramientas",
            "Simuladores",
            "Señales",
            "Apuntes",
            "Agenda",
            "Datos y ayuda",
        ]
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.addItems(self.names)
        sl.addWidget(self.nav, 1)
        sl.addWidget(
            label("ELECTROMECÁNICA\n3.er año · 2.º semestre\nv0.3 · Linux Mint")
        )
        layout.addWidget(side)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.notes = NotesPage(self.store)
        self.agenda = AgendaPage(self.store)
        self.subjects = SubjectsPage(self.store, self.navigate, self.open_notes)
        self.dashboard = Dashboard(self.store, self.navigate)
        self.math = MathPage()
        self.semester = SemesterPage(self.store)
        self.pages = [
            self.dashboard,
            self.semester,
            self.subjects,
            self.math,
            ToolsPage(),
            SimulationsPage(),
            SignalsPage(),
            self.notes,
            self.agenda,
            self.help_page(),
        ]
        for page in self.pages:
            wrapper = QWidget()
            wl = QVBoxLayout(wrapper)
            wl.setContentsMargins(22, 16, 22, 12)
            wl.addWidget(page)
            self.stack.addWidget(wrapper)
        self.nav.currentRowChanged.connect(self.select_page)
        self.nav.setCurrentRow(self.names.index("Mi semestre"))
        for page in (self.notes, self.agenda, self.subjects):
            page.changed.connect(self.dashboard.refresh)
        self.semester.changed.connect(self.notes.refresh)
        self.semester.changed.connect(self.dashboard.refresh)
        self.save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        self.save_shortcut.activated.connect(
            lambda: (
                self.notes.save()
                if self.nav.currentItem().text() == "Apuntes"
                else None
            )
        )
        self.statusBar().showMessage(
            "Listo · cálculos en SI salvo indicación · Ctrl+S guarda el apunte abierto"
        )

    def navigate(self, name):
        self.nav.setCurrentRow(self.names.index(name))

    def select_page(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard.refresh()

    def open_notes(self, subject):
        self.notes.filter.setCurrentText(subject)
        self.navigate("Apuntes")

    def help_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        heading(
            layout,
            "Datos y ayuda",
            "Tus apuntes son tuyos: guardalos, exportalos y llevá una copia de respaldo",
        )
        card, cl = panel()
        cl.addWidget(label("Almacenamiento local", "section"))
        path = label(str(self.store.path))
        path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cl.addWidget(path)
        cl.addWidget(
            label(
                "La base SQLite guarda materias, apuntes y tareas fuera de la carpeta del programa. No hay cuenta ni sincronización en la nube."
            )
        )
        row = QHBoxLayout()
        row.addWidget(button("Crear respaldo JSON", self.backup, True))
        row.addWidget(button("Restaurar respaldo…", self.restore))
        cl.addLayout(row)
        layout.addWidget(card)
        card, cl = panel()
        cl.addWidget(label("Una rutina para aprovecharlo", "section"))
        cl.addWidget(
            label(
                "1. Marcá las materias que cursás en Mi carrera.\n\n2. Registrá fechas de parciales y entregas en Agenda.\n\n3. Resolvé, graficá y compará modelos en los laboratorios.\n\n4. Guardá hipótesis, unidades, resultados y dudas en Apuntes.\n\n5. Creá un respaldo periódico en otra unidad."
            )
        )
        layout.addWidget(card)
        layout.addWidget(label("Alcance de esta versión", "section"))
        layout.addWidget(
            label(
                "Las 39 materias provienen de las imágenes, sin religión ni ética. Los bloques y temas son organizativos, no un plan oficial. “Transmisión de E” conserva el nombre abreviado de la captura."
            )
        )
        layout.addWidget(
            label(
                "Mi semestre reúne 30 herramientas para tus cinco materias actuales y Electrónica Analógica. Combina modelos educativos, propiedades reales de CoolProp y dos circuitos ejecutables con ngspice. No incluye editor libre de esquemas ni selección normativa completa de protecciones. Cada herramienta muestra sus hipótesis y unidades."
            )
        )
        layout.addWidget(
            label(
                "No se usan servicios de IA ni se envían apuntes. Se necesita Internet para instalar dependencias; el uso posterior es local.",
                "muted",
            )
        )
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def backup(self):
        if not self.notes.maybe_save():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Crear respaldo",
            f"ingenieria-lab-{datetime.now():%Y-%m-%d}.json",
            "JSON (*.json)",
        )
        if path:
            try:
                self.store.export_backup(path)
                QMessageBox.information(
                    self,
                    "Respaldo creado",
                    "Se guardaron tus apuntes, tareas y estados de materias.",
                )
            except (OSError, ValueError, sqlite3.Error) as exc:
                error(self, exc)

    def restore(self):
        if not self.notes.maybe_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar respaldo", "", "JSON (*.json)"
        )
        if not path:
            return
        if (
            QMessageBox.question(
                self,
                "Restaurar datos",
                "Se reemplazarán los apuntes, tareas y estados actuales por el respaldo. Antes se creará una copia automática. ¿Continuar?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            safety = (
                self.store.path.parent
                / f"antes-de-restaurar-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
            )
            self.store.export_backup(safety)
            self.store.import_backup(path)
            self.notes.reset_after_restore()
            self.agenda.refresh()
            self.subjects.refresh()
            self.dashboard.refresh()
            QMessageBox.information(
                self,
                "Datos restaurados",
                f"Restauración completa. Copia anterior:\n{safety}",
            )
        except (ValueError, OSError, sqlite3.Error) as exc:
            error(self, exc)

    def closeEvent(self, event):
        if not self.notes.maybe_save():
            event.ignore()
            return
        if any(
            job is not None and job.isRunning()
            for job in (self.math.job, self.semester.job)
        ):
            self.statusBar().showMessage(
                "Esperá a que finalice el cálculo antes de cerrar (máximo 20 segundos)."
            )
            event.ignore()
            return
        self.store.close()
        event.accept()
