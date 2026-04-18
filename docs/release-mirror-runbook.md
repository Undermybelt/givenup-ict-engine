# Private mirror release runbook

Purpose
- publish release tags without rewriting the primary research repo history
- keep both source repo and release repo private

Repos
- source repo: `Undermybelt/ict-engine`
- private release mirror: `Undermybelt/ict-engine-release`

When to use
- primary repo history contains oversized state artifacts or other research-only history that should not ship
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
- do not push release tags from the source repo when history contains oversized research artifacts
- source repo remains the development / experiment truth
- mirror repo remains the release transport surface
- release notes should point back to source-repo docs where needed

Post-release follow-up
- if mirror release flow becomes standard, automate it with a small script
- keep `docs/audits/release-signoff.md` current before every release
