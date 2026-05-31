import unittest
from types import SimpleNamespace

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


class IbkrContractDetailsTests(unittest.TestCase):
    def test_parser_accepts_contract_details_probe_without_historical_fetch_args(self) -> None:
        parser = fetch_external.build_parser()

        args = parser.parse_args(
            [
                "ibkr-contract-details",
                "--symbol",
                "SIL",
                "--sec-type",
                "FUT",
                "--exchange",
                "COMEX",
                "--currency",
                "USD",
                "--last-trade-date",
                "202607",
                "--multiplier",
                "1000",
                "--output",
                "/tmp/sil_contract_details.json",
            ]
        )

        self.assertEqual(args.provider, "ibkr-contract-details")
        self.assertEqual(args.symbol, "SIL")
        self.assertEqual(args.sec_type, "FUT")

    def test_contract_detail_packet_preserves_futures_secdef_fields(self) -> None:
        args = SimpleNamespace(
            symbol="SIL",
            sec_type="FUT",
            exchange="COMEX",
            currency="USD",
            primary_exchange=None,
            last_trade_date="202607",
            multiplier="1000",
            strike=None,
            right=None,
        )
        contract = SimpleNamespace(
            conId=12345,
            symbol="SIL",
            secType="FUT",
            exchange="COMEX",
            currency="USD",
            lastTradeDateOrContractMonth="202607",
            multiplier="1000",
            localSymbol="SILN6",
            tradingClass="SIL",
        )
        detail = SimpleNamespace(
            contract=contract,
            minTick=0.005,
            marketRuleIds="123",
            tradingHours="20260530:1800-1700",
            liquidHours="20260530:1800-1700",
            timeZoneId="America/New_York",
        )

        packet = fetch_external._ibkr_contract_detail_packet(args, contract, [detail])

        self.assertEqual(packet["schema_version"], "ibkr-contract-details/v1")
        self.assertEqual(packet["request"]["symbol"], "SIL")
        self.assertEqual(packet["qualified_contract"]["multiplier"], "1000")
        self.assertEqual(packet["contract_details_count"], 1)
        self.assertEqual(packet["contract_details"][0]["minTick"], 0.005)
        self.assertEqual(packet["contract_details"][0]["contract"]["localSymbol"], "SILN6")
        self.assertEqual(packet["contract_details"][0]["tradingHours"], "20260530:1800-1700")
        self.assertEqual(packet["contract_details"][0]["liquidHours"], "20260530:1800-1700")


if __name__ == "__main__":
    unittest.main()
