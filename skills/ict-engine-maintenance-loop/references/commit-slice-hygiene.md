# Commit Slice Hygiene for ICT Engine

Use when a dirty `ict-engine` tree mixes Board A/B evidence, provider/runtime fixes, generated run artifacts, and unrelated agent residue.

## Baseline sequence

1. Inspect first:
   - `git status --short`
   - `git diff --name-only`
   - `git diff --stat`
2. Estimate large or suspicious paths before staging:
   - `du -sh <path> 2>/dev/null`
   - `git ls-files <path> | wc -l`
   - `git check-ignore -v <path> || true`
3. Stage the coherent slice by explicit path. Avoid `git add .`.
4. Prove exclusions before commit:
   - `git diff --cached --name-only | grep '^support/docs/experiments/actionable-regime-confidence/runs/' || true`
   - `git diff --cached --name-only | wc -l`
   - `git status --short | grep '^?? \(0.5201009511947632\|docs/\|skills/\)' || true`
5. Verify:
   - `cargo fmt && git diff --check && git diff --cached --check`
   - `cargo check -q && cargo test -q`
   - Python research/auto-quant tests with the repo PYTHONPATH and `uv --with pytest --with pandas --with pyarrow`.
6. After commit, re-run:
   - `git status --short`
   - `git log -1 --oneline`

## Pitfalls

- `.gitignore` does not hide already tracked files. A tracked run-tree `workflow_snapshot.json` can remain modified after the run directory is ignored; leave it unstaged unless the user explicitly asks to alter or revert it.
- Multi-agent residue may include `docs/`, `skills/`, scratch numeric files, and generated evidence. Treat these as unrelated until a route or user scope says otherwise.
- Commit success is not completion if residual artifacts matter; report them explicitly in final evidence.
