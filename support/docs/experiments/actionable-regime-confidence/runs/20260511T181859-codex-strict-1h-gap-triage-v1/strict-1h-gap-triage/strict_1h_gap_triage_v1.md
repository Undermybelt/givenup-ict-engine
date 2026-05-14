# Strict 1h Gap Triage v1

Run ID: `20260511T181859+0800-codex-strict-1h-gap-triage-v1`

This triages the remaining strict exact-source `1h` ticker/root gaps from `exact_1h_source_universe_expansion_v1` without refetching provider data.

## Result

- Strict slots: `156`.
- Accepted strict rows: `41`.
- Blocked strict rows: `115`.
- Provider-ready tickers: `39/39`.
- Provider-not-ready tickers: `0`.
- Near-miss blocked rows: `34`.
- Zero-accepted-root tickers: `BA, HD, TMO, UNH`.
- Recency extension candidates available: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Gate result: `strict_1h_gap_triage_v1=provider_ready_source_label_support_blocked`.
- Full objective achieved: `false`; `update_goal=false`.

## Accepted By Root

| Root | Accepted | Blocked | Accepted tickers |
|---|---:|---:|---|
| `Bull` | 27 | 12 | AAPL, ABBV, AMZN, BAC, CAT, CSCO, CVX, GE, GOOGL, GS, JNJ, JPM, MCD, META, MS, MSFT, NFLX, NVDA, T, VZ, WFC, WMT, XOM, ^DJI, ^GSPC, ^IXIC, ^RUT |
| `Bear` | 4 | 35 | COP, NKE, PFE, SBUX |
| `Sideways` | 7 | 32 | CVX, DIS, MCD, MSFT, PFE, VZ, ^RUT |
| `Crisis` | 3 | 36 | AMD, INTC, TSLA |

## Blocker Summary

| Blocker | Count |
|---|---:|
| `heldout_time_support_below_73` | 103 |
| `heldout_time_wilson95_below_0_95` | 103 |
| `calibration_support_below_73` | 101 |
| `calibration_wilson95_below_0_95` | 101 |

## Next

Do not refetch yfinance 1h for this gap. Acquire source-owned recency extension rows or an owner-approved broader label/equivalence panel, then rerun strict ticker/root gates.
