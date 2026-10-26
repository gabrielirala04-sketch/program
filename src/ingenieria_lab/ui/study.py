from datetime import date
from pathlib import Path
import sqlite3
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPlainTextEdit,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QSplitter,
    QDateEdit,
    QMessageBox,
    QFileDialog,
    QProgressBar,
)
from ingenieria_lab.catalog import SUBJECTS, SUBJECT_NAMES, AREAS, GUIDES
from ingenieria_lab.storage.workspace import STATUSES
from ingenieria_lab.ui.common import label, button, heading, panel, error


class Dashboard(QWidget):
    def __init__(self, store, navigate):
        super().__init__()
        self.store = store
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        heading(
            layout,
            "Tu espacio de ingeniería",
            "Electromecánica · orientación electrónica",
        )
        hero, hl = panel()
        hl.addWidget(label("Aprender. Experimentar. Conectar.", "section"))
        hl.addWidget(
            label(
                "Un lugar para seguir tu carrera, explorar modelos y construir tu propio cuaderno técnico."
            )
        )
        actions = QHBoxLayout()
        actions.addWidget(
            button("Abrir simuladores", lambda: navigate("Simuladores"), True)
        )
        actions.addWidget(button("Escribir un apunte", lambda: navigate("Apuntes")))
        actions.addStretch()
        hl.addLayout(actions)
        layout.addWidget(hero)
        metrics = QHBoxLayout()
        self.metrics = []
        for title in (
            "Materias aprobadas",
            "En curso",
            "Apuntes guardados",
            "Tareas pendientes",
        ):
            frame, fl = panel()
            value = label("0", "metric")
            self.metrics.append(value)
            fl.addWidget(value)
            fl.addWidget(label(title, "muted"))
            metrics.addWidget(frame)
        layout.addLayout(metrics)
        self.progress = QProgressBar()
        self.progress.setRange(0, len(SUBJECTS))
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        self.progress_text = label("", "muted")
        layout.addWidget(self.progress_text)
        lower = QHBoxLayout()
        card, cl = panel()
        cl.addWidget(label("Próximos compromisos", "section"))
        self.tasks = label("")
        cl.addWidget(self.tasks, 1)
        cl.addWidget(button("Organizar mi agenda", lambda: navigate("Agenda")))
        lower.addWidget(card, 1)
        card, cl = panel()
        cl.addWidget(label("A mano para estudiar", "section"))
        for title, dest in [
            ("Derivadas, integrales y matrices", "Calculadora"),
            ("Circuitos, máquinas y unidades", "Herramientas"),
            ("Señales y análisis de frecuencia", "Señales"),
        ]:
            cl.addWidget(button(title, lambda checked=False, d=dest: navigate(d)))
        cl.addStretch()
        lower.addWidget(card, 1)
        layout.addLayout(lower, 1)
        layout.addWidget(
            label(
                "Trabajo local · tus apuntes no se envían a un servidor · creá respaldos desde Datos y ayuda",
                "muted",
            )
        )
        self.refresh()

    def refresh(self):
        statuses = self.store.statuses()
        tasks = [t for t in self.store.tasks() if not t["done"]]
        values = [
            list(statuses.values()).count("Aprobada"),
            list(statuses.values()).count("Cursando"),
            len(self.store.notes()),
            len(tasks),
        ]
        for w, v in zip(self.metrics, values):
            w.setText(str(v))
        self.progress.setValue(values[0])
        self.progress_text.setText(
            f"{values[0]} de {len(SUBJECTS)} materias aprobadas · seguimiento personal, sin ponderación por créditos"
        )
        self.tasks.setText(
            "\n\n".join(
                f"{'Vencida · ' if t['due'] < date.today().isoformat() else ''}{t['due']}  ·  {t['title']}\n{t['subject']}"
                for t in tasks[:4]
            )
            or "Todavía no hay compromisos pendientes.\nAgregá un parcial, una práctica o una entrega en tu agenda."
        )


