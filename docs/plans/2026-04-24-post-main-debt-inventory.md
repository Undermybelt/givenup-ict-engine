# Post-main Debt Inventory

Date: 2026-04-24

Purpose
- record the remaining non-`main.rs` debt after the runtime hotspot extraction line landed
- separate debts that are fixable in-tree from debts that require history rewrite or release-process decisions

Current baseline
- `src/main.rs` hotspot extraction is now materially closed by:
  - `8ce1024 Move runtime hotspots out of main`
  - `3e45254 Close main runtime extraction hotspot`
- current `src/main.rs` line count: `14236`

## Remaining debt

### 1. Archived backend portability debt

Status
- real
- code + script debt
- potentially closable in one focused branch

Evidence
- `docs/backend-path-audit.md`
- `docs/release-notes-draft.md`

What is still wrong
- archived/auxiliary python backends still embed machine-local absolute paths
- common offenders include:
  - repo root discovery by hard-coded path
  - cleaned data root discovery by hard-coded path
  - release binary lookup by hard-coded path

Highest-impact files called out by the audit
- `scripts/archive/factor_local_search_v2d.py`
- `scripts/archive/factor_cluster_jump_v2.py`
- `scripts/archive/pre_bayes_policy_tuning.py`

One-shot feasibility
- yes
- preferred shape:
  - shared helper for repo root discovery
  - shared helper for cleaned data root selection
  - shared helper for binary resolution
  - wrappers and archived backends consume those helpers

### 2. Release transport/history debt

Status
- real
- not fixable by ordinary in-tree code edits alone
- not a runtime bug

Evidence
- `docs/audits/release-signoff.md`
- `docs/release-mirror-runbook.md`

What is still wrong
- primary repo history contains oversized tracked artifacts
- GitHub rejects normal pushes because historical blobs exceed transport limits

Named examples already documented
- `state100/NQ/learning_state.json`
- `state_autoresearch_resume_bg/NQ/learning_state.json`

One-shot feasibility
- no, not as a normal code-only branch
- requires one of:
  - accepted permanent mirror-only release process
  - explicit history rewrite / filter-repo line
  - repository split / archival strategy

### 3. Analytics depth debt in release-facing research surfaces

Status
- real
- behavior/product debt
- closable, but not just by refactor

Evidence
- `docs/audits/release-signoff.md`
- `docs/audits/pre-release-audit.md`

Surfaces
- `research-verdict`
- contamination heuristics
- `evidence-quality-breakdown`

What is still wrong
- `research-verdict` is still compact, not a richer experiment analytics engine
- contamination heuristics remain conservative
- `evidence-quality-breakdown` still infers some terms from persisted state instead of persisting every raw intermediate directly

One-shot feasibility
- maybe, but only if treated as feature work with contract review and tests
- not a pure debt-only refactor

### 4. Historical docs still describing stale debt state

Status
- real
- documentation debt
- closable immediately

Evidence
- `docs/audits/release-signoff.md`
- `docs/audits/pre-release-audit.md`
- older closeout docs now partially stale without status notes

What is still wrong
- some historical audit surfaces still mention `src/main.rs` as the active structural hotspot even though that line has now been materially reduced

One-shot feasibility
- yes
- low risk

## Best next one-shot target

If the goal is "clear the remaining fixable debt in one branch", the best target is:

1. archived backend portability
2. stale docs that still describe `main.rs` debt as active

Do not mix in release-history rewrite unless the branch is explicitly approved as a history surgery branch.

## Honest end-state claim

After the `main.rs` extraction line, the remaining debt picture is:

- fixable in-tree:
  - archived backend portability
  - stale debt docs
- not fixable by ordinary code edits:
  - primary repo oversized-history transport blocker
- feature/depth debt rather than structural debt:
  - `research-verdict`
  - contamination heuristics
  - `evidence-quality-breakdown`
