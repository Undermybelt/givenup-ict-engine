# XAU Ehlers Roofing Trend Breakout Prep Packet

created_at: 2026-05-30T04:04:46+0800
owner: codex
agent_name: codex-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800
status: terminalized_no_launch_claim_guard
decision: launch_blocked_by_claim_guard
factor_id: xau_ehlers_roofing_trend_breakout_mtf_v1
run_root: /tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T040446+0800-codex-xau-ehlers-roofing-trend-breakout-prep.claim
session_scope: ETH/full_retained_session
rth_filter_applied: false
promotion_allowed: false
trade_usable: false
update_goal: false

## Objective

Stage a distinct XAU retained-cache trend-continuation factor lane while foreign
Board B active claims block runtime launch. This packet creates the factor-local
workdoc, claim, guarded runner, and a tested local prescreen path for a future
same-turn-clear window. It does not launch provider, IBKR, Auto-Quant,
Freqtrade, paper, sim, live, Pre-Bayes, BBN, CatBoost, execution tree, or
lifecycle commands.

## Branch

```text
FUTURES -> precious metals -> XAU retained-local
-> ETH/full_retained_session -> 1m execution origin
-> shifted 5m/15m/30m/1h/4h/1d context
-> MainRegime: TrendExpansion
-> SubRegime: CycleFilteredTrend
-> ProfitFactor: RoofingFilterBreakout
-> xau_ehlers_roofing_trend_breakout_mtf_v1
```

## Duplicate / Collision Check

Same-turn targeted claim search found prior Ehlers/Hilbert work, but not this
exact XAU retained-cache Roofing trend-breakout MTF lane:

- ES Ehlers high-frequency realized-volatility envelope was a different ES
  `HighFrequencyDensity -> IntradayCycleNoise` root and ended as no-verdict /
  rerun-blocked evidence.
- MGC Hilbert/SineWave was a different `CycleReversal` prep-only branch.
- MNQ/crypto Ichimoku and MNQ Hilbert lanes exist, so this packet avoids those
  families and instruments.

Initial compact audit before staging reported a foreign EUR/6E live runtime.
Latest compact audit at 2026-05-30T04:38+0800 reports `live_factor_processes=0`
but `active_claims=3`, `promotion_allowed_true=0`, and `trade_usable_true=0`.
The launch blockers are:

- `20260530T043351+0800-codex-nq-compound-rv-stress-feedback-materialization.claim`
- `20260530T043356+0800-codex-sr3-eth-fedpath-sofr-vwap-reclaim-prep.claim`
- `20260530T043611+0800-codex-he-eth-livestock-cutout-feedcost-vwap-reclaim-reserve.claim`

## Source / Idea Basis

This is a source-inspired technical family, not proof. Local source lookup found
existing ict-engine Ehlers/MAMA, Hilbert, and spectral-cycle references. A
same-turn HTTP probe for a legacy MESA Roofing Filter PDF URL returned `404`
after a redirect attempt, so the source URL is recorded as
`source_url_not_rate_verified`. The factor remains idea-only/prep-only until
real retained-cache or provider rows produce cost-surviving evidence.

## Data Reality

Same-turn parquet metadata readback confirmed XAU retained-local files exist
for all required frames under `/Users/thrill3r/Downloads/Tomac/factor_training/cache`:

| timeframe | rows |
|---|---:|
| 1m | 635274 |
| 5m | 320140 |
| 15m | 117561 |
| 30m | 58953 |
| 1h | 29491 |
| 4h | 7976 |
| 1d | 1551 |

## Candidate Mechanics

- Origin: XAU `1m` retained-local execution grid.
- Context: shifted `5m/15m/30m/1h/4h/1d` features only; no look-ahead.
- Trend filter: higher-timeframe slope and cycle-filtered trend agreement.
- Entry idea: Roofing-filtered momentum breakout after low-noise compression,
  with direction aligned to `1h/4h/1d` context.
- Exit idea: fixed RRR bracket or ATR-based bracket inherited from prior
  cost-surviving trend grammar; no trailing/tiny-take-profit churn.
- Cost gate: future Gate 1 must keep explicit friction stress and later verify
  the exact product cost model before downstream or practical admission.

## Prepared Artifacts

- Workdoc:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/workdoc.md`
- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T040446+0800-codex-xau-ehlers-roofing-trend-breakout-prep.claim`
- Guarded runner:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/scripts/run_xau_ehlers_roofing_trend_breakout_prep.py`
- Runner unit test:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/scripts/test_run_xau_ehlers_roofing_trend_breakout_prep.py`
- Dry-run manifest:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/checks/dry_run_manifest.json`
- Session coverage summary:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/checks/session_coverage_summary.json`
- GC/MGC cost model packet:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/checks/xau_gc_mgc_cost_model_packet.json`
- Terminal metrics:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/checks/terminal_metrics.json`
- Terminal summary:
  `/tmp/ict-engine-xau-ehlers-roofing-trend-breakout-prep-20260530T040446+0800/summaries/terminal_summary.json`

## Verification

Completed verification for this prep slice:

- `python3 -m py_compile` on the guarded runner and local unit test exited 0
  after adding the metadata coverage helper and isolating blocked-run test
  writes to a temporary run root.
