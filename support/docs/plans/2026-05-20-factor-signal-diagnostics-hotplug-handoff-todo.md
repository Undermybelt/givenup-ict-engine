# Factor Signal Diagnostics Hotplug Handoff TODO

Updated: 2026-05-20

## Route

- Primary route: `sd/ict-engine-surface-intgr`.
- External source intake: QuantInvestStrats `qis.perfstats.signal_diagnostics` pattern only; no vendored dependency, clone, install, or runtime import.
- Safety: zero-config stdlib Python script; no default state dir, provider call, credential read, or repo-local generated output.

## Implemented Slice

- Added `support/scripts/research/factor_signal_diagnostics.py`.
- Added tests in `support/scripts/research/tests/test_factor_signal_diagnostics.py`.
- Added optional profile example in `support/examples/factor_signal_diagnostics/personal_hotplug_profile.example.json`.

## Consumer Commands

Zero-config smoke:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py --demo --compact
```

Optional JSON artifact, no repo pollution:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py --demo --output /tmp/ict-engine-factor-signal-diagnostics/report.json --compact
```

User-selected hotplug profile:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py \
  --input /tmp/my_factor_panel.csv \
  --profile /tmp/ict-engine-factor-signal-profile.json \
  --cost-bps-side 2 \
  --output /tmp/ict-engine-factor-signal-diagnostics/report.json \
  --compact
```

Auto-Quant aggregate rank rows:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py \
  --rank-rows-csv /tmp/rank_rows.csv \
  --cost-bps-side 2 \
  --compact
```

Real/simulated trade feedback rows:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py \
  --real-trades-jsonl /tmp/real_trades.jsonl \
  --cost-bps-side 2 \
  --compact
```

Input CSV contract:

```text
timestamp,asset,horizon,regime,signal,forward_return
```

## Output Contract

- Compact stdout is one line for token-friendly agent use.
- Full JSON is optional via `--json` or `--output`.
- `trade_usable` remains `false`; this is Gate 1/2 diagnostic evidence only.
- When the profile includes `timeframe_ladder`, JSON includes `timeframe_ladder_summary` with covered/missing/passed horizons; no private ladder is assumed by default.
- Promotion still requires downstream Pre-Bayes, BBN, CatBoost/path-ranker, execution-tree, feedback/update, and strict cost/density gates.

## Verification

- `python3 -m unittest support/scripts/research/tests/test_factor_signal_diagnostics.py` -> OK, 6 tests.
- `python3 support/scripts/research/factor_signal_diagnostics.py --demo --compact` -> one-line token-friendly smoke output.
- `python3 support/scripts/research/factor_signal_diagnostics.py --demo --output /tmp/ict-engine-factor-signal-diagnostics/report.json --compact` -> JSON artifact written outside repo; `trade_usable=false` retained.
- Converter tests cover `--rank-rows-csv` aggregate AQ rows and `--real-trades-jsonl` trade feedback rows.
- Timeframe ladder test covers caller-selected 1m/5m/15m/30m/1h/4h/1d coverage/missing reporting.

## Next TODO

1. Add a Rust CLI wrapper only after the dirty `src/main.rs` lane is clear, or route through an existing script command surface.
2. Feed best-bucket diagnostics into candidate-pack metadata as optional evidence, not as a hard default.
3. If adopted downstream, persist artifacts under caller-supplied `/tmp/...` or explicit `--state-dir`, never repo root.
