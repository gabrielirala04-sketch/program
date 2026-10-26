"""Integración de la interfaz real Qt, sin necesitar una pantalla física."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QMessageBox
from ingenieria_lab.storage.workspace import Workspace
from ingenieria_lab.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path):
    w = MainWindow(Workspace(tmp_path / "study.db"))
    w.show()
    app.processEvents()
    yield w
    for job in (w.math.job, w.semester.job):
        if job is not None:
            job.wait(22000)
    w.notes.dirty = False
    w.close()
    app.processEvents()


def click_named(widget, text):
    target = next(b for b in widget.findChildren(QPushButton) if b.text() == text)
    QTest.mouseClick(target, Qt.MouseButton.LeftButton)


def test_navigation_and_models(window, app):
    for i, name in enumerate(window.names):
        window.navigate(name)
        app.processEvents()
        assert window.stack.currentIndex() == i
    tools = window.pages[window.names.index("Herramientas")]
    for i in range(tools.choice.count()):
        tools.choice.setCurrentIndex(i)
        assert "=" in tools.output.toPlainText()
    models = window.pages[window.names.index("Simuladores")]
    for i in range(models.choice.count()):
        models.choice.setCurrentIndex(i)
        assert models.data is not None
    signals = window.pages[window.names.index("Señales")]
    for i in range(signals.wave.count()):
        signals.wave.setCurrentIndex(i)
        signals.refresh()
        assert len(signals.v) == 1000


def test_note_save_search_and_task_complete(window, app):
    window.navigate("Apuntes")
    n = window.notes
    n.subject.setCurrentText("Circuitos eléctricos")
    n.title.setText("Ley de Kirchhoff")
    n.body.setPlainText("La suma de corrientes es cero.")
    click_named(n, "Guardar apunte")
    assert not n.dirty
    n.search.setText("corrientes")
    assert n.list.count() == 1
    n.new_note()
    n.title.setText("Segundo apunte")
    n.body.setPlainText("Potencia")
    n.save()
    n.search.clear()
    assert n.list.count() == 2
    n.list.setCurrentRow(1)
    assert n.title.text() == "Ley de Kirchhoff"
    window.navigate("Agenda")
    a = window.agenda
    a.title.setText("Resolver práctica")
    click_named(a, "Agregar tarea")
    a.table.selectRow(0)
    click_named(a, "Completar / reabrir")
    assert window.store.tasks()[0]["done"] == 1
    window.dashboard.refresh()
    assert window.dashboard.metrics[2].text() == "2"


def test_unsaved_note_cancel_and_save_before_switch(window, monkeypatch):
    n = window.notes
    n.title.setText("Uno")
    n.body.setPlainText("Original")
    n.save()
    first = n.note_id
    n.new_note()
    n.title.setText("Dos")
    n.body.setPlainText("Original dos")
    n.save()
    n.body.setPlainText("Cambio que no se debe perder")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel
    )
    n.list.setCurrentRow(1)
    assert n.title.text() == "Dos" and n.dirty
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save
    )
    n.list.setCurrentRow(1)
    assert n.note_id == first and n.title.text() == "Uno"
    assert (
        next(row for row in window.store.notes() if row["title"] == "Dos")["body"]
        == "Cambio que no se debe perder"
    )


def test_math_worker_result_and_signal_invalid_input(window, app):
    window.navigate("Calculadora")
    m = window.math
    m.expr.setText("x^3")
    m.operation.setCurrentText("Derivada")
    click_named(m, "Calcular")
    for _ in range(200):
        QTest.qWait(50)
        if not m.job.isRunning():
            break
    app.processEvents()
    assert "3*x**2" in m.output.toPlainText()
    signals = window.pages[window.names.index("Señales")]
    signals.fields["sample_rate_hz"].setValue(50)
    signals.refresh()
    assert signals.t is None and "superar 2 veces" in signals.results.text()


def test_subject_filter_and_status(window):
    s = window.subjects
    s.search.setText("Electrónica I")
    assert s.table.rowCount() == 4
    s.table.selectRow(0)
    s.status.setCurrentText("Cursando")
    s.save_status()
    assert window.store.statuses()["Electrónica I"] == "Cursando"
    s.search.setText("sin coincidencias")
    assert s.table.rowCount() == 0 and s.selected is None


def test_semester_forms_filter_and_default_landing(window, app):
    from ingenieria_lab.semester.registry import TOOLS, BY_KEY

    s = window.semester
    assert window.nav.currentItem().text() == "Mi semestre"
    visited = set()
    for i in range(s.subject.count()):
        s.subject.setCurrentIndex(i)
        for j in range(s.selection.count()):
            s.selection.setCurrentIndex(j)
            app.processEvents()
            key = s.selection.currentData()
            visited.add(key)
            assert set(s.fields) == {f.key for f in BY_KEY[key].inputs}
    assert len(visited) == len(TOOLS) == 30
    s.kind.setCurrentText("Calculadora")
    assert all(
        BY_KEY[s.selection.itemData(i)].kind == "Calculadora"
        for i in range(s.selection.count())
    )


def test_semester_calculate_save_and_csv(window, app, tmp_path, monkeypatch):
    import csv
    from PySide6.QtWidgets import QFileDialog

    s = window.semester
    s.run()
    for _ in range(440):
        QTest.qWait(50)
        if not s.job.isRunning():
            break
    app.processEvents()
    assert s.data is not None and s.compute.isEnabled()
    assert "Reacción izquierda" in s.output.toPlainText()
    s.save_note()
    note = window.store.notes()[0]
    assert (
        note["subject"] == "Resistencia de Materiales"
        and "Hipótesis" in note["body"]
        and "Luz L [m]" in note["body"]
    )
    path = tmp_path / "beam.csv"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), "CSV")
    )
    s.export_csv()
    with path.open() as file:
        rows = list(csv.reader(file))
    assert "Posición [m]" in rows[0][0] and len(rows) > 800
    s.fields["L"].setValue(3)
    assert (
        s.data is None
        and not s.export_button.isEnabled()
        and not s.note_button.isEnabled()
    )


def test_semester_worker_reports_invalid_domain(window, app):
    s = window.semester
    s.subject.setCurrentText("Cálculo Numérico")
    s.fields["expr"].setText("sqrt(-1)")
    s.run()
    for _ in range(440):
        QTest.qWait(50)
        if not s.job.isRunning():
            break
    app.processEvents()
    assert s.data is None and "No se pudo" in s.feedback.text()
    assert s.compute.isEnabled()
