from __future__ import annotations

import json
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import mim_cost_window_event_builder as builder  # noqa: E402


class MimCostWindowEventBuilderTests(unittest.TestCase):
    def _write_csv(self, path: Path) -> None:
        start = datetime(2026, 5, 21, 13, 30, tzinfo=timezone.utc)
        lines = ["ts,open,high,low,close,volume"]
        price = 100.0
        for day in range(2):
            day_start = start + timedelta(days=day)
            for idx in range(90):
                if day == 0:
                    drift = 0.035 if idx < 30 else 0.025
                    volume = 1500 + idx * 8 if idx < 30 else 900 + idx * 2
                else:
                    drift = 0.001 if idx % 2 == 0 else -0.001
                    volume = 400
                open_ = price
                close = price + drift
                high = max(open_, close) + 0.025
                low = min(open_, close) - 0.020
                timestamp = (day_start + timedelta(minutes=idx)).isoformat().replace("+00:00", "Z")
                lines.append(f"{timestamp},{open_:.6f},{high:.6f},{low:.6f},{close:.6f},{volume:.2f}")
                price = close
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_build_events_preserves_regime_root_and_provider_labels(self) -> None:
        with TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "retained.csv"
            self._write_csv(csv_path)
            events = builder.build_event_rows(
                csv_path,
                symbol="TEST",
                provider="retained-real",
                market="US_EQ",
                product="single_stock",
                branch_path=(
                    "TrendExpansion -> IntradayMomentumCostWindow -> "
                    "mim_cost_window_regime_filter -> test_mim_cost_window_v1"
                ),
            )

        self.assertEqual(len(events), 2)
        first = events[0]
        self.assertEqual(first["branch_path"], "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_cost_window_v1")
        self.assertEqual(first["main_regime"], "TrendExpansion")
        self.assertEqual(first["symbol"], "TEST")
        self.assertEqual(first["provider"], "retained-real")
        self.assertEqual(first["base_timeframe"], "1m")
        self.assertEqual(first["context_timeframes"], ["5m", "15m", "30m", "1h", "4h", "1d"])
        self.assertEqual(first["side"], 1)
        self.assertEqual(first["triple_barrier_label"], 1)
        self.assertFalse(first["promotion_allowed"])
        self.assertFalse(first["trade_usable"])
        self.assertFalse(first["downstream_allowed"])
        self.assertEqual(events[1]["side"], 0)

    def test_cli_writes_jsonl_and_summary(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "retained.csv"
            out = tmp / "events.jsonl"
            summary = tmp / "summary.json"
            self._write_csv(csv_path)

            exit_code = builder.main(
                [
                    "--input-csv",
                    str(csv_path),
                    "--output-jsonl",
                    str(out),
                    "--summary-json",
                    str(summary),
                    "--symbol",
                    "TEST",
                    "--provider",
                    "retained-real",
                    "--market",
                    "US_EQ",
                    "--product",
                    "single_stock",
                    "--branch-path",
                    "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_cost_window_v1",
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(payload), 2)
            summary_payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["event_count"], 2)
            self.assertEqual(summary_payload["eligible_long_count"], 1)
            self.assertFalse(summary_payload["promotion_allowed"])

    def test_triple_barrier_label_starts_at_event_bar_not_session_open(self) -> None:
        with TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "retained.csv"
            start = datetime(2026, 5, 21, 13, 30, tzinfo=timezone.utc)
            lines = ["ts,open,high,low,close,volume"]
            for idx in range(90):
                timestamp = (start + timedelta(minutes=idx)).isoformat().replace("+00:00", "Z")
                if idx < 30:
                    open_ = 100.0 + idx * 0.04
                    close = open_ + 0.035
                    high = close + 0.025
                    low = open_ - 0.020
                    volume = 1800
                else:
                    open_ = close = high = low = 101.20
                    volume = 900
                lines.append(f"{timestamp},{open_:.6f},{high:.6f},{low:.6f},{close:.6f},{volume:.2f}")
            csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            events = builder.build_event_rows(
                csv_path,
                symbol="TEST",
                provider="retained-real",
                market="US_EQ",
                product="single_stock",
                branch_path="TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_cost_window_v1",
            )

        self.assertEqual(events[0]["side"], 1)
        self.assertEqual(events[0]["event_ts"], "2026-05-21T13:59:00+00:00")
        self.assertEqual(events[0]["triple_barrier_label"], 0)

    def test_module_cli_help_imports_from_package_context(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "support.scripts.research.mim_cost_window_event_builder",
                "--help",
            ],
            cwd=Path(__file__).resolve().parents[4],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Build MIM cost-window event rows", result.stdout)


if __name__ == "__main__":
    unittest.main()
