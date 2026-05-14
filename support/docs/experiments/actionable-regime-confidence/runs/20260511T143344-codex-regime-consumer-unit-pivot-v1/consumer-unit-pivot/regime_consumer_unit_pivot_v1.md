# Regime Consumer Unit Pivot v1

Run ID: `20260511T143344+0800-codex-regime-consumer-unit-pivot-v1`

This run diagnoses why the current loop is producing broad negative rows and separates evidence by the downstream unit that can actually consume it.

## Diagnosis

- Root cause: the board lacks an explicit consumer-unit acceptance contract.
- The loop mixed market-regime context, cohort/root-pair support, strict ticker/root support, and direct manipulation evidence into one denominator.
- AMD/CVX `8/8` was a root-pair cohort gate; the 39-ticker `1h` expansion was a strict per-ticker/root gate.
- More provider-native timeframe sweeps would mostly mirror source-date overlap and would not acquire labels or matched direct manipulation rows.

## Consumer Unit Ledger

| Consumer Unit | Status | Evidence | Blocker |
|---|---|---|---|
| `market_regime_context_gate` | `context_ready_not_full_completion` | exact same-source daily panel plus 1w/1mo and 1h panel-context support | needs downstream-facing context packet and full-cycle/species accounting; not ticker-specific |
| `ticker_specific_signal_gate` | `partial` | strict exact 1h ticker/root rows=41/156 by root={'Bull': 27, 'Bear': 4, 'Sideways': 7, 'Crisis': 3} | sparse Bear/Sideways/Crisis per-ticker support; not a blocker for market context consumers |
| `direct_manipulation_gate` | `partial_blocked` | scoped direct varieties=pump_dump_telegram_event,dex_self_trade_order_lifecycle,dex_consecutive_self_trade_order_lifecycle,midsummer_bsc_wash_maker,midsummer_multichain_wash_maker | needs matched negatives for spoofing/layering plus quote stuffing/pinging/bear-raid/painting rows |
| `source_label_acquisition_gate` | `blocked_open` | active source-label requests remain=556 | more OHLCV/provider timeframe sweeps do not create labels; acquire rows or extend source panel |

## Decision

- Market regime context has exact-source positive supply for all four price roots.
- Ticker-specific support is partial and should not be used as a blocker for market-context consumers.
- Direct Manipulation stays partial/blocked until direct matched rows exist.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

## Next

Use this consumer-unit ledger as the acceptance contract: materialize a downstream-facing market_regime_context packet from existing exact-source positives, while routing Manipulation to direct matched-row acquisition; do not run more broad timeframe sweeps until a consumer explicitly needs ticker-specific support.
