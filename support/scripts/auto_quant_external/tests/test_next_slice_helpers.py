from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import entry_drought_diagnostic_v2 as drought  # noqa: E402
import external_regime_changepoint_labels as changepoint  # noqa: E402
import structural_feedback_trade_enricher as enricher  # noqa: E402
import structural_feedback_replay_harness as replay  # noqa: E402


class ChangePointHelperTests(unittest.TestCase):
    def test_cluster_breakpoints_merges_nearby_votes(self) -> None:
        clusters = changepoint.cluster_breakpoints(
            {
                "pelt": [10, 30, 60],
                "binseg": [11, 29, 61],
                "window": [30, 89],
            },
            tolerance=2,
        )

        self.assertEqual([item["bar_index"] for item in clusters], [10, 30, 60, 89])
        self.assertEqual(clusters[0]["vote_count"], 2)
        self.assertEqual(clusters[1]["vote_count"], 3)

    def test_transition_proximity_peaks_around_breakpoints(self) -> None:
        index = pd.date_range("2025-01-01", periods=8, freq="h", tz="UTC")
        proximity = changepoint.build_transition_proximity(index, [3], window=2)

        self.assertEqual(proximity.iloc[3], 1.0)
        self.assertEqual(proximity.iloc[1], 0.0)
        self.assertGreater(proximity.iloc[2], 0.0)
        self.assertGreater(proximity.iloc[4], 0.0)

    def test_load_candles_accepts_timestamp_column(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candles.csv"
            path.write_text(
                "timestamp,open,high,low,close,volume\n"
                "1740502800000,1,2,0.5,1.5,10\n",
                encoding="utf-8",
            )

            candles = changepoint.load_candles(path)

        self.assertEqual(len(candles), 1)
        self.assertEqual(candles.index.name, "date")
        self.assertEqual(float(candles.iloc[0]["close"]), 1.5)


class EntryDroughtHelperTests(unittest.TestCase):
    def test_gate_ablations_flag_density_bottleneck(self) -> None:
        gate_df = pd.DataFrame(
            {
                "session": [True] * 8,
                "trend": [True] * 8,
                "strict_gate": [True, True, True, True, False, False, False, False],
            },
            index=pd.date_range("2025-01-01", periods=8, freq="D", tz="UTC"),
        )

        ablations = drought.analyze_gate_ablations(gate_df)
        suspect_gates = [item["gate"] for item in drought.find_suspect_gates(ablations)]

        self.assertEqual(ablations[0]["gate"], "strict_gate")
        self.assertIn("strict_gate", suspect_gates)
        self.assertEqual(drought.classify_density_issue(gate_df, ablations), "over_gating_issue")


class StructuralFeedbackEnricherTests(unittest.TestCase):
    def test_attach_structural_feedback_maps_trade_to_template(self) -> None:
        trade = {
            "trade_id": "t-1",
            "symbol": "NQ",
            "realized_outcome": "win",
            "pnl": 0.02,
            "close_ts_ms": 1_745_427_900_000,
        }
        template = {
            "template_feedback": {
                "structural_feedback": {
                    "protocol_version": "structural-feedback-v1",
                    "recommendation_id": "structural-feedback:NQ:node:path",
                    "recommended_at": "2026-05-07T09:56:50Z",
                    "node_id": "node-1",
                    "branch_id": "branch-1",
                    "scenario_id": "scenario-1",
                    "path_id": "path-1",
                    "followed_path": True,
                },
                "model_probabilities_before_trade": {
                    "selected_direction": "Bull",
                    "selected_probability": 0.62,
                    "long_score": 0.62,
                    "short_score": 0.38,
                    "win_prob_long": 0.62,
                    "win_prob_short": 0.38,
                    "uncertainty": 0.10,
                },
            }
        }

        enriched = enricher.attach_structural_feedback(trade, template)

        self.assertEqual(enriched["structural_feedback"]["path_id"], "path-1")
        self.assertEqual(
            enriched["model_probabilities_before_trade"]["selected_probability"],
            0.62,
        )
        self.assertEqual(enriched["realized_outcome"], "win")

    def test_enrich_jsonl_round_trip_writes_only_matched_records(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            trades_path = tmp / "trades.jsonl"
            pending_path = tmp / "pending_update_history.json"
            output_path = tmp / "enriched.jsonl"

            trades_path.write_text(
                "\n".join(
                    [
                        '{"trade_id":"t-1","symbol":"NQ","realized_outcome":"win","pnl":0.02,"close_ts_ms":1745427900000}',
                        '{"trade_id":"t-2","symbol":"NQ","realized_outcome":"loss","pnl":-0.01,"close_ts_ms":1745427901000}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            pending_path.write_text(
                '[{"template_feedback":{"structural_feedback":{"protocol_version":"structural-feedback-v1","recommendation_id":"rec-1","recommended_at":"2026-05-07T09:56:50Z","node_id":"node-1","branch_id":"branch-1","scenario_id":"scenario-1","path_id":"path-1","followed_path":true},"model_probabilities_before_trade":{"selected_direction":"Bull","selected_probability":0.62,"long_score":0.62,"short_score":0.38,"win_prob_long":0.62,"win_prob_short":0.38,"uncertainty":0.1}}}]',
                encoding="utf-8",
            )

            summary = enricher.enrich_real_trades_jsonl(
                trades_path=trades_path,
                pending_update_history_path=pending_path,
                output_path=output_path,
            )

            self.assertEqual(summary["matched"], 1)
            self.assertEqual(summary["unmatched"], 1)
            lines = [line for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(lines), 1)
            payload = pd.Series([lines[0]]).apply(lambda x: __import__("json").loads(x)).iloc[0]
            self.assertEqual(payload["structural_feedback"]["path_id"], "path-1")

    def test_emit_structural_feedback_probe_uses_target_lineage(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target_csv = tmp / "target.csv"
            output_path = tmp / "feedback.json"
            target_csv.write_text(
                "symbol,candidate_set_id,candidate_set_size,rank,path_id,scenario_id,path_label,direction,generated_at,behavior_policy_probability,current_posterior,raw_path_score\n"
                "NQ,set-1,3,1,path-1,scenario-1,trend_follow,Observe,2026-05-09T00:00:00Z,0.37,0.46,0.47\n",
                encoding="utf-8",
            )

            summary = enricher.emit_structural_feedback_probe(
                target_csv=target_csv,
                output_path=output_path,
                realized_outcome="win",
                pnl=0.03,
            )

            payload = __import__("json").loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["ok"])
            self.assertEqual(payload["protocol_version"], "structural-feedback-v1")
            self.assertEqual(payload["path_id"], "path-1")
            self.assertEqual(payload["scenario_id"], "scenario-1")
            self.assertEqual(payload["candidate_set_id"], "set-1")
            self.assertEqual(payload["realized_outcome"], "win")
            self.assertEqual(payload["model_probabilities_before_trade"]["selected_probability"], 0.37)

    def test_emit_structural_feedback_probe_prefers_explicit_branch_path_fields(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target_csv = tmp / "target.csv"
            output_path = tmp / "feedback.json"
            branch_path = "Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12"
            target_csv.write_text(
                "symbol,candidate_set_id,candidate_set_size,rank,path_id,regime_profit_branch_path,main_regime,sub_regime,sub_sub_regime_or_profit_factor,profit_factor,direction,generated_at,behavior_policy_probability,current_posterior,raw_path_score\n"
                f"NQ,set-1,3,1,path:scenario:generic,{branch_path},Bull,ProviderTrend,EmaRsiContinuation,ProviderBtcEmaRsiHold12,Bull,2026-05-09T00:00:00Z,0.37,0.46,0.47\n",
                encoding="utf-8",
            )

            enricher.emit_structural_feedback_probe(
                target_csv=target_csv,
                output_path=output_path,
                realized_outcome="win",
                pnl=0.03,
            )

            payload = __import__("json").loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["path_id"], branch_path)
            self.assertEqual(payload["regime_profit_branch_path"], branch_path)
            self.assertEqual(payload["main_regime"], "Bull")
            self.assertEqual(payload["sub_regime"], "ProviderTrend")
            self.assertEqual(payload["sub_sub_regime_or_profit_factor"], "EmaRsiContinuation")
            self.assertEqual(payload["profit_factor"], "ProviderBtcEmaRsiHold12")
            self.assertEqual(
                payload["branch_path_segments"],
                [
                    "Bull",
                    "ProviderTrend",
                    "EmaRsiContinuation",
                    "ProviderBtcEmaRsiHold12",
                ],
            )
            self.assertEqual(payload["branch_path_depth"], 4)
            self.assertEqual(payload["branch_path_leaf"], "ProviderBtcEmaRsiHold12")
            self.assertEqual(payload["branch_id"], "Bull -> ProviderTrend")
            self.assertEqual(payload["scenario_id"], "Bull -> ProviderTrend -> EmaRsiContinuation")

    def test_emit_structural_feedback_probe_accepts_compact_branch_path_separator(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            target_csv = tmp / "target.csv"
            output_path = tmp / "feedback.json"
            branch_path = "Bull->ProviderTrend->EmaRsiContinuation->ProviderBtcEmaRsiHold12"
            target_csv.write_text(
                "symbol,candidate_set_id,candidate_set_size,rank,path_id,regime_profit_branch_path,direction,generated_at,behavior_policy_probability,current_posterior,raw_path_score\n"
                f"NQ,set-1,3,1,path:scenario:generic,{branch_path},Bull,2026-05-09T00:00:00Z,0.37,0.46,0.47\n",
                encoding="utf-8",
            )

            enricher.emit_structural_feedback_probe(
                target_csv=target_csv,
                output_path=output_path,
                realized_outcome="win",
                pnl=0.03,
            )

            payload = __import__("json").loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["path_id"], branch_path)
            self.assertEqual(payload["main_regime"], "Bull")
            self.assertEqual(payload["sub_regime"], "ProviderTrend")
            self.assertEqual(payload["sub_sub_regime_or_profit_factor"], "EmaRsiContinuation")
            self.assertEqual(payload["profit_factor"], "ProviderBtcEmaRsiHold12")
            self.assertEqual(
                payload["branch_path_segments"],
                [
                    "Bull",
                    "ProviderTrend",
                    "EmaRsiContinuation",
                    "ProviderBtcEmaRsiHold12",
                ],
            )
            self.assertEqual(payload["branch_path_depth"], 4)
            self.assertEqual(payload["branch_path_leaf"], "ProviderBtcEmaRsiHold12")

    def test_layer_contract_enrichment_overrides_stale_source_and_keeps_branch(self) -> None:
        trade = {
            "schema_version": "1.0",
            "symbol": "B2R_YAHOO_BTC_PULLBACK_PRECISION_104902",
            "trade_id": "trade-1",
            "strategy_name": "ProviderCryptoMomentumStateV1",
            "auto_quant_run_id": "stale-run",
            "open_ts_ms": 1,
            "close_ts_ms": 2,
            "direction": "Bull",
            "pnl": 0.01,
            "realized_outcome": "win",
            "regime_profit_branch_path": "Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1",
        }

        enriched = enricher.enrich_trade_with_layer_contract(
            trade,
            auto_quant_run_id="20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1",
            symbol="BTC_USDT",
            provider_provenance={
                "provider": "yfinance",
                "provider_symbol": "BTC-USD",
                "timeframe": "1h",
                "source_csv": "provider-csv/yfinance_btc_usd_1h.csv",
            },
            pre_bayes_filter_state={"gate": "pass_neutralized", "canonical_regime": "range"},
            bbn_posterior={"canonical_regime": "range", "confidence": 0.52},
            catboost_path_ranker_label={"score_model_family": "catboost", "label": "observed_win"},
            execution_tree_decision={"ready": False, "actionable": False, "review": "observe"},
            failure_reason="execution_tree_observe_only",
            quality_weight=0.25,
        )

        self.assertEqual(
            enriched["auto_quant_run_id"],
            "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1",
        )
        self.assertEqual(enriched["symbol"], "BTC_USDT")
        self.assertEqual(enriched["provider_provenance"]["provider"], "yfinance")
        self.assertEqual(enriched["pre_bayes_filter_state"]["gate"], "pass_neutralized")
        self.assertEqual(enriched["bbn_posterior"]["canonical_regime"], "range")
        self.assertEqual(enriched["catboost_path_ranker_label"]["label"], "observed_win")
        self.assertEqual(enriched["execution_tree_decision"]["review"], "observe")
        self.assertEqual(enriched["failure_reason"], "execution_tree_observe_only")
        self.assertEqual(enriched["quality_weight"], 0.25)
        self.assertEqual(enriched["main_regime"], "Bull")
        self.assertEqual(enriched["sub_regime"], "ProviderCryptoMomentum")
        self.assertEqual(enriched["sub_sub_regime_or_profit_factor"], "RsiMidlineExpansion")
        self.assertEqual(enriched["profit_factor"], "ProviderCryptoMomentumStateV1")
        self.assertEqual(
            enriched["branch_path_segments"],
            [
                "Bull",
                "ProviderCryptoMomentum",
                "RsiMidlineExpansion",
                "ProviderCryptoMomentumStateV1",
            ],
        )
        self.assertEqual(enriched["branch_path_depth"], 4)
        self.assertEqual(enriched["branch_path_leaf"], "ProviderCryptoMomentumStateV1")
        self.assertNotIn("104902", enriched["symbol"])


class StructuralFeedbackReplayHarnessTargetTests(unittest.TestCase):
    def test_generate_observation_passes_exact_branch_path_to_probe_emitter(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            symbol = "NQ"
            branch_path = (
                "TrendExpansion -> EnergyRotation -> pullback_reclaim_continuation -> "
                "energy_rotation_pullback_reclaim_ibkr_xle_1m_v1"
            )
            candles = [
                {
                    "timestamp": f"2026-05-01T00:{minute:02d}:00Z",
                    "open": 100 + minute,
                    "high": 101 + minute,
                    "low": 99 + minute,
                    "close": 100 + minute,
                    "volume": 1000,
                }
                for minute in range(8)
            ]
            emit_probe_cmds: list[list[str]] = []
            original_run = replay.run

            def fake_run(cmd: list[str], *, cwd: Path = replay.REPO_ROOT):
                target_csv = (
                    tmp
                    / "state"
                    / symbol
                    / "policy_training"
                    / "structural_path_ranking_target.csv"
                )
                target_csv.parent.mkdir(parents=True, exist_ok=True)
                target_csv.write_text(
                    "symbol,candidate_set_id,candidate_set_size,rank,path_id,regime_profit_branch_path,"
                    "main_regime,sub_regime,sub_sub_regime_or_profit_factor,profit_factor,direction,"
                    "generated_at,behavior_policy_probability,current_posterior,raw_path_score\n"
                    "NQ,set-1,2,1,Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> "
                    "order_block_variant_classifier_v1,Transition -> OrderBlockVariant -> "
                    "ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1,Transition,"
                    "OrderBlockVariant,ob_mitigation_breaker_rejection,order_block_variant_classifier_v1,"
                    "Bull,2026-05-09T00:00:00Z,0.37,0.46,0.47\n"
                    f"NQ,set-1,2,2,{branch_path},{branch_path},TrendExpansion,EnergyRotation,"
                    "pullback_reclaim_continuation,energy_rotation_pullback_reclaim_ibkr_xle_1m_v1,"
                    "Bull,2026-05-09T00:00:00Z,0.33,0.44,0.45\n",
                    encoding="utf-8",
                )
                if str(replay.ENRICHER) in cmd and "emit-probe" in cmd:
                    emit_probe_cmds.append(cmd)
                    output_path = Path(cmd[cmd.index("--output") + 1])
                    path_id = cmd[cmd.index("--path-id") + 1]
                    enricher.emit_structural_feedback_probe(
                        target_csv=target_csv,
                        output_path=output_path,
                        path_id=path_id,
                        realized_outcome="win",
                    )

                class Result:
                    stdout = '{"mature_rows": 1, "history_mature_rows": 1, "summary_line": "ok"}'

                return Result()

            try:
                replay.run = fake_run
                observation = replay.generate_observation(
                    symbol=symbol,
                    candles=candles,
                    output_root=tmp,
                    prior_state=None,
                    index=3,
                    lookback=3,
                    horizon=2,
                    threshold=0.001,
                    observation_id=1,
                    branch_path=branch_path,
                )
            finally:
                replay.run = original_run

            self.assertEqual(observation["outcome"], "win")
            self.assertTrue(emit_probe_cmds, "emit-probe should be called")
            self.assertIn("--path-id", emit_probe_cmds[0])
            payload = __import__("json").loads(
                (tmp / "feedback" / "structural_feedback_obs_01.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(payload["path_id"], branch_path)


class StructuralFeedbackReplayHarnessTests(unittest.TestCase):
    def test_outcome_from_forward_window_labels_directional_move(self) -> None:
        candles = [
            {"close": 100.0, "high": 100.0, "low": 100.0},
            {"close": 100.1, "high": 100.4, "low": 99.9},
            {"close": 100.4, "high": 100.5, "low": 100.0},
        ]

        outcome, pnl, exit_close = replay.outcome_from_forward_window(
            candles,
            entry_index=0,
            horizon=2,
            threshold=0.001,
        )

        self.assertEqual(outcome, "win")
        self.assertAlmostEqual(pnl, 0.004)
        self.assertEqual(exit_close, 100.4)

    def test_load_candles_accepts_wrapped_payload(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candles.json"
            path.write_text(
                '{"symbol":"NQ","candles":[{"timestamp":"t","open":1,"high":1,"low":1,"close":1,"volume":1}]}',
                encoding="utf-8",
            )

            candles = replay.load_candles(path)

        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0]["timestamp"], "t")

    def test_pnl_cli_arg_keeps_negative_value_attached(self) -> None:
        self.assertEqual(replay.pnl_cli_arg(-0.001), "--pnl=-0.001")

    def test_generate_observation_materializes_distinct_multi_tf_windows(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            symbol = "NQ"
            aq_data_dir = tmp / "aq_data"
            aq_data_dir.mkdir(parents=True, exist_ok=True)
            timeframe_specs = {
                "1m": ("2026-05-01T04:00:00Z", "min"),
                "5m": ("2026-05-01T03:40:00Z", "5min"),
                "15m": ("2026-05-01T03:00:00Z", "15min"),
                "30m": ("2026-05-01T01:30:00Z", "30min"),
                "1h": ("2026-05-01T00:00:00Z", "h"),
                "4h": ("2026-04-30T00:00:00Z", "4h"),
                "1d": ("2026-04-24T00:00:00Z", "D"),
            }
            for timeframe, (start, freq) in timeframe_specs.items():
                frame = pd.DataFrame(
                    {
                        "date": pd.date_range(start, periods=8, freq=freq),
                        "open": [100 + idx for idx in range(8)],
                        "high": [101 + idx for idx in range(8)],
                        "low": [99 + idx for idx in range(8)],
                        "close": [100 + idx for idx in range(8)],
                        "volume": [1000 + idx for idx in range(8)],
                    }
                )
                frame.to_feather(aq_data_dir / f"{symbol}_USD-{timeframe}.feather")

            candles = [
                {
                    "timestamp": f"2026-05-01T04:0{minute}:00Z",
                    "open": 100 + minute,
                    "high": 101 + minute,
                    "low": 99 + minute,
                    "close": 100 + minute,
                    "volume": 1000 + minute,
                }
                for minute in range(8)
            ]
            analyze_cmds: list[list[str]] = []
            original_run = replay.run

            def fake_run(cmd: list[str], *, cwd: Path = replay.REPO_ROOT):
                target_csv = (
                    tmp
                    / "state"
                    / symbol
                    / "policy_training"
                    / "structural_path_ranking_target.csv"
                )
                target_csv.parent.mkdir(parents=True, exist_ok=True)
                if "export-structural-path-ranking-target" in cmd:
                    target_csv.write_text(
                        "symbol,candidate_set_id,candidate_set_size,rank,path_id,scenario_id,path_label,direction,generated_at,behavior_policy_probability,current_posterior,raw_path_score\n"
                        "NQ,set-1,3,1,path-1,scenario-1,trend_follow,Bull,2026-05-09T00:00:00Z,0.37,0.46,0.47\n",
                        encoding="utf-8",
                    )
                if "analyze" in cmd:
                    analyze_cmds.append(cmd)
                if str(replay.ENRICHER) in cmd and "emit-probe" in cmd:
                    output_path = Path(cmd[cmd.index("--output") + 1])
                    enricher.emit_structural_feedback_probe(
                        target_csv=target_csv,
                        output_path=output_path,
                        realized_outcome="win",
                    )

                class Result:
                    stdout = '{"mature_rows": 1, "history_mature_rows": 1, "summary_line": "ok"}'

                return Result()

            try:
                replay.run = fake_run
                replay.generate_observation(
                    symbol=symbol,
                    candles=candles,
                    output_root=tmp,
                    prior_state=None,
                    index=4,
                    lookback=3,
                    horizon=2,
                    threshold=0.001,
                    observation_id=1,
                    aq_data_dir=aq_data_dir,
                )
            finally:
                replay.run = original_run

            self.assertEqual(len(analyze_cmds), 1)
            analyze_cmd = analyze_cmds[0]
            data_root = Path(analyze_cmd[analyze_cmd.index("--data-root") + 1])
            self.assertTrue(data_root.exists())
            for timeframe in replay.MULTI_TIMEFRAME_INTERVALS:
                frame_path = data_root / f"cleaned-{timeframe}" / f"{symbol.lower()}.continuous-{timeframe}.json"
                self.assertTrue(frame_path.exists(), frame_path)
                payload = replay.load_candles(frame_path)
                self.assertEqual(len(payload), 5)
            ltf_payload = replay.load_candles(
                data_root / "cleaned-1m" / f"{symbol.lower()}.continuous-1m.json"
            )
            mtf_payload = replay.load_candles(
                data_root / "cleaned-15m" / f"{symbol.lower()}.continuous-15m.json"
            )
            htf_payload = replay.load_candles(
                data_root / "cleaned-1h" / f"{symbol.lower()}.continuous-1h.json"
            )
            self.assertEqual(ltf_payload[-1]["timestamp"], "2026-05-01T04:04:00Z")
            self.assertEqual(mtf_payload[-1]["timestamp"], "2026-05-01T04:00:00Z")
            self.assertEqual(htf_payload[-1]["timestamp"], "2026-05-01T04:00:00Z")

    def test_generate_observation_supports_distinct_aq_symbol_and_state_symbol(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            symbol = "TOMAC_NQ_OPENING_DRIVE_TWOLEG_EXACT_DOWNSTREAM_V1"
            aq_data_dir = tmp / "aq_data"
            aq_data_dir.mkdir(parents=True, exist_ok=True)
            for timeframe, freq in {
                "1m": "min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "h",
                "4h": "4h",
                "1d": "D",
            }.items():
                frame = pd.DataFrame(
                    {
                        "date": pd.date_range("2026-05-01T00:00:00Z", periods=8, freq=freq),
                        "open": [100 + idx for idx in range(8)],
                        "high": [101 + idx for idx in range(8)],
                        "low": [99 + idx for idx in range(8)],
                        "close": [100 + idx for idx in range(8)],
                        "volume": [1000 + idx for idx in range(8)],
                    }
                )
                frame.to_feather(aq_data_dir / f"NQ_USD-{timeframe}.feather")

            candles = [
                {
                    "timestamp": f"2026-05-01T00:0{minute}:00Z",
                    "open": 100 + minute,
                    "high": 101 + minute,
                    "low": 99 + minute,
                    "close": 100 + minute,
                    "volume": 1000 + minute,
                }
                for minute in range(8)
            ]
            original_run = replay.run

            def fake_run(cmd: list[str], *, cwd: Path = replay.REPO_ROOT):
                target_csv = (
                    tmp
                    / "state"
                    / symbol
                    / "policy_training"
                    / "structural_path_ranking_target.csv"
                )
                target_csv.parent.mkdir(parents=True, exist_ok=True)
                if "export-structural-path-ranking-target" in cmd:
                    target_csv.write_text(
                        "symbol,candidate_set_id,candidate_set_size,rank,path_id,scenario_id,path_label,direction,generated_at,behavior_policy_probability,current_posterior,raw_path_score\n"
                        f"{symbol},set-1,3,1,path-1,scenario-1,trend_follow,Bull,2026-05-09T00:00:00Z,0.37,0.46,0.47\n",
                        encoding="utf-8",
                    )
                if str(replay.ENRICHER) in cmd and "emit-probe" in cmd:
                    output_path = Path(cmd[cmd.index("--output") + 1])
                    enricher.emit_structural_feedback_probe(
                        target_csv=target_csv,
                        output_path=output_path,
                        realized_outcome="win",
                    )

                class Result:
                    stdout = '{"mature_rows": 1, "history_mature_rows": 1, "summary_line": "ok"}'

                return Result()

            try:
                replay.run = fake_run
                replay.generate_observation(
                    symbol=symbol,
                    aq_symbol="NQ",
                    candles=candles,
                    output_root=tmp,
                    prior_state=None,
                    index=4,
                    lookback=3,
                    horizon=2,
                    threshold=0.001,
                    observation_id=1,
                    aq_data_dir=aq_data_dir,
                )
            finally:
                replay.run = original_run

            data_root = tmp / "windows" / "obs_01_clean_root"
            expected = data_root / "cleaned-1m" / f"{symbol.lower()}.continuous-1m.json"
            self.assertTrue(expected.exists(), expected)
            self.assertEqual(
                replay.load_candles(expected)[-1]["timestamp"],
                "2026-05-01T00:04:00Z",
            )

    def test_timeframe_feather_path_accepts_futures_suffix(self) -> None:
        with TemporaryDirectory() as tmpdir:
            aq_data_dir = Path(tmpdir)
            futures_path = aq_data_dir / "NQ_USD-1m-futures.feather"
            futures_path.write_text("placeholder", encoding="utf-8")

            resolved = replay.timeframe_feather_path(aq_data_dir, "NQ", "1m")

        self.assertEqual(resolved, futures_path)

    def test_run_replay_count_one_selects_single_observation(self) -> None:
        candles = [
            {
                "timestamp": f"2026-05-01T00:{minute:02d}:00Z",
                "open": 100 + minute,
                "high": 101 + minute,
                "low": 99 + minute,
                "close": 100 + minute,
                "volume": 1000 + minute,
            }
            for minute in range(10)
        ]
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            candles_path = tmp / "candles.json"
            candles_path.write_text(json.dumps({"candles": candles}), encoding="utf-8")
            original_generate = replay.generate_observation

            def fake_generate_observation(**kwargs):
                return {"observation_id": kwargs["observation_id"], "mature_rows": kwargs["observation_id"]}

            try:
                replay.generate_observation = fake_generate_observation
                summary = replay.run_replay(
                    candles_path=candles_path,
                    output_root=tmp / "out",
                    symbol="NQ",
                    count=1,
                    lookback=3,
                    horizon=2,
                    threshold=0.001,
                    prior_state=None,
                )
            finally:
                replay.generate_observation = original_generate

        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["final_mature_rows"], 1)

    def test_run_replay_can_finalize_execution_materialization_from_selected_observation(self) -> None:
        candles = [
            {
                "timestamp": f"2026-05-01T00:{minute:02d}:00Z",
                "open": 100 + minute,
                "high": 101 + minute,
                "low": 99 + minute,
                "close": 100 + minute,
                "volume": 1000 + minute,
            }
            for minute in range(10)
        ]
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            candles_path = tmp / "candles.json"
            candles_path.write_text(json.dumps({"candles": candles}), encoding="utf-8")
            run_calls: list[list[str]] = []
            original_generate = replay.generate_observation
            original_run = replay.run

            def fake_generate_observation(**kwargs):
                obs_id = kwargs["observation_id"]
                data_root = kwargs["output_root"] / "windows" / f"obs_{obs_id:02d}_clean_root"
                data_root.mkdir(parents=True, exist_ok=True)
                return {
                    "observation_id": obs_id,
                    "mature_rows": obs_id,
                    "data_root": str(data_root),
                    "data_path": str(data_root / "cleaned-1m" / "nq.continuous-1m.json"),
                }

            def fake_run(cmd: list[str], *, cwd: Path = replay.REPO_ROOT):
                run_calls.append(cmd)

                class Result:
                    stdout = '{"ok": true}'

                return Result()

            try:
                replay.generate_observation = fake_generate_observation
                replay.run = fake_run
                summary = replay.run_replay(
                    candles_path=candles_path,
                    output_root=tmp / "out",
                    symbol="NQ",
                    count=3,
                    lookback=3,
                    horizon=2,
                    threshold=0.001,
                    prior_state=None,
                    execution_materialization_observation_id=2,
                )
            finally:
                replay.generate_observation = original_generate
                replay.run = original_run

        self.assertEqual(summary["execution_materialization"]["observation_id"], 2)
        analyze_calls = [cmd for cmd in run_calls if "analyze" in cmd]
        self.assertEqual(len(analyze_calls), 1)
        analyze_cmd = analyze_calls[0]
        self.assertIn("--data-root", analyze_cmd)
        self.assertTrue(
            str(Path(analyze_cmd[analyze_cmd.index("--data-root") + 1])).endswith(
                "obs_02_clean_root"
            )
        )
        self.assertIn("--state-dir", analyze_cmd)

    def test_run_materialization_only_analyzes_explicit_existing_data_root(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prior_state = tmp / "prior_state"
            prior_symbol_dir = prior_state / "NQ"
            prior_symbol_dir.mkdir(parents=True)
            (prior_symbol_dir / "workflow_snapshot.json").write_text(
                '{"symbol":"NQ"}', encoding="utf-8"
            )
            data_root = tmp / "windows" / "obs_09_clean_root"
            data_root.mkdir(parents=True)
            output_root = tmp / "out"
            run_calls: list[list[str]] = []
            original_run = replay.run

            def fake_run(cmd: list[str], *, cwd: Path = replay.REPO_ROOT):
                run_calls.append(cmd)

                class Result:
                    stdout = '{"ok": true}'

                return Result()

            try:
                replay.run = fake_run
                summary = replay.run_materialization_only(
                    output_root=output_root,
                    symbol="NQ",
                    prior_state=prior_state,
                    data_root=data_root,
                    data_path=None,
                    observation_label="obs_09",
                )
            finally:
                replay.run = original_run

            self.assertEqual(summary["count"], 0)
            self.assertEqual(summary["execution_materialization"]["observation_label"], "obs_09")
            copied = output_root / "state" / "NQ" / "workflow_snapshot.json"
            self.assertTrue(copied.exists(), copied)
            analyze_calls = [cmd for cmd in run_calls if "analyze" in cmd]
            self.assertEqual(len(analyze_calls), 1)
            analyze_cmd = analyze_calls[0]
            self.assertIn("--data-root", analyze_cmd)
            self.assertEqual(Path(analyze_cmd[analyze_cmd.index("--data-root") + 1]), data_root)
            self.assertIn("--state-dir", analyze_cmd)

    def test_parse_args_allows_materialization_only_without_candles(self) -> None:
        args = replay.parse_args(
            [
                "--output-root",
                "/tmp/out",
                "--symbol",
                "NQ",
                "--execution-materialization-data-root",
                "/tmp/windows/obs_09_clean_root",
            ]
        )

        self.assertIsNone(args.candles)
        self.assertEqual(args.execution_materialization_data_root, "/tmp/windows/obs_09_clean_root")

    def test_parse_args_requires_candles_without_materialization_only_input(self) -> None:
        with self.assertRaises(SystemExit):
            replay.parse_args(["--output-root", "/tmp/out", "--symbol", "NQ"])


if __name__ == "__main__":
    unittest.main()
