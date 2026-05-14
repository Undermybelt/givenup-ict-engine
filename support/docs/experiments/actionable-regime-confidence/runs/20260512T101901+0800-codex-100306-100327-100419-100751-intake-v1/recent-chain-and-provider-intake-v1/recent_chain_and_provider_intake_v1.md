# Recent Chain And Provider Intake v1

Run id: `20260512T101901+0800-codex-100306-100327-100419-100751-intake-v1`

Scope: count-once intake for unregistered evidence roots `100306`, `100327`, `100419`, and `100751`. This is duplicate-aware evidence registration only. It does not select `HTF`, `MTF`, or `LTF`, approve source/control evidence, mutate canonical intake, promote Auto-Quant, BBN/CatBoost/path-ranking, or execution-tree output, make a trade claim, or authorize `update_goal`.

## Counted Roots

| Root | Gate | Decision |
|---|---|---|
| `20260512T100306+0800-codex-board-b-recorded-mtf-provider-chain-refresh-v1` | `recorded_mtf_catboost_registered_artifact_observe_only` | Ordered provider -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-candidate chain was exercised and branch-preserving, but execution stayed observe-only. |
| `20260512T100327+0800-codex-board-b-recorded-branch-runtime-refresh-v1` | `recorded_branch_runtime_refresh_provider_fetches_succeeded_execution_observe_only` | yfinance, local-stdio TradingView, Kraken public, and IBKR gateway fetches produced rows, but catalog readiness stayed conservative and execution stayed observe-only. |
| `20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1` | `provider_owned_yahoo_nq_preseeded_into_autoquant_no_promotion` | Provider-owned Yahoo NQ 1h rows were acquired and preseeded into an isolated Auto-Quant workspace; no TOMAC run in the prepare readback and no mature observations. |
| `20260512T100751+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1` | `recorded_mtf_refreshed_history_catboost_applied_execution_observe_only` | Auto-Quant import, BBN prior dry-run, dry-run real-trade ingest, CatBoost train/apply, structural path scores, and execution-candidate readback all ran; terminal execution still `observe` / `ready=false`. |

## Shared Outcome

- Accepted rows added: `0`
- Source/control evidence acquired: `false`
- Explicit selected-history choice: `false`
- Canonical merge: `false`
- Selected-data AutoQuant promotion: `false`
- Downstream promotion: `false`
- Every-regime 95%-99% objective: `false`
- Trade usable: `false`
- Promotion allowed: `false`
- update_goal: `false`

## Next

Do not repeat these same provider or recorded-MTF readback shapes. The next non-duplicative move is one of:

- real R6/R5/R3 source/control unlock,
- explicit selected-history approval for exactly one recorded branch lane,
- a longer or different provider-owned Auto-Quant input that produces nonzero mature rooted observations,
- or a coordinated structural-feedback owner fix in the dirty shared worktree.
