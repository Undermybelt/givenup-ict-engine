from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import fetch_external as fetch  # noqa: E402


class HubbleRequestTests(unittest.TestCase):
    def test_cn_request_maps_interval_and_dates(self) -> None:
        path, params = fetch.build_hubble_kline_request(
            market="cn",
            symbol="000001.SZ",
            interval="1w",
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 31),
        )

        self.assertEqual(path, "/api/v2/cnstock/stocks")
        self.assertEqual(params["symbol"], "000001.SZ")
        self.assertEqual(params["interval"], "weekly")
        self.assertEqual(params["startDate"], "20240101")
        self.assertEqual(params["endDate"], "20240131")

    def test_hk_request_rejects_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not support --limit"):
            fetch.build_hubble_kline_request(
                market="hk",
                symbol="00700.HK",
                interval="1d",
                start=datetime(2024, 3, 1),
                end=datetime(2024, 4, 5),
                limit=10,
            )

    def test_crypto_request_requires_exchange(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --exchange"):
            fetch.build_hubble_kline_request(
                market="crypto",
                symbol="BTCUSDT",
                interval="1d",
                limit=100,
            )


class HubblePayloadTests(unittest.TestCase):
    def test_parse_hubble_payload_reads_nested_data_rows(self) -> None:
        frame = fetch.parse_hubble_kline_payload(
            {
                "symbol": "000001.SZ",
                "data": [
                    {
                        "time": 1704067200000,
                        "open": 10.5,
                        "high": 10.8,
                        "low": 10.4,
                        "close": 10.7,
                        "volume": 1234567,
                    }
                ],
            }
        )

        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["close"], 10.7)
        self.assertEqual(frame.iloc[0]["volume"], 1234567.0)
        self.assertEqual(str(frame.iloc[0]["date"]), "2024-01-01 00:00:00+00:00")

    def test_parse_hubble_payload_accepts_list_rows_and_yyyymmdd_dates(self) -> None:
        frame = fetch.parse_hubble_kline_payload(
            {
                "result": {
                    "list": [
                        ["20240102", "1.0", "2.0", "0.5", "1.5", "10"],
                        ["20240101", "0.9", "1.9", "0.4", "1.4", "9"],
                    ]
                }
            }
        )

        self.assertEqual(list(frame["close"]), [1.4, 1.5])
        self.assertEqual(list(frame["volume"]), [9.0, 10.0])
        self.assertEqual(str(frame.iloc[0]["date"]), "2024-01-01 00:00:00+00:00")


class HubbleEnvTests(unittest.TestCase):
    def test_from_env_uses_upstream_default_key_when_override_missing(self) -> None:
        with mock.patch.dict(
            fetch.os.environ,
            {fetch.HUBBLE_BASE_URL_ENV: "http://example.test:3101"},
            clear=True,
        ):
            client = fetch.HubbleFetcher.from_env()

        self.assertEqual(client.base_url, "http://example.test:3101")
        self.assertEqual(
            client.session.headers["X-API-Key"],
            fetch.HUBBLE_DEFAULT_API_KEY,
        )

    def test_from_env_prefers_explicit_key_override(self) -> None:
        with mock.patch.dict(
            fetch.os.environ,
            {
                fetch.HUBBLE_BASE_URL_ENV: "http://example.test:3101",
                fetch.HUBBLE_API_KEY_ENV: "override-key",
            },
            clear=True,
        ):
            client = fetch.HubbleFetcher.from_env()

        self.assertEqual(client.session.headers["X-API-Key"], "override-key")


if __name__ == "__main__":
    unittest.main()
