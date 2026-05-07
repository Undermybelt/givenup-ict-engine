# Auto-Quant Post-Factor Runtime Closure TODO

> Authoritative execution board for the runtime closure that begins **after** factor / regime research has already produced worthwhile candidates.
> Keep this board separate from `docs/plans/2026-05-05-execution-tree-factor-auto-quant-todo.md`.

**Goal:** turn selected Auto-Quant factor / regime outputs into real runtime recommendation support through the existing `ict-engine` surfaces for BBN prior/posterior updates, structural path ranking, and execution-tree / workflow evidence.

**Architecture:** factor discovery stays in Auto-Quant and additive external helpers. This board starts only once a candidate pack or regime artifact is good enough to test runtime adoption. Use the existing public CLI and persisted artifact surfaces first; only reopen repo code if the no-code runtime closure trial proves an actual handoff, lineage, or status-surface gap.

**Tech Stack:** `./target/debug/ict-engine auto-quant-results-import`, `auto-quant-prior-init`, `auto-quant-ingest-real-trades`, `export-structural-path-ranking-target`, `policy-training-status`, `register-structural-path-ranking-trainer-artifact`, `apply-structural-path-ranking-external-scores`, `analyze`, `workflow-status`, `artifact-status`, `/tmp/...` state dirs, Auto-Quant `strategy_library.json`, realized-trades JSONL artifacts, and existing `workflow_snapshot.json` / `execution_tree_trace.json` surfaces.

**Baseline / Authority Refs:** `docs/plans/2026-05-05-execution-tree-factor-auto-quant-todo.md`, `docs/202605071246nextstep`, `docs/2026-04-26-auto-quant-bbn-prior-init-plan.md`, `docs/2026-04-26-auto-quant-real-trades-plan.md`, `docs/plans/2026-05-02-catboost-path-ranking-target-design.md`, `docs/structural-belief-learning-repo-map.md`, `src/main.rs`, `src/application/auto_quant/command_entry.rs`, `src/application/orchestration/structural_playbook.rs`, `src/application/orchestration/execution_tree.rs`.

**Compatibility Boundary:** preserve zero-config public CLI behavior, consumer-usable status surfaces, token-friendly human/compact summaries, and low-pollution execution through explicit `/tmp/...` state dirs. Do not reopen factor-family search here unless a runtime closure blocker proves the candidate package itself is not importable. Do not rely on manual JSON surgery in `state/` or `policy_training/` as the canonical workflow.

---

## Decision Lock

- [x] `docs/202605071246nextstep` is directionally correct: the project has meaningful factor / regime progress, but the end-to-end runtime closure after factor discovery is still partial.
- [x] The current factor todo remains authoritative for factor discovery, regime validation, and external strategy iteration.
- [x] This board is the authority for the **post-factor** closure path:
  - `Auto-Quant candidate artifact`
  - `regime / filter adoption evidence`
  - `BBN prior / posterior evidence`
  - `CatBoost / structural path-ranking evidence`
  - `execution tree / workflow before-after evidence`
- [x] Existing repo public surfaces are real and must be used before reopening repo code:
  - `auto-quant-results-import`
  - `auto-quant-prior-init`
  - `auto-quant-ingest-real-trades`
  - `export-structural-path-ranking-target`
  - `policy-training-status`
  - `register-structural-path-ranking-trainer-artifact`
  - `apply-structural-path-ranking-external-scores`
  - `analyze`
  - `workflow-status`
- [x] Standalone factor backtests, regime F1, or prior-init alone do **not** count as runtime closure.
- [x] Structural path ranking remains an external-trainer boundary until enough real raw-scored mature rows exist; do not fake a trained CatBoost runtime just because target/export/status surfaces are present.

## Hard Constraints

- Keep `/tmp/...` state isolation for every real closure trial.
- Do not manually edit `state/<symbol>/bbn_network.json`, `learning_state.json`, or `policy_training/*.json*` except for explicit rollback recipes already documented by the repo.
- Prefer no-code closure using existing public commands before any repo code change.
- If code reopens, keep it minimal and bounded to the missing handoff / lineage / status surface.
- Do not reopen factor-family search, provider expansion, or unrelated runtime refactors in this board.
- Update this same markdown in place after each real slice.

## Current Diagnosis

### Already true in repo

