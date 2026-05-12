from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from klasbot import db
from klasbot.auth import hash_pin


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an initial Klasbot admin teacher.")
    parser.add_argument("--name", required=True, help="Admin teacher name")
    parser.add_argument("--pin", required=True, help="Admin PIN")
    args = parser.parse_args()

    db.init_db()
    existing_admins = [teacher for teacher in db.list_teachers() if teacher["is_admin"]]
    if existing_admins:
        names = ", ".join(teacher["name"] for teacher in existing_admins)
        raise SystemExit(f"Admin already exists: {names}")

    teacher = db.create_teacher(args.name, hash_pin(args.pin), is_admin=True)
    print(f"Created admin teacher #{teacher['id']}: {teacher['name']}")


if __name__ == "__main__":
    main()
