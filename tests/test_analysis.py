import unittest

from latency_lens import RequestEvent, evaluate_budgets, summarize_routes


class RouteSummaryTests(unittest.TestCase):
    def test_groups_and_summarizes_routes(self) -> None:
        events = [
            RequestEvent("GET /a", 10, 200),
            RequestEvent("GET /a", 20, 500),
            RequestEvent("GET /a", 15, 200),
            RequestEvent("GET /a", 12, 404),
            RequestEvent("GET /b", 5, 204),
        ]
        a, b = summarize_routes(events)
        self.assertEqual((a.route, a.count, a.median_ms), ("GET /a", 4, 13.5))
        self.assertEqual(a.p95_ms, 20)
        self.assertEqual(a.client_error_rate, 0.25)
        self.assertEqual(a.server_error_rate, 0.25)
        self.assertEqual(a.error_rate, a.server_error_rate)
        self.assertEqual((b.route, b.maximum_ms), ("GET /b", 5))

    def test_empty_input_has_no_summaries(self) -> None:
        self.assertEqual(summarize_routes([]), [])

    def test_rejects_invalid_events(self) -> None:
        for args in (("", 1, 200), ("GET /", -1, 200), ("GET /", 1, 99)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                RequestEvent(*args)

    def test_evaluates_user_supplied_latency_budget(self) -> None:
        summaries = summarize_routes(
            [RequestEvent("fast", 10, 200), RequestEvent("slow", 30, 200)]
        )
        evaluations = evaluate_budgets(summaries, 20, minimum_samples=1)
        self.assertEqual([item.status for item in evaluations], ["within_budget", "over_budget"])

    def test_marks_low_volume_route_as_insufficient(self) -> None:
        summary = summarize_routes([RequestEvent("GET /", 10, 200)])
        self.assertEqual(
            evaluate_budgets(summary, 20, minimum_samples=2)[0].status,
            "insufficient_samples",
        )

    def test_validates_budget_configuration(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_budgets([], 0)
        with self.assertRaises(ValueError):
            evaluate_budgets([], 10, minimum_samples=0)


if __name__ == "__main__":
    unittest.main()