class SubjectsPage(QWidget):
    changed = Signal()

    def __init__(self, store, navigate, open_notes):
        super().__init__()
        self.store = store
        self.navigate = navigate
        self.open_notes = open_notes
        self.selected = None
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Mi carrera",
            "39 materias de tus imágenes · buscá, organizá y seguí tu avance",
        )
        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar materia o tema…")
        self.area = QComboBox()
        self.area.addItems(["Todas las áreas", *AREAS])
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos los estados", *STATUSES])
        row.addWidget(self.search, 2)
        row.addWidget(self.area)
        row.addWidget(self.status_filter)
        layout.addLayout(row)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Materia", "Área", "Bloque", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        layout.addWidget(self.table, 1)
        card, cl = panel()
        self.name = label("Seleccioná una materia", "section")
        self.topics = label("")
        self.guide = label("")
        self.formula = label("", "muted")
        for w in (self.name, self.topics, self.guide, self.formula):
            cl.addWidget(w)
        buttons = QHBoxLayout()
        self.status = QComboBox()
        self.status.addItems(STATUSES)
        buttons.addWidget(label("Mi estado"))
        buttons.addWidget(self.status)
        buttons.addWidget(button("Guardar estado", self.save_status, True))
        buttons.addWidget(button("Ver apuntes", self.notes))
        buttons.addWidget(button("Abrir herramienta sugerida", self.tool))
        cl.addLayout(buttons)
        layout.addWidget(card)
        layout.addWidget(
            label(
                "Los bloques reproducen el orden de las capturas; no representan semestres ni correlatividades oficiales. Los temas son orientativos. Religión y ética excluidas.",
                "muted",
            )
        )
        self.search.textChanged.connect(self.refresh)
        self.area.currentTextChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.table.itemSelectionChanged.connect(self.select)
        self.refresh()

    def refresh(self):
        saved = self.store.statuses()
        query = self.search.text().casefold()
        rows = [
            s
            for s in SUBJECTS
            if query in (s.name + " " + s.topics).casefold()
            and (self.area.currentIndex() == 0 or s.area == self.area.currentText())
            and (
                self.status_filter.currentIndex() == 0
                or saved[s.name] == self.status_filter.currentText()
            )
        ]
        self.table.setRowCount(0)
        for i, s in enumerate(rows):
            self.table.insertRow(i)
            for j, value in enumerate((s.name, s.area, str(s.block), saved[s.name])):
                self.table.setItem(i, j, QTableWidgetItem(value))
        if rows:
            self.table.selectRow(0)
        else:
            self.selected = None
            self.name.setText("Sin coincidencias")
            self.topics.clear()
            self.guide.clear()
            self.formula.clear()

    def select(self):
        row = self.table.currentRow()
        if row < 0 or self.table.item(row, 0) is None:
            return
        self.selected = next(
            s for s in SUBJECTS if s.name == self.table.item(row, 0).text()
        )
        s = self.selected
        self.name.setText(s.name)
        self.topics.setText(s.topics)
        _, guide, formula = GUIDES[s.area]
        self.guide.setText(guide)
        self.formula.setText(formula)
        self.status.setCurrentText(self.store.statuses()[s.name])

    def save_status(self):
        if self.selected:
            try:
                self.store.set_status(self.selected.name, self.status.currentText())
                self.refresh()
                self.changed.emit()
            except sqlite3.Error as exc:
                error(self, exc)

    def notes(self):
        if self.selected:
            self.open_notes(self.selected.name)

    def tool(self):
        if self.selected:
            self.navigate(GUIDES[self.selected.area][0])


