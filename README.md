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
python3 -m unittest discover -s tests
```

The output is descriptive. It does not establish an SLO or statistical
significance, and low-volume routes should be interpreted cautiously.
Optional budget evaluation always uses a caller-supplied threshold and reports
`insufficient_samples` until the configured sample floor is reached.
