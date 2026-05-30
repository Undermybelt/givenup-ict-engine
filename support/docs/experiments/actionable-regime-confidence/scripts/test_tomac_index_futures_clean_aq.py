#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import argparse
from subprocess import TimeoutExpired
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


SCRIPT = Path(__file__).with_name("run_tomac_index_futures_clean_aq_v1.py")
SPEC = importlib.util.spec_from_file_location("tomac_index_futures_clean_aq", SCRIPT)


class TomacIndexFuturesCleanAqTest(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        assert SPEC is not None and SPEC.loader is not None
        sys.modules[SPEC.name] = module
        SPEC.loader.exec_module(module)
        return module

    def test_pyarrow_missing_reexecs_through_auto_quant_python(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            preferred_python = Path(tmpdir) / "aq-python"
            preferred_python.write_text("", encoding="utf-8")

            argv = ["runner.py", "--root", "/tmp/run", "--symbols", "ES"]
            reexec_argv = module.pyarrow_runtime_reexec_argv(
                current_executable=Path("/usr/bin/python3"),
                preferred_python=preferred_python,
                argv=argv,
                pyarrow_available=False,
                script_path=Path("/repo/run_tomac_index_futures_clean_aq_v1.py"),
            )

            self.assertEqual(
                reexec_argv,
                [
                    str(preferred_python),
                    "/repo/run_tomac_index_futures_clean_aq_v1.py",
                    "--root",
                    "/tmp/run",
                    "--symbols",
                    "ES",
                ],
            )

    def test_outright_filter_rejects_calendar_spreads(self) -> None:
        module = self.load_module()

        self.assertTrue(module.is_outright_contract("ESM5", "ES"))
        self.assertTrue(module.is_outright_contract("YMU25", "YM"))
        self.assertTrue(module.is_outright_contract("NQH6", "NQ"))
        self.assertTrue(module.is_outright_contract("GCG1", "XAU"))
        self.assertFalse(module.is_outright_contract("ESM1-ESU1", "ES"))
        self.assertFalse(module.is_outright_contract("ESM5/ESU5", "ES"))
        self.assertFalse(module.is_outright_contract("MESH5", "ES"))
        self.assertFalse(module.is_outright_contract("GCG1-GCJ1", "XAU"))

    def test_selects_current_highest_volume_outright_per_timestamp(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            [
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "ESH5",
                    "open": 5200,
                    "high": 5201,
                    "low": 5199,
                    "close": 5200.5,
                    "volume": 10,
                },
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "ESM5",
                    "open": 5210,
                    "high": 5211,
                    "low": 5209,
                    "close": 5210.5,
                    "volume": 300,
                },
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "ESH5-ESM5",
                    "open": 10,
                    "high": 11,
                    "low": 9,
                    "close": 10.5,
                    "volume": 9999,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "symbol": "ESH5",
                    "open": 5200.5,
                    "high": 5202,
                    "low": 5200,
                    "close": 5201.5,
                    "volume": 400,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "symbol": "ESM5",
                    "open": 5210.5,
                    "high": 5212,
                    "low": 5210,
                    "close": 5211.5,
                    "volume": 200,
                },
            ]
        )

        selected, stats = module.select_front_outright_rows(frame, "ES")

        self.assertEqual(list(selected["contract"]), ["ESM5", "ESH5"])
        self.assertEqual(stats["spread_rows_dropped"], 1)
        self.assertEqual(stats["duplicate_timestamp_rows_dropped"], 2)

    def test_selects_xau_gc_outrights_instead_of_dropping_every_row(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            [
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "GCG5",
                    "open": 2300.0,
                    "high": 2301.0,
                    "low": 2299.0,
                    "close": 2300.5,
                    "volume": 120,
                },
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "GCG5-GCJ5",
                    "open": 1.0,
                    "high": 1.2,
                    "low": 0.8,
                    "close": 1.1,
                    "volume": 9999,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "symbol": "GCJ5",
                    "open": 2301.0,
                    "high": 2302.0,
                    "low": 2300.0,
                    "close": 2301.5,
                    "volume": 200,
                },
            ]
        )

        selected, stats = module.select_front_outright_rows(frame, "XAU")

        self.assertEqual(list(selected["contract"]), ["GCG5", "GCJ5"])
        self.assertEqual(stats["spread_rows_dropped"], 1)
        self.assertEqual(stats["duplicate_timestamp_rows_dropped"], 0)

    def test_back_adjust_uses_only_boundary_prices_and_writes_ledger(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            [
                {
                    "date": "2025-03-17T13:30:00Z",
                    "contract": "ESH5",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 10,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "contract": "ESM5",
                    "open": 110.0,
                    "high": 111.0,
                    "low": 109.0,
                    "close": 110.5,
                    "volume": 20,
                },
                {
                    "date": "2025-03-17T13:32:00Z",
                    "contract": "ESM5",
                    "open": 110.5,
                    "high": 112.0,
                    "low": 110.0,
                    "close": 111.0,
                    "volume": 25,
                },
            ]
        )

        adjusted, ledger = module.back_adjust_rolls(frame, symbol="ES")

        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["old_contract"], "ESH5")
        self.assertEqual(ledger[0]["new_contract"], "ESM5")
        self.assertEqual(ledger[0]["prev_raw_close"], 100.0)
        self.assertEqual(ledger[0]["new_raw_open"], 110.0)
        self.assertEqual(ledger[0]["adjustment_delta"], -10.0)
        self.assertEqual(float(adjusted.iloc[1]["open"]), 100.0)
        self.assertEqual(float(adjusted.iloc[1]["close"]), 100.5)
        self.assertEqual(float(adjusted.iloc[2]["close"]), 101.0)

    def test_resample_timeframes_from_clean_one_minute(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2025-03-17T13:30:00Z", periods=5, freq="1min"),
                "open": [1, 2, 3, 4, 5],
                "high": [2, 3, 4, 5, 6],
                "low": [0, 1, 2, 3, 4],
                "close": [1.5, 2.5, 3.5, 4.5, 5.5],
                "volume": [10, 20, 30, 40, 50],
            }
        )

        resampled = module.resample_clean_ohlcv(frame, "5m")

        self.assertEqual(len(resampled), 1)
        self.assertEqual(float(resampled.iloc[0]["open"]), 1.0)
        self.assertEqual(float(resampled.iloc[0]["high"]), 6.0)
        self.assertEqual(float(resampled.iloc[0]["low"]), 0.0)
        self.assertEqual(float(resampled.iloc[0]["close"]), 5.5)
        self.assertEqual(float(resampled.iloc[0]["volume"]), 150.0)

    def test_dense_calendar_for_aq_fills_only_from_past_close(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-03-17T13:30:00Z", "2025-03-17T13:40:00Z"],
                    utc=True,
                ),
                "open": [100.0, 103.0],
                "high": [101.0, 104.0],
                "low": [99.0, 102.0],
                "close": [100.5, 103.5],
                "volume": [10.0, 20.0],
            }
        )

        dense, stats = module.dense_calendar_for_aq(frame, "5m")

        self.assertEqual(list(dense["date"].dt.strftime("%H:%M")), ["13:30", "13:35", "13:40"])
        fill_row = dense.iloc[1]
        self.assertEqual(float(fill_row["open"]), 100.5)
        self.assertEqual(float(fill_row["high"]), 100.5)
        self.assertEqual(float(fill_row["low"]), 100.5)
        self.assertEqual(float(fill_row["close"]), 100.5)
        self.assertEqual(float(fill_row["volume"]), 0.0)
        self.assertEqual(stats["filled_rows"], 1)
        self.assertFalse(stats["future_lookahead"])

    def test_clean_source_to_1m_records_eth_full_session_coverage(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "es.csv"
            pd.DataFrame(
                [
                    {
                        "ts_event": "2025-03-17T08:00:00.000000000Z",
                        "open": 100.0,
                        "high": 101.0,
                        "low": 99.0,
                        "close": 100.5,
                        "volume": 10,
                        "symbol": "ESH5",
                    },
                    {
                        "ts_event": "2025-03-17T13:30:00.000000000Z",
                        "open": 101.0,
                        "high": 102.0,
                        "low": 100.0,
                        "close": 101.5,
                        "volume": 20,
                        "symbol": "ESH5",
                    },
                    {
                        "ts_event": "2025-03-17T21:30:00.000000000Z",
                        "open": 102.0,
                        "high": 103.0,
                        "low": 101.0,
                        "close": 102.5,
                        "volume": 30,
                        "symbol": "ESH5",
                    },
                ]
            ).to_csv(csv_path, index=False)

            _, _, stats = module.clean_source_to_1m(
                module.TomacSource(symbol="ES", source_csv=csv_path),
                start="2025-03-17",
                end="2025-03-17",
                chunksize=2,
            )

        self.assertEqual(stats["session_scope"], "ETH/full_retained_session")
        self.assertFalse(stats["rth_filter_applied"])
        self.assertTrue(stats["eth_full_retained_session_evidence"])
        self.assertEqual(stats["eth_full_retained_coverage_status"], "verified_retained_rows_outside_rth")
        self.assertEqual(stats["outside_rth_1m_rows"], 2)
        self.assertEqual(stats["rth_1m_rows"], 1)
        self.assertIn("outside CME/CBOT equity-index RTH", stats["session_coverage_evidence"])

    def test_generated_strategy_shifts_entry_and_exit_signals(self) -> None:
        module = self.load_module()

        source = module.strategy_source(module.candidate_specs()[0], symbol="ES", timeframe="5m")

        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        self.assertIn('metadata.get("pair") != "ES/USD"', source)
        self.assertIn("factor_id: tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1", source)
        self.assertIn(
            "branch_path: TrendExpansion -> SessionLiquidity -> "
            "OpeningDriveRvolVwapContinuation -> "
            "tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1",
            source,
        )
        self.assertNotIn("shift(-", source)

    def test_sanitize_aq_subprocess_env_disables_user_site_and_path_injection(self) -> None:
        module = self.load_module()

        env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": "/tmp/bad/site-packages",
            "PYTHONHOME": "/tmp/bad/home",
            "PYTHONUSERBASE": "/tmp/bad/userbase",
        }

        sanitized = module.sanitize_aq_subprocess_env(env)

        self.assertEqual(sanitized["PATH"], "/usr/bin:/bin")
        self.assertEqual(sanitized["PYTHONNOUSERSITE"], "1")
        self.assertNotIn("PYTHONPATH", sanitized)
        self.assertNotIn("PYTHONHOME", sanitized)
        self.assertNotIn("PYTHONUSERBASE", sanitized)

    def test_run_stages_aq_only_for_symbols_with_cleaned_sources(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            source = module.TomacSource(symbol="NQ", source_csv=Path("/tmp/nq.csv"))
            staged_symbols = []

            module.source_universe = lambda: [source]
            module.write_clean_bundle = lambda *args, **kwargs: {"symbol": source.symbol}

            def fake_stage_aq_inputs(*args, **kwargs):
                staged_symbols.extend(kwargs["symbols"])
                return {"workspace": str(root / "aq_workspace"), "strategy_specs": []}

            module.stage_aq_inputs = fake_stage_aq_inputs

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="NQ,XAU",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1m",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=False,
                aq_smoke_timeframe="1m",
                aq_symbol_limit=2,
                clean_only=True,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(staged_symbols, ["NQ"])
            self.assertEqual(summary["requested_symbols"], ["NQ", "XAU"])
            self.assertEqual(summary["symbols"], ["NQ"])
            self.assertEqual(summary["skipped_symbols"], ["XAU"])

    def test_run_stages_xau_when_requested_and_supported_by_default_source_universe(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            staged_symbols = []

            module.write_clean_bundle = lambda source, **kwargs: {"symbol": source.symbol}

            def fake_stage_aq_inputs(*args, **kwargs):
                staged_symbols.extend(kwargs["symbols"])
                return {"workspace": str(root / "aq_workspace"), "strategy_specs": []}

            module.stage_aq_inputs = fake_stage_aq_inputs

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="NQ,XAU",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1m",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=False,
                aq_smoke_timeframe="1m",
                aq_symbol_limit=2,
                clean_only=True,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(staged_symbols, ["NQ", "XAU"])
            self.assertEqual(summary["requested_symbols"], ["NQ", "XAU"])
            self.assertEqual(summary["symbols"], ["NQ", "XAU"])
            self.assertEqual(summary["skipped_symbols"], [])

    def test_run_cmd_timeout_normalizes_bytes_from_timeout_expired(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            root.mkdir(parents=True, exist_ok=True)
            with patch.object(
                module.subprocess,
                "run",
                side_effect=TimeoutExpired(["fake"], timeout=1, output=b"raw-out", stderr=b"raw-err"),
            ):
                result = module.run_cmd(root, "timeout_bytes_object", ["fake"], root, timeout=1)

            self.assertEqual(result["exit"], 124)
            self.assertTrue(result["timed_out"])
            self.assertIn("raw-err", (root / "command-output/timeout_bytes_object.err").read_text())
            self.assertIn("raw-out", (root / "command-output/timeout_bytes_object.out").read_text())

    def test_claim_collision_guard_blocks_foreign_active_claim_before_aq(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [
                {
                    "claim_file": "foreign.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/foreign-root",
                    "tmp_root": "/tmp/foreign-root",
                    "scope": "foreign Board B lane",
                },
                {
                    "claim_file": "own.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/own-root",
                    "tmp_root": "/tmp/own-root",
                    "scope": "own Board B lane",
                },
            ],
            "live_factor_processes": [
                {"pid": 123, "run_root": "/tmp/foreign-live", "command_excerpt": "run_tomac.py"}
            ],
        }

        guard = module.claim_collision_blockers(audit, allowed_roots={Path("/tmp/own-root")})

        self.assertFalse(guard["pass"])
        self.assertEqual([item["claim_file"] for item in guard["foreign_active_claims"]], ["foreign.claim"])
        self.assertEqual([item["pid"] for item in guard["foreign_live_processes"]], [123])

    def test_claim_collision_guard_allows_own_active_claim(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [
                {
                    "claim_file": "own.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/own-root",
                    "tmp_root": "/tmp/own-root",
                    "scope": "own Board B lane",
                }
            ],
            "live_factor_processes": [],
        }

        guard = module.claim_collision_blockers(audit, allowed_roots={Path("/tmp/own-root")})

        self.assertTrue(guard["pass"])
        self.assertEqual(guard["foreign_active_claims"], [])
        self.assertEqual(guard["foreign_live_processes"], [])

    def test_claim_collision_guard_allows_parent_claim_root_for_child_aq_root(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [
                {
                    "claim_file": "own-parent.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/own-root",
                    "tmp_root": "/tmp/own-root",
                    "scope": "own Board B parent lane",
                }
            ],
            "live_factor_processes": [],
        }

        roots = module.allowed_collision_roots(Path("/tmp/own-root/aq"), Path("/repo/runs/own"))
        guard = module.claim_collision_blockers(audit, allowed_roots=roots)

        self.assertTrue(guard["pass"])
        self.assertEqual(guard["foreign_active_claims"], [])

    def test_run_blocks_foreign_claim_before_cleaning_or_staging_when_aq_enabled(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            source = module.TomacSource(symbol="ES", source_csv=Path("/tmp/es.csv"))
            calls = {"clean": 0, "stage": 0}

            module.source_universe = lambda: [source]

            def fake_write_clean_bundle(*args, **kwargs):
                calls["clean"] += 1
                return {"symbol": source.symbol}

            def fake_stage_aq_inputs(*args, **kwargs):
                calls["stage"] += 1
                return {"workspace": str(root / "aq_workspace"), "strategy_specs": []}

            def fake_guard(*args, **kwargs):
                self.assertEqual(args[:2], (root, compact))
                self.assertEqual(kwargs["allowed_roots"], module.allowed_collision_roots(root, compact))
                return {
                    "pass": False,
                    "decision": "launch_blocked_by_foreign_claim_or_runtime",
                    "foreign_active_claims": [{"claim_file": "foreign.claim"}],
                    "foreign_live_processes": [],
                }

            module.write_clean_bundle = fake_write_clean_bundle
            module.stage_aq_inputs = fake_stage_aq_inputs
            module.run_claim_collision_audit = fake_guard

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="ES",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1m",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=False,
                aq_smoke_timeframe="1m",
                aq_symbol_limit=1,
                clean_only=False,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(calls, {"clean": 0, "stage": 0})
            self.assertEqual(summary["decision"], "launch_blocked_by_foreign_claim_or_runtime")
            self.assertEqual(summary["clean_bundles"], [])
            self.assertEqual(summary["aq_staging"], [])
            self.assertFalse(summary["promotion_allowed"])
            self.assertFalse(summary["trade_usable"])

    def test_xau_uses_precious_metals_cost_profile(self) -> None:
        module = self.load_module()

        profile = module.futures_cost_profile("XAU")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.root_symbol, "XAU")
        self.assertEqual(module.product_label_for_symbol("XAU"), "precious_metals_futures")

    def test_generated_strategy_for_vwap_killzone_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "vwap_reclaim_persistence_killzone_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: RangeTransition -> VWAPMeanReclaim -> "
            "VwapReclaimPersistence -> KillzoneFilter -> "
            "tomac_idxfut_clean_vwap_reclaim_persistence_killzone_filter_1m_v1",
            source,
        )
        self.assertIn('elif "vwap_reclaim_persistence_killzone_filter" == "vwap_reclaim_persistence_killzone_filter":', source)
        self.assertIn("killzone_window = (", source)
        self.assertIn("reclaim_long", source)
        self.assertIn("reclaim_short", source)

    def test_generated_strategy_for_vwap_rvol_trend_quality_child_keeps_exact_branch_and_mtf_context(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "vwap_reclaim_rvol_trend_quality_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn("can_short = True", source)
        self.assertIn(
            "branch_path: RangeTransition -> VWAPMeanReclaim -> "
            "VwapReclaimPersistence -> RvolTrendQualityFilter -> "
            "tomac_idxfut_clean_vwap_reclaim_rvol_trend_quality_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "vwap_reclaim_rvol_trend_quality_filter" == '
            '"vwap_reclaim_rvol_trend_quality_filter":',
            source,
        )
        self.assertIn("pd.merge_asof", source)
        self.assertIn("trend_aligned_votes", source)
        self.assertIn("trend_counter_votes", source)
        self.assertIn("rolling(5).sum().ge(5)", source)
        self.assertIn('dataframe["trend_counter_votes"].ge(1)', source)
        self.assertIn("distance_quality = vwap_dist_atr.le(0.6)", source)
        self.assertIn("vwap_quality_any", source)
        self.assertIn("vwap_quality_first_daily", source)
        self.assertRegex(
            source,
            r'vwap_quality_any\.groupby\(\s*dataframe\["date"\]\.dt\.strftime\("%Y-%m-%d"\)\s*\)\.cumsum\(\)\.eq\(1\)',
        )
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_generated_strategy_for_impulse_hold_persistence_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "impulse_follow_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> ImpulseFollowThrough -> HoldPersistence -> "
            "tomac_idxfut_clean_impulse_follow_hold_persistence_1m_v1",
            source,
        )
        self.assertIn('elif "impulse_follow_hold_persistence" == "impulse_follow_hold_persistence":', source)
        self.assertIn("hold_persistence = (", source)
        self.assertIn("trend_root", source)
        self.assertIn("continuation", source)

    def test_candidate_specs_include_impulse_hold_persistence_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["impulse_follow_hold_persistence"].branch_path,
            "TrendExpansion -> ImpulseFollowThrough -> HoldPersistence",
        )

    def test_generated_strategy_for_vwap_rvol_trend_quality_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "vwap_reclaim_rvol_trend_quality_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: RangeTransition -> VWAPMeanReclaim -> "
            "VwapReclaimPersistence -> RvolTrendQualityFilter -> "
            "tomac_idxfut_clean_vwap_reclaim_rvol_trend_quality_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "vwap_reclaim_rvol_trend_quality_filter" == "vwap_reclaim_rvol_trend_quality_filter":',
            source,
        )
        self.assertIn("vwap_quality_persistence = (", source)
        self.assertIn("trend_quality_ok = (", source)
        self.assertIn("rvol_quality_ok = dataframe[\"rvol96\"].between(0.80, 5.0)", source)

    def test_candidate_specs_include_vwap_rvol_trend_quality_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["vwap_reclaim_rvol_trend_quality_filter"].branch_path,
            "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence -> RvolTrendQualityFilter",
        )

    def test_generated_strategy_for_camarilla_r3_s3_reclaim_keeps_exact_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "camarilla_r3_s3_reclaim"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1",
        )
        self.assertIn("can_short = True", source)
        self.assertIn(
            "branch_path: RangeReversion -> CamarillaPivotReclaim -> "
            "camarilla_r3_s3_reclaim_v1 -> "
            "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "camarilla_r3_s3_reclaim" == "camarilla_r3_s3_reclaim":',
            source,
        )
        self.assertIn('dataframe["camarilla_r3"]', source)
        self.assertIn('dataframe["camarilla_s3"]', source)
        self.assertIn('dataframe["camarilla_s4"]', source)
        self.assertIn("s3_reclaim", source)
        self.assertIn("r3_reclaim", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)

    def test_candidate_specs_include_camarilla_r3_s3_reclaim(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(by_key["camarilla_r3_s3_reclaim"].direction, "long_short")
        self.assertEqual(
            by_key["camarilla_r3_s3_reclaim"].branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1",
        )

    def test_generated_strategy_for_nr7_excursion_cap_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "nr7_range_expansion_excursion_cap"
        )
        source = module.strategy_source(spec, symbol="6E", timeframe="1m")

        self.assertIn(
            "branch_path: RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> ExcursionCap -> "
            "tomac_idxfut_clean_nr7_range_expansion_excursion_cap_1m_v1",
            source,
        )
        self.assertIn('elif "nr7_range_expansion_excursion_cap" == "nr7_range_expansion_excursion_cap":', source)
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("vwap_excursion_ok", source)
        self.assertIn("reclaim_discount_ok", source)

    def test_candidate_specs_include_nr7_excursion_cap_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["nr7_range_expansion_excursion_cap"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> ExcursionCap",
        )

    def test_generated_strategy_for_nr7_vwap_hold_persistence_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "nr7_range_expansion_vwap_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="6E", timeframe="1m")

        self.assertIn(
            "branch_path: RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> VwapHoldPersistence -> "
            "tomac_idxfut_clean_nr7_range_expansion_vwap_hold_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "nr7_range_expansion_vwap_hold_persistence" == "nr7_range_expansion_vwap_hold_persistence":',
            source,
        )
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("vwap_hold_bias", source)
        self.assertIn("session_participation", source)

    def test_candidate_specs_include_nr7_vwap_hold_persistence_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["nr7_range_expansion_vwap_hold_persistence"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> VwapHoldPersistence",
        )

    def test_generated_strategy_for_nr7_killzone_filter_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "nr7_range_expansion_killzone_filter"
        )
        source = module.strategy_source(spec, symbol="6E", timeframe="1m")

        self.assertIn(
            "branch_path: RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> KillzoneFilter -> "
            "tomac_idxfut_clean_nr7_range_expansion_killzone_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "nr7_range_expansion_killzone_filter" == "nr7_range_expansion_killzone_filter":',
            source,
        )
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("killzone_window", source)
        self.assertIn("session_participation", source)

    def test_candidate_specs_include_nr7_killzone_filter_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["nr7_range_expansion_killzone_filter"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> KillzoneFilter",
        )

    def test_generated_strategy_for_prior_day_multifactor_confluence_volume_child_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_multifactor_confluence_volume_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertIn(
            "branch_path: RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim -> VolumeConfirmation -> "
            "tomac_idxfut_clean_prior_day_multifactor_confluence_volume_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_multifactor_confluence_volume_reclaim" == '
            '"prior_day_multifactor_confluence_volume_reclaim":',
            source,
        )
        self.assertIn("can_short = True", source)
        self.assertIn("long_score = (", source)
        self.assertIn("short_score = (", source)
        self.assertIn("raw = trading_window & long_score.ge(4)", source)
        self.assertIn("short_raw = trading_window & short_score.ge(4)", source)
        self.assertIn("extreme_wpr_long = dataframe[\"wpr14\"].lt(-85)", source)
        self.assertIn("extreme_wpr_short = dataframe[\"wpr14\"].gt(-15)", source)
        self.assertIn("volume_confirm = dataframe[\"rvol20\"].gt(1.2)", source)
        self.assertIn("low_vol_env = dataframe[\"atr14\"] < dataframe[\"atr_ma50\"]", source)
        self.assertIn("trend_ok_long = dataframe[\"ema20\"] > dataframe[\"ema50\"]", source)
        self.assertIn("trend_ok_short = dataframe[\"ema20\"] < dataframe[\"ema50\"]", source)

    def test_candidate_specs_include_prior_day_multifactor_confluence_volume_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_multifactor_confluence_volume_reclaim"].direction,
            "long_short",
        )
        self.assertEqual(
            by_key["prior_day_multifactor_confluence_volume_reclaim"].branch_path,
            "RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim -> VolumeConfirmation",
        )

    def test_generated_strategy_for_prior_day_extreme_killzone_child_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> KillzoneFilter -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter" == '
            '"prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter":',
            source,
        )
        self.assertIn("killzone_window", source)
        self.assertIn("session_participation", source)
        self.assertIn("prior_day_retest", source)

    def test_candidate_specs_include_prior_day_extreme_killzone_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> KillzoneFilter",
        )

    def test_generated_strategy_for_prior_day_extreme_participation_quality_guard_child_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard" == '
            '"prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard":',
            source,
        )
        self.assertIn("participation_impulse", source)
        self.assertIn("volume_acceptance", source)
        self.assertIn("trend_efficiency_guard", source)
        self.assertIn('dataframe["vol96"] = ', source)
        self.assertIn('dataframe["close_location"] = ', source)

    def test_candidate_specs_include_prior_day_extreme_participation_quality_guard_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard",
        )

    def test_generated_strategy_for_prior_day_extreme_participation_quality_guard_nq_cadence_lift_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> "
            "ParticipationQualityGuard -> NQCadenceLift -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift" == '
            '"prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift":',
            source,
        )
        self.assertIn("first_chance_window", source)
        self.assertIn("second_chance_reclaim", source)
        self.assertIn("late_morning_window", source)
        self.assertIn("post_lunch_window", source)

    def test_candidate_specs_include_prior_day_extreme_participation_quality_guard_nq_cadence_lift(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard -> NQCadenceLift",
        )

    def test_generated_strategy_for_ultimate_ict_volume_spike_reclaim_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_reclaim" == '
            '"ultimate_ict_zone_volume_spike_reclaim":',
            source,
        )
        self.assertIn("killzone_window", source)
        self.assertIn("liquidity_sweep", source)
        self.assertIn("extreme_wpr", source)
        self.assertIn("ict_zone", source)
        self.assertIn("volume_spike", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_exit_persistence_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_exit_persistence"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> ExitPersistence",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> ExitPersistence -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_exit_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_exit_persistence" == '
            '"ultimate_ict_zone_volume_spike_exit_persistence":',
            source,
        )
        self.assertIn("score6_urgency", source)
        self.assertIn("persistence_window", source)
        self.assertIn("volume_spike", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_session_open_bias_cap_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_session_open_bias_cap"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_session_open_bias_cap_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_session_open_bias_cap" == '
            '"ultimate_ict_zone_volume_spike_session_open_bias_cap":',
            source,
        )
        self.assertIn("ny_killzone", source)
        self.assertIn("session_open_bias", source)
        self.assertIn("vwap_reclaim", source)
        self.assertIn("macd_bias", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_vwap_hold_persistence_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_vwap_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> VwapHoldPersistence",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> VwapHoldPersistence -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_vwap_hold_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_vwap_hold_persistence" == '
            '"ultimate_ict_zone_volume_spike_vwap_hold_persistence":',
            source,
        )
        self.assertIn("vwap_reclaim", source)
        self.assertIn("vwap_hold", source)
        self.assertIn("persistence_bias", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_session_open_vwap_hold_compound_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> "
            "SessionOpenBiasCap -> VwapHoldPersistence",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap -> VwapHoldPersistence -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence" == '
            '"ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence":',
            source,
        )
        self.assertIn("session_open_bias", source)
        self.assertIn("vwap_reclaim", source)
        self.assertIn("vwap_hold", source)
        self.assertIn("persistence_bias", source)

    def test_generated_strategy_for_wpr_fractal_no_be_session_bias_cap_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_no_be_session_bias_cap"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> SessionBiasCap",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalNoBreakEvenFullTarget -> SessionBiasCap -> "
            "tomac_idxfut_clean_wpr_fractal_no_be_session_bias_cap_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_no_be_session_bias_cap" == '
            '"wpr_fractal_no_be_session_bias_cap":',
            source,
        )
        self.assertIn("session_bias_cap_window", source)
        self.assertIn("liquidity_sweep", source)
        self.assertIn("wpr_reclaim", source)
        self.assertIn("session_open_bias", source)
        self.assertIn("vwap_hold", source)

    def test_generated_strategy_for_wpr_fractal_no_be_higher_frame_slope_confirm_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_no_be_higher_frame_slope_confirm"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> HigherFrameSlopeConfirm",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalNoBreakEvenFullTarget -> HigherFrameSlopeConfirm -> "
            "tomac_idxfut_clean_wpr_fractal_no_be_higher_frame_slope_confirm_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_no_be_higher_frame_slope_confirm" == '
            '"wpr_fractal_no_be_higher_frame_slope_confirm":',
            source,
        )
        self.assertIn("higher_frame_slope_confirm", source)
        self.assertIn("ema55_slope_atr", source)
        self.assertIn("ema144_slope_atr", source)
        self.assertIn("liquidity_sweep", source)

    def test_generated_strategy_for_wpr_fractal_ict_zone_reclaim_keeps_exact_source_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_ict_zone_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalIctZoneReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalIctZoneReclaim -> "
            "tomac_idxfut_clean_wpr_fractal_ict_zone_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_ict_zone_reclaim" == '
            '"wpr_fractal_ict_zone_reclaim":',
            source,
        )
        self.assertIn("wpr14", source)
        self.assertIn("bull_fvg", source)
        self.assertIn("bear_fvg", source)
        self.assertIn("bull_ob_low", source)
        self.assertIn("bear_ob_high", source)
        self.assertIn("liquidity_sweep", source)
        self.assertIn("short_liquidity_sweep", source)
        self.assertIn("wpr_reclaim", source)
        self.assertIn("short_wpr_reclaim", source)
        self.assertIn("ict_zone", source)
        self.assertIn("short_ict_zone", source)

    def test_generated_strategy_indicators_skip_non_target_pairs_before_heavy_columns(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_ict_zone_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        indicator_start = source.index("def populate_indicators")
        first_heavy_indicator = source.index('dataframe["ema21"] = ta.EMA', indicator_start)
        pair_guard = source.index('metadata.get("pair") != "ES/USD"', indicator_start)
        early_indicator_body = source[indicator_start:first_heavy_indicator]

        self.assertLess(pair_guard, first_heavy_indicator)
        self.assertIn('if metadata.get("pair") != "ES/USD":', early_indicator_body)
        self.assertIn("return dataframe", early_indicator_body)

    def test_generated_strategy_for_wpr_adx_fractal_sweep_reclaim_keeps_parent_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_adx_fractal_sweep_reclaim"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprAdxTrendAlignedReclaim -> "
            "tomac_idxfut_clean_wpr_adx_fractal_sweep_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_adx_fractal_sweep_reclaim" == '
            '"wpr_adx_fractal_sweep_reclaim":',
            source,
        )
        self.assertIn("hour_open_bias", source)
        self.assertIn("volume_ratio", source)
        self.assertIn("adx14", source)
        self.assertIn("confirmed_ssl", source)
        self.assertIn("confirmed_bsl", source)

    def test_generated_strategy_for_wpr_adx_hurst_profile_mss_reclaim_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_adx_hurst_profile_mss_reclaim"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> "
            "tomac_idxfut_clean_wpr_adx_hurst_profile_mss_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_adx_hurst_profile_mss_reclaim" == '
            '"wpr_adx_hurst_profile_mss_reclaim":',
            source,
        )
        self.assertIn("hurst64", source)
        self.assertIn("profile_poc96", source)
        self.assertIn("bull_mss", source)
        self.assertIn("bear_fvg", source)

    def test_generated_strategy_for_liquidity_sweep_adx_liquidity_pool_context_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "liquidity_sweep_adx_liquidity_pool_context"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> LiquiditySweepDisplacement -> "
            "AdxTrendStrengthReclaim -> LiquidityPoolContextFilter",
        )
        self.assertIn(
            "branch_path: TrendExpansion -> LiquiditySweepDisplacement -> "
            "AdxTrendStrengthReclaim -> LiquidityPoolContextFilter -> "
            "tomac_idxfut_clean_liquidity_sweep_adx_liquidity_pool_context_1m_v1",
            source,
        )
        self.assertIn(
            'elif "liquidity_sweep_adx_liquidity_pool_context" == '
            '"liquidity_sweep_adx_liquidity_pool_context":',
            source,
        )
        self.assertIn("liquidity_pool_band", source)
        self.assertIn("sellside_pool_cluster", source)
        self.assertIn("bull_mss", source)
        common_bear_fvg = 'dataframe["bear_fvg"] = dataframe["high"] < dataframe["prev2_low"]'
        first_family_branch = source.index(
            'if "liquidity_sweep_adx_liquidity_pool_context" == "wpr_adx_hurst_profile_mss_reclaim":'
        )
        self.assertLess(
            source.find(common_bear_fvg),
            first_family_branch,
        )

    def test_generated_strategy_for_value_area_vpoc_htf_trend_mss_filter_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "value_area_vpoc_htf_trend_mss_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeTransition -> MarketProfileValueAreaAcceptance -> "
            "VpocReclaimContinuation -> HtfTrendResonanceMssFilter",
        )
        self.assertIn(
            "branch_path: RangeTransition -> MarketProfileValueAreaAcceptance -> "
            "VpocReclaimContinuation -> HtfTrendResonanceMssFilter -> "
            "tomac_idxfut_clean_value_area_vpoc_htf_trend_mss_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "value_area_vpoc_htf_trend_mss_filter" == '
            '"value_area_vpoc_htf_trend_mss_filter":',
            source,
        )
        self.assertIn('for label, rule in {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}.items():', source)
        self.assertIn("session_profile_poc_price", source)
        self.assertIn("session_profile_value_area_pos", source)
        self.assertIn("session_or_breakout_atr", source)
        self.assertIn("session_profile_rotation_factor", source)
        self.assertIn("trend_resonance_long", source)
        self.assertIn("bull_mss", source)
        self.assertIn("bear_fvg", source)

    def test_generated_value_area_strategy_uses_incremental_session_profile_updates(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "value_area_vpoc_htf_trend_mss_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertNotIn("open_range_rows = [row for row in session_rows if row[0] <= open_range_end]", source)
        self.assertNotIn("initial_balance_rows = [row for row in session_rows if row[0] <= initial_balance_end]", source)
        self.assertNotIn("for _, _, _, close_value, volume_value in session_rows:", source)
        self.assertNotIn("ts_local.normalize() + pd.Timedelta(hours=9, minutes=30)", source)
        self.assertNotIn("open_range_end = current_anchor + pd.Timedelta(minutes=10)", source)
        self.assertIn("or_high = max(or_high, highs[idx])", source)
        self.assertIn("ib_high = max(ib_high, highs[idx])", source)
        self.assertIn("profile_map[level] = profile_map.get(level, 0.0) + max(float(volumes[idx]), 0.0)", source)
        self.assertIn("minute_of_day = (ny_dates.dt.hour * 60 + ny_dates.dt.minute).to_numpy(dtype=int)", source)
        self.assertIn("session_minute = minute_of_day[idx]", source)

    def test_generated_strategy_for_wpr_fractal_no_be_fulltarget_keeps_parent_root(self) -> None:
        module = self.load_module()

        spec = module.candidate_specs(families=["wpr_fractal_no_be_fulltarget"])[0]
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalNoBreakEvenFullTarget -> "
            "tomac_idxfut_clean_wpr_fractal_no_be_fulltarget_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_no_be_fulltarget" == '
            '"wpr_fractal_no_be_fulltarget":',
            source,
        )
        self.assertIn("liquidity_sweep", source)
        self.assertIn("wpr_reclaim", source)
        self.assertIn("full_target_bias", source)
        self.assertIn("can_short = True", source)
        self.assertIn("short_liquidity_sweep", source)
        self.assertIn("enter_short", source)
        self.assertIn("wpr_reclaim", source)

    def test_generated_strategy_for_crabel_nr7_intraday_expansion_continuation_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "crabel_nr7_intraday_expansion_continuation"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> "
            "IntradayExpansionContinuation",
        )
        self.assertIn(
            "branch_path: VolatilityCompressionExpansion -> CrabelNR7 -> "
            "Nr7CrabelExpansion -> IntradayExpansionContinuation -> "
            "tomac_idxfut_clean_crabel_nr7_intraday_expansion_continuation_1m_v1",
            source,
        )
        self.assertIn(
            'elif "crabel_nr7_intraday_expansion_continuation" == '
            '"crabel_nr7_intraday_expansion_continuation":',
            source,
        )
        self.assertIn("nr7_range", source)
        self.assertIn("nr7_break", source)
        self.assertIn("opening_break", source)
        self.assertIn("continuation_follow_through", source)
        self.assertIn("session_expansion_hold", source)

    def test_generated_strategy_for_crabel_nr7_intraday_expansion_continuation_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "crabel_nr7_intraday_expansion_continuation"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> IntradayExpansionContinuation",
        )
        self.assertIn(
            "branch_path: VolatilityCompressionExpansion -> CrabelNR7 -> "
            "Nr7CrabelExpansion -> IntradayExpansionContinuation -> "
            "tomac_idxfut_clean_crabel_nr7_intraday_expansion_continuation_1m_v1",
            source,
        )
        self.assertIn(
            'elif "crabel_nr7_intraday_expansion_continuation" == '
            '"crabel_nr7_intraday_expansion_continuation":',
            source,
        )
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("opening_break = dataframe[\"close\"] > dataframe[\"opening_high30\"]", source)
        self.assertIn("continuation_follow_through", source)
        self.assertIn("session_expansion_hold", source)

    def test_generated_strategy_for_fractal_liquidity_macd_rsi_divergence_reclaim_keeps_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "fractal_liquidity_macd_rsi_divergence_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdRsiDivergenceReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> FractalLiquiditySweep -> "
            "MacdRsiDivergenceReclaim -> "
            "tomac_idxfut_clean_fractal_liquidity_macd_rsi_divergence_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "fractal_liquidity_macd_rsi_divergence_reclaim" == '
            '"fractal_liquidity_macd_rsi_divergence_reclaim":',
            source,
        )
        self.assertIn("macd_bullish_divergence", source)
        self.assertIn("macd_bearish_divergence", source)
        self.assertIn("killzone_window", source)
        self.assertIn("midnight_discount", source)
        self.assertIn("midnight_premium", source)

    def test_generated_strategy_for_fractal_liquidity_macd_divergence_reclaim_keeps_macd_only_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "fractal_liquidity_macd_divergence_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdDivergenceReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> FractalLiquiditySweep -> "
            "MacdDivergenceReclaim -> "
            "tomac_idxfut_clean_fractal_liquidity_macd_divergence_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "fractal_liquidity_macd_divergence_reclaim" == '
            '"fractal_liquidity_macd_divergence_reclaim":',
            source,
        )
        self.assertIn("macd_bullish_divergence", source)
        self.assertIn("macd_bearish_divergence", source)
        self.assertIn("fractal_sweep_long", source)
        self.assertIn("fractal_sweep_short", source)
        branch_start = source.index(
            'elif "fractal_liquidity_macd_divergence_reclaim" == '
            '"fractal_liquidity_macd_divergence_reclaim":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        macd_only_block = source[branch_start:next_branch]
        self.assertNotIn('dataframe["rsi14"].gt(30)', macd_only_block)
        self.assertNotIn('dataframe["rsi14"].lt(70)', macd_only_block)

    def test_generated_strategy_for_ote_fvg_order_block_reclaim_session_directional_bias_keeps_exact_child_root(
        self,
    ) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ote_fvg_order_block_reclaim_session_directional_bias"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> LiquiditySweepIctRetracement -> OteFvgOrderBlockReclaim -> SessionDirectionalBias",
        )
        self.assertIn(
            "branch_path: RangeReversion -> LiquiditySweepIctRetracement -> "
            "OteFvgOrderBlockReclaim -> SessionDirectionalBias -> "
            "tomac_idxfut_clean_ote_fvg_order_block_reclaim_session_directional_bias_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ote_fvg_order_block_reclaim_session_directional_bias" == '
            '"ote_fvg_order_block_reclaim_session_directional_bias":',
            source,
        )
        self.assertIn("liquidity_sweep_long", source)
        self.assertIn("liquidity_sweep_short", source)
        self.assertIn("ict_zone_long", source)
        self.assertIn("ict_zone_short", source)
        self.assertIn("bull_session_bias", source)
        self.assertIn("bear_session_bias", source)
        self.assertIn("mtf_bias_long", source)
        self.assertIn("mtf_bias_short", source)
        self.assertIn("short_raw", source)

    def test_candidate_specs_include_fractal_liquidity_macd_rsi_divergence_reclaim(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["fractal_liquidity_macd_rsi_divergence_reclaim"].branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdRsiDivergenceReclaim",
        )

    def test_candidate_specs_include_fractal_liquidity_macd_divergence_reclaim(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["fractal_liquidity_macd_divergence_reclaim"].branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdDivergenceReclaim",
        )

    def test_candidate_specs_include_ote_fvg_order_block_reclaim_session_directional_bias(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["ote_fvg_order_block_reclaim_session_directional_bias"].branch_path,
            "RangeReversion -> LiquiditySweepIctRetracement -> OteFvgOrderBlockReclaim -> SessionDirectionalBias",
        )

    def test_candidate_specs_include_crabel_nr7_intraday_expansion_continuation(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["crabel_nr7_intraday_expansion_continuation"].branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> "
            "IntradayExpansionContinuation",
        )

    def test_candidate_specs_include_public_family_rotation_roots(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["opening_drive_breakout"].branch_path,
            "TrendExpansion -> OpeningDriveBreakout -> OpeningDriveBreakout",
        )

    def test_candidate_specs_include_crabel_nr7_intraday_expansion_continuation(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["crabel_nr7_intraday_expansion_continuation"].branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> IntradayExpansionContinuation",
        )
        self.assertEqual(
            by_key["supertrend_adx_displacement"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackOrLiquiditySweepReclaim",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_reclaim"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaim",
        )
        self.assertEqual(
            by_key["supertrend_adx_turtle_soup_sweep_reversal"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TurtleSoupSweepReversal",
        )
        self.assertEqual(
            by_key["supertrend_adx_liquidity_sweep_reclaim"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> LiquiditySweepReclaim",
        )
        self.assertEqual(
            by_key["liquidity_sweep_adx_liquidity_pool_context"].branch_path,
            "TrendExpansion -> LiquiditySweepDisplacement -> "
            "AdxTrendStrengthReclaim -> LiquidityPoolContextFilter",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_ote_fvg_ob"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimOteFvgOb",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistence",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_high_conviction"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceHighConviction",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_opening_drive"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceOpeningDrive",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_opening_drive_soft"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceOpeningDriveSoft",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_vwap_excursion_cap"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceVwapExcursionCap",
        )
        self.assertEqual(
            by_key["mass_index_vortex_trend_continuation"].branch_path,
            "TrendExpansion -> VolatilityExpansionTrend -> MassIndexBulge -> VortexDirectionalContinuation",
        )
        self.assertEqual(
            by_key["aroon_cci_trend_continuation"].branch_path,
            "TrendExpansion -> DirectionalPersistence -> AroonCciTrendContinuation",
        )
        self.assertEqual(
            by_key["aroon_cci_cadence_lift_symbol_guard"].branch_path,
            "TrendExpansion -> DirectionalPersistence -> AroonCciTrendContinuation -> CadenceLiftSymbolGuard",
        )
        self.assertEqual(
            by_key["vwap_reclaim_persistence"].branch_path,
            "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
        )
        self.assertEqual(
            by_key["vwap_reclaim_persistence_killzone_filter"].branch_path,
            "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence -> KillzoneFilter",
        )
        self.assertEqual(
            by_key["donchian_turtle_breakout"].branch_path,
            "TrendExpansion -> BreakoutPersistence -> DonchianTurtleBreakout",
        )
        self.assertEqual(
            by_key["vwap_washout_reclaim"].branch_path,
            "RangeReversion -> VwapStretch -> VwapWashoutReclaim",
        )
        self.assertEqual(
            by_key["dense_trend_pullback_reclaim"].branch_path,
            "TrendExpansion -> PullbackReclaim -> DenseTrendPullbackReclaim",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuation",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ExitPersistence",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> CusumDeadzoneGate",
        )
        self.assertEqual(
            by_key["opening_drive_twoleg_continuation_exit_persistence"].branch_path,
            "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation -> ExitPersistence",
        )
        self.assertEqual(
            by_key["impulse_follow"].branch_path,
            "TrendExpansion -> ImpulseFollowThrough -> ImpulseFollowThrough",
        )
        self.assertEqual(
            by_key["wpr_extreme_mean_reclaim"].branch_path,
            "TrendExpansion -> WprExtremePullback -> MeanReclaim",
        )
        self.assertEqual(
            by_key["nr7_range_expansion"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion",
        )
        self.assertEqual(
            by_key["connors_rsi2_rebound"].branch_path,
            "RangeReversion -> ExhaustionWashout -> ConnorsRsi2Rebound",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_reclaim"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_vwap_hold_persistence"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> VwapHoldPersistence",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> "
            "SessionOpenBiasCap -> VwapHoldPersistence",
        )
        self.assertEqual(
            by_key["wpr_fractal_no_be_session_bias_cap"].branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> SessionBiasCap",
        )
        self.assertEqual(
            by_key["wpr_fractal_no_be_higher_frame_slope_confirm"].branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> HigherFrameSlopeConfirm",
        )
        self.assertEqual(
            by_key["ote_liquidity_sweep_fvg_ob_reclaim"].branch_path,
            "TrendExpansion -> OteLiquiditySweepReclaim -> FvgObReentry",
        )
        self.assertEqual(
            by_key["ote_fvg_order_block_reclaim_session_directional_bias"].branch_path,
            "RangeReversion -> LiquiditySweepIctRetracement -> OteFvgOrderBlockReclaim -> SessionDirectionalBias",
        )
        self.assertEqual(
            by_key["h4_midnight_macd_rsi_pullback"].branch_path,
            "TrendExpansion -> H4StructureMidnightBias -> MacdRsiPullback",
        )
        self.assertEqual(
            by_key["liquidity_purge_rejection"].branch_path,
            "RangeTransition -> LiquidityPurgeRejection -> KillzoneReversal",
        )
        self.assertEqual(
            by_key["momentum_divergence_reclaim"].branch_path,
            "TrendExpansion -> MomentumDivergence -> DivergenceReclaim",
        )
        self.assertEqual(
            by_key["fractal_liquidity_macd_rsi_divergence_reclaim"].branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdRsiDivergenceReclaim",
        )
        self.assertEqual(
            by_key["midnight_open_liquidity_sweep_macd_divergence_reclaim"].branch_path,
            "RangeReversion -> MidnightOpenDiscountPremiumBias -> LiquiditySweepReclaim -> MacdDivergenceReclaim",
        )
        self.assertEqual(
            by_key["silver_bullet_rsi_sniper"].branch_path,
            "SessionRhythm -> SilverBulletSniper -> RsiAtrReversal",
        )
        self.assertEqual(
            by_key["session_window_sweep_reclaim"].branch_path,
            "SessionRhythm -> KillzoneLiquiditySweep -> SessionWindowSweepReclaim",
        )

    def test_candidate_specs_can_select_only_next_family_rotation(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(
            families=[
                "opening_drive_breakout",
                "supertrend_adx_displacement",
                "supertrend_adx_pullback_reclaim",
                "supertrend_adx_turtle_soup_sweep_reversal",
                "supertrend_adx_liquidity_sweep_reclaim",
                "supertrend_adx_pullback_ote_fvg_ob",
                "supertrend_adx_pullback_exit_persistence",
                "supertrend_adx_pullback_exit_persistence_high_conviction",
                "supertrend_adx_pullback_exit_persistence_opening_drive",
                "supertrend_adx_pullback_exit_persistence_opening_drive_soft",
                "supertrend_adx_pullback_exit_persistence_vwap_excursion_cap",
                "vwap_reclaim_persistence",
                "donchian_turtle_breakout",
                "dense_trend_pullback_reclaim",
                "prior_day_extreme_continuation",
                "prior_day_extreme_continuation_mtf_resonance_guard",
                "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
                "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
                "prior_day_liquidity_sweep_reversal",
                "impulse_follow",
                "wpr_extreme_mean_reclaim",
                "nr7_range_expansion",
                "connors_rsi2_rebound",
                "ultimate_ict_zone_volume_spike_reclaim",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap",
                "ultimate_ict_zone_volume_spike_vwap_hold_persistence",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
                "ote_liquidity_sweep_fvg_ob_reclaim",
                "ote_fvg_order_block_reclaim_session_directional_bias",
                "h4_midnight_macd_rsi_pullback",
                "liquidity_purge_rejection",
                "momentum_divergence_reclaim",
                "fractal_liquidity_macd_rsi_divergence_reclaim",
                "fractal_liquidity_macd_divergence_reclaim",
                "silver_bullet_rsi_sniper",
                "session_window_sweep_reclaim",
            ]
        )

        self.assertEqual(
            [spec.key for spec in specs],
            [
                "opening_drive_breakout",
                "vwap_reclaim_persistence",
                "donchian_turtle_breakout",
                "dense_trend_pullback_reclaim",
                "prior_day_extreme_continuation",
                "prior_day_extreme_continuation_mtf_resonance_guard",
                "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
                "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
                "prior_day_liquidity_sweep_reversal",
                "impulse_follow",
                "wpr_extreme_mean_reclaim",
                "nr7_range_expansion",
                "supertrend_adx_displacement",
                "supertrend_adx_turtle_soup_sweep_reversal",
                "supertrend_adx_pullback_reclaim",
                "supertrend_adx_liquidity_sweep_reclaim",
                "supertrend_adx_pullback_ote_fvg_ob",
                "supertrend_adx_pullback_exit_persistence",
                "supertrend_adx_pullback_exit_persistence_high_conviction",
                "supertrend_adx_pullback_exit_persistence_opening_drive",
                "supertrend_adx_pullback_exit_persistence_opening_drive_soft",
                "supertrend_adx_pullback_exit_persistence_vwap_excursion_cap",
                "connors_rsi2_rebound",
                "ultimate_ict_zone_volume_spike_reclaim",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap",
                "ultimate_ict_zone_volume_spike_vwap_hold_persistence",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
                "ote_liquidity_sweep_fvg_ob_reclaim",
                "ote_fvg_order_block_reclaim_session_directional_bias",
                "h4_midnight_macd_rsi_pullback",
                "liquidity_purge_rejection",
                "momentum_divergence_reclaim",
                "fractal_liquidity_macd_rsi_divergence_reclaim",
                "fractal_liquidity_macd_divergence_reclaim",
                "silver_bullet_rsi_sniper",
                "session_window_sweep_reclaim",
            ],
        )

        with self.assertRaisesRegex(ValueError, "unknown candidate families"):
            module.candidate_specs(families=["does_not_exist"])

    def test_candidate_specs_can_select_liquidity_sweep_adx_liquidity_pool_context_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["liquidity_sweep_adx_liquidity_pool_context"])

        self.assertEqual([spec.key for spec in specs], ["liquidity_sweep_adx_liquidity_pool_context"])

    def test_candidate_specs_can_select_reference_hurst_profile_range_compression_release_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["wpr_adx_reference_hurst_profile_range_compression_release"])

        self.assertEqual(
            [spec.key for spec in specs],
            ["wpr_adx_reference_hurst_profile_range_compression_release"],
        )
        self.assertEqual(specs[0].main_regime, "RangeReversion")
        self.assertEqual(specs[0].sub_regime, "PdhPdlFractalLiquiditySweep")
        self.assertEqual(specs[0].profit_factor, "WprAdxTrendAlignedReclaim")
        self.assertEqual(specs[0].child_profit_factor, "HurstProfileMssReclaim")
        self.assertEqual(
            specs[0].extra_profit_factors,
            ("ReferenceHurstProfileRangeCompressionRelease",),
        )

    def test_candidate_specs_can_select_regression_channel_r2_slope_breadth_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["regression_channel_r2_slope_breadth"])

        self.assertEqual([spec.key for spec in specs], ["regression_channel_r2_slope_breadth"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RegressionChannelTrend")
        self.assertEqual(specs[0].profit_factor, "R2SlopePersistence")
        self.assertEqual(specs[0].child_profit_factor, "CrossIndexBreadthConfirmation")
        self.assertEqual(specs[0].extra_profit_factors, ("AtrStopHoldCompression",))
        self.assertEqual(
            specs[0].branch_path_with_factor("1m"),
            "TrendExpansion -> RegressionChannelTrend -> R2SlopePersistence -> "
            "CrossIndexBreadthConfirmation -> AtrStopHoldCompression -> "
            "tomac_idxfut_clean_regression_channel_r2_slope_breadth_1m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="1m")
        self.assertIn("regression_channel_r2_slope_breadth", source)
        self.assertIn("regression_slope_bps_96", source)
        self.assertIn("regression_r2_96", source)
        self.assertIn("cross_index_breadth_proxy", source)
        self.assertIn("atr_stop_hold_compression", source)

    def test_source_universe_includes_tomac_6e_long_history(self) -> None:
        module = self.load_module()

        by_symbol = {source.symbol: source for source in module.source_universe()}

        self.assertIn("6E", by_symbol)
        self.assertEqual(
            by_symbol["6E"].source_csv,
            Path("/Users/thrill3r/Downloads/Tomac/eur future 2015-2025/glbx-mdp3-20150101-20251231.ohlcv-1m.csv"),
        )

    def test_public_family_strategy_source_is_materially_distinct(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        opening_breakout = module.strategy_source(by_key["opening_drive_breakout"], symbol="NQ", timeframe="1m")
        vwap_persist = module.strategy_source(by_key["vwap_reclaim_persistence"], symbol="NQ", timeframe="1m")
        supertrend = module.strategy_source(by_key["supertrend_adx_displacement"], symbol="NQ", timeframe="1m")
        pullback = module.strategy_source(by_key["supertrend_adx_pullback_reclaim"], symbol="NQ", timeframe="1m")
        turtle_soup = module.strategy_source(
            by_key["supertrend_adx_turtle_soup_sweep_reversal"], symbol="NQ", timeframe="1m"
        )
        sweep = module.strategy_source(by_key["supertrend_adx_liquidity_sweep_reclaim"], symbol="NQ", timeframe="1m")
        ote_desc = module.strategy_source(by_key["supertrend_adx_pullback_ote_fvg_ob"], symbol="NQ", timeframe="1m")
        exit_desc = module.strategy_source(by_key["supertrend_adx_pullback_exit_persistence"], symbol="NQ", timeframe="1m")
        high_conv = module.strategy_source(by_key["supertrend_adx_pullback_exit_persistence_high_conviction"], symbol="NQ", timeframe="1m")
        opening_drive = module.strategy_source(by_key["supertrend_adx_pullback_exit_persistence_opening_drive"], symbol="NQ", timeframe="1m")
        opening_drive_soft = module.strategy_source(
            by_key["supertrend_adx_pullback_exit_persistence_opening_drive_soft"],
            symbol="NQ",
            timeframe="1m",
        )
        excursion_cap = module.strategy_source(
            by_key["supertrend_adx_pullback_exit_persistence_vwap_excursion_cap"],
            symbol="NQ",
            timeframe="1m",
        )
        mass_vortex = module.strategy_source(
            by_key["mass_index_vortex_trend_continuation"], symbol="NQ", timeframe="1m"
        )
        aroon_cci = module.strategy_source(
            by_key["aroon_cci_trend_continuation"], symbol="NQ", timeframe="1m"
        )
        aroon_cci_cadence = module.strategy_source(
            by_key["aroon_cci_cadence_lift_symbol_guard"], symbol="NQ", timeframe="1m"
        )
        donchian = module.strategy_source(by_key["donchian_turtle_breakout"], symbol="NQ", timeframe="1m")
        dense_pullback = module.strategy_source(by_key["dense_trend_pullback_reclaim"], symbol="NQ", timeframe="1m")
        prior_day = module.strategy_source(by_key["prior_day_extreme_continuation"], symbol="NQ", timeframe="1m")
        prior_day_mtf_guard = module.strategy_source(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard"], symbol="NQ", timeframe="1m"
        )
        prior_day_mtf_guard_exit = module.strategy_source(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence"],
            symbol="NQ",
            timeframe="1m",
        )
        prior_day_mtf_guard_cusum_deadzone = module.strategy_source(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate"],
            symbol="NQ",
            timeframe="1m",
        )
        opening_drive_twoleg_exit = module.strategy_source(
            by_key["opening_drive_twoleg_continuation_exit_persistence"],
            symbol="NQ",
            timeframe="1m",
        )
        prior_day_sweep = module.strategy_source(by_key["prior_day_liquidity_sweep_reversal"], symbol="NQ", timeframe="1m")
        impulse = module.strategy_source(by_key["impulse_follow"], symbol="NQ", timeframe="1m")
        wpr = module.strategy_source(by_key["wpr_extreme_mean_reclaim"], symbol="NQ", timeframe="1m")
        nr7 = module.strategy_source(by_key["nr7_range_expansion"], symbol="NQ", timeframe="1m")
        connors = module.strategy_source(by_key["connors_rsi2_rebound"], symbol="NQ", timeframe="1m")
        ultimate_ict = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_reclaim"], symbol="NQ", timeframe="1m"
        )
        ultimate_ict_session_open = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap"], symbol="NQ", timeframe="1m"
        )
        ultimate_ict_vwap_hold = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_vwap_hold_persistence"], symbol="NQ", timeframe="1m"
        )
        ultimate_ict_compound = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence"],
            symbol="NQ",
            timeframe="1m",
        )
        wpr_no_be_session_bias = module.strategy_source(
            by_key["wpr_fractal_no_be_session_bias_cap"], symbol="ES", timeframe="1m"
        )
        wpr_no_be_higher_frame_slope = module.strategy_source(
            by_key["wpr_fractal_no_be_higher_frame_slope_confirm"], symbol="ES", timeframe="1m"
        )
        ote_liq = module.strategy_source(by_key["ote_liquidity_sweep_fvg_ob_reclaim"], symbol="NQ", timeframe="1m")
        ote_session_bias = module.strategy_source(
            by_key["ote_fvg_order_block_reclaim_session_directional_bias"], symbol="ES", timeframe="1m"
        )
        h4_midnight = module.strategy_source(by_key["h4_midnight_macd_rsi_pullback"], symbol="NQ", timeframe="1m")
        purge = module.strategy_source(by_key["liquidity_purge_rejection"], symbol="NQ", timeframe="1m")
        divergence = module.strategy_source(by_key["momentum_divergence_reclaim"], symbol="NQ", timeframe="1m")
        fractal_divergence = module.strategy_source(
            by_key["fractal_liquidity_macd_rsi_divergence_reclaim"], symbol="NQ", timeframe="1m"
        )
        midnight_liquidity_macd_divergence = module.strategy_source(
            by_key["midnight_open_liquidity_sweep_macd_divergence_reclaim"], symbol="ES", timeframe="1m"
        )
        silver_bullet = module.strategy_source(by_key["silver_bullet_rsi_sniper"], symbol="NQ", timeframe="1m")

        self.assertIn("opening_drive_breakout", opening_breakout)
        self.assertIn("opening_window", opening_breakout)
        self.assertIn("opening_breakout", opening_breakout)
        self.assertIn("opening_drive_context", opening_breakout)
        self.assertIn('dataframe["close"] > dataframe["prior_high80"]', opening_breakout)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', opening_breakout)
        self.assertIn("supertrend_trend", supertrend)
        self.assertIn("vwap_reclaim_persistence", vwap_persist)
        self.assertIn("session_vwap", vwap_persist)
        self.assertIn("vwap_excursion_long", vwap_persist)
        self.assertIn("reclaim_long", vwap_persist)
        self.assertIn("long_transition | short_transition", vwap_persist)
        self.assertIn("adx14", supertrend)
        self.assertIn("sweep_low40", supertrend)
        self.assertIn("supertrend_adx_displacement", supertrend)
        self.assertIn("supertrend_adx_pullback_reclaim", pullback)
        self.assertIn('dataframe["close"] > dataframe["ema21"]', pullback)
        self.assertIn("supertrend_adx_turtle_soup_sweep_reversal", turtle_soup)
        self.assertIn("TurtleSoupSweepReversal", turtle_soup)
        self.assertIn("killzone_window", turtle_soup)
        self.assertIn("liquidity_sweep", turtle_soup)
        self.assertIn("close_reclaim", turtle_soup)
        self.assertIn("momentum_reversal", turtle_soup)
        self.assertIn("supertrend_adx_liquidity_sweep_reclaim", sweep)
        self.assertIn("sweep_close_reclaim", sweep)
        self.assertIn("supertrend_adx_pullback_ote_fvg_ob", ote_desc)
        self.assertIn("ote_long_62", ote_desc)
        self.assertIn("bull_ob_low", ote_desc)
        self.assertIn("ict_zone", ote_desc)
        self.assertIn("supertrend_adx_pullback_exit_persistence", exit_desc)
        self.assertIn("late_failure", exit_desc)
        self.assertIn('dataframe["close"] < dataframe["session_vwap"]', exit_desc)
        self.assertIn("supertrend_adx_pullback_exit_persistence_high_conviction", high_conv)
        self.assertIn("breakout_bias", high_conv)
        self.assertIn('dataframe["ema55"] > dataframe["ema89"]', high_conv)
        self.assertIn("supertrend_adx_pullback_exit_persistence_opening_drive", opening_drive)
        self.assertIn("minute_of_day_ny", opening_drive)
        self.assertIn("opening_window", opening_drive)
        self.assertIn("supertrend_adx_pullback_exit_persistence_opening_drive_soft", opening_drive_soft)
        self.assertIn("opening_drive_context", opening_drive_soft)
        self.assertIn("breakout_bias", opening_drive_soft)
        self.assertIn("(opening_drive_context | breakout_bias)", opening_drive_soft)
        self.assertIn("supertrend_adx_pullback_exit_persistence_vwap_excursion_cap", excursion_cap)
        self.assertIn("vwap_excursion_ok", excursion_cap)
        self.assertIn("reclaim_discount_ok", excursion_cap)
        self.assertIn("exit_persistence_guard = True", excursion_cap)
        self.assertIn("mass_index_vortex_trend_continuation", mass_vortex)
        self.assertIn("mass_index25", mass_vortex)
        self.assertIn("vortex_plus14", mass_vortex)
        self.assertIn("vortex_minus14", mass_vortex)
        self.assertIn("economic_slope", mass_vortex)
        self.assertIn("ema21_slope_bps_12", mass_vortex)
        self.assertIn("ema55_slope_bps_48", mass_vortex)
        self.assertIn("breakout_hold", mass_vortex)
        self.assertIn("aroon_cci_trend_continuation", aroon_cci)
        self.assertIn("aroon_up25", aroon_cci)
        self.assertIn("aroon_down25", aroon_cci)
        self.assertIn("cci20", aroon_cci)
        self.assertIn("directional_persistence", aroon_cci)
        self.assertIn("cci_impulse", aroon_cci)
        self.assertIn("economic_slope", aroon_cci)
        self.assertIn("continuation_hold", aroon_cci)
        self.assertIn("aroon_cci_cadence_lift_symbol_guard", aroon_cci_cadence)
        self.assertIn('metadata.get("pair") in ("NQ/USD", "ES/USD")', aroon_cci_cadence)
        self.assertIn("cci_reacceleration", aroon_cci_cadence)
        self.assertIn("cci_zero_reclaim", aroon_cci_cadence)
        self.assertIn("cadence_lift_hold", aroon_cci_cadence)
        self.assertIn("economic_slope", aroon_cci_cadence)
        self.assertIn('metadata.get("pair") != "NQ/USD"', donchian)
        self.assertIn("prior_high80", donchian)
        self.assertIn("donchian_turtle_breakout", donchian)
        self.assertIn("dense_trend_pullback_reclaim", dense_pullback)
        self.assertIn('dataframe["ema96"] > dataframe["ema390"]', dense_pullback)
        self.assertIn('dataframe["close"].shift(5) < dataframe["ema32"].shift(5)', dense_pullback)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', dense_pullback)
        self.assertIn("prior_day_extreme_continuation", prior_day)
        self.assertIn("prior_day_high", prior_day)
        self.assertIn("prior_day_range", prior_day)
        self.assertIn("persist = crossed & crossed.shift(1) & crossed.shift(2)", prior_day)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', prior_day)
        self.assertIn(
            "TrendExpansion -> PriorDayExtremeContinuation -> "
            "PriorDayExtremeContinuationMtfResonanceGuard -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_1m_v1",
            prior_day_mtf_guard,
        )
        self.assertIn("prior_day_extreme_continuation_mtf_resonance_guard", prior_day_mtf_guard)
        self.assertIn("mtf_fast_alignment", prior_day_mtf_guard)
        self.assertIn("mtf_slow_alignment", prior_day_mtf_guard)
        self.assertIn("mtf_resonance_guard", prior_day_mtf_guard)
        self.assertIn(
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> "
            "ExitPersistence -> tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence_1m_v1",
            prior_day_mtf_guard_exit,
        )
        self.assertIn(
            "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
            prior_day_mtf_guard_exit,
        )
        self.assertIn("exit_persistence_window", prior_day_mtf_guard_exit)
        self.assertIn("persistence_bias", prior_day_mtf_guard_exit)
        self.assertIn("exit_persistence_guard = True", prior_day_mtf_guard_exit)
        self.assertIn(
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> "
            "CusumDeadzoneGate -> tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate_1m_v1",
            prior_day_mtf_guard_cusum_deadzone,
        )
        self.assertIn(
            "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
            prior_day_mtf_guard_cusum_deadzone,
        )
        self.assertIn("cusum_positive_event", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn("deadzone_excursion", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn("rearm_breakout", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn("cooldown_bars_remaining", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn(
            "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation -> ExitPersistence -> tomac_idxfut_clean_opening_drive_twoleg_continuation_exit_persistence_1m_v1",
            opening_drive_twoleg_exit,
        )
        self.assertIn("opening_drive_twoleg_continuation_exit_persistence", opening_drive_twoleg_exit)
        self.assertIn("second_leg_reclaim", opening_drive_twoleg_exit)
        self.assertIn("exit_persistence_guard = True", opening_drive_twoleg_exit)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', opening_drive_twoleg_exit)
        self.assertIn("prior_day_liquidity_sweep_reversal", prior_day_sweep)
        self.assertIn("sweep_depth", prior_day_sweep)
        self.assertIn('dataframe["low"] < dataframe["prior_day_low"]', prior_day_sweep)
        self.assertIn('dataframe["close"] > dataframe["prior_day_low"]', prior_day_sweep)
        self.assertIn('dataframe["minute_of_day_ny"].between(9 * 60 + 35, 14 * 60 + 30)', prior_day_sweep)
        self.assertIn("down_extension", prior_day_sweep)
        self.assertIn("impulse_follow", impulse)
        self.assertIn("bar_range_atr", impulse)
        self.assertIn('dataframe["body_atr"].between(0.45, 3.2)', impulse)
        self.assertIn('dataframe["close"] > dataframe["close"].shift(1)', impulse)
        self.assertIn("wpr_extreme_mean_reclaim", wpr)
        self.assertIn("wpr14", wpr)
        self.assertIn('dataframe["wpr14"].lt(-80)', wpr)
        self.assertIn('dataframe["close"] > dataframe["range_low40"]', wpr)
        self.assertIn("nr7_range", nr7)
        self.assertIn("prior_nr7", nr7)
        self.assertIn("connors_rsi", connors)
        self.assertIn("rsi2", connors)
        self.assertIn("ultimate_ict_zone_volume_spike_reclaim", ultimate_ict)
        self.assertIn("KillzoneLiquiditySweep", ultimate_ict)
        self.assertIn("extreme_wpr", ultimate_ict)
        self.assertIn("ict_zone", ultimate_ict)
        self.assertIn("volume_spike", ultimate_ict)
        self.assertIn("ultimate_ict_zone_volume_spike_session_open_bias_cap", ultimate_ict_session_open)
        self.assertIn("SessionOpenBiasCap", ultimate_ict_session_open)
        self.assertIn("session_open_bias", ultimate_ict_session_open)
        self.assertIn("vwap_reclaim", ultimate_ict_session_open)
        self.assertIn("macd_bias", ultimate_ict_session_open)
        self.assertIn("ultimate_ict_zone_volume_spike_vwap_hold_persistence", ultimate_ict_vwap_hold)
        self.assertIn("VwapHoldPersistence", ultimate_ict_vwap_hold)
        self.assertIn("vwap_reclaim", ultimate_ict_vwap_hold)
        self.assertIn("vwap_hold", ultimate_ict_vwap_hold)
        self.assertIn("persistence_bias", ultimate_ict_vwap_hold)
        self.assertIn(
            "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
            ultimate_ict_compound,
        )
        self.assertIn("SessionOpenBiasCap -> VwapHoldPersistence", ultimate_ict_compound)
        self.assertIn("session_open_bias", ultimate_ict_compound)
        self.assertIn("vwap_reclaim", ultimate_ict_compound)
        self.assertIn("vwap_hold", ultimate_ict_compound)
        self.assertIn("persistence_bias", ultimate_ict_compound)
        self.assertIn("wpr_fractal_no_be_session_bias_cap", wpr_no_be_session_bias)
        self.assertIn("PdhPdlFractalLiquiditySweep", wpr_no_be_session_bias)
        self.assertIn("SessionBiasCap", wpr_no_be_session_bias)
        self.assertIn("session_bias_cap_window", wpr_no_be_session_bias)
        self.assertIn("session_open_bias", wpr_no_be_session_bias)
        self.assertIn("vwap_hold", wpr_no_be_session_bias)
        self.assertIn("wpr_fractal_no_be_higher_frame_slope_confirm", wpr_no_be_higher_frame_slope)
        self.assertIn("HigherFrameSlopeConfirm", wpr_no_be_higher_frame_slope)
        self.assertIn("higher_frame_slope_confirm", wpr_no_be_higher_frame_slope)
        self.assertIn("ema55_slope_atr", wpr_no_be_higher_frame_slope)
        self.assertIn("ema144_slope_atr", wpr_no_be_higher_frame_slope)
        self.assertIn("ote_liquidity_sweep_fvg_ob_reclaim", ote_liq)
        self.assertIn("OteLiquiditySweepReclaim", ote_liq)
        self.assertIn("liquidity_sweep", ote_liq)
        self.assertIn("near_fvg", ote_liq)
        self.assertIn("near_ob", ote_liq)
        self.assertIn("ote_fvg_order_block_reclaim_session_directional_bias", ote_session_bias)
        self.assertIn("LiquiditySweepIctRetracement", ote_session_bias)
        self.assertIn("SessionDirectionalBias", ote_session_bias)
        self.assertIn("bull_session_bias", ote_session_bias)
        self.assertIn("bear_session_bias", ote_session_bias)
        self.assertIn("mtf_bias_long", ote_session_bias)
        self.assertIn("mtf_bias_short", ote_session_bias)
        self.assertIn("liquidity_sweep_short", ote_session_bias)
        self.assertIn("h4_midnight_macd_rsi_pullback", h4_midnight)
        self.assertIn("h4_structure_bias", h4_midnight)
        self.assertIn("midnight_open", h4_midnight)
        self.assertIn("macd_reclaim", h4_midnight)
        self.assertIn("liquidity_purge_rejection", purge)
        self.assertIn("killzone_window", purge)
        self.assertIn("purge", purge)
        self.assertIn("macd_hist", purge)
        self.assertIn("momentum_divergence_reclaim", divergence)
        self.assertIn("momentum_divergence", divergence)
        self.assertIn('dataframe["macd_line"] > dataframe["macd_line"].shift(5)', divergence)
        self.assertIn("fractal_liquidity_macd_rsi_divergence_reclaim", fractal_divergence)
        self.assertIn("FractalLiquiditySweep", fractal_divergence)
        self.assertIn("midnight_open", fractal_divergence)
        self.assertIn("macd_divergence", fractal_divergence)
        self.assertIn("structure_bias_long", fractal_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)', fractal_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 50)', fractal_divergence)
        self.assertIn('dataframe["rsi14"].gt(30)', fractal_divergence)
        self.assertIn('dataframe["rsi14"].lt(70)', fractal_divergence)
        self.assertIn(
            "midnight_open_liquidity_sweep_macd_divergence_reclaim",
            midnight_liquidity_macd_divergence,
        )
        self.assertIn("MidnightOpenDiscountPremiumBias", midnight_liquidity_macd_divergence)
        self.assertIn("midnight_open", midnight_liquidity_macd_divergence)
        self.assertIn("liq_low20", midnight_liquidity_macd_divergence)
        self.assertIn("liq_high20", midnight_liquidity_macd_divergence)
        self.assertIn("macd_line", midnight_liquidity_macd_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)', midnight_liquidity_macd_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)', midnight_liquidity_macd_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(13 * 60 + 30, 16 * 60)', midnight_liquidity_macd_divergence)
        self.assertIn("silver_bullet_rsi_sniper", silver_bullet)
        self.assertIn("silver_bullet_window", silver_bullet)
        self.assertIn('dataframe["minute_of_day_ny"].between(10 * 60, 11 * 60)', silver_bullet)
        self.assertIn('dataframe["rsi14"].between(22, 40)', silver_bullet)
        self.assertNotIn(
            "shift(-",
            opening_breakout
            + vwap_persist
            + supertrend
            + pullback
            + turtle_soup
            + sweep
            + ote_desc
            + exit_desc
            + high_conv
            + opening_drive
            + opening_drive_soft
            + excursion_cap
            + donchian
            + dense_pullback
            + prior_day
            + prior_day_mtf_guard
            + prior_day_mtf_guard_exit
            + prior_day_sweep
            + impulse
            + wpr
            + nr7
            + connors
            + ultimate_ict
            + ultimate_ict_session_open
            + ultimate_ict_vwap_hold
            + ultimate_ict_compound
            + wpr_no_be_session_bias
            + ote_liq
            + h4_midnight
            + purge
            + divergence
            + fractal_divergence
            + silver_bullet,
        )

    def test_strategy_source_uses_symbol_specific_product_provenance_label(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        fx_source = module.strategy_source(by_key["connors_rsi2_rebound"], symbol="6E", timeframe="1m")
        index_source = module.strategy_source(by_key["nr7_range_expansion"], symbol="NQ", timeframe="1m")
        opening_source = module.strategy_source(by_key["opening_drive_breakout"], symbol="YM", timeframe="1m")

        self.assertIn("product: fx_futures", fx_source)
        self.assertIn("product: equity_index", index_source)
        self.assertIn("product: equity_index", opening_source)

    def test_strategy_source_produces_session_open_when_child_branches_reference_it(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        source = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_exit_persistence"], symbol="NQ", timeframe="1m"
        )

        self.assertIn('dataframe["close"] > dataframe["session_open"]', source)
        self.assertIn('dataframe["session_open"] =', source)

    def test_timeframe_class_suffix_uses_exact_ladder_mapping(self) -> None:
        module = self.load_module()

        self.assertEqual(module.timeframe_class_suffix("1m"), "OneMin")
        self.assertEqual(module.timeframe_class_suffix("5m"), "FiveMin")
        self.assertEqual(module.timeframe_class_suffix("15m"), "FifteenMin")
        self.assertEqual(module.timeframe_class_suffix("30m"), "ThirtyMin")
        self.assertEqual(module.timeframe_class_suffix("1h"), "OneHour")
        self.assertEqual(module.timeframe_class_suffix("4h"), "FourHour")
        self.assertEqual(module.timeframe_class_suffix("1d"), "OneDay")

    def test_aq_workspace_timerange_matches_clean_window(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            workspace = module.prepare_aq_workspace(
                Path(tmp),
                symbols=["ES"],
                timeframe="5m",
                start="2025-03-01",
                end="2025-03-10",
            )
            config = json.loads((workspace / "config.tomac.json").read_text(encoding="utf-8"))
            copied_runner = (workspace / "run_tomac.py").read_text(encoding="utf-8")

        self.assertEqual(config["timerange"], "20250301-20250310")
        self.assertEqual(config["trading_mode"], "futures")
        self.assertEqual(config["margin_mode"], "isolated")
        self.assertEqual(config["dataformat_ohlcv"], "feather")

        self.assertIn("def _synthetic_leverage_tiers", copied_runner)
        self.assertIn("exchange._leverage_tiers[pair]", copied_runner)

    def test_stage_aq_inputs_uses_futures_datadir(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="5min"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(clean_dir / "ES_USD-5m.feather")

            staged = module.stage_aq_inputs(
                root,
                symbols=["ES"],
                timeframe="5m",
                start="2025-03-17",
                end="2025-03-18",
            )

            staged_path = Path(staged["data"][0])
            self.assertEqual(
                staged_path,
                root / "aq_workspaces/5m/user_data/data/futures/ES_USD-5m-futures.feather",
            )
            self.assertTrue(staged_path.exists())
            self.assertEqual(
                staged["strategy_specs"][0]["branch_path"],
                "TrendExpansion -> SessionLiquidity -> OpeningDriveRvolVwapContinuation -> "
                "tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1",
            )

    def test_score_rows_keeps_symbol_specific_regime_branch_and_cost_gate(self) -> None:
        module = self.load_module()

        specs = module.generated_strategy_specs(["ES"], "5m")
        stdout = "\n".join(
            [
                "---",
                "strategy:         TomacESOpeningDriveRvolVwapContinuationFiveMinCleanV1",
                "pairs:            ES/USD,YM/USD,NQ/USD",
                "sharpe:           1.8000",
                "sortino:          2.1000",
                "calmar:           1.2000",
                "total_profit_pct: 200.0000",
                "trade_count:      1500",
                "win_rate_pct:     55.0000",
                "profit_factor:    1.4500",
                "per_pair:",
                "  ES/USD: sharpe=1.80 trades=1500 profit_pct=200.00 dd_pct=-4.00 wr=55.0 pf=1.45",
                "  YM/USD: sharpe=9.99 trades=999 profit_pct=999.00 dd_pct=-1.00 wr=99.0 pf=9.99",
            ]
        )

        rows = module.score_rows(stdout, specs)
        per_pair = [row for row in rows if row["scope"] == "per_pair"]

        self.assertEqual(len(per_pair), 1)
        self.assertEqual(per_pair[0]["symbol"], "ES")
        self.assertTrue(per_pair[0]["gate1_survivor"])
        self.assertEqual(
            per_pair[0]["branch_path"],
            "TrendExpansion -> SessionLiquidity -> OpeningDriveRvolVwapContinuation -> "
            "tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1",
        )
        self.assertAlmostEqual(per_pair[0]["5bps_per_side_total_profit_pct"], 50.0)

    def test_score_rows_uses_symbol_specific_futures_cost_for_gate1(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "ES",
                "pair": "ES/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticCostProbe",
                "factor_id": "synthetic_cost_probe",
                "branch_path": "TrendExpansion -> SyntheticCostProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 120,
                "wins": 70,
                "losses": 50,
                "days": 60,
                "total_profit_pct": 20.0,
                "representative_entry_price": 5200.0,
            }
        )

        self.assertEqual(row["cost_profile_id"], "CME_ES_IBKR_verified_20260530_v1")
        self.assertGreater(row["instrument_round_trip_cost_pct"], 0.0)
        self.assertLess(row["instrument_round_trip_cost_pct"], 0.10)
        self.assertGreater(row["instrument_cost_total_profit_pct"], row["5bps_per_side_total_profit_pct"])
        self.assertTrue(row["survives_instrument_cost"])
        self.assertTrue(row["gate1_survivor"])

    def test_verified_es_nq_ym_cost_profiles_use_ibkr_fee_components(self) -> None:
        module = self.load_module()

        expected = {
            "ES": ("CME", 0.25, 12.5),
            "NQ": ("CME", 0.25, 5.0),
            "YM": ("CBOT", 1.0, 5.0),
        }
        for symbol, (exchange, tick_size, tick_value) in expected.items():
            with self.subTest(symbol=symbol):
                profile = module.futures_cost_profile(symbol)

                self.assertIsNotNone(profile)
                self.assertEqual(profile.exchange, exchange)
                self.assertEqual(profile.tick_size, tick_size)
                self.assertEqual(profile.tick_value, tick_value)
                self.assertEqual(profile.commission_per_contract_side, 0.85)
                self.assertEqual(profile.exchange_fees_per_contract_side, 1.38)
                self.assertEqual(profile.regulatory_fees_per_contract_side, 0.02)
                self.assertAlmostEqual(
                    2.0
                    * (
                        profile.commission_per_contract_side
                        + profile.exchange_fees_per_contract_side
                        + profile.regulatory_fees_per_contract_side
                    ),
                    4.50,
                )
                self.assertIn("IBKR", profile.source)

    def test_wrapper_uses_shared_verified_micro_futures_cost_profile(self) -> None:
        module = self.load_module()

        profile = module.futures_cost_profile("MNQ")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.profile_id, "CME_MNQ_IBKR_verified_20260530_v1")
        self.assertEqual(profile.root_symbol, "MNQ")
        self.assertAlmostEqual(profile.all_in_per_contract_per_side, 0.62)
        self.assertTrue(profile.verified_for_promotion)

    def test_nq_realistic_contract_cost_wall_is_sub_bps_not_10bps_stress(self) -> None:
        module = self.load_module()

        profile = module.futures_cost_profile("NQ")

        self.assertIsNotNone(profile)
        self.assertAlmostEqual(profile.round_trip_fee_cash(), 4.50)
        self.assertAlmostEqual(profile.round_trip_cost_cash(), 19.50)
        self.assertLess(profile.round_trip_cost_pct(15000.0) * 100.0, 0.70)

    def test_cost_wall_buckets_distinguish_bps_false_negative_from_no_edge_churn(self) -> None:
        module = self.load_module()

        false_negative = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "NQ",
                "pair": "NQ/USD",
                "timeframe": "1m",
                "strategy_name": "SyntheticBpsFalseNegative",
                "factor_id": "synthetic_bps_false_negative",
                "branch_path": "TrendExpansion -> SyntheticBpsFalseNegative",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 100,
                "wins": 52,
                "losses": 48,
                "days": 100,
                "total_profit_pct": 1.0,
                "representative_entry_price": 15000.0,
            }
        )
        churn = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "NQ",
                "pair": "NQ/USD",
                "timeframe": "1m",
                "strategy_name": "SyntheticNoEdgeChurn",
                "factor_id": "synthetic_no_edge_churn",
                "branch_path": "MicroScalp -> SyntheticNoEdgeChurn",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 26304,
                "wins": 13200,
                "losses": 13104,
                "days": 1260,
                "total_profit_pct": 8.41728,
                "representative_entry_price": 15000.0,
            }
        )

        self.assertTrue(false_negative["survives_instrument_cost"])
        self.assertFalse(false_negative["survives_5bps_per_side"])
        self.assertEqual(false_negative["cost_wall_bucket"], "bps_stress_false_negative_recheck")
        self.assertGreater(false_negative["gross_edge_bps_per_trade"], false_negative["instrument_cost_bps_per_trade"])

        self.assertFalse(churn["survives_instrument_cost"])
        self.assertEqual(churn["cost_wall_bucket"], "zero_edge_churn_not_rescued_by_realistic_cost")
        self.assertLess(churn["gross_edge_bps_per_trade"], churn["instrument_cost_bps_per_trade"])

    def test_score_rows_uses_actual_backtest_span_for_density(self) -> None:
        module = self.load_module()

        specs = module.generated_strategy_specs(["NQ"], "1m", families=["aroon_cci_trend_continuation"])
        stdout = "\n".join(
            [
                "Backtested 2021-01-04 02:40:00 -> 2021-02-15 23:16:00 | Max open trades : 1",
                "---",
                "strategy:         TomacNQAroonCciTrendContinuationOneMinCleanV1",
                "pairs:            NQ/USD",
                "sharpe:           2.8979",
                "sortino:          9.2213",
                "calmar:           128.0706",
                "total_profit_pct: 4.0000",
                "trade_count:      50",
                "win_rate_pct:     58.8235",
                "profit_factor:    2.3566",
                "per_pair:",
                "  NQ/USD: sharpe=2.8979 trades=50 profit_pct=6.00 dd_pct=-0.71 wr=58.8 pf=2.36",
            ]
        )

        rows = module.score_rows(stdout, specs)
        per_pair = next(row for row in rows if row["scope"] == "per_pair")

        self.assertGreater(per_pair["trades_per_day"], 1.0)
        self.assertTrue(per_pair["density_target_1_to_3_per_day"])

    def test_score_rows_recovers_freqtrade_result_table_when_timeout_precedes_machine_block(self) -> None:
        module = self.load_module()

        specs = module.generated_strategy_specs(["NQ"], "1m", families=["regression_channel_r2_slope_breadth"])
        stdout = "\n".join(
            [
                "Result for strategy TomacNQRegressionChannelR2SlopeBreadthOneMinCleanV1",
                "│ NQ/USD │    304 │         0.02 │       7547.257 │         7.55 │      0:57:00 │  148     0   156  48.7 │",
                "│ ES/USD │      0 │          0.0 │          0.000 │          0.0 │         0:00 │    0     0     0     0 │",
                "│  TOTAL │    304 │         0.02 │       7547.257 │         7.55 │      0:57:00 │  148     0   156  48.7 │",
                "│ Backtesting from              │ 2021-01-04 02:40:00            │",
                "│ Backtesting to                │ 2025-12-31 00:00:00            │",
                "│ Total/Daily Avg Trades        │ 304 / 0.17                     │",
                "│ Total profit %                │ 7.55%                          │",
                "│ Sortino                       │ 0.43                           │",
                "│ Sharpe                        │ 0.24                           │",
                "│ Calmar                        │ 2.34                           │",
                "│ Profit factor                 │ 1.20                           │",
                "│ Max % of account underwater   │ 3.38%                          │",
                "Backtested 2021-01-04 02:40:00 -> 2025-12-31 00:00:00 | Max open trades : 1",
                "│ TomacNQRegressionChannelR2SlopeBreadthOneMinCleanV1 │    304 │         0.02 │       7547.257 │         7.55 │      0:57:00 │  148     0   156  48.7 │ 3543.122 USD  3.38% │",
            ]
        )

        rows = module.score_rows(stdout, specs)
        per_pair = next(row for row in rows if row["scope"] == "per_pair")

        self.assertEqual(per_pair["symbol"], "NQ")
        self.assertEqual(per_pair["trade_count"], 304)
        self.assertAlmostEqual(per_pair["total_profit_pct"], 7.55)
        self.assertAlmostEqual(per_pair["profit_factor"], 1.20)
        self.assertTrue(per_pair["survives_instrument_cost"])
        self.assertFalse(per_pair["survives_5bps_per_side"])
        self.assertFalse(per_pair["density_target_1_to_3_per_day"])
        self.assertFalse(per_pair["gate1_survivor"])

    def test_gate1_survivor_accepts_bidirectional_parent_replay_direction(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "ES",
                "pair": "ES/USD",
                "timeframe": "1m",
                "strategy_name": "TomacESWprFractalNoBeFullTargetOneMinCleanV1",
                "factor_id": "tomac_idxfut_clean_wpr_fractal_no_be_fulltarget_1m_v1",
                "branch_path": (
                    "RangeReversion -> PdhPdlFractalLiquiditySweep -> "
                    "WprFractalNoBreakEvenFullTarget -> "
                    "tomac_idxfut_clean_wpr_fractal_no_be_fulltarget_1m_v1"
                ),
                "family": "wpr_fractal_no_be_fulltarget",
                "direction": "long_short",
                "trade_count": 120,
                "wins": 80,
                "losses": 40,
                "days": 60,
                "total_profit_pct": 20.0,
                "representative_entry_price": 5200.0,
            }
        )

        self.assertTrue(row["direction_consistent_local"])
        self.assertTrue(row["gate1_survivor"])

    def test_gate1_survivor_uses_verified_futures_contract_cost_not_5bps_stress(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "NQ",
                "pair": "NQ/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticHardCostProbe",
                "factor_id": "synthetic_hard_cost_probe",
                "branch_path": "RangeConsolidation -> SyntheticHardCostProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 1362,
                "wins": 690,
                "losses": 671,
                "days": 1260,
                "total_profit_pct": 18.17,
                "representative_entry_price": 18000.0,
            }
        )

        self.assertTrue(row["density_target_1_to_3_per_day"])
        self.assertTrue(row["survives_instrument_cost"])
        self.assertFalse(row["survives_1bps_per_side"])
        self.assertFalse(row["survives_2bps_per_side"])
        self.assertFalse(row["survives_5bps_per_side"])
        self.assertEqual(row["cost_stress_5bps_role"], "telemetry_not_futures_hard_gate")
        self.assertTrue(row["gate1_survivor"])

    def test_gate1_survivor_blocks_unverified_default_futures_cost_profile(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "RTY",
                "pair": "RTY/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticUnverifiedDefaultCostProfile",
                "factor_id": "synthetic_unverified_default_cost_profile",
                "branch_path": "TrendExpansion -> SyntheticUnverifiedDefaultCostProfile",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 120,
                "wins": 70,
                "losses": 50,
                "days": 60,
                "total_profit_pct": 20.0,
                "representative_entry_price": 2100.0,
            }
        )

        self.assertEqual(row["cost_profile_id"], "CME_RTY_default_v1")
        self.assertEqual(row["cost_model_status"], "default_assumption_unverified")
        self.assertFalse(row["cost_model_verified_for_promotion"])
        self.assertTrue(row["survives_instrument_cost"])
        self.assertEqual(row["cost_model_blocker"], "cost_model_unverified")
        self.assertFalse(row["gate1_survivor"])

    def test_cost_survival_is_separate_from_trade_sample_floor(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "ES",
                "pair": "ES/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticSparseProfitableProbe",
                "factor_id": "synthetic_sparse_profitable_probe",
                "branch_path": "TrendExpansion -> SyntheticSparseProfitableProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 20,
                "wins": 12,
                "losses": 8,
                "days": 10,
                "total_profit_pct": 100.0,
                "representative_entry_price": 5200.0,
            }
        )

        self.assertTrue(row["survives_5bps_per_side"])
        self.assertTrue(row["survives_instrument_cost"])
        self.assertFalse(row["minimum_trade_sample_floor_met"])
        self.assertTrue(row["density_target_1_to_3_per_day"])
        self.assertFalse(row["gate1_survivor"])

    def test_gate_summary_does_not_promote_retired_transition_fields_as_hard_gates(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_1m.out"
            stdout_path.parent.mkdir(parents=True)
            stdout_path.write_text("", encoding="utf-8")

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="1m",
                command={
                    "name": "run_tomac_1m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_1m.err"),
                    "exit_path": str(root / "checks/run_tomac_1m.exit"),
                },
                specs=[],
            )

        required_next = gate["hard_promotion_gates_required_next"]
        self.assertNotIn("transition_hazard_lt_0_60", required_next)
        self.assertNotIn("pda_hybrid_alignment_true", required_next)
        self.assertIn("duration_readiness_confirmed", required_next)
        self.assertIn("path_ranker_or_catboost_runtime_score_visible", required_next)
        self.assertIn("execution_tree_readiness_gte_0_65", required_next)

    def test_gate_summary_reports_realistic_cost_survivors_without_gate1_promotion(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_1m.out"
            stdout_path.parent.mkdir(parents=True)
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        "strategy:         TomacNQRegressionChannelR2SlopeBreadthOneMinCleanV1",
                        "pairs:            NQ/USD",
                        "sharpe:           0.2400",
                        "sortino:          0.4300",
                        "calmar:           2.3400",
                        "total_profit_pct: 7.5500",
                        "trade_count:      304",
                        "win_rate_pct:     48.7000",
                        "profit_factor:    1.2000",
                        "per_pair:",
                        "  NQ/USD: sharpe=0.24 trades=304 profit_pct=7.55 dd_pct=-3.38 wr=48.7 pf=1.20",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="1m",
                command={
                    "name": "run_tomac_1m",
                    "exit": 124,
                    "timed_out": True,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_1m.err"),
                    "exit_path": str(root / "checks/run_tomac_1m.exit"),
                },
                specs=module.generated_strategy_specs(["NQ"], "1m", families=["regression_channel_r2_slope_breadth"]),
                clean_bundles=[
                    {
                        "symbol": "NQ",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth",
                    }
                ],
            )

        self.assertEqual(gate["decision"], "observation_realistic_cost_survivor_needs_non_cost_gate_repair")
        self.assertFalse(gate["downstream_allowed"])
        self.assertEqual([row["pair"] for row in gate["realistic_cost_survivors_before_gate1"]], ["NQ/USD"])
        self.assertEqual([row["pair"] for row in gate["bps_stress_false_negative_rechecks"]], ["NQ/USD"])
        self.assertEqual(gate["realistic_cost_survivors_before_gate1"][0]["cost_wall_bucket"], "bps_stress_false_negative_recheck")
        self.assertFalse(gate["survivors_instrument_cost"])

    def test_gate_summary_blocks_downstream_without_eth_full_session_evidence(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_1m.out"
            stdout_path.parent.mkdir(parents=True)
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        "strategy:         TomacESOpeningDriveRvolVwapContinuationOneMinCleanV1",
                        "pairs:            ES/USD",
                        "sharpe:           2.0000",
                        "sortino:          2.0000",
                        "calmar:           2.0000",
                        "total_profit_pct: 200.0000",
                        "trade_count:      1500",
                        "win_rate_pct:     55.0000",
                        "profit_factor:    1.5000",
                        "per_pair:",
                        "  ES/USD: sharpe=2.00 trades=1500 profit_pct=200.00 dd_pct=-4.00 wr=55.0 pf=1.50",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="1m",
                command={
                    "name": "run_tomac_1m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_1m.err"),
                    "exit_path": str(root / "checks/run_tomac_1m.exit"),
                },
                specs=module.generated_strategy_specs(["ES"], "1m", families=["opening_drive_rvol_vwap_continuation"]),
                clean_bundles=[
                    {
                        "symbol": "ES",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": False,
                        "eth_full_retained_coverage_status": "session_scope_unverified_no_rows_outside_rth",
                    }
                ],
            )

        self.assertEqual(gate["decision"], "blocked_session_scope_unverified_no_downstream")
        self.assertFalse(gate["downstream_allowed"])
        self.assertFalse(gate["pre_bayes_allowed"])
        self.assertFalse(gate["bbn_allowed"])
        self.assertFalse(gate["survivors_5bps"])
        self.assertEqual(gate["session_scope"], "ETH/full_retained_session")
        self.assertFalse(gate["eth_full_retained_session_evidence"])

    def test_gate_summary_uses_instrument_cost_as_authority_and_5bps_as_stress(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_5m.out"
            stdout_path.parent.mkdir(parents=True)
            specs = module.generated_strategy_specs(
                ["NQ"],
                "5m",
                families=["opening_drive_rvol_vwap_continuation"],
            )
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        f"strategy:         {specs[0].class_name}",
                        "pairs:            NQ/USD",
                        "sharpe:           1.2000",
                        "sortino:          1.8000",
                        "calmar:           2.1000",
                        "total_profit_pct: 18.1700",
                        "trade_count:      1362",
                        "win_rate_pct:     50.6610",
                        "profit_factor:    1.1200",
                        "per_pair:",
                        "  NQ/USD: sharpe=1.20 trades=1362 profit_pct=18.17 dd_pct=-4.00 wr=50.7 pf=1.12",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="5m",
                command={
                    "name": "run_tomac_5m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_5m.err"),
                    "exit_path": str(root / "checks/run_tomac_5m.exit"),
                },
                specs=specs,
                clean_bundles=[
                    {
                        "symbol": "NQ",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth",
                    }
                ],
            )

        self.assertEqual(gate["decision"], "gate1_autoquant_instrument_cost_density_survivor_downstream_required")
        self.assertTrue(gate["downstream_allowed"])
        self.assertEqual(gate["cost_gate_authority"], "instrument_cost")
        self.assertEqual(gate["cost_stress_5bps_role"], "telemetry_not_futures_hard_gate")
        self.assertEqual(len(gate["survivors_instrument_cost"]), 1)
        self.assertEqual(gate["survivors_declared_cost"], gate["survivors_instrument_cost"])
        self.assertEqual(gate["raw_survivors_before_session_scope"], gate["raw_instrument_cost_survivors_before_session_scope"])
        survivor = gate["survivors_instrument_cost"][0]
        self.assertTrue(survivor["survives_instrument_cost"])
        self.assertFalse(survivor["survives_5bps_per_side"])
        self.assertEqual(gate["survivors_5bps"], [])
        self.assertEqual(gate["cost_stress_survivors_5bps"], [])

    def test_run_reuse_clean_loads_existing_bundle_without_raw_source(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            feather = clean_dir / "ES_USD-5m.feather"
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="5min"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(feather)
            bundle = {
                "symbol": "ES",
                "source_csv": "/does/not/exist.csv",
                "timeframes": {
                    "5m": {
                        "symbol": "ES",
                        "timeframe": "5m",
                        "quality_ok": True,
                        "feather": str(feather),
                    }
                },
            }
            (clean_dir / "clean_quality.json").write_text(json.dumps(bundle), encoding="utf-8")
            original_universe = module.source_universe
            module.source_universe = lambda: [
                module.TomacSource(symbol="ES", source_csv=Path("/does/not/exist.csv"))
            ]
            try:
                summary = module.run(
                    module.argparse.Namespace(
                        root=str(root),
                        compact_root=str(root / "compact"),
                        symbols="ES",
                        start="2025-03-17",
                        end="2025-03-18",
                        timeframes="5m",
                        max_rows=None,
                        chunksize=10,
                        clean_only=True,
                        reuse_clean=True,
                        aq_smoke_timeframe=None,
                        aq_symbol_limit=1,
                        timeout=10,
                    )
                )
            finally:
                module.source_universe = original_universe

            self.assertEqual(summary["clean_bundles"][0]["source_csv"], "/does/not/exist.csv")
            self.assertEqual(summary["aq_staging"], [])

    def test_generated_strategy_specs_can_select_camarilla_r3_s3_reclaim_branch(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        spec = by_key["camarilla_r3_s3_reclaim"]
        generated = module.generated_strategy_specs(
            ["NQ"],
            "1m",
            families=["camarilla_r3_s3_reclaim"],
        )

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(generated[0].class_name, "TomacNQCamarillaR3S3ReclaimOneMinCleanV1")
        self.assertEqual(generated[0].factor_id, "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1")
        self.assertEqual(
            generated[0].branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1 -> "
            "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1",
        )

    def test_generated_strategy_for_camarilla_r3_s3_reclaim_uses_prior_session_reclaim(self) -> None:
        module = self.load_module()

        spec = next(item for item in module.candidate_specs() if item.key == "camarilla_r3_s3_reclaim")
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1 -> "
            "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1",
            source,
        )
        self.assertIn('elif "camarilla_r3_s3_reclaim" == "camarilla_r3_s3_reclaim":', source)
        self.assertIn('dataframe["cam_r3"]', source)
        self.assertIn('dataframe["cam_s3"]', source)
        self.assertIn("s3_reclaim", source)
        self.assertIn("r3_reclaim", source)
        self.assertIn("camarilla_extension", source)
        self.assertIn("short_raw", source)
        self.assertIn("session_vwap", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_generated_strategy_for_lunch_liquidity_vacuum_vwap_magnet_reversal(self) -> None:
        module = self.load_module()

        spec = next(
            item
            for item in module.candidate_specs()
            if item.key == "lunch_liquidity_vacuum_vwap_magnet_reversal"
        )
        generated = module.generated_strategy_specs(
            ["NQ"],
            "1m",
            families=["lunch_liquidity_vacuum_vwap_magnet_reversal"],
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "SessionRhythm -> LunchLiquidityVacuum -> VwapMagnetReversal",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            generated[0].class_name,
            "TomacNQLunchLiquidityVacuumVwapMagnetReversalOneMinCleanV1",
        )
        self.assertEqual(
            generated[0].factor_id,
            "tomac_idxfut_clean_lunch_liquidity_vacuum_vwap_magnet_reversal_1m_v1",
        )
        self.assertIn(
            "branch_path: SessionRhythm -> LunchLiquidityVacuum -> VwapMagnetReversal -> "
            "tomac_idxfut_clean_lunch_liquidity_vacuum_vwap_magnet_reversal_1m_v1",
            source,
        )
        self.assertIn(
            'elif "lunch_liquidity_vacuum_vwap_magnet_reversal" == '
            '"lunch_liquidity_vacuum_vwap_magnet_reversal":',
            source,
        )
        self.assertIn('dataframe["minute_of_day_ny"].between(11 * 60 + 20, 13 * 60 + 40)', source)
        self.assertIn("liquidity_vacuum", source)
        self.assertIn("vwap_magnet_distance", source)
        self.assertIn("mtf_range_votes", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)


if __name__ == "__main__":
    unittest.main()
