# Board B AQ-First Nursery LTF RunTOMAC v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T093210+0800-codex-board-b-aq-first-nursery-ltf-runtomac-v1`

Mode: `incubation_only` / `non_promoting_aq_feedback`

Source handoff: `docs/experiments/actionable-regime-confidence/runs/20260512T092832+0800-codex-board-b-aq-first-nursery-ltf-v1/state_b2r_nq_ltf_nursery_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/auto_quant_handoff.factor_research.json`

## Evidence

- First wrapper stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T093210+0800-codex-board-b-aq-first-nursery-ltf-runtomac-v1/command-output/01_run_tomac.out`
- First wrapper stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T093210+0800-codex-board-b-aq-first-nursery-ltf-runtomac-v1/command-output/01_run_tomac.err`
- Workspace-owned run stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T093210+0800-codex-board-b-aq-first-nursery-ltf-runtomac-v1/command-output/02_run_tomac_workspace.out`
- Workspace-owned run stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T093210+0800-codex-board-b-aq-first-nursery-ltf-runtomac-v1/command-output/02_run_tomac_workspace.err`
- Workspace-owned run exit: `docs/experiments/actionable-regime-confidence/runs/20260512T093210+0800-codex-board-b-aq-first-nursery-ltf-runtomac-v1/command-output/02_run_tomac_workspace.exit`

## Readback

- The first wrapper invoked `uv run --with ta-lib .../run_tomac.py` from the ict-engine root and failed before measurement with `ModuleNotFoundError: No module named 'freqtrade'`. Root cause: wrong `uv` project owner, not a strategy result.
- The workspace-owned invocation used `uv --directory .../.deps/auto-quant run --with ta-lib run_tomac.py`, proving the Auto-Quant workspace dependencies are the runtime owner.
- The workspace-owned run exited `1`: `0` successful backtests, `1` failed strategy, `OperationalException: No pair in whitelist`.
- Diagnostic readback showed the configured pair `B2R_NQ_COST_CRISIS_REPAIR_032157/USD` was present in the synthetic exchange market map, tradable, active, and quoted in `USD`.
- The remaining blocker is Freqtrade pairlist validation: `expand_pairlist(..., keep_invalid=True)` removes underscore-containing pair strings, so the branch-symbol pair is filtered before measurement.

## Decision

- Gate: `aq_first_nursery_ltf_runtomac_v1=pairlist_underscore_filter_no_mature_observations`
- Mature rooted branch observations added: `0`
- Selected-data AutoQuant promotion: `false`
- Downstream promotion rerun: `false`
- Promotion allowed: `false`
- `update_goal=false`

## Next

- Do not repeat this LTF synthetic TOMAC shape until the run-local Auto-Quant workspace uses a Freqtrade-compatible pair alias or pairlist sanitizer.
- Prefer recorded-history nursery replay paths with nonzero mature observations, especially the earlier precision-fixed recorded-MTF feedback, over underscore-bearing synthetic/provider-LTF symbols that fail before measurement.
