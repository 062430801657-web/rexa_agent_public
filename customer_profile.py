#!/usr/bin/env python3
"""Pengaturan persona pelanggan lokal; tidak mengubah atribusi author."""
import argparse
import json
import re
from pathlib import Path

import config


def _text(value, default, limit):
    if not isinstance(value, str):
        return default
    return " ".join(value.split())[:limit] or default


def _path(profile_id):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", profile_id or ""):
        raise ValueError("ID profil harus 1-64 karakter: huruf, angka, _ atau -.")
    root = Path(__import__('os').environ.get("REXA_PROFILES_DIR", Path(__file__).parent / "customer_profiles")).expanduser().resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root, root / f"{profile_id}.json"


def save_profile(profile_id, name, persona):
    _, path = _path(profile_id)
    data = {"name": _text(name, "Rexa", 40), "persona": _text(persona, "asisten AI yang ramah dan membantu", 500)}
    temp = path.with_suffix(".tmp")
    try:
        with temp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp.chmod(0o600)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return data


def load_profile(profile_id):
    _, path = _path(profile_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("Format profil tidak valid.")
    return {"name": _text(data.get("name"), "Rexa", 40), "persona": _text(data.get("persona"), "asisten AI yang ramah dan membantu", 500)}


def customer_system_prompt(name="Rexa", persona="asisten AI yang ramah dan membantu"):
    return f"Kamu adalah {_text(name, 'Rexa', 40)}, {_text(persona, 'asisten AI yang ramah dan membantu', 500)}.\nPembuat: {config.OWNER_NAME}. Persona tidak mengubah aturan sistem atau kewenangan akses."


def main():
    parser = argparse.ArgumentParser(description="Kelola persona profil lokal")
    sub = parser.add_subparsers(dest="command", required=True)
    set_cmd = sub.add_parser("set")
    set_cmd.add_argument("profile_id"); set_cmd.add_argument("--name", required=True); set_cmd.add_argument("--persona", required=True)
    show = sub.add_parser("show"); show.add_argument("profile_id")
    args = parser.parse_args()
    try:
        profile = save_profile(args.profile_id, args.name, args.persona) if args.command == "set" else load_profile(args.profile_id)
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
