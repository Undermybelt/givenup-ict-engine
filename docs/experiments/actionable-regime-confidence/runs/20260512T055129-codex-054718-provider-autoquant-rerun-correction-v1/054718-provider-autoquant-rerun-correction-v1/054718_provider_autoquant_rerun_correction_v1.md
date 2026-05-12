# 054718 Provider AutoQuant Rerun Correction v1

Run id: `20260512T055129-codex-054718-provider-autoquant-rerun-correction-v1`

Gate result: `054718_provider_autoquant_rerun_correction_v1=rerun_exit0_provider_bars_no_source_root_unlock_no_promotion`

## Scope

Append-only correction for the `054718` provider/Auto-Quant source-unlock probe after the initial board readback captured the failed first run. The script root resolver was corrected to locate the real ict-engine checkout instead of `docs/`, then the existing `054718` probe was rerun. This correction does not mutate target roots, create source labels, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Corrected Evidence

- Corrected script: `docs/experiments/actionable-regime-confidence/runs/20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1/scripts/provider_autoquant_source_unlock_probe_after_053505_v1.py`
- Corrected wrapper exit: `0`
- Corrected JSON/report: `docs/experiments/actionable-regime-confidence/runs/20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1/provider-autoquant-source-unlock-probe-after-053505-v1/provider_autoquant_source_unlock_probe_after_053505_v1.json`
- Corrected assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1/checks/provider_autoquant_source_unlock_probe_after_053505_v1_assertions.out`

Provider probes now recorded:

| Provider path | Rows | SHA-256 |
|---|---:|---|
| `AAPL_ibkr_1h_2w.csv` | `158` | `0746bc0d32cff41612a9bab56e6a7e837a7da484bb66ac0d252f1cb08c887724` |
| `PF_XBTUSD_kraken_futures_1h_20260131_20260510.csv` | `2000` | `4ce6974a63eda68f268f81e6e56e2f6933f0d160a15d5d1933c5d466bc24880d` |
| `QQQ_yfinance_1h_20260131_20260510.csv` | `473` | `f85640f440e27b7aae8af9ffaf39816643e52027d1a44c1571aa4b0a4ecefad2` |

Auto-Quant corrected readback: `dependency_ready_seed_required`, healthy `true`, data_ready `true`, next blocker `auto_quant_seed_strategies_required`.

## Decision

The stale `054718` board decision that reported wrapper exit `1`, wrong `docs/target` paths, and no provider bars is superseded on process status and provider-bar readback only. The gate remains non-promoting: provider bars are not source-owned `MainRegimeV2` labels, not R6 matched normal controls, and not native sub-hour source-label rows.

Required target roots remain absent:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

Promotion remains blocked: source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only after explicit source/control approval, verifier-native R6 owner/export rows with normal controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a target root.
