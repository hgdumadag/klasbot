from __future__ import annotations

import argparse
import json
from http.cookiejar import CookieJar
from urllib import request


class JsonClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookies = CookieJar()
        self.opener = request.build_opener(request.HTTPCookieProcessor(self.cookies))

    def get(self, path: str) -> dict:
        with self.opener.open(f"{self.base_url}{path}", timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def post(self, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload or {}).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple Klasbot API smoke test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()

    client = JsonClient(args.base_url)
    print("healthz", client.get("/healthz"))
    print("login", client.post("/api/auth/login", {"pin": args.pin})["teacher"])
    print("me", client.get("/api/me")["teacher"])
    print("ollama", client.get("/api/ollama/status"))
    print("library_count", len(client.get("/api/library")["outputs"]))


if __name__ == "__main__":
    main()
