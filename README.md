# latency-lens

Dependency-free tools for turning request timing events into inspectable route
summaries. The first increment reads JSON Lines events and reports count,
median, nearest-rank p95, maximum latency, and error rate for each route.

Each input line must contain `route`, `duration_ms`, and `status`:

```json
{"route":"GET /items","duration_ms":12.4,"status":200}
```

```bash
PYTHONPATH=src python3 -m latency_lens requests.jsonl
PYTHONPATH=src python3 -m latency_lens requests.jsonl --budget-ms 250 --minimum-samples 20
PYTHONPATH=src python3 -m latency_lens requests.jsonl --budget-ms 250 --budget-scope non_error
python3 -m unittest discover -s tests
```

The output is descriptive. It does not establish an SLO or statistical
significance, and low-volume routes should be interpreted cautiously.
Optional budget evaluation always uses a caller-supplied threshold and reports
`insufficient_samples` until the configured sample floor is reached.
It also reports signed `headroom_ms` (budget minus observed p95) and
`utilization` (observed p95 divided by the budget). A negative headroom or
utilization above 1 indicates a breach. These values are descriptive even when
the status is `insufficient_samples`; the sample status remains the confidence
guardrail.

Client-error (4xx) and server-error (5xx) counts and rates are reported
separately. The raw counts keep small denominators visible, while the rates aid
comparison across routes. This keeps caller mistakes from being silently
merged with service failures.
Each route also reports the count, median, and nearest-rank p95 for non-error
responses (status below 400). Those fields are `null` when a route has no
non-error observations. Budget evaluation uses all responses by default;
`--budget-scope non_error` instead uses the non-error count and p95. This can
separate successful-response latency from error-path behavior, but both scopes
should be inspected rather than using one to conceal the other.
