---
name: ict-engine-release-mirror-ci
description: Use when publishing ict-engine to the private release mirror, when GitHub Actions fails after publication, when a published tag needs correction, or when source repo and release mirror targets may be confused.
---

# ICT Engine Release Mirror CI

## Core rule

Publishing is part of verification. Local gates prove the export is worth publishing; the release mirror and its remote GitHub Actions prove cross-OS consumer safety. Do not stop at local green when the user's concern is whether another operating system will fail.

For `ict-engine`, the outward release target is `Undermybelt/ict-engine-release`. The source repo `Undermybelt/givenup-ict-engine` is provenance and development history, not the release surface.

## Use when

- User says release, publish, 发布, 发版, mirror, `ict-engine-release`, GitHub Actions failed after publish, run failed, cross-OS CI, correction release.
- A tag already exists and the remote release or CI is wrong.
- Local source checks pass but the release mirror may differ.
- Dirty shared checkout makes packaging or docs/runtime gates unreliable.

## Release loop

1. Re-read repo-local instructions and live handoff/TODO surfaces before touching files.
2. Protect the shared checkout: `git status --short`, stage exact files only, never `git add .` from a dirty `ict-engine` tree.
3. Build a clean committed export or clean mirror clone. Validate from that clean tree, not from a dirty working tree.
4. Run CI-equivalent local gates before publishing:
   - `python3 support/scripts/ci/check_docs_runtime_isolation.py`
   - release privacy audit with compact output and `release_blocking_hits=0`
   - `cargo fmt --check`
   - `cargo clippy --all-targets -- -D warnings`
   - `cargo test`
   - zero-config consumer smoke such as `provider-status --compact`, demo `analyze`, and `workflow-status` with a fresh `/tmp` state dir
5. Push source commits for provenance when appropriate, but publish releases, tags, and release notes on `Undermybelt/ict-engine-release`.
6. After publishing, verify the real remote state:
   - mirror `main` ref
   - tag object/peeled commit
   - GitHub release page or `gh release view`
   - GitHub Actions run conclusion
7. Treat flaky GitHub API/TLS/EOF polling as inconclusive, not as success or failure. Cross-check with `git ls-remote`, HTML release/run pages, and retries with short timeouts.

## If remote CI fails after publish

1. Inspect the exact remote run logs first; do not infer from local output.
2. Reproduce in a clean export/mirror clone with the same gate that failed.
3. Patch the source of the failure without weakening the gate.
4. Commit the fix in source if it belongs to source; then carry it into the release mirror.
5. Do not rewrite, move, or delete a published tag. Bump to a new patch version and publish a correction release.
6. Verify the new release tag and the new Actions run to `completed/success`.

Concrete precedent: `v0.1.5` mirror CI failed because `check_docs_runtime_isolation.py` caught a test fixture literal under `support/docs/plans/old.md`. The fix was to move that fixture literal to `support/docs/audits/old.md`, preserving privacy-audit coverage. The correction release was `v0.1.6`; `v0.1.5` was not rewritten.

## Mirror safety

- If mirror push rejects as non-fast-forward, preserve mirror history: fetch/clone the mirror, copy the clean export into it, commit normally, and push. Do not force-push unless the user explicitly asks and accepts history rewrite.
- Keep package-manager publication disabled unless the user explicitly changes policy. For Rust crates, `publish = false` remains a public-surface guard.
- Treat the mirror as public even if access is limited: run privacy/secret scans before release.
- Verify docs/runtime isolation in the exact exported tree. Local source may contain planning docs or fixtures that clean CI rejects.

## Required evidence

Final evidence must name:

- source HEAD commit and whether it was pushed
- release mirror repo, mirror `main` commit, and release tag commit
- release URL and Actions run URL
- local clean export path or clean mirror clone path
- local gates run and their pass/fail result
- remote Actions final conclusion
- if a previous tag failed, the old tag, reason, and correction tag

## Red flags

- Publishing to `givenup-ict-engine` when the task is an outward ict-engine release.
- Calling the job done after local checks without reading the remote mirror Actions result.
- Retrying local fixes while never publishing; that cannot reveal cross-OS CI failures.
- Rewriting a published failed tag instead of issuing a correction release.
- Trusting one failed API poll as the run conclusion.
- Running release packaging from a dirty shared checkout and assuming consumers see the same tree.

## Chinese triggers

`发布错仓库`, `发布到mirror`, `release mirror`, `ict-engine-release`, `givenup-ict-engine`, `GitHub Actions failed`, `run failed`, `发布后CI失败`, `跨OS CI`, `修复后发布`, `correction release`, `不要重写tag`, `发布才知道别的OSbug`.
