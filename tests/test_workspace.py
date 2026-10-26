import json
import pytest
from ingenieria_lab.storage.workspace import Workspace
from ingenieria_lab.catalog import SUBJECTS


def test_catalog_matches_requested_exclusions():
    assert len(SUBJECTS) == 39
    assert len({s.name for s in SUBJECTS}) == 39
    excluded = ("ética", "bioetica", "eclesiologia", "sacramentos", "religión")
    assert not any(word in s.name.lower() for s in SUBJECTS for word in excluded)


def test_save_reopen_search_and_update(tmp_path):
    path = tmp_path / "study.db"
    store = Workspace(path)
    note_id = store.save_note("Electrónica I", "Diodos", "Umbral y modelo ideal")
    store.save_note("Electrónica I", "Diodos revisados", "Modelo exponencial", note_id)
    store.set_status("Electrónica I", "Cursando")
    task_id = store.add_task("Electrónica I", "Preparar parcial", "2026-11-05")
    store.set_done(task_id, True)
    store.close()
    reopened = Workspace(path)
    assert (
        reopened.notes("EXPONENCIAL", "Electrónica I")[0]["title"] == "Diodos revisados"
    )
    assert reopened.notes("exponencial", "Álgebra Lineal") == []
    assert reopened.statuses()["Electrónica I"] == "Cursando"
    assert reopened.tasks()[0]["done"] == 1
    reopened.close()


def test_backup_roundtrip_and_atomic_invalid_restore(tmp_path):
    store = Workspace(tmp_path / "source.db")
    store.save_note("General", "Prueba", "Texto unicode: Ω µ á")
    store.add_task("General", "Entrega", "2026-12-01")
    store.set_status("Cálculo II", "Aprobada")
    backup = tmp_path / "backup.json"
    store.export_backup(backup)
    other = Workspace(tmp_path / "other.db")
    other.import_backup(backup)
    assert (
        other.notes() == store.notes()
        and other.tasks() == store.tasks()
        and other.statuses() == store.statuses()
    )
    broken = json.loads(backup.read_text())
    broken["tasks"][0]["due"] = "fecha inválida"
    backup.write_text(json.dumps(broken))
    with pytest.raises(ValueError):
        other.import_backup(backup)
    assert other.notes() == store.notes() and other.tasks() == store.tasks()
    with pytest.raises(ValueError):
        store.export_backup(store.path)
    store.close()
    other.close()


def test_crud_and_bad_inputs(tmp_path):
    store = Workspace(tmp_path / "test.db")
    with pytest.raises(ValueError):
        store.save_note("General", " ", "body")
    with pytest.raises(ValueError):
        store.add_task("General", "Task", "2026-02-30")
    with pytest.raises(ValueError):
        store.set_status("Unknown", "Aprobada")
    n = store.save_note("General", "Title", "Body")
    store.delete_note(n)
    assert not store.notes()
    t = store.add_task("General", "Task", "2026-11-01")
    store.delete_task(t)
    assert not store.tasks()
    store.close()
