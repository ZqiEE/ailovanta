from __future__ import annotations

import argparse

import httpx


EVENTS = [
    {"event_type": "chat", "quantity": 1, "source": "demo"},
    {"event_type": "chat", "quantity": 2, "source": "demo"},
    {"event_type": "training", "quantity": 5, "source": "demo"},
    {"event_type": "dashboard", "quantity": 1, "source": "demo"},
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create demo usage events")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="local")
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        for event in EVENTS:
            response = client.post(f"{api}/usage/events", json={"user_id": args.user_id, **event})
            response.raise_for_status()
            print(response.json())
        summary = client.get(f"{api}/usage/summary", params={"user_id": args.user_id})
        summary.raise_for_status()
        print("summary:", summary.json())


if __name__ == "__main__":
    main()
