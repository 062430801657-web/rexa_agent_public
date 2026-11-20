import argparse
import os
import sqlite3
import sys
from pathlib import Path

from core.agent import RexaAgent


def show_dashboard():
    import config

    db_path = Path(config.DB_PATH)
    if db_path.exists():
        try:
            with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3) as conn:
                counts = {
                    table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("memories", "messages", "tasks", "evolution_log")
                }
        except sqlite3.Error as exc:
            print(f"Database tidak terbaca: {exc}", file=sys.stderr)
            return 1
    else:
        counts = dict.fromkeys(("memories", "messages", "tasks", "evolution_log"), 0)

    width = 56
    def row(text):
        text = str(text)
        if len(text) > width:
            text = text[:width - 1] + "…"
        print("│" + text.ljust(width) + "│")

    title = f" {config.AGENT_NAME.upper()} — AI ASSISTANT "
    print("╭" + "─" * width + "╮")
    row(title.center(width))
    print("├" + "─" * width + "┤")
    row(f"  Model cepat    {config.FAST_MODEL}")
    row(f"  Model mendalam {config.DEEP_REASONING_MODEL}")
    row(f"  Penyedia API   {config.API_BASE_URL}")
    print("├" + "─" * width + "┤")
    row(f"  Memori {counts['memories']}    Pesan tersimpan {counts['messages']}")
    row(f"  Tugas {counts['tasks']}    Catatan evolusi {counts['evolution_log']}")
    skills_dir = Path(os.environ.get("REXA_SKILLS_DIR", Path(__file__).parent / "skills")).expanduser()
    skill_count = sum(1 for _ in skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else 0
    row(f"  Skills lokal {skill_count}    Python {sys.version_info.major}.{sys.version_info.minor}")
    row(f"  Database {db_path}")
    print("├" + "─" * width + "┤")
    row("  Status: lokal · API key " + ("terpasang" if config.API_KEY else "belum diatur"))
    print("╰" + "─" * width + "╯")
    print("Jalankan `python cli.py` untuk mulai chat.\n")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Rexa AI")
    parser.add_argument("--deep", action="store_true", help="Pakai model reasoning")
    parser.add_argument("--session", default="default", help="ID sesi lokal")
    parser.add_argument("--message", help="Kirim satu pesan lalu keluar")
    parser.add_argument("--dashboard", action="store_true", help="Tampilkan ringkasan instalasi lokal")
    args = parser.parse_args()
    if args.dashboard:
        return show_dashboard()
    if not args.message and not sys.stdin.isatty():
        return show_dashboard()
    try:
        agent = RexaAgent(deep_reasoning=args.deep)
    except Exception as exc:
        parser.exit(2, f"Gagal memulai Rexa: {exc}\nAtur REXA_API_KEY di environment.\n")
    if args.message:
        print(agent.run(args.message, session_id=args.session))
        return
    print("Rexa siap. Ketik /exit untuk keluar.")
    while True:
        try:
            text = input("\nKamu> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in {"/exit", "/quit"}:
            break
        if text:
            try:
                print(f"\n{os.environ.get('REXA_AGENT_NAME', 'Rexa')}> {agent.run(text, session_id=args.session)}")
            except Exception as exc:
                print(f"Rexa gagal memproses pesan: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
