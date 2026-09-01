import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .analysis import RequestEvent, summarize_routes


def load_events(path: Path) -> list[RequestEvent]:
    events: list[RequestEvent] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                events.append(
                    RequestEvent(
                        route=str(payload["route"]),
                        duration_ms=float(payload["duration_ms"]),
                        status=int(payload["status"]),
                    )
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid event on line {line_number}: {error}") from error
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize request latency JSONL")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps([asdict(item) for item in summarize_routes(load_events(args.path))], indent=2))


if __name__ == "__main__":
    main()

