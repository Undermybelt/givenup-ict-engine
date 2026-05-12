# Local Databento Multi-Futures Nonqualifying Source Screen v1

Run id: `20260512T025801-codex-local-databento-multi-futures-nonqualifying-source-screen-v1`

Gate result: `local_databento_multi_futures_nonqualifying_source_screen_v1=databento_ohlcv_multi_futures_found_not_r6_r3_r5_qualifying_no_promotion`

Source root: `/Users/thrill3r/Downloads/Tomac`

Readback:
- Symbols screened: `ES, 6E, GC, NQ, YM`
- Dataset(s): `GLBX.MDP3`
- Schema(s): `ohlcv-1m`
- Local OHLCV files found: `5`
- CSV artifact: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T025801-codex-local-databento-multi-futures-nonqualifying-source-screen-v1/local-databento-multi-futures-nonqualifying-source-screen-v1/local_databento_multi_futures_nonqualifying_source_screen_v1.csv`

Decision:
- This is real local Databento/Tomac futures breadth for ES, NQ, YM, 6E, and GC.
- It is OHLCV `1m` bar evidence, not CME Market Depth / Market by Order / full order-lifecycle evidence.
- It does not provide source-owned normal controls, explicit same-exhibit `FLIP` control approval, accepted source labels, or per-regime qualifying-condition labels.
- It does not close R6 owner/control, R3 native-subhour source-label, or R5 source-panel recency-extension gates.
- It does not justify canonical merge or downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion.

Promotion guards:
- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion rerun allowed: `false`
- Strict full objective achieved: `false`
- `update_goal=false`
- Runtime code changed: `false`
- Shared intake mutated: `false`
- R3/R5/R6 roots mutated: `false`
- Thresholds relaxed: `false`
- Raw data committed: `false`
- Trade usable: `false`

Next:
- Preserve the Current Cursor next action for R6. Continue only from licensed owner/operator R6 controls, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` labels before canonical merge and downstream promotion.
