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
- largely closed on 2026-04-24
- keep as regression-watch debt, not an active hotspot

Evidence
- `docs/backend-path-audit.md`
- `docs/release-notes-draft.md`

What changed
- active `scripts/` path discovery now routes through `scripts/path_defaults.py`
- named archived backends no longer embed machine-local `/Users/...` repo/data/bin paths
- policy-training helper scripts no longer hard-code repo-local absolute paths

Residual caveat
- experiment scripts still assume a Tomac-style cleaned-data layout unless the corresponding env vars are overridden
- that is a workflow assumption, not the old machine-local absolute-path bug

One-shot feasibility
- already landed in-tree
- future work here is regression prevention, not a remaining one-shot target

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

1. stale docs that still describe old debt state
2. any optional feature-depth work on `research-verdict` / contamination / evidence-quality surfaces

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
