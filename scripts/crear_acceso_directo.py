"""Crea un lanzador de usuario conforme al formato Desktop Entry, sin sudo."""

import os
from pathlib import Path


def quote_exec(value):
    text = str(value)
    if "\n" in text or "\r" in text:
        raise ValueError("La ruta no puede contener saltos de línea")
    for before, after in [
        ("\\", "\\\\"),
        ('"', '\\"'),
        ("`", "\\`"),
        ("$", "\\$"),
        ("%", "%%"),
    ]:
        text = text.replace(before, after)
    return '"' + text + '"'


def create_launcher(root=None, data_home=None):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    python = root / ".venv/bin/python"
    if not python.is_file():
        raise ValueError("Primero creá el entorno virtual .venv")
    directory = (
        Path(
            data_home
            or os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))
        )
        / "applications"
    )
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "ingenieria-lab.desktop"
    target.write_text(
        "[Desktop Entry]\nType=Application\nName=Ingeniería Lab\nComment=Laboratorios y cuaderno de ingeniería\n"
        + f"Exec={quote_exec(python)} {quote_exec(root / 'main.py')}\n"
        + f"Icon={root / 'docs/icon.svg'}\nTerminal=false\nCategories=Education;Math;\nStartupNotify=true\n",
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    print("Acceso directo:", create_launcher())