class NotesPage(QWidget):
    changed = Signal()

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.note_id = None
        self.loading = False
        self.dirty = False
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Cuaderno de estudio",
            "Apuntes por materia · búsqueda por contenido · exportación Markdown",
        )
        split = QSplitter()
        layout.addWidget(split, 1)
        left = QWidget()
        ll = QVBoxLayout(left)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar en títulos y apuntes…")
        ll.addWidget(self.search)
        self.filter = QComboBox()
        self.filter.addItems(["Todas", "General", *SUBJECT_NAMES])
        ll.addWidget(self.filter)
        self.list = QListWidget()
        ll.addWidget(self.list, 1)
        ll.addWidget(button("+ Nuevo apunte", self.new_note, True))
        split.addWidget(left)
        right = QWidget()
        rl = QVBoxLayout(right)
        self.subject = QComboBox()
        self.subject.addItems(["General", *SUBJECT_NAMES])
        rl.addWidget(self.subject)
        self.title = QLineEdit()
        self.title.setPlaceholderText("Título del apunte")
        rl.addWidget(self.title)
        self.body = QPlainTextEdit()
        self.body.setPlaceholderText(
            "Escribí ideas, fórmulas, ejercicios resueltos y dudas.\n\nPodés usar Markdown y exportar el texto para conservarlo."
        )
        rl.addWidget(self.body, 1)
        row = QHBoxLayout()
        row.addWidget(button("Guardar apunte", self.save, True))
        row.addWidget(button("Exportar .md", self.export))
        row.addWidget(button("Eliminar", self.delete))
        rl.addLayout(row)
        self.feedback = label("Sin cambios pendientes", "muted")
        rl.addWidget(self.feedback)
        split.addWidget(right)
        split.setSizes([300, 650])
        self.search.textChanged.connect(self.refresh)
        self.filter.currentTextChanged.connect(self.refresh)
        self.list.currentItemChanged.connect(self.load)
        self.title.textChanged.connect(self.mark_dirty)
        self.body.textChanged.connect(self.mark_dirty)
        self.subject.currentTextChanged.connect(self.mark_dirty)
        self.refresh()

    def mark_dirty(self):
        if not self.loading:
            self.dirty = True
            self.feedback.setText("Cambios sin guardar")

    def maybe_save(self):
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Apunte sin guardar",
            "¿Querés guardar los cambios antes de continuar?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        self.dirty = False
        return True

    def refresh(self):
        # Filtrar la lista no modifica el editor ni descarta borradores.
        self.list.blockSignals(True)
        self.list.clear()
        for note in self.store.notes(self.search.text(), self.filter.currentText()):
            item = QListWidgetItem(f"{note['title']}\n{note['subject']}")
            item.setData(Qt.ItemDataRole.UserRole, note)
            self.list.addItem(item)
            if note["id"] == self.note_id:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)

    def load(self, current, previous):
        if current is None:
            return
        note = current.data(Qt.ItemDataRole.UserRole)
        if note["id"] == self.note_id:
            return
        if not self.maybe_save():
            self.list.blockSignals(True)
            self.list.setCurrentItem(previous)
            self.list.blockSignals(False)
            return
        self.loading = True
        self.note_id = note["id"]
        self.subject.setCurrentText(note["subject"])
        self.title.setText(note["title"])
        self.body.setPlainText(note["body"])
        self.loading = False
        self.dirty = False
        self.feedback.setText("Apunte guardado · " + note["updated"][:10])
        self.refresh()

    def new_note(self):
        if not self.maybe_save():
            return
        self.loading = True
        self.note_id = None
        self.title.clear()
        self.body.clear()
        self.subject.setCurrentText(
            self.filter.currentText()
            if self.filter.currentText() != "Todas"
            else "General"
        )
        self.list.clearSelection()
        self.loading = False
        self.dirty = False
        self.feedback.setText("Nuevo apunte")
        self.title.setFocus()

    def save(self):
        try:
            self.note_id = self.store.save_note(
                self.subject.currentText(),
                self.title.text(),
                self.body.toPlainText(),
                self.note_id,
            )
            self.dirty = False
            self.feedback.setText("Guardado en este equipo")
            self.refresh()
            self.changed.emit()
            return True
        except (ValueError, sqlite3.Error) as exc:
            error(self, exc)
            return False

    def export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar apunte", "apunte.md", "Markdown (*.md)"
        )
        if path:
            try:
                Path(path).write_text(
                    f"# {self.title.text()}\n\nMateria: {self.subject.currentText()}\n\n{self.body.toPlainText()}\n",
                    encoding="utf-8",
                )
            except OSError as exc:
                error(self, exc)

    def delete(self):
        if self.note_id is None:
            return
        if (
            QMessageBox.question(
                self,
                "Eliminar apunte",
                "¿Eliminar este apunte? Esta acción no se puede deshacer.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.store.delete_note(self.note_id)
            self.dirty = False
            self.new_note()
            self.refresh()
            self.changed.emit()
        except sqlite3.Error as exc:
            error(self, exc)

    def reset_after_restore(self):
        self.dirty = False
        self.note_id = None
        self.new_note()
        self.refresh()


class AgendaPage(QWidget):
    changed = Signal()

    def __init__(self, store):
        super().__init__()
        self.store = store
        layout = QVBoxLayout(self)
        heading(
            layout,
            "Agenda de estudio",
            "Parciales, prácticas, entregas y pequeños próximos pasos",
        )
        card, cl = panel()
        self.title = QLineEdit()
        self.title.setPlaceholderText("¿Qué necesitás preparar o entregar?")
        cl.addWidget(self.title)
        row = QHBoxLayout()
        self.subject = QComboBox()
        self.subject.addItems(["General", *SUBJECT_NAMES])
        self.due = QDateEdit(QDate.currentDate())
        self.due.setCalendarPopup(True)
        self.due.setDisplayFormat("dd/MM/yyyy")
        row.addWidget(self.subject, 2)
        row.addWidget(label("Fecha"))
        row.addWidget(self.due)
        row.addWidget(button("Agregar tarea", self.add, True))
        cl.addLayout(row)
        layout.addWidget(card)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Estado", "Fecha", "Tarea", "Materia"])
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
        row = QHBoxLayout()
        row.addWidget(button("Completar / reabrir", self.toggle))
        row.addWidget(button("Eliminar seleccionada", self.delete))
        row.addStretch()
        layout.addLayout(row)
        self.message = label("", "muted")
        layout.addWidget(self.message)
        self.refresh()

    def refresh(self):
        self.rows = self.store.tasks()
        self.table.setRowCount(len(self.rows))
        for i, t in enumerate(self.rows):
            status = (
                "Completada"
                if t["done"]
                else ("Vencida" if t["due"] < date.today().isoformat() else "Pendiente")
            )
            for j, value in enumerate((status, t["due"], t["title"], t["subject"])):
                self.table.setItem(i, j, QTableWidgetItem(value))
        self.message.setText(
            f"{sum(not t['done'] for t in self.rows)} pendientes · {sum(bool(t['done']) for t in self.rows)} completadas"
            if self.rows
            else "Tu agenda está vacía. Agregá tu próxima entrega para empezar."
        )

    def add(self):
        try:
            self.store.add_task(
                self.subject.currentText(),
                self.title.text(),
                self.due.date().toString("yyyy-MM-dd"),
            )
            self.title.clear()
            self.refresh()
            self.changed.emit()
        except (ValueError, sqlite3.Error) as exc:
            error(self, exc)

    def toggle(self):
        row = self.table.currentRow()
        if row < 0:
            return
        try:
            task = self.rows[row]
            self.store.set_done(task["id"], not task["done"])
            self.refresh()
            self.changed.emit()
        except sqlite3.Error as exc:
            error(self, exc)

    def delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if (
            QMessageBox.question(
                self, "Eliminar tarea", "¿Eliminar la tarea seleccionada?"
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.store.delete_task(self.rows[row]["id"])
            self.refresh()
            self.changed.emit()
        except sqlite3.Error as exc:
            error(self, exc)
