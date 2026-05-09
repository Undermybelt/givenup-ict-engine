# 2026-05-09 Regime Bundle BBN Diagnostics Handoff TODO

## Mission

Continue `regime-consumer-bundle -> BBN diagnostics -> execution consumer surface` closure.

Hard constraints:
- zero config by default: no new required env/config
- token friendly: compact machine fields and short trace lines
- no pollution: runtime smoke state under `/tmp/...`
- no debt: tests plus real CLI proof before claiming done
- hot-plug: only active when user passes `--regime-consumer-bundle`; default path unchanged
- user-specific content preserved: VRP/NQ bundle fields remain sidecar payload, not hardwired into core defaults

## Route / Skill

- Route alias: `ict-engine-runtime`
- Router read: `~/.hermes/routing/skill-router.md`
- Project router: `~/.hermes/routing/project-router.md` missing, no override
- Repo guide read: `AGENTS.md`
- Skill used: `~/.hermes/skills/ict-engine/ict-engine-runtime/SKILL.md`
- References used:
  - `references/mainline-regime-catboost-execution-audit.md`
  - `references/mainline-consumer-reason-field.md`
  - `references/regime-consumer-bundle-and-mature-ranker-validation.md`

## Current slice

Goal: feed existing `RegimeReadOnlyBbnSoftEvidence` into analyze/analyze-live diagnostics without mutating posterior math.

Implemented so far:
- Added `RegimeConsumerBundleAdapter::bbn_soft_evidence_trace_entries()`.
- Emits compact fields:
  - `regime_bbn_soft_evidence_strength=strong|moderate|neutral`
  - `regime_bbn_soft_evidence_weight=0.900|0.650|0.000`
  - `regime_bbn_decision_state=<state>`
  - `regime_bbn_trade_usable=<bool>`
  - `regime_bbn_label=<label>`
  - `regime_bbn_label_set=<comma-list>`
  - `regime_bbn_transition_hazard=<float>`
  - `regime_bbn_reasons=<comma-list>`
- `analyze` and `analyze-live` now append those fields to:
  - `report.supporting.artifact_action_summary`
  - `report.supporting.pre_bayes_evidence_filter.rationale` as `read_only_<entry>`
  - `report.supporting.pre_bayes_evidence_filter.evidence_assignments` as `read_only_<key>=<value>`
- Added adapter test for compact BBN soft evidence trace entries.

Validation done:
- `cargo test --test regime_consumer_bundle_adapter -- --nocapture` -> 12/12 pass
- `cargo check` -> pass
- `cargo build --bin ict-engine` -> pass
- real CLI smoke wrote `/tmp/ict-mainline-regime-audit/analyze-regime-bundle-bbn.json`
- smoke assertion result: `ok neutral 0.000`
- implementation commit already present: `58c17b6 feat: surface regime bundle bbn trace`

## Files touched this slice

- `src/application/regime/consumer_bundle_adapter.rs`
- `src/analyze_command.rs`
- `src/analyze_live_command.rs`
- `tests/regime_consumer_bundle_adapter.rs`
- `docs/plans/2026-05-09-regime-bundle-bbn-diagnostics-handoff-todo.md`

## TODO next

### P0 - Finish verification

- [x] Run focused adapter test.
- [x] Run `cargo check`.
- [x] Run `cargo build --bin ict-engine`.
- [x] Run real `analyze` smoke with `/tmp/ict-mainline-regime-audit/regime-consumer-bundle-sample.json`.
- [x] Confirm JSON fields in:
  - `report.supporting.artifact_action_summary`
  - `report.supporting.pre_bayes_evidence_filter.rationale`
  - `report.supporting.pre_bayes_evidence_filter.evidence_assignments.read_only_regime_bbn_soft_evidence_strength`

### P1 - Runtime smoke command

```bash
BASE=/tmp/ict-mainline-regime-audit
cargo build --bin ict-engine
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-root "$BASE" \
  --state-dir "$BASE/state" \
  --output-format json \
  --inline-ledger \
  --regime-consumer-bundle "$BASE/regime-consumer-bundle-sample.json" \
  > "$BASE/analyze-regime-bundle-bbn.json"
python3 - <<'PY'
import json
p='/tmp/ict-mainline-regime-audit/analyze-regime-bundle-bbn.json'
d=json.load(open(p))
s=d['report']['supporting']
a=s['artifact_action_summary']
f=s['pre_bayes_evidence_filter']
assert 'regime_bbn_soft_evidence_strength=strong' in a
assert 'regime_bbn_soft_evidence_weight=0.900' in a
assert 'read_only_regime_bbn_soft_evidence_strength' in f['evidence_assignments']
assert f['evidence_assignments']['read_only_regime_bbn_soft_evidence_strength'] == 'strong'
assert any(x == 'read_only_regime_bbn_soft_evidence_strength=strong' for x in f['rationale'])
print('ok')
PY
```

### P2 - Commit discipline

- [x] Run `git status --short` before staging.
- [x] Implementation committed in `58c17b6 feat: surface regime bundle bbn trace`.
- [x] Stage and commit this handoff doc only; leave unrelated dirty files untouched.
- Commit: pending in this session until git commit completes.

## Open design boundary

This slice intentionally does not change posterior math. It is diagnostic-only and read-only. Promotion to actual BBN posterior influence should be a later feature gate with explicit field names and separate tests.
