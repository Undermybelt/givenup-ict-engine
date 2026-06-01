# Regime consumer bundle + mature ranker validation

Use when continuing the mainline regime -> BBN/pre-bayes -> CatBoost/path-ranker -> execution/recommendation closure audit.

## Regime consumer bundle trace integration

Runtime pattern:
- `analyze` and `analyze-live` accept an optional `--regime-consumer-bundle <path>` plus strict flag.
- Load the bundle before state mutation so `--regime-consumer-bundle-strict` fails early.
- Append compact read-only trace lines to `report.supporting.artifact_action_summary`:
  - `regime_bundle_status=loaded|missing|invalid|disabled`
  - `regime_bundle_path=<path>`
  - `regime_decision_state=<state>`
  - `regime_trade_usable=<bool>`
  - `regime_final_label=<label>`
  - `regime_execution_tree_hint=<accept_regime|transition_guardrail|unknown_abstain>`
- Keep a combined `regime_bundle_trace:<entry>|...` line plus individual entries for machine consumers.

Verification fixture shape:
```json
{
  "schema_version": "regime-consumer-bundle/v1",
  "latest_decision": {
    "decision_state": "single_label_99",
    "trade_usable": true,
    "final_label": "primary::TrendExpansion",
    "label_set": ["primary::TrendExpansion"],
    "abstain_reasons": []
  },
  "consumer_hints": {
    "execution_tree_hint": "accept_regime",
    "bbn_evidence_hint": {
      "regime_decision_state": "single_label_99",
      "regime_trade_usable": true,
      "regime_label": "primary::TrendExpansion",
      "regime_transition_hazard": 0.0,
      "regime_decision_reasons": []
    }
  }
}
```

Smoke command:
```bash
BASE=/tmp/ict-mainline-regime-audit
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-root "$BASE" \
  --state-dir "$BASE/state" \
  --output-format json \
  --inline-ledger \
  --regime-consumer-bundle "$BASE/regime-consumer-bundle-sample.json" \
  > "$BASE/analyze-regime-bundle.json"
```

Check:
```bash
python3 - <<'PY'
import json
p='/tmp/ict-mainline-regime-audit/analyze-regime-bundle.json'
data=json.load(open(p))
summary=data['report']['supporting']['artifact_action_summary']
keys=[x for x in summary if x.startswith('regime_bundle') or x.startswith('regime_')]
assert 'regime_bundle_status=loaded' in keys
assert 'regime_decision_state=single_label_99' in keys
assert 'regime_execution_tree_hint=accept_regime' in keys
PY
```

## Read-only BBN soft evidence mapping

`RegimeConsumerBundleAdapter::to_read_only_bbn_soft_evidence()` should remain non-mutating and safe for missing/invalid bundles.

Mapping:
- `single_label_99` + `trade_usable=true` -> `Strong`, weight `0.9`
- `single_label_95` + `trade_usable=true` -> `Moderate`, weight `0.65`
- missing / invalid / disabled / transitional / label_set / unknown_abstain -> `Neutral`, weight `0.0`

Preserve fields for future consumers even when neutral:
- `decision_state`
- `trade_usable`
- `label`
- `label_set`
- `transition_hazard`
- `reasons`

Tests:
```bash
cargo test --test regime_consumer_bundle_adapter -- --nocapture
```

### BBN diagnostics surface

For diagnostic-only closure, add `RegimeConsumerBundleAdapter::bbn_soft_evidence_trace_entries()` and append its entries only when `--regime-consumer-bundle` is supplied. Keep it read-only: do not alter posterior math in the same slice.

Expected compact fields:
- `regime_bbn_soft_evidence_strength=strong|moderate|neutral`
- `regime_bbn_soft_evidence_weight=0.900|0.650|0.000`
- `regime_bbn_decision_state=<state>`
- `regime_bbn_trade_usable=<bool>`
- `regime_bbn_label=<label>` or `regime_bbn_label_set=<comma-list>`

Consumer surfaces to prove:
- `report.supporting.artifact_action_summary`
- `report.supporting.pre_bayes_evidence_filter.rationale` as `read_only_<entry>`
- `report.supporting.pre_bayes_evidence_filter.evidence_assignments` as `read_only_<key>=<value>`

Runtime smoke should assert shape, not a hard `strong`, because the sample bundle in `/tmp/ict-mainline-regime-audit` may be overwritten by previous sidecar runs and legitimately produce `neutral` (observed `ok neutral 0.000`).

## Mature ranker validation result

Known mature state used in audit:
- `/tmp/ict-engine-structural-replay-29/state`

Comparison copies:
- registered: `/tmp/ict-mainline-regime-audit/state-mature-ranker-registered`
- disabled: `/tmp/ict-mainline-regime-audit/state-mature-ranker-disabled`

Commands:
```bash
./target/debug/ict-engine policy-training-status --symbol NQ --state-dir <state> --human
./target/debug/ict-engine workflow-status --symbol NQ --state-dir <state> --human
./target/debug/ict-engine workflow-status --symbol NQ --state-dir <state> --phase structural-recommended-path-bundle --human
```

Observed registered runtime:
- `runtime_selection=enabled_registered_model_ready`
- `runtime_mode=candidate_set_only`
- `runtime_source=registered_model_artifact`
- `runtime_matches=1`

Validation interpretation:
- `raw_scored_mature=2/30`
- `production_validation=2/30`
- `observation_validation=30/30`
- `calibration=evaluated`
- `quality_ready=true`
- `ready=true`

Conclusion:
- readiness can be satisfied by observation validation even when target-row / production validation remain below `30/30`.
- In this state, registered-model vs disabled runtime did not change `workflow-status --phase structural-recommended-path-bundle --human` selected path or next command; difference surfaced in policy runtime source/status.

## Pitfalls

- Rebuild binary before CLI smoke; `cargo check` alone is insufficient.
- Use `python3`, not `python`, on macOS where `python` may be absent.
- Do not stop at source fields; prove JSON and human outputs consume the fields.
- Keep repo state clean: stage only touched files; this repo often has unrelated dirty files from other agents.
- Do not run `cargo fmt -- <files>` expecting scoped Rust formatting; it can still dirty many unrelated Rust files. For ict-engine multi-agent work, either avoid formatting unless necessary or run `rustfmt --edition 2021 <touched-file.rs>...` on only this slice's files.