- `Auto-Quant -> BBN prior-init` is not hypothetical; public import and prior-init commands already exist and are wired.
- `Auto-Quant -> real trade posterior feedback` is not hypothetical; `auto-quant-ingest-real-trades` already exists as a batch feedback surface.
- `CatBoost/path-ranking target export and status` are not hypothetical; public export, status, trainer-artifact registration, and external-score apply surfaces already exist.
- `Execution tree` is not hypothetical; the scorer, `execution_tree_trace.json`, and workflow snapshot consumption already exist.

### Still not closed

- There is no single authoritative board that starts **after** factor discovery and drives the candidate through these runtime layers in order.
- The factor board currently proves research value, not whether runtime recommendation support actually changed.
- The repo still lacks accepted evidence that a current promotable candidate pack has been:
  - imported as canonical Auto-Quant strategy-library material
  - used to mutate BBN priors in a controlled state dir
  - optionally fed back through real-trade ingestion
  - exported into structural path-ranking targets from the same state
  - given enough scored mature rows to validate a trained path ranker
  - proven to change or not change execution-tree / workflow outputs with exact before/after artifacts

### Why this board exists

- The factor board is intentionally repo-code-frozen and research-heavy.
- The post-factor closure path may require:
  - command-sequence discipline
  - provenance / lineage audit
  - runtime before/after diffing
  - possibly small repo code slices if the existing surfaces stop short
- Mixing those responsibilities back into the factor board hides whether the project is actually becoming more actionable for live suggestions.

## Current Todo Board

### Done

- [x] Audited the current factor todo and confirmed it is strong as a factor / regime research board but not sufficient as an end-to-end runtime closure board.
- [x] Audited `docs/202605071246nextstep` and accepted its core diagnosis: the main gap is post-factor closure, especially through BBN / path ranking / execution-tree evidence.
- [x] Verified that the repo already exposes public surfaces for:
  - `auto-quant-results-import`
  - `auto-quant-prior-init`
  - `auto-quant-ingest-real-trades`
  - `policy-training-status`
  - `register-structural-path-ranking-trainer-artifact`
  - `apply-structural-path-ranking-external-scores`
  - `export-structural-path-ranking-target`
  - `analyze`
  - `workflow-status`
- [x] Split board ownership:
  - factor / regime search remains on `2026-05-05-execution-tree-factor-auto-quant-todo.md`
  - post-factor runtime closure moves here
- [x] **2026-05-07 Slice 1: VRP V2 pandas candidate import and prior-init closure.**
  - created `strategy_library.json` for VRPCompression_V2_NQ_15m (pandas script, not FreqTrade)
  - validation metrics: 815 trades / Sharpe 3.329 / max DD -3.70% over 8Y (2019-2025)
  - `auto-quant-results-import`: succeeded, `n_ok=1`, `library_artifact_id=auto_quant_strategy_library_NQ_20260507T095702.840788000Z`
  - `auto-quant-prior-init --dry-run`: showed CPT diff `[win=277, loss=538, be=0]` → `final_probs=[0.346, 0.000, 0.654]`
  - `auto-quant-prior-init`: applied, `prior_init_artifact_id=auto_quant_prior_init_NQ_20260507T095722.161320000Z`
  - `workflow-status`: phase=analyze, gate=pass_neutralized, entry=medium, direction=Bull
  - `execution_tree_trace.json`: branch=transition_guardrail, bias=guarded, gate=observe, execution_score=0.58
  - `pre-bayes-status`: gate=pass_neutralized, soft_evidence=yes, long=0.551
  - `policy-training-status`: structural path ranking target export missing (expected — no external ranker yet)
  - state dir: `/tmp/vrp-v2-runtime-closure/`

### Next

- [ ] Run analyze with real NQ data and capture execution-tree before/after:
  - current blocker: full 15m dataset times out; need smaller slice or optimized run
  - fallback: use existing `/tmp/ict-engine-family-a-profile/NQ/` which has prior analyze artifacts
- [ ] Export structural path-ranking targets from the post-prior state:
  - `export-structural-path-ranking-target`
  - `policy-training-status`
- [ ] Document exact blocker for external ranker artifact:
  - current state: no trained CatBoost/XGBoost model on structural path ranking
  - raw-scored mature rows = 0
  - calibration not possible without external trainer
- [ ] Decide whether to:
  - accept VRP V2 as deployable based on pandas evidence alone (recommended per factor todo)
  - or invest in CatBoost policy surface training for Layer 2 enrichment
- [ ] If accepting VRP V2 as deployable:
  - close this post-factor board with explicit verdict
  - hand off to production/monitoring phase

