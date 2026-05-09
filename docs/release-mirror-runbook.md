# Private mirror release runbook

Purpose
- publish release tags without rewriting the primary research repo history
- keep both source repo and release repo private

Status note (2026-04-24)
- the original source-repo oversized-history blocker has been cleared
- source repo pushes are available again
- this runbook remains valid as a clean tree-state release flow, but it is no longer required by an unresolved history transport failure

Repos
- source repo: `Undermybelt/ict-engine`
- private release mirror: `Undermybelt/ict-engine-release`

## Current constraint

- Source repo history is now pushable after generated `state*` artifacts were removed from git history.
- Mirror release is still the preferred clean release transport when you want the published repo to reflect current tree state rather than full development history.
- Source repo remains the development truth; mirror repo remains the curated release surface.

When to use
- whenever a new release tag is needed
- release should represent current tree state, not full experimental history

Release flow

1. verify source repo
```bash
cargo check
cargo test
python3 scripts/help_audit.py
cargo run --quiet -- research-verdict --symbol DEMO --state-dir state
cargo run --quiet -- evidence-quality-breakdown --symbol DEMO --state-dir state
```

2. export current tree state
```bash
rm -rf /tmp/ict-engine-release-export
mkdir -p /tmp/ict-engine-release-export
git archive --format=tar HEAD | tar -x -C /tmp/ict-engine-release-export
```

3. initialize clean release repo
```bash
cd /tmp/ict-engine-release-export
git init
git checkout -b main
git add .
git commit -m "release: ict-engine v0.0.1"
```

4. point at private mirror and publish
```bash
git remote add origin https://github.com/Undermybelt/ict-engine-release.git
git tag -a v0.0.1 -m "v0.0.1"
git push origin main
git push origin v0.0.1
```

5. create private GitHub release
```bash
gh release create v0.0.1 \
  --repo Undermybelt/ict-engine-release \
  --title "v0.0.1" \
  --notes-file docs/audits/release-signoff.md
```

Rules
- source repo remains the development / experiment truth
- mirror repo remains the preferred clean release transport surface
- release notes should point back to source-repo docs where needed
- bump the version (`v0.0.1` → `v0.0.2` → …) every release; refresh `docs/audits/release-signoff.md` and `docs/release-notes-draft.md` before running the runbook

Post-release follow-up
- if mirror release flow becomes standard, automate it with a small script
- keep `docs/audits/release-signoff.md` current before every release