- `/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python -m unittest scripts/test_run_xau_ehlers_roofing_trend_breakout_prep.py` exited 0 with 3 tests after a RED failure confirmed the coverage helper was missing.
- `--coverage-check` exited 0, wrote `checks/session_coverage_summary.json`,
  and confirmed outside-NY-RTH rows for XAU `1m/5m/15m/30m/1h/4h/1d`:
  `354634/221876/84425/42369/21829/6161/1551`. It records
  `metadata_only=true`, `provider_or_aq_launched=false`,
  `local_screen_launched=false`, `paper_or_sim_launched=false`, and
  `downstream_launched=false`.
- `--dry-run` exited 0, wrote the manifest, and reported all XAU ladder files
  present.
- `--check-claim-guard` exited 3 under crowded state.
- Guarded `--run` exited 3 before any data screen, provider, AQ, paper, sim,
  live, or downstream launch. It wrote a terminal packet with
  `decision=launch_blocked_by_claim_guard`.
- The current terminal packet records `foreign_attention_claim_count=3`,
  `local_screen_launched=false`, `provider_or_aq_launched=false`, and practical
  flags false.
- `checks/local_prescreen_summary.json` is intentionally absent because the
  claim guard blocked before XAU parquet data reads.
- Later same-turn audit at 2026-05-30T04:47+0800 still reported
  `status=needs_attention`, `active_claims=1`, and `live_factor_processes=0`,
  so no guarded AutoQuant/local screen launch was safe.
- A final same-turn audit at 2026-05-30T04:57+0800 still reported
  `status=needs_attention`, now with `active_claims=2` and
  `live_factor_processes=1` under a EUR run root, so AutoQuant/local screen
  launch remained explicitly blocked.
- During that wait window, the lane refreshed official IBKR/COMEX cost-model
  evidence only. `checks/xau_gc_mgc_cost_model_packet.json` validates `GC=2.52`
  per side / `5.04` round turn and `MGC=0.97` per side / `1.94` round turn,
  with broker-side secdef evidence for `GC` multiplier `100`, tick `0.1`, tick
  value `10`, and `MGC` multiplier `10`, tick `0.1`, tick value `1`. CME
  contract-spec HTML fetches failed from this host with curl exit `35`, so they
  are recorded but not used as verified sources.
- Cost survival remains unverified because continuous retained `XAU` rows still
  must map to exact `GC` or `MGC` contract months and roll rules before Gate 1,
  downstream, paper/sim, promotion, or trade-usability claims.
- Follow-up non-colliding mapping prep at 2026-05-30T05:19+0800 ran under a
  separate `/tmp` claim while a foreign EUR/6E local screen remained live. It
  launched no provider, AQ, local screen, paper, sim, live, or downstream path.
  Artifacts:
  `/tmp/ict-engine-xau-continuous-contract-mapping-prep-20260530T050546+0800/checks/xau_highest_volume_outright_gc_selection_summary.json`,
  `/tmp/ict-engine-xau-continuous-contract-mapping-prep-20260530T050546+0800/checks/xau_symbology_roll_segments.json`,
  and
  `/tmp/ict-engine-xau-continuous-contract-mapping-prep-20260530T050546+0800/checks/xau_raw_front_contract_match_summary.json`.
- Mapping prep found that retained XAU parquet cache files preserve only
  `datetime/open/high/low/close/volume`, not `symbol`, `instrument_id`, contract
  month, or roll adjustment. The raw Databento-style source and symbology are
  therefore required for cost attribution.
- The XAU symbology source is all `GC` root (`1,077,103` symbology rows,
  `7,018` raw symbols), so this lane maps to full-size COMEX `GC`, not `MGC`.
  The MGC cost reference remains comparison-only for this XAU runner.
- A naive `symbology.csv` date -> instrument_id rule is not usable for this
  runner's roll/cost proof: it selected only `125,051` rows, included spread
  symbols such as `GCG2-GCH2`, and covered only `2021-07-12` to `2023-06-09`.
- The runner-compatible raw selection rule is highest-volume positive outright
  `GC` per timestamp, rejecting symbols containing `-`. That selected
  `1,769,524` rows from `5,333,532` raw rows, dropped `1,976,135`
  spread/non-outright rows and `1,587,873` duplicate timestamp rows by volume,
  selected `55` GC contracts/instrument ids, and selected `0` MGC rows.
- Cost-model implication: ordinary IBKR cost reference for this lane is the GC
  packet (`2.52` USD per side / `5.04` USD round turn per contract before
  separate spread/slippage). Cost survival still remains unverified because the
  runner-compatible selection has `15,861` timestamp-level contract changes,
  which is a volume-leader selection rule, not a stable contract-month roll
  policy. Promotion, trade usability, and update-goal flags remain false.
- Claim JSON validated with `python3 -m json.tool`; terminal JSON validation is
  recorded under the run-root checks directory.

## Prepared Local Prescreen

The guarded runner now has a local Python prescreen path behind the claim guard.
When a future same-turn audit clears, `--run` will read the XAU retained-cache
`1m` origin and shifted `5m/15m/30m/1h/4h/1d` context, build Roofing-style
momentum/compression/breakout features, split train/OOS by time, and write
`checks/local_prescreen_summary.json`. That output remains Python-only screen
evidence and keeps `promotion_allowed=false`, `trade_usable=false`, and
`update_goal=false` until provider/AQ/downstream/lifecycle gates pass.

## Terminal Decision

terminal_status: terminalized
terminal_decision: launch_blocked_by_claim_guard
terminalized_at: 2026-05-30T04:38:57+0800

promotion_allowed: false
trade_usable: false
update_goal: false
