from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from klasbot import db
from klasbot.curriculum import ingest_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import normalized curriculum JSON into SQLite.")
    parser.add_argument("paths", nargs="+", help="JSON files or folders containing JSON files")
    return parser.parse_args()


def expand_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.json")))
        else:
            paths.append(path)
    return paths


def main() -> None:
    args = parse_args()
    db.init_db()
    for path in expand_paths(args.paths):
        document = ingest_json(source_path=path)
        summary = document.get("parse_summary", {})
        print(
            f"Imported {document['subject']}: {document['unit_count']} units, "
            f"confidence {summary.get('average_confidence', 0)}, "
            f"warnings {summary.get('warning_count', 0)}"
        )


if __name__ == "__main__":
    main()
