#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

printf '\nInstalasi selesai. Edit .env, isi REXA_API_KEY, lalu jalankan: .venv/bin/python cli.py\n'