### Not Yet

- [ ] New factor-family search
- [ ] New regime-feature experimentation
- [ ] Provider expansion beyond what the chosen candidate package already needs
- [ ] Runtime rewrites not justified by a proven closure blocker
- [ ] Claiming trained CatBoost runtime closure from target-export/status surfaces alone

## Ordered Execution Checklist

1. Choose one already-worthwhile candidate pack from the factor board; do not start from a speculative new factor.
2. Materialize the candidate adoption package and log the exact artifact paths.
3. Capture baseline runtime evidence in a fresh `/tmp/...` state dir:
   - `./target/debug/ict-engine workflow-status --symbol <SYMBOL> --state-dir /tmp/<state> --human`
   - `./target/debug/ict-engine analyze --symbol <SYMBOL> --data-root <DATA_ROOT> --state-dir /tmp/<state> --human`
4. Run:
   - `./target/debug/ict-engine auto-quant-results-import --symbol <SYMBOL> --state-dir /tmp/<state> --library <strategy_library.json> --dry-run`
   - then the same command without `--dry-run` if the manifest is correct
5. Run:
   - `./target/debug/ict-engine auto-quant-prior-init --symbol <SYMBOL> --state-dir /tmp/<state> --dry-run`
   - then the same command without `--dry-run` once the CPT diff and ledger intent are understood
6. Re-run:
   - `workflow-status --human`
   - `analyze --human`
   - diff `workflow_snapshot.json` and `execution_tree_trace.json`
7. If a realized-trades JSONL exists, run:
   - `./target/debug/ict-engine auto-quant-ingest-real-trades --symbol <SYMBOL> --state-dir /tmp/<state> --trades <artifact.jsonl> --dry-run`
   - then the same command without `--dry-run`
8. Export structural path-ranking targets from the same state:
   - `./target/debug/ict-engine export-structural-path-ranking-target --symbol <SYMBOL> --state-dir /tmp/<state>`
   - `./target/debug/ict-engine policy-training-status --symbol <SYMBOL> --state-dir /tmp/<state> --human`
9. Only if a real external trainer artifact and score file exist, run:
   - `./target/debug/ict-engine register-structural-path-ranking-trainer-artifact --symbol <SYMBOL> --state-dir /tmp/<state> --artifact-uri <URI> --model-family <FAMILY> --score-column <COLUMN>`
   - `./target/debug/ict-engine apply-structural-path-ranking-external-scores --symbol <SYMBOL> --state-dir /tmp/<state> --scores-file <scores.csv-or-jsonl>`
   - then re-run `policy-training-status`, `workflow-status`, and `analyze`
10. If any step fails, persist the exact blocker before moving to the next layer.

## Success Standard

This board is successful only if all of the following become true for at least one real candidate pack:

- the candidate is expressed as a canonical Auto-Quant import artifact, not just an external note;
- BBN prior-init is applied or explicitly blocked with exact evidence;
- real-trade posterior ingestion is applied or explicitly blocked with exact evidence;
- structural path-ranking export/status is produced from the same runtime state;
- trained-ranker application is either executed with real artifacts or explicitly blocked with exact evidence;
- execution-tree / workflow before-after evidence shows whether runtime recommendation support actually changed.

This board is **not** successful if:

- it only proves factor backtests again;
- it only proves regime F1 again;
- it only proves that prior-init moved numbers without checking downstream runtime surfaces;
- it only proves target export/status without a real judgment on whether path ranking is actionable;
- it claims runtime closure without exact `workflow_snapshot` / `execution_tree_trace` before-after evidence.

## Verification

- `./target/debug/ict-engine auto-quant-results-import --help`
- `./target/debug/ict-engine auto-quant-prior-init --help`
- `./target/debug/ict-engine auto-quant-ingest-real-trades --help`
- `./target/debug/ict-engine export-structural-path-ranking-target --help`
- `./target/debug/ict-engine policy-training-status --help`
- `./target/debug/ict-engine analyze --help`
- `./target/debug/ict-engine workflow-status --help`
- exact `/tmp/...` state-dir snapshots for before and after each successful mutation

## Conclusion

The right next move is **not** “继续堆更多因子就算闭环”, and also not “马上重写整个 runtime”. The right move is:

- keep the factor board focused on factor / regime discovery;
- use this board to prove whether the existing repo surfaces can already carry one good candidate through BBN, path ranking, and execution-tree recommendation support;
- only if that proof fails, reopen the smallest code slice needed.
