# TrendExpansion BOCPD/Dynamic-Momentum/VHF-CHOP MTF Fail-Closed

Use this note when the user asks for expansion/trend-only factor training or
source-backed factor tailoring under the strict rule: enter only when closed-bar
evidence predicts `TrendExpansion`; all other regimes are reference/veto only.

## Slice

- Date: 2026-05-31
- Repo: `<ict-engine-repo>`
- Source packet: `support/docs/experiments/actionable-regime-confidence/20260531T222217+0800-codex-trendexpansion-transition-tailor-source-intake.md`
- Exact-AQ packet: `support/docs/experiments/actionable-regime-confidence/20260531T235023+0800-codex-trendexpansion-bocpd-dynmom-vhfchop-mtf-exact-aq.md`
- Run root: `/tmp/ict-engine-trendexpansion-bocpd-dynmom-vhfchop-mtf-exact-aq-20260531T235023+0800`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T235023+0800-codex-trendexpansion-bocpd-dynmom-vhfchop-mtf-exact-aq.claim`

## Source Intake

The source-backed composite used these ideas only as hypothesis/intake, not as
promotion evidence:

- Adams/MacKay BOCPD for completed-bar state-change admission.
- Time-series momentum as the parent trend prior and higher-timeframe veto.
- VHF and CHOP as no-trend/chop vetoes and transition confirmation.
- Public technical-analysis implementation references for indicator definition
  cross-checking only; do not import external repo code into runtime.

## No-Lookahead Contract

- `entry_allowed_regimes=TrendExpansion` only.
- `other_regimes_policy=reference_veto_only_no_entry`.
- No realized future trend label may be used as entry eligibility.
- BOCPD/reset, dynamic momentum, VHF, CHOP, and breakout levels must be shifted
  to completed-bar availability before entry.
- Market, stop, or limit entry variants are legal only after the closed signal
  bar exists; earliest modeled fill is next bar or later.

## Exact-AQ Result

AutoQuant/Freqtrade completed six independent NQ timeframes (`5m`, `15m`,
`30m`, `1h`, `4h`, `1d`) with exit code `0` and exported trades. The run was
gross/Freqtrade execution evidence only because `config.tomac.json` had
`fee=0.0`; the review subtracted shared verified NQ IBKR commission via
`support/scripts/research/instrument_cost_model.py`.

Cost/split/year review:
`/tmp/ict-engine-trendexpansion-bocpd-dynmom-vhfchop-mtf-exact-aq-20260531T235023+0800/checks/aq_metrics_with_ibkr_nq_fee.json`

| Timeframe | Trades | NQ IBKR-fee net pct | Net PF | Verdict |
|---|---:|---:|---:|---|
| 5m | 3170 | +2.9635 | 1.0065 | weak; middle split negative and 2 years negative |
| 15m | 1381 | +0.7977 | 1.0026 | weak; first split negative and 2 years negative |
| 30m | 823 | +32.9245 | 1.1596 | best lead; middle split negative and 2023 negative |
| 1h | 408 | +10.7659 | 1.0873 | low density; final split negative and 2025 negative |
| 4h | 125 | -9.2430 | 0.8805 | negative |
| 1d | 16 | -8.8679 | 0.6835 | sparse negative |

## Reusable Lesson

This packet is not trade-usable and must remain `promotion_allowed=false`,
`trade_usable=false`, and `update_goal=false`. The useful lead is only the `30m`
child: it preserved the requested expansion/trend-only structure and survived
verified NQ commission in aggregate, but failed chronological split/year
stability. Future work should mutate only the 30m parent lead first, targeting
the negative middle split / 2023 regime pocket without lowering gates.

Do not repeat the six-timeframe BOCPD/dynamic-momentum/VHF-CHOP packet unchanged.
Do not paper/sim/live this branch, and do not launch downstream lifecycle until a
repaired exact-AQ child passes instrument-cost net, split/year stability,
ETH/full-retained session evidence, downstream lifecycle, and accepted execution
feedback.
