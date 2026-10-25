from dataclasses import dataclass
from math import ceil, isfinite
from statistics import median
from typing import Iterable, Optional


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
    non_error_count: int
    non_error_median_ms: Optional[float]
    non_error_p95_ms: Optional[float]
    error_count: int
    error_median_ms: Optional[float]
    error_p95_ms: Optional[float]
    client_error_count: int
    server_error_count: int
    client_error_rate: float
    server_error_rate: float

    @property
    def error_rate(self) -> float:
        """Backward-compatible alias for the original server-error metric."""
        return self.server_error_rate


@dataclass(frozen=True)
class BudgetEvaluation:
    route: str
    budget_ms: float
    observed_p95_ms: Optional[float]
    headroom_ms: Optional[float]
    utilization: Optional[float]
    sample_count: int
    minimum_samples: int
    scope: str
    status: str


def summarize_routes(events: Iterable[RequestEvent]) -> list[RouteSummary]:
    grouped: dict[str, list[RequestEvent]] = {}
    for event in events:
        grouped.setdefault(event.route, []).append(event)

    summaries: list[RouteSummary] = []
    for route, route_events in sorted(grouped.items()):
        durations = sorted(event.duration_ms for event in route_events)
        p95_index = ceil(0.95 * len(durations)) - 1
        non_error_durations = sorted(
            event.duration_ms for event in route_events if event.status < 400
        )
        non_error_p95_index = (
            ceil(0.95 * len(non_error_durations)) - 1
            if non_error_durations
            else None
        )
        error_durations = sorted(
            event.duration_ms for event in route_events if event.status >= 400
        )
        error_p95_index = (
            ceil(0.95 * len(error_durations)) - 1 if error_durations else None
        )
        client_errors = sum(400 <= event.status < 500 for event in route_events)
        server_errors = sum(event.status >= 500 for event in route_events)
        summaries.append(
            RouteSummary(
                route=route,
                count=len(route_events),
                median_ms=median(durations),
                p95_ms=durations[p95_index],
                maximum_ms=durations[-1],
                non_error_count=len(non_error_durations),
                non_error_median_ms=(
                    median(non_error_durations) if non_error_durations else None
                ),
                non_error_p95_ms=(
                    non_error_durations[non_error_p95_index]
                    if non_error_p95_index is not None
                    else None
                ),
                error_count=len(error_durations),
                error_median_ms=(
                    median(error_durations) if error_durations else None
                ),
                error_p95_ms=(
                    error_durations[error_p95_index]
                    if error_p95_index is not None
                    else None
                ),
                client_error_count=client_errors,
                server_error_count=server_errors,
                client_error_rate=client_errors / len(route_events),
                server_error_rate=server_errors / len(route_events),
            )
        )
    return summaries


def evaluate_budgets(
    summaries: Iterable[RouteSummary],
    budget_ms: float,
    *,
    minimum_samples: int = 20,
    scope: str = "all",
) -> list[BudgetEvaluation]:
    if not isfinite(budget_ms) or budget_ms <= 0:
        raise ValueError("budget_ms must be finite and positive")
    if minimum_samples < 1:
        raise ValueError("minimum_samples must be positive")
    if scope not in {"all", "non_error", "error"}:
        raise ValueError("scope must be 'all', 'non_error', or 'error'")
    evaluations: list[BudgetEvaluation] = []
    for summary in summaries:
        if scope == "all":
            sample_count = summary.count
            observed_p95_ms = summary.p95_ms
        elif scope == "non_error":
            sample_count = summary.non_error_count
            observed_p95_ms = summary.non_error_p95_ms
        else:
            sample_count = summary.error_count
            observed_p95_ms = summary.error_p95_ms

        if sample_count < minimum_samples:
            status = "insufficient_samples"
        elif observed_p95_ms is not None and observed_p95_ms <= budget_ms:
            status = "within_budget"
        else:
            status = "over_budget"
        evaluations.append(
            BudgetEvaluation(
                route=summary.route,
                budget_ms=budget_ms,
                observed_p95_ms=observed_p95_ms,
                headroom_ms=(
                    budget_ms - observed_p95_ms
                    if observed_p95_ms is not None
                    else None
                ),
                utilization=(
                    observed_p95_ms / budget_ms
                    if observed_p95_ms is not None
                    else None
                ),
                sample_count=sample_count,
                minimum_samples=minimum_samples,
                scope=scope,
                status=status,
            )
        )
    return evaluations
