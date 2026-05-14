# Hugging Face Dark Pool Synthetic Manipulation Audit

Run ID: `20260511T094950+0800-codex-hf-dark-pool-synthetic-manipulation-audit`

Source: `https://huggingface.co/datasets/solsticestudioai/dark-pool-pack`

## Result

- Dataset rows inspected under `/tmp`: `10000`.
- `Market_Manipulation_Spoofing` candidate positives: `3333`.
- `Legitimate_High_Risk_Activity` benign lookalikes: `3334`.
- Event timestamp rows: `10000`; telemetry timestamp rows: `10000`.
- Synthetic rows: `10000`.
- The dataset card and schema state that the sample is synthetic and contains no real transactions.
- The rows have labels and timestamps, but lack real venue/order-book/order-lifecycle provenance.
- Accepted V6 roots added: `0`.
- Accepted direct `ManipulationLiquidityEngineering` rows/windows added: `0`.

## Gate

`blocked_hf_dark_pool_pack_synthetic_not_accepted`

Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
