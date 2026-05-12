# 065652 AutoQuant Threaded DNS Prepare After 065116

Run id: `20260512T065652+0800-codex-autoquant-threaded-dns-prepare-after-065116-v1`

State dir: `/tmp/ict-engine-board-a-064259-runtime-v1`

Purpose: close out the `065116` AutoQuant prepare blocker as a diagnostic/runtime-readiness issue only. The prior failure was isolated to AutoQuant/Freqtrade market loading through aiohttp's async DNS resolver path; system DNS and curl were not the boundary.

## Run-Local Resolver Patch

The run added a local `PYTHONPATH` shim at:

- `docs/experiments/actionable-regime-confidence/runs/20260512T065652+0800-codex-autoquant-threaded-dns-prepare-after-065116-v1/pythonpath/sitecustomize.py`

The shim only overrides aiohttp resolver selection in the process using this `PYTHONPATH`:

```python
import aiohttp.resolver as _resolver
_resolver.DefaultResolver = _resolver.ThreadedResolver
```

This is diagnostic and run-local. It does not modify repo runtime code, AutoQuant source, or the managed workspace.

## Commands

- `PYTHONPATH=.../pythonpath ./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-board-a-064259-runtime-v1`
- `./target/debug/ict-engine auto-quant-status --state-dir /tmp/ict-engine-board-a-064259-runtime-v1 --output-format json`

## Results

- `auto_quant_prepare_threaded_dns.exit`: `0`
- `auto_quant_prepare_threaded_dns.stdout`: `status=prepared`, `data_ready=true`, `dependency_status_before=dependency_ready_data_ready`, `dependency_status_after=dependency_ready_data_ready`
- `auto_quant_status_after_threaded_dns_prepare.exit`: `0`
- `auto_quant_status_after_threaded_dns_prepare.stdout`: `status=dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, `data_ready=true`
- Managed AutoQuant commit: `34ba6b6ee6aa69813a50a72158d4c089d97afb96`
- Recommended next command from status: `uv run --with ta-lib /tmp/ict-engine-board-a-064259-runtime-v1/auto-quant/.deps/auto-quant/run.py`

## Gate Readback

This run proves the local AutoQuant dependency/data preparation surface can become healthy when aiohttp is forced away from the failing async DNS resolver path.

This run does not satisfy Board B promotion gates:

- No non-quarantined R3/R5/R6 source/control root was approved.
- No explicit user-selected historical path was supplied for exactly one of `HTF=1d`, `MTF=4h`, or `LTF=1h`.
- No selected-data AutoQuant strategy training was run by this artifact.
- No canonical merge was performed.
- No filter / Pre-Bayes -> BBN -> CatBoost / path-ranking -> execution-tree promotion rerun was performed.
- `promotion_allowed=false`.
- `update_goal=false`.

Board B remains fail-closed at cursor `034002/downstream-combined-v1`.
