# Mature target rows from feedback replay

Use when `analyze` exists and BBN/CatBoost surfaces are wired, but `structural_path_ranking_target` still shows `mature_rows=0` / `rows_with_training_weight=0`.

## Pattern

1. Preserve the original state root. Work in a copied state, e.g. `state_matured`, unless the user explicitly wants mutation of the canonical run.
2. Verify an analyze snapshot exists first:
   - `state/<SYMBOL>/workflow_snapshot.json` has `latest_analyze != null`
   - `workflow-status --symbol <SYMBOL> --state-dir <state> --human` shows the analyze phase, not bootstrap.
3. Build or reuse a realized-trades JSONL in `RealTradeRecord` format. Required branch fields:
   - `regime_profit_branch_path`
   - `main_regime`
   - `sub_regime`
   - `sub_sub_regime_or_profit_factor`
   - `profit_factor`
4. Run dry-run ingest, then applied ingest:

```bash
ict-engine auto-quant-ingest-real-trades \
  --symbol <SYMBOL> \
  --state-dir <copied_state> \
  --trades <real_trades.jsonl> \
  --dry-run

ict-engine auto-quant-ingest-real-trades \
  --symbol <SYMBOL> \
  --state-dir <copied_state> \
  --trades <real_trades.jsonl>
```

5. Re-export target and inspect policy status:

```bash
ict-engine export-structural-path-ranking-target \
  --symbol <SYMBOL> --state-dir <copied_state>

ict-engine policy-training-status \
  --symbol <SYMBOL> --state-dir <copied_state> --output-format json

ict-engine workflow-status \
  --symbol <SYMBOL> --state-dir <copied_state> --human
```

## Acceptance checks

Expect:
- `auto_quant_real_trade_entry_v1.ready=true`
- `matched_rows > 0`
- `structural_path_ranking_target.mature_rows > 0`
- `rows_with_training_weight > 0`
- validation may become `raw_scored_mature >= 30` / `production_validation >= 30` / `observation_validation >= 30`

Still fail-closed unless execution tree admits it. `mature_rows` and `ranker_validation.ready=true` do not imply live-trade readiness.

## Truth labels

- Real broker fills: promotable evidence candidate only after normal execution-tree/live-admission gates.
- AQ/Freqtrade exported real per-trade rows: structural feedback evidence; must preserve trade-level PnL and branch path.
- AQ `sample_trades` from grid metrics: replay/diagnostic evidence only. It can prove the mature-row bridge works, but must be labelled as `sample-trade structural feedback replay`, not live fill evidence.

## Pitfalls

- Do not synthesize feedback from aggregate metrics alone. Use per-trade rows when available; if using sample rows, label them diagnostic.
- Do not mutate the original closure state by default; copy it first.
- If `workflow-status` remains `observe/transition_guardrail`, report that plainly even when target maturity is fixed.
- A small current `mature_rows` count can coexist with large `history_mature_rows`; report both.
