# Andrews Pitchfork Median Rejoin AQ Prep

- created_at: `2026-05-31T05:07:03+0800`
- owner: `codex`
- agent_name: `codex-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- route_alias: `local/ict-engi-fact-rese-muta`
- workdoc: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep.claim`
- repo_run_root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep-v1`
- factor_family: `andrews_pitchfork_median_rejoin`
- status: `terminalized_training_prep_no_launch`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Guard

The current runtime window is occupied by foreign live roots. Initial compact
audit showed the MMI local screen live, and the follow-up compact audit at
`2026-05-31T05:12:53+0800` still reported `status=needs_attention`,
`active_claims=2`, `live_factor_processes=3`, `trade_usable_true=0`, and
`promotion_allowed_true=0`.

This packet is no-launch by design. It creates the training document,
factor-local workdoc, claim, and AQ strategy material only. No provider, IBKR
historical, AutoQuant/Freqtrade/TOMAC backtest, local screen, paper/sim/live,
downstream lifecycle, feedback ingestion, or policy training command was
launched.

## Duplicate Check

Focused searches found no exact `Andrews`, `Pitchfork`, `median line`,
`median_line`, or `Schiff` lane in current claims or actionable-regime-confidence
docs/scripts. This is distinct from the active MMI lane and from recent Kairi,
ETH OTE, VHF, Kase/DevStop, Ichimoku, Chande/CFO, Donchian, volatility shock,
and volume-zone work.

## Source-Backed Hypothesis

Andrews' Pitchfork is a median-line trend-channel tool built from three pivots.
It uses a median line plus two parallel lines for dynamic support/resistance and
breakout/breakdown interpretation:

- `https://help.ctrader.com/knowledge-base/line-studies-tools/andrews-pitchfork/`
- `https://commodity.com/technical-analysis/andrews-pitchfork/`
- `https://www.metastock.com/customer/resources/taaz/?p=33`

Candidate branch:

`RegimeRoot -> TrendExpansion -> MedianLineChannel -> AndrewsPitchforkRejoin -> MtfSlopeResonance -> tomac_idxfut_andrews_pitchfork_median_rejoin_<timeframe>_v1`

Timeframe policy:

- each of `5m`, `15m`, `30m`, `1h`, `4h`, `1d` is an independent factor first.
- multi-timeframe resonance is only a later filter after single-timeframe evidence exists.
- session target is `ETH/full_retained_session`; RTH-only rows cannot promote.

The expected edge is controlled trend rejoin after price reacts toward the
median line and resumes in the direction of the parent channel. It must fail
closed if pivot extraction is unstable, the channel is too narrow to clear
product-specific cost, or exact AQ/downstream/paper-feedback gates do not pass.

## Prepared Material

- strategy material: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/aq_workspace/user_data/strategies_external/TomacAndrewsPitchforkMedianRejoinPrepV1.py`
- retained TOMAC data links: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/aq_workspace/user_data/data/futures`
- retained TOMAC source summary: `/tmp/ict-engine-tomac-aq-data-stage-20260530T212321+0800/summary.json`
- workdoc: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/workdoc.md`
- terminal metrics: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/checks/terminal_metrics.json`

Classes:

- `TomacAndrewsPitchforkMedianRejoin5mPrepV1`
- `TomacAndrewsPitchforkMedianRejoin15mPrepV1`
- `TomacAndrewsPitchforkMedianRejoin30mPrepV1`
- `TomacAndrewsPitchforkMedianRejoin1hPrepV1`
- `TomacAndrewsPitchforkMedianRejoin4hPrepV1`
- `TomacAndrewsPitchforkMedianRejoin1dPrepV1`

## Verification

- `python3 -m json.tool /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep.claim` -> pass.
- `python3 -m py_compile /tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/aq_workspace/user_data/strategies_external/TomacAndrewsPitchforkMedianRejoinPrepV1.py` -> pass.
- retained TOMAC feather link staging -> `21` links for `NQ/YM/XAU` across `1m/5m/15m/30m/1h/4h/1d`, with `0` broken links.
- class readback -> base class plus independent `5m/15m/30m/1h/4h/1d` classes present.
- follow-up compact audit did not list this Andrews prep as an attention claim.

## Next Legal Step

After a same-turn audit shows `active_claims=0` and `live_factor_processes=0`,
run the exact AQ candidate beginning with `15m` or `30m` NQ/YM/XAU, then
inspect terminal metrics before any downstream step.

Do not change `promotion_allowed`, `trade_usable`, or `update_goal` from this
prep packet.
