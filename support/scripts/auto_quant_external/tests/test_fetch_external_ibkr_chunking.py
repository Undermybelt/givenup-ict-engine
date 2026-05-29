import unittest

from support.scripts.auto_quant_external import fetch_external


class IbkrHistoricalChunkingTests(unittest.TestCase):
    def test_one_minute_thirty_day_request_is_split_into_daily_chunks(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("1 min", "30 D")

        self.assertEqual(len(chunks), 30)
        self.assertEqual({chunk.duration for chunk in chunks}, {"1 D"})

    def test_five_minute_three_month_request_is_split_into_weekly_chunks(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("5 mins", "3 M")

        self.assertGreaterEqual(len(chunks), 12)
        self.assertEqual({chunk.duration for chunk in chunks}, {"1 W"})

    def test_daily_two_year_request_stays_single_chunk(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("1 day", "2 Y")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].duration, "2 Y")

    def test_bar_size_matching_is_case_and_whitespace_insensitive(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("  1   MIN  ", "30 D")

        self.assertEqual(len(chunks), 30)
        self.assertEqual({chunk.duration for chunk in chunks}, {"1 D"})

    def test_ibkr_port_auto_probe_selects_reachable_gateway(self) -> None:
        port = fetch_external._resolve_ibkr_gateway_port(
            "127.0.0.1",
            None,
            purpose="ibkr-historical",
            probe=lambda _host, candidate: candidate == 4002,
        )

        self.assertEqual(port, 4002)

    def test_ibkr_port_auto_probe_respects_explicit_port(self) -> None:
        port = fetch_external._resolve_ibkr_gateway_port(
            "127.0.0.1",
            7496,
            purpose="ibkr-historical",
            probe=lambda _host, _candidate: False,
        )

        self.assertEqual(port, 7496)


class IbkrHistoricalRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_on_empty_bars_reconnects_once_and_returns_second_result(self) -> None:
        attempts: list[str] = []
        reconnects: list[str] = []

        async def request_once():
            attempts.append("request")
            if len(attempts) == 1:
                return []
            return ["bar"]

        async def reconnect_once():
            reconnects.append("reconnect")

        bars, used_attempts = await fetch_external._ibkr_retry_empty_historical_request(
            request_once,
            reconnect_once,
        )

        self.assertEqual(bars, ["bar"])
        self.assertEqual(used_attempts, 2)
        self.assertEqual(len(reconnects), 1)

    async def test_retry_on_empty_bars_stops_after_max_attempts(self) -> None:
        attempts: list[str] = []
        reconnects: list[str] = []

        async def request_once():
            attempts.append("request")
            return []

        async def reconnect_once():
            reconnects.append("reconnect")

        bars, used_attempts = await fetch_external._ibkr_retry_empty_historical_request(
            request_once,
            reconnect_once,
        )

        self.assertEqual(bars, [])
        self.assertEqual(used_attempts, 2)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(len(reconnects), 1)

    async def test_retry_on_empty_bars_can_stop_without_reconnect(self) -> None:
        attempts: list[str] = []
        reconnects: list[str] = []

        async def request_once():
            attempts.append("request")
            return []

        async def reconnect_once():
            reconnects.append("reconnect")

        bars, used_attempts = await fetch_external._ibkr_retry_empty_historical_request(
            request_once,
            reconnect_once,
            should_retry=lambda: False,
        )

        self.assertEqual(bars, [])
        self.assertEqual(used_attempts, 1)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(len(reconnects), 0)


class IbkrRequestErrorClassificationTests(unittest.TestCase):
    def test_different_ip_request_error_is_not_retryable(self) -> None:
        classification = fetch_external._ibkr_classify_historical_request_error(
            162,
            "Trading TWS session is connected from a different IP address",
        )

        self.assertEqual(classification.category, "broker_session_authority_blocked")
        self.assertFalse(classification.retryable)

    def test_generic_request_error_stays_retryable(self) -> None:
        classification = fetch_external._ibkr_classify_historical_request_error(
            504,
            "Not connected",
        )

        self.assertEqual(classification.category, "request_error")
        self.assertTrue(classification.retryable)


if __name__ == "__main__":
    unittest.main()
