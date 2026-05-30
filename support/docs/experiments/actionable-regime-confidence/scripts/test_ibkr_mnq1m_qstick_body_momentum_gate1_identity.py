#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("run_ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1.py")
EXPECTED_BRANCH = "CandleBodyMomentum -> QstickBodyMomentum -> QstickBodyMomentum -> ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("ibkr_mnq_qstick_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrMnqQstickGate1IdentityTest(unittest.TestCase):
    def test_strategy_source_keeps_mnq_identity_without_legacy_branch_prefix(self) -> None:
        wrapper = load_wrapper()
        source = wrapper.strategy_source("ExampleStrategy", wrapper.base.VARIANTS[0])

        self.assertEqual(wrapper.base.AQ_SYMBOL, "IBKR_MNQ1M_QSTICK_BODY_MOMENTUM_7D_GATE1_V1")
        self.assertEqual(wrapper.base.FACTOR_ID, "ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1")
        self.assertEqual(wrapper.base.BRANCH_PATH, EXPECTED_BRANCH)
        self.assertNotIn("FUTURES ->", wrapper.base.BRANCH_PATH)
        self.assertNotIn("equity_index", wrapper.base.BRANCH_PATH)
        self.assertNotIn("MNQ -> 1m", wrapper.base.BRANCH_PATH)
        self.assertIn("class ExampleStrategy", source)
        self.assertIn("ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1", source)

    def test_materials_keep_provider_labels_separate_from_branch_identity(self) -> None:
        wrapper = load_wrapper()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            (root / "agent-material").mkdir(parents=True)
            wrapper.base.ROOT = root
            data_path = root / "data/provider/normalized/ibkr_mnq_202606_1m_7d.csv"
            data_path.parent.mkdir(parents=True)
            data_path.write_text("date,open,high,low,close,volume\n2026-05-19 13:30:00,1,1,1,1,1\n", encoding="utf-8")

            materials = wrapper.write_materials(data_path)

            self.assertEqual(len(materials), 4)
            for material in materials:
                payload = json.loads(material.read_text(encoding="utf-8"))
                profile = payload["consumer_evidence_profile"]
                self.assertEqual(payload["symbol"], "MNQ")
                self.assertIn("ibkr-mnq-qstick-body-momentum", payload["package_id"])
                self.assertEqual(profile["provider"], "IBKR")
                self.assertEqual(profile["root_symbol"], "MNQ")
                self.assertEqual(profile["exchange"], "CME")
                self.assertEqual(profile["last_trade_date"], "202606")
                self.assertEqual(profile["branch_path"], EXPECTED_BRANCH)
                self.assertEqual(profile["regime_profit_branch_path"], EXPECTED_BRANCH)
                self.assertEqual(profile["main_regime"], "CandleBodyMomentum")
                self.assertEqual(profile["sub_regime"], "QstickBodyMomentum")
                self.assertEqual(profile["sub_sub_regime_or_profit_factor"], "QstickBodyMomentum")
                self.assertEqual(profile["profit_factor_id"], "ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1")

    def test_materials_can_emit_retained_mtf_ladder(self) -> None:
        wrapper = load_wrapper()

        self.assertEqual(
            set(wrapper.TIMEFRAME_SOURCES),
            {"1m", "5m", "15m", "30m", "1h", "4h", "1d"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            (root / "agent-material").mkdir(parents=True)
            wrapper.base.ROOT = root
            data_paths = {}
            for timeframe in ("1m", "5m"):
                data_path = root / f"data/provider/normalized/ibkr_mnq_202606_{timeframe}_test.csv"
                data_path.parent.mkdir(parents=True, exist_ok=True)
                data_path.write_text(
                    "date,open,high,low,close,volume\n2026-05-19 13:30:00,1,1,1,1,1\n",
                    encoding="utf-8",
                )
                data_paths[timeframe] = data_path

            materials = wrapper.write_materials(data_paths)

            self.assertEqual(len(materials), 8)
            material_timeframes = set()
            for material in materials:
                payload = json.loads(material.read_text(encoding="utf-8"))
                profile = payload["consumer_evidence_profile"]
                material_timeframes.add(profile["material_timeframe"])
                self.assertEqual(profile["branch_path"], EXPECTED_BRANCH)
                self.assertEqual(profile["regime_profit_branch_path"], EXPECTED_BRANCH)
                self.assertEqual(profile["base_timeframe"], "1m")
                self.assertEqual(profile["training_timeframe"], "1m")
                self.assertIn(profile["material_timeframe"], payload["package_id"])
                self.assertEqual(payload["timeframe"], profile["material_timeframe"])
            self.assertEqual(material_timeframes, {"1m", "5m"})

    def test_mtf_rank_rows_use_verified_instrument_cost_not_fixed_bps_ladder(self) -> None:
        wrapper = load_wrapper()

        rows, survivors, branch_ok = wrapper.score_rank_rows_with_instrument_cost(
            [
                {
                    "package_id": "ibkr-mnq-qstick-body-momentum-qstick-dense-1m-mtf-v1",
                    "trade_count": 8,
                    "total_profit_pct": 0.80,
                    "win_rate_pct": 62.5,
                    "branch_path": EXPECTED_BRANCH,
                },
                {
                    "package_id": "ibkr-mnq-qstick-body-momentum-qstick-balanced-5m-mtf-v1",
                    "trade_count": 4,
                    "total_profit_pct": 0.20,
                    "win_rate_pct": 50.0,
                    "branch_path": EXPECTED_BRANCH,
                },
            ],
            representative_price=20000.0,
        )

        self.assertTrue(branch_ok)
        self.assertEqual(survivors, ["MNQ/qstick_dense/1m", "MNQ/qstick_balanced/5m"])
        self.assertIn("instrument_cost_total_profit_pct", rows[0])
        self.assertIn("survives_instrument_cost", rows[0])
        self.assertNotIn("5bps_per_side_total_profit_pct", rows[0])
        self.assertNotIn("survives_5bps_per_side", rows[0])


if __name__ == "__main__":
    unittest.main()
