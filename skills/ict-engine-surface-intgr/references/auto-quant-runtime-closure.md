# Auto-Quant post-factor runtime closure

Use this reference when a factor-research candidate must be carried through ict-engine runtime surfaces after discovery.

## Pattern proven in session

1. Choose an already-promotable factor/regime package from the factor board; do not start new factor search.
2. Materialize a canonical `strategy_library.json` artifact, even if the source is a pandas/replay harness rather than Auto-Quant freqtrade logs.
3. Run public surfaces in an isolated `/tmp/...` state dir:
   - `auto-quant-results-import`
   - `auto-quant-prior-init --dry-run`
   - `auto-quant-prior-init`
   - `artifact-status --latest-only`
   - `analyze --demo --human` or the real data equivalent
   - `workflow-status --human --stable`
   - `export-structural-path-ranking-target`
   - `policy-training-status --human`
4. Treat prior-init as partial closure only. It proves BBN prior mutation, not posterior feedback or execution-tree improvement by itself.
5. Record exact artifact ids and state paths in the todo board after every slice.

## Exporter bridge

A small Python exporter can bridge replay-harness results into the Rust importer if it emits the schema accepted by `src/application/auto_quant/results/manifest.rs`:

- top-level: `manifest_version`, `exported_at`, `auto_quant_repo_url`, `auto_quant_pinned_ref`, `config_path`, `timeframe`, `log_path`, `strategies`, `validation_errors`
- per strategy: `name`, `file_path`, `metadata`, `status`, `validation_metrics`, `per_pair_metrics`, `pairs`, `timerange`, `commit`, `error`
- validation metrics: `sharpe`, `sortino`, `calmar`, `total_profit_pct`, `max_drawdown_pct`, `trade_count`, `win_rate_pct`, `profit_factor`

If the candidate has richer sleeve semantics, do not leave them only in free text long-term. Add structured fields or a companion artifact for:

- execution filter
- BBN/posterior filter
- timeframe
- validation window
- source harness
- trade-level realized rows

### Pandas-script → strategy_library.json bridge (proven 2026-05-07)

When the factor source is a pandas replay harness (not FreqTrade), synthesize `strategy_library.json` directly:

```python
from datetime import datetime, timezone
import json

library = {
    "manifest_version": "1.0",
    "exported_at": datetime.now(timezone.utc).isoformat(),
    "auto_quant_repo_url": "pandas_script",  # signal non-FreqTrade source
    "config_path": "scripts/auto_quant_external/<script>.py",
    "timeframe": "<base_tf>",
    "strategies": [{
        "name": "<StrategyName>_<tf>",
        "file_path": "scripts/auto_quant_external/<script>.py",
        "metadata": {
            "strategy": "<StrategyName>",
            "mutation_id": "pandas-<slug>",
            "base_factor": "<factor_key>",
            "hypothesis": "<one-line deployable thesis>",
            "paradigm": "<trend|mean_reversion|vrp|etc>",
            "status": "active",
            "created": "<date>"
        },
        "status": "ok",
        "validation_metrics": {
            "sharpe": <float>,
            "sortino": <float>,
            "calmar": <float>,
            "total_profit_pct": <float>,
            "max_drawdown_pct": <float>,
            "trade_count": <int>,
            "win_rate_pct": <float>,
            "profit_factor": <float>
        },
        "per_pair_metrics": { "<SYMBOL>": { ... } },
        "pairs": ["<SYMBOL>"],
        "timerange": "<start> -> <end>",
        "commit": "pandas_script",
        "error": None
    }]
}
write_file(path="/tmp/<name>_strategy_library.json", content=json.dumps(library, indent=2))
```

Then import via: `ict-engine auto-quant-results-import --symbol <SYM> --state-dir /tmp/<state> --library /tmp/<name>_strategy_library.json`

This bypasses the freqtrade export step while preserving the importer contract.

## Common blockers

- No realized-trades JSONL: `auto-quant-ingest-real-trades` cannot run; write/export trade rows first.
- Path ranking export works but trained runtime remains blocked when `mature_rows=0`, `raw_scored_mature=0/30`, or `trainer_artifact=missing`.
- `workflow-status` before `analyze` may show `no_workflow_state`; run `analyze` in the same state before judging runtime surfaces.
- `cargo fmt --all --check` may expose pre-existing Rust formatting drift. Do not claim Rust formatting regression unless touched Rust files differ.
- **Demo data vs real data**: `analyze --demo` produces valid execution-tree trace but not representative of real-market scores. If full dataset times out, compare before/after using prior state dirs with real-data artifacts rather than claiming demo-driven improvement.
- **Structural path ranking blocked by design**: After prior-init, `policy-training-status` will report `raw_scored_mature=0` and `runtime_selection=disabled` unless an external CatBoost/XGBoost trainer artifact exists. This is expected for pure-pandas candidates; do not treat it as a surface bug. Record it as an explicit blocker or accept the candidate as deployable on prior-init + execution-tree evidence alone.

## Evidence bundle shape

Capture:

- candidate artifact path
- state dir
- import artifact id
- prior-init artifact id
- CPT before/after row
- artifact-status rows and path existence
- `workflow_snapshot.json` and `execution_tree_trace.json` paths
- path-ranking target row counts and readiness line
- exact blocker for posterior ingestion or trained-ranker application

### Execution-tree comparison table

When comparing before/after across state dirs, capture:

| metric | before | after |
|--------|--------|-------|
| execution_score | | |
| execution_readiness | | |
| branch | | |
| gate_status | | |
| quality | | |
| prediction_vote | | |

Key fields from `execution_tree_trace.json`:
- `output.execution_score`
- `output.branch`
- `output.execution_bias`
- `output.gate_status`
- `output.split_reason_lineage[0]` (execution_readiness)
- `execution_shap_top_k[0].feature` and `.feature_value` (top contributor)

Key fields from `workflow_snapshot.json`:
- `latest_analyze.selected_entry_quality`
- `latest_analyze.selected_direction`
- `latest_analyze.pre_bayes_gate_status`
- `latest_analyze.pre_bayes_evidence_quality_score`

## Follow-up rule

Once a package crosses import + prior-init, pause new factor search until posterior ingestion / structured lineage gaps are closed or explicitly rejected. Otherwise the project keeps proving research value without runtime adoption closure.
