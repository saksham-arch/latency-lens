from dataclasses import dataclass
from math import ceil, isfinite
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class RequestEvent:
    route: str
    duration_ms: float
    status: int

    def __post_init__(self) -> None:
        if not self.route.strip():
            raise ValueError("route must not be empty")
        if not isfinite(self.duration_ms) or self.duration_ms < 0:
            raise ValueError("duration_ms must be finite and non-negative")
        if not 100 <= self.status <= 599:
            raise ValueError("status must be between 100 and 599")


@dataclass(frozen=True)
class RouteSummary:
    route: str
    count: int
    median_ms: float
    p95_ms: float
    maximum_ms: float
    error_rate: float


def summarize_routes(events: Iterable[RequestEvent]) -> list[RouteSummary]:
    grouped: dict[str, list[RequestEvent]] = {}
    for event in events:
        grouped.setdefault(event.route, []).append(event)

    summaries: list[RouteSummary] = []
    for route, route_events in sorted(grouped.items()):
        durations = sorted(event.duration_ms for event in route_events)
        p95_index = ceil(0.95 * len(durations)) - 1
        errors = sum(event.status >= 500 for event in route_events)
        summaries.append(
            RouteSummary(
                route=route,
                count=len(route_events),
                median_ms=median(durations),
                p95_ms=durations[p95_index],
                maximum_ms=durations[-1],
                error_rate=errors / len(route_events),
            )
        )
    return summaries

