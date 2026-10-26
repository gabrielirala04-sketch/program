"""Persistencia local y respaldos portables; no necesita servicios externos."""

from __future__ import annotations
import json
import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from ingenieria_lab.catalog import SUBJECT_NAMES

STATUSES = ("Pendiente", "Cursando", "Aprobada")


def data_directory() -> Path:
    if os.environ.get("INGENIERIA_LAB_DATA_DIR"):
        return Path(os.environ["INGENIERIA_LAB_DATA_DIR"]).expanduser()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "IngenieriaLab"
    return (
        Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        / "ingenieria-lab"
    )


class Workspace:
    def __init__(self, path: Path | None = None):
        self.path = path if path is not None else data_directory() / "estudio.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS subjects(name TEXT PRIMARY KEY, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, subject TEXT NOT NULL,
                title TEXT NOT NULL, body TEXT NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, subject TEXT NOT NULL,
                title TEXT NOT NULL, due TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0);
        """)
        self.db.commit()

    def statuses(self):
        saved = dict(self.db.execute("SELECT name,status FROM subjects"))
        return {name: saved.get(name, "Pendiente") for name in SUBJECT_NAMES}

    def set_status(self, name, status):
        if name not in SUBJECT_NAMES or status not in STATUSES:
            raise ValueError("Materia o estado inválido")
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO subjects VALUES (?,?)", (name, status)
            )

    def notes(self, query="", subject="Todas"):
        rows = self.db.execute(
            "SELECT * FROM notes ORDER BY updated DESC,id DESC"
        ).fetchall()
        return [
            dict(r)
            for r in rows
            if (subject == "Todas" or r["subject"] == subject)
            and query.casefold() in (r["title"] + " " + r["body"]).casefold()
        ]

    def save_note(self, subject, title, body, note_id=None):
        if subject not in ["General", *SUBJECT_NAMES] or not title.strip():
            raise ValueError("Elegí una materia y escribí un título")
        values = (subject, title.strip(), body, datetime.now(timezone.utc).isoformat())
        with self.db:
            if note_id is None:
                return self.db.execute(
                    "INSERT INTO notes(subject,title,body,updated) VALUES (?,?,?,?)",
                    values,
                ).lastrowid
            if not self.db.execute(
                "UPDATE notes SET subject=?,title=?,body=?,updated=? WHERE id=?",
                (*values, note_id),
            ).rowcount:
                raise ValueError("El apunte ya no existe")
        return note_id

    def delete_note(self, note_id):
        with self.db:
            self.db.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def tasks(self):
        return [
            dict(r) for r in self.db.execute("SELECT * FROM tasks ORDER BY done,due,id")
        ]

    def add_task(self, subject, title, due):
        if subject not in ["General", *SUBJECT_NAMES] or not title.strip():
            raise ValueError("Escribí una tarea y elegí una materia")
        date.fromisoformat(due)
        with self.db:
            return self.db.execute(
                "INSERT INTO tasks(subject,title,due) VALUES (?,?,?)",
                (subject, title.strip(), due),
            ).lastrowid

    def set_done(self, task_id, done):
        with self.db:
            self.db.execute(
                "UPDATE tasks SET done=? WHERE id=?", (int(bool(done)), task_id)
            )

    def delete_task(self, task_id):
        with self.db:
            self.db.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def export_backup(self, path):
        data = {
            "version": 1,
            "subjects": self.statuses(),
            "notes": self.notes(),
            "tasks": self.tasks(),
        }
        target = Path(path)
        if target.resolve() == self.path.resolve():
            raise ValueError("El respaldo no puede sobrescribir la base de datos")
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp.replace(target)

    def import_backup(self, path):
        """Valida completamente antes de reemplazar; transacción atómica."""
        source = Path(path)
        if source.stat().st_size > 20_000_000:
            raise ValueError("Respaldo demasiado grande (máximo 20 MB)")
        data = json.loads(source.read_text(encoding="utf-8"))
        try:
            if data["version"] != 1 or not isinstance(data["subjects"], dict):
                raise ValueError()
            if set(data["subjects"]) - set(SUBJECT_NAMES):
                raise ValueError()
            if any(v not in STATUSES for v in data["subjects"].values()):
                raise ValueError()
            for key in ("notes", "tasks"):
                if not isinstance(data[key], list):
                    raise ValueError()
                ids = set()
                for row in data[key]:
                    if type(row["id"]) is not int or row["id"] <= 0 or row["id"] in ids:
                        raise ValueError()
                    ids.add(row["id"])
                    if row["subject"] not in ["General", *SUBJECT_NAMES]:
                        raise ValueError()
                    if not isinstance(row["title"], str) or not row["title"].strip():
                        raise ValueError()
                    if key == "notes":
                        if not isinstance(row["body"], str):
                            raise ValueError()
                        datetime.fromisoformat(row["updated"])
                    else:
                        date.fromisoformat(row["due"])
                        if type(row["done"]) is not int or row["done"] not in (0, 1):
                            raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError(
                "El archivo no es un respaldo válido de Ingeniería Lab"
            ) from exc
        with self.db:
            for table in ("subjects", "notes", "tasks"):
                self.db.execute(f"DELETE FROM {table}")
            self.db.executemany(
                "INSERT INTO subjects VALUES (?,?)", data["subjects"].items()
            )
            self.db.executemany(
                "INSERT INTO notes VALUES (?,?,?,?,?)",
                [
                    (r["id"], r["subject"], r["title"], r["body"], r["updated"])
                    for r in data["notes"]
                ],
            )
            self.db.executemany(
                "INSERT INTO tasks VALUES (?,?,?,?,?)",
                [
                    (r["id"], r["subject"], r["title"], r["due"], r["done"])
                    for r in data["tasks"]
                ],
            )

    def close(self):
        self.db.close()
