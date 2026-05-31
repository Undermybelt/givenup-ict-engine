from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import ibkr_execution_readback as readback  # noqa: E402


class IbkrExecutionReadbackTests(unittest.TestCase):
    def test_fill_to_readback_row_preserves_exec_and_commission_evidence(self) -> None:
        fill = SimpleNamespace(
            contract=SimpleNamespace(
                conId=750150196,
                symbol="NQ",
                secType="FUT",
                exchange="CME",
                currency="USD",
                localSymbol="NQM6",
            ),
            execution=SimpleNamespace(
                execId="0000e2.1",
                time=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
                side="BOT",
                shares=1.0,
                price=18800.25,
                orderId=17,
                permId=9917,
                clientId=42,
                exchange="CME",
            ),
            commissionReport=SimpleNamespace(
                execId="0000e2.1",
                commission=2.25,
                currency="USD",
                realizedPNL=0.0,
            ),
        )

        row = readback.fill_to_readback_row(fill)

        self.assertEqual(row["contract"]["symbol"], "NQ")
        self.assertEqual(row["contract"]["localSymbol"], "NQM6")
        self.assertEqual(row["exec_id"], "0000e2.1")
        self.assertEqual(row["time"], "2026-05-15T10:00:00Z")
        self.assertEqual(row["side"], "BOT")
        self.assertAlmostEqual(row["commission"], 2.25)
        self.assertTrue(row["commission_report_present"])
        self.assertTrue(row["broker_fill_evidence"])

    def test_fill_without_commission_report_is_diagnostic_not_broker_feedback(self) -> None:
        fill = SimpleNamespace(
            contract=SimpleNamespace(conId=1, symbol="NQ", secType="FUT", exchange="CME", currency="USD", localSymbol="NQM6"),
            execution=SimpleNamespace(
                execId="0000e2.1",
                time=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
                side="BOT",
                shares=1.0,
                price=18800.25,
                orderId=17,
                permId=9917,
                clientId=42,
                exchange="CME",
            ),
            commissionReport=SimpleNamespace(execId="", commission=0.0, currency="", realizedPNL=0.0),
        )

        row = readback.fill_to_readback_row(fill)

        self.assertIsNone(row["commission"])
        self.assertIsNone(row["realized_pnl"])
        self.assertFalse(row["commission_report_present"])
        self.assertFalse(row["broker_fill_evidence"])

    def test_write_readback_packet_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "ibkr_execution_readback.json"
            args = SimpleNamespace(
                host="127.0.0.1",
                port=4002,
                symbol="NQ",
                sec_type="FUT",
                exchange="CME",
                side="",
                account="",
                time="",
                local_symbol="",
                filter_client_id=0,
                require_commission_report=True,
            )

            packet = readback.write_readback_packet(
                output=output,
                rows=[],
                args=args,
                selected_client_id=24,
                attempted_client_id_conflicts=[],
            )

            self.assertEqual(packet["execution_rows_total"], 0)
            self.assertFalse(packet["promotion_allowed"])
            self.assertFalse(packet["trade_usable"])
            self.assertFalse(packet["update_goal"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["schema_version"], "ibkr-execution-readback/v1")


if __name__ == "__main__":
    unittest.main()
