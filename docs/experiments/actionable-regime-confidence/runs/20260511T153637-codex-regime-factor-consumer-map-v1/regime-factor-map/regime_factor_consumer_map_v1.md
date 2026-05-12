# Regime Factor Consumer Map v1

Run ID: `20260511T153637+0800-codex-regime-factor-consumer-map-v1`

## Decision

- Gate result: `regime_factor_consumer_map_v1=accepted_95_all_active_lanes_scoped_full_species_still_blocked`.
- `Bull`, `Bear`, `Sideways`, and `Crisis` each have an accepted 95% `market_regime_context` factor.
- `Manipulation` has an accepted 95% scoped direct overlay factor from direct event/order-lifecycle/on-chain rows.
- This corrects the blocker shape: spoofing/layering is a missing species expansion, not proof that `Manipulation` has no accepted factor.
- Full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Consumer Map

| Regime | Role | Consumer factor | Confidence floor | Allowed action | Limit |
|---|---|---|---:|---|---|
| Bull | MainRegimeV2_price_root | market_regime_context | 0.9797225384 | pre_bayes_regime_context; bbn_soft_evidence_context; catboost_path_ranker_context; execution_tree_sizing_or_suppression_context | Not ticker-specific alpha, not intraday transition timing, not full-cycle/full-species completion. |
| Bear | MainRegimeV2_price_root | market_regime_context | 0.963920242 | pre_bayes_regime_context; bbn_soft_evidence_context; catboost_path_ranker_context; execution_tree_sizing_or_suppression_context | Not ticker-specific alpha, not intraday transition timing, not full-cycle/full-species completion. |
| Sideways | MainRegimeV2_price_root | market_regime_context | 0.9529358324 | pre_bayes_regime_context; bbn_soft_evidence_context; catboost_path_ranker_context; execution_tree_sizing_or_suppression_context | Not ticker-specific alpha, not intraday transition timing, not full-cycle/full-species completion. |
| Crisis | MainRegimeV2_price_root | market_regime_context | 0.9619059575 | pre_bayes_regime_context; bbn_soft_evidence_context; catboost_path_ranker_context; execution_tree_sizing_or_suppression_context | Not ticker-specific alpha, not intraday transition timing, not full-cycle/full-species completion. |
| Manipulation | separate_direct_overlay | direct_manipulation_overlay | 0.967945 | suppression; cooldown; abstain; risk overlay; BBN soft evidence; execution-tree audit field | Scoped direct coverage only. Missing or blocked varieties remain abstain: pump_dump_social_text_or_twitter, spoofing_layering_enforcement_cases, local_spoofing_repos, quote_stuffing, pinging, bear_raid_or_painting_tape |

## Manipulation Rule

Emit `direct_manipulation_overlay` only when one of the accepted direct source subtypes is present:

- `pump_dump_telegram_event`: min Wilson95 LCB `0.999701`; 61515 positive Telegram pump events; 61445 same-coin non-event controls; artifact `docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.md`.
- `dex_self_trade_order_lifecycle`: min Wilson95 LCB `0.998671`; 12671 positive self-trade rows; 10000 negative controls; artifact `docs/experiments/actionable-regime-confidence/runs/20260511T101019-codex-zenodo-dex-selftrade-direct-gate/direct-gate/zenodo_dex_selftrade_direct_gate_report.md`.
- `dex_consecutive_self_trade_order_lifecycle`: min Wilson95 LCB `0.979218`; 200000 streamed rows; 12671 positives; 187329 negatives; artifact `docs/experiments/actionable-regime-confidence/runs/20260511T102332-codex-zenodo-dex-consecutive-selftrade-gate/direct-gate/zenodo_dex_consecutive_selftrade_gate.md`.
- `midsummer_bsc_wash_maker`: min Wilson95 LCB `0.995736`; 1870 positive BSC wash-maker rows; 2994 negative controls; artifact `docs/experiments/actionable-regime-confidence/runs/20260511T111122-codex-midsummer-meme-direct-wash-audit/midsummer-meme-audit/midsummer_meme_direct_wash_audit.md`.
- `midsummer_multichain_wash_maker`: min Wilson95 LCB `0.967945`; 5693 new accepted base/ethereum/solana wash-maker positive rows; artifact `docs/experiments/actionable-regime-confidence/runs/20260511T112642-codex-midsummer-chain-slice-expansion-audit/chain-slice-audit/midsummer_chain_slice_expansion_audit.md`.

Blocked or missing direct varieties stay `abstain`, not proxy-filled:

- pump_dump_social_text_or_twitter, spoofing_layering_enforcement_cases, local_spoofing_repos, quote_stuffing, pinging, bear_raid_or_painting_tape

## Next

Use this map as the downstream consumer contract. Reopen spoofing/layering only after source-owned positive rows and matched negative controls exist.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/checks/regime_factor_consumer_map_v1_assertions.out`
