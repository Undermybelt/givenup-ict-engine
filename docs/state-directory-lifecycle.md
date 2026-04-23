# State Directory Lifecycle

Default behavior:

- If `--state-dir` is omitted, `ict-engine` uses `ICT_ENGINE_STATE_DIR` when set.
- Otherwise it falls back to `./state`.
- On first auto-creation of `./state` outside an `ict-engine` or Cargo project directory, the CLI prints a warning to `stderr`.

Recommended layout:

- Keep one persistent state directory per experiment stream.
- Treat `state_autoresearch_smoke` as a small reusable smoke baseline.
- Treat other `state_*` directories as disposable session artifacts unless you intentionally preserve them.

Operational guidance:

- Prefer an explicit path for scripted runs: `--state-dir /tmp/ict-engine-smoke`
- Prefer `ICT_ENGINE_STATE_DIR` for interactive sessions
- Periodically inspect size with `du -sh state*`
- Archive or delete stale `state_*` directories once their artifacts are no longer needed

Cleanup helper:

- `scripts/state_cleanup.sh` lists the largest local `state*` directories and suggests removal commands without deleting anything automatically.
