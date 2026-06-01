# Release mirror README-only sync

Use when the operator asks to mirror a single upstream README formatting/docs commit into the public release repository.

## Pattern

1. Route through `ict-engine-maintenance-loop` and read the mirror repo's nearest `CLAUDE.md` / `AGENT.md` before changing files.
2. Identify the release mirror clone/worktree explicitly. On this host, prior mirror clones appeared under `/private/tmp/ict-engine-v0.1.3-mirror.*`, with remote `Undermybelt/ict-engine-release.git`; do not assume the main development repo is the mirror.
3. Verify the source commit is README-only before applying it:
   - `git -C <source> show --stat --oneline --name-status <commit> -- README.md`
   - `git -C <source> diff <commit>^ <commit> -- README.md > /tmp/ict-readme-<commit>.patch`
4. Verify the destination is clean enough for this slice and only stage README:
   - `git -C <mirror> status --short --branch`
   - `git -C <mirror> apply --check /tmp/ict-readme-<commit>.patch`
   - `git -C <mirror> apply /tmp/ict-readme-<commit>.patch`
5. Prove parity and one-file scope before commit:
   - `git -C <source> show <commit>:README.md > /tmp/ict-src-readme`
   - `cmp -s /tmp/ict-src-readme <mirror>/README.md`
   - `git -C <mirror> diff --check -- README.md`
   - `git -C <mirror> diff --name-only` must be only `README.md`.
6. Commit with the source commit subject if appropriate. If push is rejected as non-fast-forward, fetch shallow remote and rebase the README-only commit onto `origin/main` instead of force-pushing:
   - `git -C <mirror> fetch --depth=1 origin main`
   - `git -C <mirror> rebase --onto origin/main <old-base> main`
7. Push only `main`, then verify remote head:
   - `git -C <mirror> push origin main`
   - `git -C <mirror> ls-remote origin refs/heads/main`

## Pitfalls

- The source development repo may have a very dirty `main`; do not stage or clean it for a release mirror README sync.
- A release mirror clone can be shallow/grafted. A normal fetch may fail or produce partial history; shallow `fetch --depth=1 origin main` is sufficient when rebasing a single local docs commit.
- Do not update tags unless the operator explicitly asks. A README-only mirror-main update is not a release retag.
- Do not run full Rust validation for pure README parity unless requested; verify file parity, one-file scope, markdown diff check, and remote head.
