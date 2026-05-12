from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from klasbot.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
from klasbot.ollama_client import OllamaClient
from klasbot.prompts import build_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Klasbot prompt against Ollama.")
    parser.add_argument("--kind", choices=["lesson_plan", "assessment"], default="lesson_plan")
    parser.add_argument("--format", default="DLP")
    parser.add_argument("--subject")
    parser.add_argument("--topic")
    parser.add_argument("--grade", action="append", dest="grade_levels", default=[])
    parser.add_argument("--resource", action="append", dest="resources", default=[])
    parser.add_argument("--json", dest="json_path", help="Read inputs from a JSON file instead of flags")
    return parser.parse_args()


def load_inputs(args: argparse.Namespace) -> dict:
    if args.json_path:
        return json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    if not args.subject or not args.topic:
        raise SystemExit("--subject and --topic are required unless --json is used")
    return {
        "kind": args.kind,
        "format": args.format,
        "subject": args.subject,
        "topic": args.topic,
        "grade_levels": args.grade_levels,
        "resources": args.resources,
    }


async def main() -> None:
    args = parse_args()
    inputs = load_inputs(args)
    prompt = build_prompt(inputs)
    client = OllamaClient(OLLAMA_BASE_URL, OLLAMA_TIMEOUT_SECONDS)

    print(f"Model: {OLLAMA_MODEL}")
    print(f"Subject: {inputs['subject']} | Topic: {inputs['topic']}")
    print("---")

    started = time.perf_counter()
    token_count = 0
    async for token in client.stream_generate(OLLAMA_MODEL, prompt):
        token_count += 1
        print(token, end="", flush=True)
    elapsed = max(time.perf_counter() - started, 0.001)
    print()
    print("---")
    print(f"Chunks: {token_count} | Elapsed: {elapsed:.1f}s | Chunks/sec: {token_count / elapsed:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
