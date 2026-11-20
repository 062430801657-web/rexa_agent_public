# Rexa Agent

Asisten AI Python dengan memori SQLite lokal, percakapan CLI, tool web/memori, dan pemuat skills lokal.

## Instalasi

Python 3.10+ diperlukan. Linux/macOS/WSL:

```bash
./install.sh
```

Lalu edit `.env`, isi `REXA_API_KEY` dengan API key milikmu. Jalankan:

```bash
.venv/bin/python cli.py
```

Windows PowerShell: buat venv (`py -m venv .venv`), pasang dependensi (`.venv\Scripts\python -m pip install -r requirements.txt`), salin `.env.example` menjadi `.env`, isi API key, lalu jalankan `.venv\Scripts\python cli.py`.

Jalankan `python cli.py --message "Halo"` untuk satu pesan. Skill hanya dimuat dari direktori instalasi `skills/` (atau `REXA_SKILLS_DIR`); salin hanya skills yang sudah diaudit.

## Data

Database memori dibuat lokal pada `REXA_DB_PATH` (default `./rexa.db`) dan tidak untuk dikomit.
