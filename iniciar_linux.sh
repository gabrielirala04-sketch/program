#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Primero seguí la instalación del README para crear .venv e instalar las dependencias.' >&2
  exit 1
fi
exec .venv/bin/python main.py
