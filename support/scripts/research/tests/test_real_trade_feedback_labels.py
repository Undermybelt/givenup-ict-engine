from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import real_trade_feedback_labels as builder  # noqa: E402


def _ts_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000)


class RealTradeFeedbackLabelsTests(unittest.TestCase):
    def test_build_labels_maps_trade_wire_with_floor_alignment(self) -> None:
        candles = [
            {"timestamp": "2026-05-15T10:00:00Z", "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0},
            {"timestamp": "2026-05-15T10:05:00Z", "open": 100.0, "high": 101.5, "low": 99.9, "close": 101.0},
            {"timestamp": "2026-05-15T10:10:00Z", "open": 101.0, "high": 102.5, "low": 100.8, "close": 102.0},
            {"timestamp": "2026-05-15T10:15:00Z", "open": 102.0, "high": 103.5, "low": 101.8, "close": 103.0},
        ]
        trade_wire = [
            {
                "trade_id": "trade-1",
                "open_ts_ms": _ts_ms("2026-05-15T10:05:00Z"),
                "close_ts_ms": _ts_ms("2026-05-15T10:20:00Z"),
                "direction": "Bull",
                "pnl": 10.0,
                "structural_feedback": {"exit_reason": "roi"},
                "regime_profit_branch_path": "TrendExpansion -> SessionLiquidity -> factor -> factor_v1",
                "main_regime": "TrendExpansion",
                "sub_regime": "SessionLiquidity",
                "sub_sub_regime_or_profit_factor": "factor",
                "profit_factor": "factor_v1",
            }
        ]

        labels = builder.build_labels(
            candles=candles,
            trade_wire=trade_wire,
            sl_mult=0.01,
            max_alignment_gap_bars=3,
        )

        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0]["trade_id"], "trade-1")
        self.assertEqual(labels[0]["entry_index"], 1)
        self.assertEqual(labels[0]["exit_index"], 3)
        self.assertEqual(labels[0]["barrier_hit"], "roi")
        self.assertEqual(labels[0]["side"], 1)
        self.assertEqual(labels[0]["meta_label"], 1)
        self.assertAlmostEqual(labels[0]["entry_price"], 101.0)
        self.assertAlmostEqual(labels[0]["exit_price"], 103.0)
        self.assertAlmostEqual(labels[0]["gross_return"], (103.0 - 101.0) / 101.0)
        self.assertAlmostEqual(labels[0]["realized_R"], ((103.0 - 101.0) / 101.0) / 0.01)

    def test_cli_writes_labels_jsonl(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            candles_json = tmp / "candles.json"
            trade_wire_jsonl = tmp / "trade_wire.jsonl"
            output_jsonl = tmp / "labels.jsonl"
            candles_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "data": [
                                    {"timestamp": "2026-05-15T10:00:00Z", "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0},
                                    {"timestamp": "2026-05-15T10:05:00Z", "open": 100.0, "high": 101.5, "low": 99.9, "close": 101.0},
                                    {"timestamp": "2026-05-15T10:10:00Z", "open": 101.0, "high": 102.5, "low": 100.8, "close": 102.0},
                                ]
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            trade_wire_jsonl.write_text(
                json.dumps(
                    {
                        "trade_id": "trade-1",
                        "open_ts_ms": _ts_ms("2026-05-15T10:05:00Z"),
                        "close_ts_ms": _ts_ms("2026-05-15T10:10:00Z"),
                        "direction": "Bull",
                        "pnl": 5.0,
                        "structural_feedback": {"exit_reason": "roi"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = builder.main(
                [
                    "--candles-json",
                    str(candles_json),
                    "--trade-wire-jsonl",
                    str(trade_wire_jsonl),
                    "--output-jsonl",
                    str(output_jsonl),
                ]
            )

            self.assertEqual(exit_code, 0)
            first = json.loads(output_jsonl.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(first["trade_id"], "trade-1")

    def test_cli_writes_accepted_ibkr_paper_feedback_jsonl(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            captures_jsonl = tmp / "ibkr_paper_captures.jsonl"
            output_jsonl = tmp / "accepted_feedback.jsonl"
            captures_jsonl.write_text(
                json.dumps(
                    {
                        "trade_id": "rv-paper-0001",
                        "entry_exec_id": "0000e1.1",
                        "exit_exec_id": "0000e1.2",
                        "order_id": 17,
                        "client_id": 42,
                        "perm_id": 9917,
                        "conid": 568465095,
                        "local_symbol": "NQM6",
                        "sec_type": "FUT",
                        "exchange": "CME",
                        "currency": "USD",
                        "side": "BUY",
                        "quantity": 1,
                        "open_ts_ms": _ts_ms("2026-05-15T10:00:00Z"),
                        "close_ts_ms": _ts_ms("2026-05-15T11:00:00Z"),
                        "open_rate": 18800.25,
                        "close_rate": 18818.75,
                        "commission": 4.50,
                        "commission_currency": "USD",
                        "realized_pnl": 370.0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = builder.main(
                [
                    "--ibkr-paper-captures-jsonl",
                    str(captures_jsonl),
                    "--output-jsonl",
                    str(output_jsonl),
                    "--symbol",
                    "TOMAC_REALIZED_VOL_FIXEDHOLD_PRACTICAL_LIFECYCLE_V1",
                    "--strategy-name",
                    "tomac_idxfut_clean_realized_vol_term_structure_breakout_1h_v1",
                    "--factor-id",
                    "tomac_idxfut_clean_realized_vol_term_structure_breakout_1h_v1",
                    "--branch-path",
                    "TrendExpansion -> RealizedVolTermStructure -> factor_v1",
                    "--auto-quant-run-id",
                    "ibkr-paper-capture-20260530",
                    "--feedback-source",
                    "auto_quant_real_trades:paper_execution_feedback:realized_vol_fixedhold_v1",
                ]
            )

            self.assertEqual(exit_code, 0)
            first = json.loads(output_jsonl.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(first["feedback_source"], "auto_quant_real_trades:paper_execution_feedback:realized_vol_fixedhold_v1")
            self.assertTrue(first["broker_realized"])
            self.assertTrue(first["broker_fill_evidence"])

    def test_builder_preserves_actual_outcome_sign_when_proxy_return_disagrees(self) -> None:
        candles = [
            {"timestamp": "2026-05-15T10:00:00Z", "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0},
            {"timestamp": "2026-05-15T10:05:00Z", "open": 100.0, "high": 100.2, "low": 99.0, "close": 99.5},
            {"timestamp": "2026-05-15T10:10:00Z", "open": 99.5, "high": 99.8, "low": 98.8, "close": 99.0},
        ]
        trade_wire = [
            {
                "trade_id": "trade-actual-win",
                "open_ts_ms": _ts_ms("2026-05-15T10:00:00Z"),
                "close_ts_ms": _ts_ms("2026-05-15T10:10:00Z"),
                "direction": "Bull",
                "pnl": 12.0,
                "realized_outcome": "win",
                "structural_feedback": {"exit_reason": "roi"},
            }
        ]

        labels = builder.build_labels(
            candles=candles,
            trade_wire=trade_wire,
            sl_mult=0.01,
            max_alignment_gap_bars=3,
        )

        self.assertEqual(labels[0]["meta_label"], 1)
        self.assertGreater(labels[0]["gross_return"], 0.0)
        self.assertGreater(labels[0]["realized_R"], 0.0)

    def test_builder_prefers_wire_rates_when_present(self) -> None:
        candles = [
            {"timestamp": "2026-05-15T10:00:00Z", "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0},
            {"timestamp": "2026-05-15T10:05:00Z", "open": 100.0, "high": 100.2, "low": 98.8, "close": 99.0},
            {"timestamp": "2026-05-15T10:10:00Z", "open": 99.0, "high": 99.3, "low": 98.5, "close": 98.9},
        ]
        trade_wire = [
            {
                "trade_id": "trade-wire-rates",
                "open_ts_ms": _ts_ms("2026-05-15T10:00:00Z"),
                "close_ts_ms": _ts_ms("2026-05-15T10:10:00Z"),
                "direction": "Bull",
                "pnl": 20.0,
                "realized_outcome": "win",
                "open_rate": 101.0,
                "close_rate": 103.0,
                "min_rate": 100.5,
                "max_rate": 103.5,
                "structural_feedback": {"exit_reason": "roi"},
            }
        ]

        labels = builder.build_labels(
            candles=candles,
            trade_wire=trade_wire,
            sl_mult=0.01,
            max_alignment_gap_bars=3,
        )

        self.assertAlmostEqual(labels[0]["entry_price"], 101.0)
        self.assertAlmostEqual(labels[0]["exit_price"], 103.0)
        self.assertAlmostEqual(labels[0]["gross_return"], (103.0 - 101.0) / 101.0)

    def test_build_labels_from_trade_wire_without_candles_uses_timeframe_alignment(self) -> None:
        trade_wire = [
            {
                "trade_id": "trade-long",
                "open_ts_ms": _ts_ms("2026-05-15T10:00:00Z"),
                "close_ts_ms": _ts_ms("2026-05-15T10:15:00Z"),
                "direction": "Bull",
                "open_rate": 100.0,
                "close_rate": 102.0,
                "min_rate": 99.0,
                "max_rate": 103.0,
                "profit_ratio": 0.02,
                "realized_outcome": "win",
                "regime_profit_branch_path": "SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio -> factor_v1",
            },
            {
                "trade_id": "trade-short",
                "open_ts_ms": _ts_ms("2026-05-15T10:05:00Z"),
                "close_ts_ms": _ts_ms("2026-05-15T10:20:00Z"),
                "direction": "Bear",
                "open_rate": 200.0,
                "close_rate": 202.0,
                "min_rate": 198.0,
                "max_rate": 203.0,
                "profit_ratio": -0.01,
                "realized_outcome": "loss",
                "regime_profit_branch_path": "SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio -> factor_v1",
            },
        ]

        labels = builder.build_labels_from_trade_wire(
            trade_wire=trade_wire,
            sl_mult=0.01,
            timeframe_ms=5 * 60 * 1000,
            round_trip_cost_fraction=0.0005,
        )

        self.assertEqual([label["trade_id"] for label in labels], ["trade-long", "trade-short"])
        self.assertEqual(labels[0]["entry_index"], 0)
        self.assertEqual(labels[0]["exit_index"], 3)
        self.assertEqual(labels[1]["entry_index"], 1)
        self.assertEqual(labels[1]["exit_index"], 4)
        self.assertEqual(labels[0]["meta_label"], 1)
        self.assertEqual(labels[1]["meta_label"], 0)
        self.assertAlmostEqual(labels[0]["mfe"], 0.03)
        self.assertAlmostEqual(labels[0]["mae"], -0.01)
        self.assertAlmostEqual(labels[1]["mfe"], 0.01)
        self.assertAlmostEqual(labels[1]["mae"], -0.015)
        self.assertAlmostEqual(labels[0]["realized_R"], (0.02 - 0.0005) / 0.01)

    def test_build_accepted_paper_execution_feedback_requires_broker_fill_evidence(self) -> None:
        captures = [
            {
                "trade_id": "rv-paper-0001",
                "entry_exec_id": "0000e1.1",
                "exit_exec_id": "0000e1.2",
                "order_id": 17,
                "client_id": 42,
                "perm_id": 9917,
                "conid": 568465095,
                "local_symbol": "NQM6",
                "sec_type": "FUT",
                "exchange": "CME",
                "currency": "USD",
                "side": "BUY",
                "quantity": 1,
                "open_ts_ms": _ts_ms("2026-05-15T10:00:00Z"),
                "close_ts_ms": _ts_ms("2026-05-15T11:00:00Z"),
                "open_rate": 18800.25,
                "close_rate": 18818.75,
                "commission": 4.50,
                "commission_currency": "USD",
                "realized_pnl": 370.0,
                "source": "ibkr_reqExecutions_execDetails_commissionReport",
            }
        ]

        rows = builder.build_accepted_paper_execution_feedback_rows(
            captures,
            symbol="TOMAC_REALIZED_VOL_FIXEDHOLD_PRACTICAL_LIFECYCLE_V1",
            strategy_name="tomac_idxfut_clean_realized_vol_term_structure_breakout_1h_v1",
            factor_id="tomac_idxfut_clean_realized_vol_term_structure_breakout_1h_v1",
            branch_path="TrendExpansion -> RealizedVolTermStructure -> factor_v1",
            auto_quant_run_id="ibkr-paper-capture-20260530",
            feedback_source="auto_quant_real_trades:paper_execution_feedback:realized_vol_fixedhold_v1",
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["schema_version"], "1.0")
        self.assertEqual(row["strategy_mutation_id"], "tomac_idxfut_clean_realized_vol_term_structure_breakout_1h_v1")
        self.assertEqual(row["source"], "auto_quant_real_trades:paper_execution_feedback:realized_vol_fixedhold_v1")
        self.assertTrue(row["broker_realized"])
        self.assertTrue(row["broker_fill_evidence"])
        self.assertEqual(row["direction"], "Bull")
        self.assertEqual(row["realized_outcome"], "win")
        self.assertEqual(row["session_scope"], "ETH/full_retained_session")
        self.assertFalse(row["rth_filter_applied"])
        self.assertEqual(row["broker_execution"]["entry_exec_id"], "0000e1.1")
        self.assertEqual(row["broker_execution"]["exit_exec_id"], "0000e1.2")
        self.assertEqual(row["broker_execution"]["commission_currency"], "USD")

        with self.assertRaisesRegex(ValueError, "commission"):
            builder.build_accepted_paper_execution_feedback_rows(
                [{**captures[0], "commission": None}],
                symbol="S",
                strategy_name="strategy",
                factor_id="factor",
                branch_path="Branch -> factor",
                auto_quant_run_id="run",
                feedback_source="auto_quant_real_trades:paper_execution_feedback:test",
            )

        with self.assertRaisesRegex(ValueError, "simulated"):
            builder.build_accepted_paper_execution_feedback_rows(
                captures,
                symbol="S",
                strategy_name="strategy",
                factor_id="factor",
                branch_path="Branch -> factor",
                auto_quant_run_id="run",
                feedback_source="auto_quant_real_trades:simulated_backtest:test",
            )


if __name__ == "__main__":
    unittest.main()
