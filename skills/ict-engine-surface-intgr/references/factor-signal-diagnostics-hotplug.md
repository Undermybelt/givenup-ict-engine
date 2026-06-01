# Factor signal diagnostics hotplug pattern

Session source: 2026-05-20 ict-engine external repo intake and implementation.

## When to use

Use this pattern when ict-engine needs a consumer-safe factor diagnostic surface inspired by external quant libraries, especially QuantInvestStrats `qis.perfstats.signal_diagnostics`, without vendoring external code or loading user-private data by default.

## Durable pattern

- Keep the first slice zero-config and stdlib-only when possible.
- Provide a bundled `--demo` path for clean consumer smoke checks.
- Keep stdout compact by default; write JSON only when the caller passes an explicit `--output`, preferably under `/tmp/...`.
- Treat personal market/data choices as hotplug profile inputs, not defaults.
- Mark diagnostic output as evidence only: `trade_usable=false` until strict downstream gates pass.
- Preserve branch identity fields when converting evidence:
  - `regime_profit_branch_path`
  - `root_regime` / inferred regime bucket
  - `horizon` / timeframe
  - symbol or asset
- Support aggregate Auto-Quant rows and real/simulated trade rows as optional converters, but keep them caller-selected:
  - `--rank-rows-csv`
  - `--real-trades-jsonl`
- If the hotplug profile includes `timeframe_ladder`, emit `timeframe_ladder_summary` with covered, missing, and passed horizons. This supports personal 1m/5m/15m/30m/1h/4h/1d workflows without making that ladder a public default.
- Candidate packs may opt in with `--signal-diagnostics-json`; only compact diagnostic metadata is embedded under `signal_diagnostics_evidence`, and it remains `diagnostic_only=true` / `trade_usable=false` unless downstream gates explicitly promote later.
- Candidate-pack surfaces should also have a `--demo` mode so open-source consumers can generate the full three-artifact pack with no manifest, provider, credential, or repo-local state.

## Useful fields for diagnostics

Core input panel:

```text
timestamp,asset,horizon,regime,signal,forward_return
```

Core output metrics:

- `n`
- `asset_count`
- `beta`
- `t_stat`
- `ic_pearson`
- `ic_spearman`
- `mean_signed_return_bps_after_cost`
- `root_delta_bps`
- `candidate_passed_gate`
- `promotion_allowed`
- `trade_usable=false`

Candidate-pack diagnostic metadata:

- `signal_diagnostics_evidence.schema_version`
- `diagnostic_only=true`
- `promotion_allowed`
- `trade_usable=false`
- `best_bucket`
- `timeframe_ladder_summary`

## Pitfalls

- Do not make external repo code a runtime dependency just because its metric design is useful.
- Do not wire into `src/main.rs` while that file is dirty from unrelated lanes; prefer a standalone support script first.
- Do not let a positive diagnostic imply live promotion. It is Gate 1/2 evidence only.
- Do not write repo-local generated reports by default.
- Do not bake a single operator's symbols, provider paths, or private data roots into public defaults; use an optional profile example instead.
- Do not require a real Auto-Quant manifest for smoke testing; provide a tiny deterministic `--demo` manifest/candidate.

## Verification pattern

Run all of these before commit:

```bash
python3 -m unittest support/scripts/research/tests/test_factor_signal_diagnostics.py
python3 -m unittest support/scripts/research/tests/test_factor_candidate_pack.py
python3 support/scripts/research/factor_signal_diagnostics.py --demo --compact
python3 support/scripts/research/factor_signal_diagnostics.py --demo --output /tmp/ict-engine-factor-signal-diagnostics/report.json --compact
python3 support/scripts/research/factor_candidate_pack.py --demo --output-dir /tmp/ict-engine-candidate-pack-demo
```

If converters are present, smoke both:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py --rank-rows-csv /tmp/rank_rows.csv --cost-bps-side 0 --compact
python3 support/scripts/research/factor_signal_diagnostics.py --real-trades-jsonl /tmp/real_trades.jsonl --cost-bps-side 0 --compact
```

If ladder support is changed, verify profile-selected coverage/missing output with a `/tmp/...` CSV/profile pair and inspect `timeframe_ladder_summary` in the JSON artifact.

If candidate-pack attachment is changed, verify a composed smoke:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py --demo --output /tmp/ict-engine-factor-signal-diagnostics/report.json --compact
python3 support/scripts/research/factor_candidate_pack.py --demo --signal-diagnostics-json /tmp/ict-engine-factor-signal-diagnostics/report.json --output-dir /tmp/ict-engine-candidate-pack-demo
```
