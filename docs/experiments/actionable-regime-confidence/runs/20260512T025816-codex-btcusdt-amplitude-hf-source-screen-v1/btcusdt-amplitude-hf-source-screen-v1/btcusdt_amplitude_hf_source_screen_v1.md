# BTCUSDT Amplitude Hugging Face Source Screen v1

Run id: `20260512T025816-codex-btcusdt-amplitude-hf-source-screen-v1`

Gate result: `btcusdt_amplitude_hf_source_screen_v1=single_symbol_derived_amplitude_regime_labels_no_promotion`

Source:
- Dataset: `123olp/btcusdt-amplitude-top100`
- URL: https://huggingface.co/datasets/123olp/btcusdt-amplitude-top100
- Public: `True`; gated: `False`; disabled: `False`
- Dataset SHA: `ff9d802e45cad196a06fc11beb541afff253d76e`
- Last modified: `2026-05-10T23:20:31.000Z`

Readback:
- Manifest symbol: `BTCUSDT`
- Manifest timeframes: `1m, 5m, 15m, 1h, 4h, 1d, 1w`
- Top100 rows from manifest: `700`
- Event-window rows from manifest: `413359`
- Forward-return rows from manifest: `2800`
- Derived top100 rows summarized in-memory: `700`
- Derived symbols: `BTCUSDT`
- Derived regime phases: `{"bear": 101, "bull": 599}`
- Regime windows: `3` rows; max window end `2026-12-31 23:59:59 UTC`

Decision:
- This is useful source-discovery evidence for BTCUSDT amplitude research, but not a Board A promotion input.
- It is single-symbol BTCUSDT only and does not provide cross-instrument or cross-market validation.
- Labels are derived bull/bear cycle context attached to amplitude Top100 events, not source-owned `MainRegimeV2` root exports.
- The visible label set does not cover `Sideways` or `Crisis`, and it does not provide direct `Manipulation` positive/negative controls.
- The regime-window table includes a future-dated recovery-cycle window ending after this screen date, so it cannot be treated as independent observed source labels for acceptance.
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
- Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.
