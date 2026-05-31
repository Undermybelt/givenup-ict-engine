from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import ibkr_paper_roundtrip_smoke as smoke  # noqa: E402


class IbkrPaperRoundtripSmokeTests(unittest.TestCase):
    def test_rejects_live_ports_even_with_paper_account_prefix(self) -> None:
        with self.assertRaisesRegex(ValueError, "live IBKR port"):
            smoke.validate_paper_order_context(
                port=4001,
                managed_accounts=["DU1234567"],
                requested_account=None,
            )

    def test_requires_du_or_df_paper_account(self) -> None:
        with self.assertRaisesRegex(ValueError, "paper account"):
            smoke.validate_paper_order_context(
                port=4002,
                managed_accounts=["U1234567"],
                requested_account=None,
            )

    def test_selects_requested_paper_account_when_managed(self) -> None:
        context = smoke.validate_paper_order_context(
            port=4002,
            managed_accounts=["DU1111111", "DU2222222"],
            requested_account="DU2222222",
        )

        self.assertEqual(context.account, "DU2222222")
        self.assertEqual(context.account_type, "paper")

    def test_execution_requires_explicit_confirmation_and_exact_contract(self) -> None:
        args = SimpleNamespace(
            execute_paper_roundtrip=True,
            i_understand_paper_orders=False,
            local_symbol="NQM6",
            last_trade_date_or_contract_month="",
        )

        with self.assertRaisesRegex(ValueError, "explicit confirmation"):
            smoke.validate_execution_request(args)

        args.i_understand_paper_orders = True
        args.local_symbol = ""
        with self.assertRaisesRegex(ValueError, "exact futures contract"):
            smoke.validate_execution_request(args)

    def test_terminal_packet_is_fail_closed_for_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            packet = smoke.write_terminal_packet(
                root=root,
                status="dry_run_preflight_only",
                decision="paper_order_not_submitted",
                account="DU1234567",
                port=4002,
                client_id=37,
                contract={"symbol": "NQ", "secType": "FUT", "localSymbol": "NQM6"},
                order_events=[],
                execution_readback=None,
                blockers=["dry-run default"],
            )

            self.assertFalse(packet["promotion_allowed"])
            self.assertFalse(packet["trade_usable"])
            self.assertFalse(packet["update_goal"])
            self.assertEqual(packet["same_tree_practical_closure"], None)
            written = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(written["decision"], "paper_order_not_submitted")

    def test_order_status_event_records_cancel_diagnostics(self) -> None:
        trade = SimpleNamespace(
            orderStatus=SimpleNamespace(status="PreSubmitted", filled=0.0, remaining=1.0),
            fills=[],
            log=[
                SimpleNamespace(status="PendingSubmit", message="", errorCode=0),
                SimpleNamespace(status="PreSubmitted", message="will not be placed until market open", errorCode=399),
            ],
        )
        trade.isDone = lambda: False

        event = smoke.order_status_event(trade, "cancel_after_no_fill")

        self.assertEqual(event["action"], "cancel_after_no_fill")
        self.assertEqual(event["status"], "PreSubmitted")
        self.assertEqual(event["remaining"], 1.0)
        self.assertEqual(event["log_tail"][-1]["error_code"], 399)


if __name__ == "__main__":
    unittest.main()
