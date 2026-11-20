#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Python 3 tidak ditemukan. Pasang Python 3.10+ terlebih dahulu.\n' >&2
  exit 1
fi

if ! python3 -c 'import venv' >/dev/null 2>&1; then
  printf 'Modul venv tidak tersedia. Di Kali/Debian, jalankan: sudo apt install python3-venv\n' >&2
  exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

printf '\nInstalasi selesai. Edit .env, isi REXA_API_KEY, lalu jalankan: .venv/bin/python cli.py\n'