# 105738 Provider Crypto TP/SL Search Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T105738+0800-codex-board-b-provider-crypto-tpsl-search-v1`

Source data root: `docs/experiments/actionable-regime-confidence/runs/20260512T103437+0800-codex-board-b-yahoo-crypto-momentum-market-aq-v1/workspace/auto-quant-yahoo-crypto-momentum/user_data/data`

## Result

The bounded interactive search was stopped before candidate emission.

- Exit marker: `killed_slow_search`
- Exit note: `killed after exceeding bounded interactive window; no candidate set emitted`
- Stdout bytes: `0`
- Stderr bytes: `0`
- Candidate rows emitted: `0`

## Decision

This root is diagnostic only. It did not emit a candidate set, did not complete an Auto-Quant/TOMAC strategy run, did not produce provider-matrix AQ provenance, and did not run the ordered downstream chain through Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution tree.

Board effect: accepted rows added `0`; mature rooted branch observations promoted `0`; source/control evidence acquired `false`; explicit selected-history approval `false`; canonical merge `false`; selected-data AutoQuant promotion `false`; downstream promotion `false`; strict full objective `false`; trade usable `false`; promotion allowed `false`; `update_goal=false`.

## Next

Do not repeat this unbounded TP/SL grid shape. A future TP/SL search needs a bounded candidate budget and still cannot promote unless the selected branch carries provider-matrix AQ provenance and survives the ordered downstream readback.
