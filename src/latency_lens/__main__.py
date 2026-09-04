import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .analysis import RequestEvent, evaluate_budgets, summarize_routes


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
    parser.add_argument("--budget-ms", type=float)
    parser.add_argument("--minimum-samples", type=int, default=20)
    args = parser.parse_args()
    summaries = summarize_routes(load_events(args.path))
    payload = [asdict(item) for item in summaries]
    if args.budget_ms is not None:
        evaluations = evaluate_budgets(
            summaries, args.budget_ms, minimum_samples=args.minimum_samples
        )
        for item, evaluation in zip(payload, evaluations):
            item["budget"] = asdict(evaluation)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
