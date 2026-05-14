# Local Databento GC Nonqualifying Source Screen v1

Run id: `20260512T025156-codex-local-databento-gc-nonqualifying-source-screen-v1`

Gate result: `local_databento_gc_nonqualifying_source_screen_v1=databento_ohlcv_found_not_r6_r3_r5_qualifying_no_promotion`

Local source:
- Directory: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025`
- Manifest: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/manifest.json`
- Metadata: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/metadata.json`
- Data file: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/glbx-mdp3-20210106-20260105.ohlcv-1m.csv`

Readback:
- Dataset: `GLBX.MDP3`
- Schema: `ohlcv-1m`
- Symbol request: `GC.FUT`
- Input symbology: `parent`
- Output symbology: `instrument_id`
- Range: `2021-01-06` through `2026-01-05`
- CSV lines: `5333533`
- Data SHA-256: `3e566d0c7181c6fbddf80be1ec7fbb33987240a6aa495caa27b275d034fa174d`
- Metadata SHA-256: `94540e3b4fbb05f81266faf699f6a1def03accc0f9f9985163475f4cd6f03fc1`
- Manifest SHA-256: `660ddde764da1e65ecda084575956e3f4923fca27340e56c73552b789ad8613f`

Decision:
- This is real local Databento OHLCV evidence for gold futures.
- It is not R6 Oystacher owner/control evidence because it is not CME Market Depth / Market by Order / order-lifecycle data and does not provide source-owned normal controls.
- It is not an explicit same-exhibit `FLIP` control approval.
- It is not R3 native-subhour source-label evidence because it has native sub-hour bars but no accepted source labels or per-regime qualifying-condition labels.
- It is not R5 source-panel recency-extension evidence because the data ends before the post-`2026-01-30` recency gap.
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
- Preserve the Current Cursor next action for R6. The qualifying unlock is still licensed owner/operator R6 controls, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` labels before canonical merge and downstream promotion.
