# Provider LTF Nursery Pair Whitelist Correction v1

Run id: `20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1`

Gate result: `provider_ltf_nursery_v1=data_ready_then_autoq_cwd_pair_whitelist_blocked`

## Scope

Terminal correction for the provider-LTF nursery path after the Auto-Quant workspace was prepared successfully. The earlier wrong-cwd run that reported `No module named 'freqtrade'` is stale for the corrected terminal path. The corrected run uses the Auto-Quant repo root and fails later, at pair whitelist resolution.

## Readback

- Prepare exit: `0`
- Auto-Quant data ready after prepare: `true`
- Auto-Quant status: `dependency_ready_data_ready`
- Corrected Auto-Quant CWD run exit: `1`
- Corrected Auto-Quant CWD error: `No pair in whitelist.`
- Previous wrong-cwd run exit: `1`
- Previous wrong-cwd error: `No module named 'freqtrade'`

## Decision

The blocker is now the pair label / whitelist mapping, not Auto-Quant data readiness and not the missing `freqtrade` import.

Selected history remains false. Source/control evidence remains false. Selected-data AutoQuant promotion remains false. Downstream promotion rerun remains false. Promotion allowed remains false. `update_goal=false`.

## Artifacts

- Prepare stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/01_auto_quant_prepare_provider_ltf.out`
- Prepare stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/01_auto_quant_prepare_provider_ltf.err`
- Prepare exit: `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/01_auto_quant_prepare_provider_ltf.exit`
- Wrong-cwd run stdout/stderr/exit: `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/02_run_tomac_provider_ltf.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/02_run_tomac_provider_ltf.err`, `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/02_run_tomac_provider_ltf.exit`
- Corrected Auto-Quant CWD run stdout/stderr/exit: `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/03_run_tomac_provider_ltf_autoq_cwd.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/03_run_tomac_provider_ltf_autoq_cwd.err`, `docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/command-output/03_run_tomac_provider_ltf_autoq_cwd.exit`

