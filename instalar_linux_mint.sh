#!/usr/bin/env bash
# Instalación local en venv; --sistema instala dependencias de Mint con apt.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
case "${1:-}" in
  --sistema)
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip libgl1 libegl1 libxcb-cursor0 \
      libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
      libxcb-render-util0 libxcb-xinerama0 ngspice
    ;;
  '') ;;
  *) echo 'Uso: bash instalar_linux_mint.sh [--sistema]' >&2; exit 2 ;;
esac
lab_python="${PYTHON_BIN:-}"
if [[ -z "$lab_python" ]]; then
  for candidate in python3 python3.14 python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,15)))' 2>/dev/null; then
      lab_python="$candidate"
      break
    fi
  done
fi
if [[ -z "$lab_python" ]] || ! "$lab_python" -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,15)))'; then
  echo 'Se necesita Python 3.11–3.14. Mint 22 trae Python 3.12.' >&2
  echo 'En Mint 21, indicá un Python compatible ya instalado: PYTHON_BIN=python3.12 bash instalar_linux_mint.sh' >&2
  echo 'No reemplaces el Python del sistema.' >&2
  exit 1
fi
if [[ ! -d .venv ]]; then
  "$lab_python" -m venv .venv
fi
if [[ ! -x .venv/bin/python ]] || ! .venv/bin/python -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,15)))'; then
  echo 'La carpeta .venv existente no es compatible. Conservála aparte y repetí la instalación para crear una nueva.' >&2
  exit 1
fi
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip check
.venv/bin/python scripts/crear_acceso_directo.py
if ! command -v ngspice >/dev/null; then
  echo 'Ngspice no está en PATH. Los dos laboratorios SPICE requieren: sudo apt install ngspice'
fi
printf '\nInstalación completa. Abrí Ingeniería Lab desde el menú o ejecutá: bash iniciar_linux.sh\n'
