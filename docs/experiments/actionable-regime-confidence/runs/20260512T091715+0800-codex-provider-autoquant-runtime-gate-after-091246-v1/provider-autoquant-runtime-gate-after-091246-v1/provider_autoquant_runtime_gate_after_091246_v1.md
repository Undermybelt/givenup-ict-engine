# Provider / Auto-Quant Runtime Gate After 091246 v1

Run id: `20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1`

Gate result: `provider_autoquant_runtime_gate_after_091246_v1=autoquant_dependency_ready_prepare_blocked_provider_partial_no_promotion`

## Scope

Read-only runtime gate after the `091246` source/control refresh. It checks provider readiness for yfinance, TradingViewRemix, IBKR, and Kraken, then reuses the repo's managed Auto-Quant surfaces to confirm whether the dependency can boot and prepare data. It does not run selected-data AutoQuant promotion, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, or any trade step.

## Readback

- Board B SHA-256 before artifact: `e8bc22587afd4cb40207b78b533028476a5818d3dd0d20eb8114c46eb169e808`.
- yfinance live ready: `True`.
- yfinance market_data ready: `True`.
- TradingViewRemix ready: `True`.
- Kraken CLI ready: `True`.
- Kraken public market-data ready: `False`.
- IBKR market-data ready: `False`.
- IBKR gateway reachable: `True`.
- Auto-Quant bootstrap healthy: `True`.
- Auto-Quant dependency healthy after bootstrap: `True`.
- Auto-Quant data ready after prepare: `False`.
- Auto-Quant prepare return code: `1`.
- Auto-Quant prepare DNS blocked: `True`.

## Decision

The provider surface is partially ready: yfinance and TradingViewRemix are ready, Kraken CLI is ready, and IBKR gateway port 4002 is reachable, but IBKR market-data remains dependency-blocked and Kraken public remains dependency-blocked.

Auto-Quant itself is now bootstrapped and dependency-healthy, but data preparation is still blocked by network/DNS access to Binance. That means the downstream selected-data AutoQuant chain is still not promotable from this slice.

Accepted rows added `0`; source/control evidence acquired false; selected history false; selected-data AutoQuant promotion false; downstream promotion rerun false; promotion allowed false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/provider-autoquant-runtime-gate-after-091246-v1/provider_autoquant_runtime_gate_after_091246_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/provider-autoquant-runtime-gate-after-091246-v1/provider_autoquant_runtime_gate_after_091246_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/checks/provider_autoquant_runtime_gate_after_091246_v1_assertions.out`
- Provider status agent raw stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/raw/provider_status_agent.stdout.txt`
- Provider status agent raw stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/raw/provider_status_agent.stderr.txt`
- Provider status jsonl raw stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/raw/provider_status_jsonl.stdout.txt`
- Workflow status raw stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/raw/workflow_status_bootstrap_agent.stdout.txt`
- Auto-Quant bootstrap raw stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/raw/auto_quant_bootstrap.stdout.txt`
- Auto-Quant prepare raw stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1/raw/auto_quant_prepare.stderr.txt`

## Next

Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated R6/R5/R3 source-control rows with matched controls and provenance, explicit same-exhibit `FLIP`-as-control approval, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, or verifier-native Crisis-capable R3 native-subhour labels before verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal`.
