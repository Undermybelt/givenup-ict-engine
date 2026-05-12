# BearExpansion Legacy Reissue Audit

Run id: `20260511T042030+0800-codex-bear-expansion-legacy-reissue-audit`.

## Decision

- Gate result: `blocked_bear_expansion_legacy_reissue_missing_directional_bear_semantics`
- Accepted new active roots: none
- Missing active roots remain: `BearExpansion`, `Manipulation`

## Findings

- `docs/experiments/actionable-regime-confidence/runs/20260510T232808-codex-broader-mtf-regime-search/audit/broader_mtf_regime_acceptance_audit.json`: `trend_base AND drawdown64 >= -0.001320604675` -> blocked; accepted TrendExpansion packet is directionless or non-bearish; it does not prove directional BearExpansion under the active root contract.
- `docs/experiments/actionable-regime-confidence/runs/20260510T214429-codex-legacy-regime-contract-reissue/legacy-contract/legacy_regime_contract_reissue_report.json`: `trend_persistence_16 >= 1 AND stretch64 >= 0.05054785682` -> blocked; accepted TrendExpansion packet is directionless or non-bearish; it does not prove directional BearExpansion under the active root contract.
- `docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json`: `trend_persistence_16 >= 1 AND stretch64 >= 0.05054785682` -> blocked; accepted TrendExpansion packet is directionless or non-bearish; it does not prove directional BearExpansion under the active root contract.
