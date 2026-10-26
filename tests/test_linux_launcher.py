import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "launcher", ROOT / "scripts/crear_acceso_directo.py"
)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_desktop_launcher_with_spaces_and_percent(tmp_path):
    root = tmp_path / "Ingeniería 100% laboratorio"
    (root / ".venv/bin").mkdir(parents=True)
    (root / ".venv/bin/python").write_text("placeholder")
    target = launcher.create_launcher(root, tmp_path / "data")
    text = target.read_text()
    assert "100%% laboratorio" in text and "Terminal=false" in text
    assert str(root / "docs/icon.svg") in text
    assert target == tmp_path / "data/applications/ingenieria-lab.desktop"


def test_shell_launchers_have_valid_syntax():
    for name in ("iniciar_linux.sh", "instalar_linux_mint.sh"):
        subprocess.run(["bash", "-n", str(ROOT / name)], check=True)
