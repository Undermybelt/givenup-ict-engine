# ES/NQ Source Crosswalk Calibration v1

Run ID: `20260511T135932+0800-codex-es-nq-source-crosswalk-calibration-v1`

This run uses local ES/NQ `15m` history only for target session coverage and derived `1h` coverage. It does not use target OHLCV as labels; source labels remain the stock-market-regimes daily parent roots.

## Result

- Scoped ES/NQ `15m/1h` crosswalk slots: `16`.
- Accepted source-label crosswalk attachment rows: `2`.
- Blocked crosswalk attachment rows: `14`.
- Accepted full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `es_nq_crosswalk_calibration_v1_accepted2_blocked14_not_full_objective`.

## Policy

- ES=F -> ^GSPC is treated as a direct index-future-to-source-index parent-day context policy.
- NQ=F -> ^IXIC remains blocked because NQ tracks Nasdaq 100 while the source panel has Nasdaq Composite.
- Target 15m bars are used only to prove target session-date coverage; derived 1h coverage requires at least four 15m bars on the session date.
- No target OHLCV, HMM state, generated label, strategy prediction, or future return is used as a label.

## Accepted Slots

| Instrument | Timeframe | Root |
|---|---|---|
| `ES=F` | `15m` | `Bull` |
| `ES=F` | `1h` | `Bull` |

## Root Support by Scoped Slot

| Instrument | Timeframe | Root | Relation Accepted | Cal Support | Cal Wilson95 | Heldout-Time Support | Heldout-Time Wilson95 | Accepted | Blocker |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `ES=F` | `15m` | `Bear` | `true` | 8 | 0.675592 | 3 | 0.438503 | `false` | `calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `ES=F` | `15m` | `Bull` | `true` | 320 | 0.988138 | 160 | 0.976554 | `true` | `` |
| `ES=F` | `15m` | `Crisis` | `true` | 0 | 0.000000 | 0 | 0.000000 | `false` | `calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `ES=F` | `15m` | `Sideways` | `true` | 134 | 0.972131 | 65 | 0.944198 | `false` | `heldout_time_wilson95_below_0_95` |
| `ES=F` | `1h` | `Bear` | `true` | 2 | 0.342380 | 3 | 0.438503 | `false` | `calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `ES=F` | `1h` | `Bull` | `true` | 233 | 0.983780 | 139 | 0.973107 | `true` | `` |
| `ES=F` | `1h` | `Crisis` | `true` | 0 | 0.000000 | 0 | 0.000000 | `false` | `calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `ES=F` | `1h` | `Sideways` | `true` | 88 | 0.958173 | 53 | 0.932418 | `false` | `heldout_time_wilson95_below_0_95` |
| `NQ=F` | `15m` | `Bear` | `false` | 49 | 0.927302 | 82 | 0.955249 | `false` | `crosswalk_relation_policy_unresolved|calibration_support_below_50|calibration_wilson95_below_0_95` |
| `NQ=F` | `15m` | `Bull` | `false` | 190 | 0.980182 | 64 | 0.943376 | `false` | `crosswalk_relation_policy_unresolved|heldout_time_wilson95_below_0_95` |
| `NQ=F` | `15m` | `Crisis` | `false` | 9 | 0.700855 | 24 | 0.862024 | `false` | `crosswalk_relation_policy_unresolved|calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `NQ=F` | `15m` | `Sideways` | `false` | 34 | 0.898485 | 56 | 0.935806 | `false` | `crosswalk_relation_policy_unresolved|calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_wilson95_below_0_95` |
| `NQ=F` | `1h` | `Bear` | `false` | 24 | 0.862024 | 77 | 0.952482 | `false` | `crosswalk_relation_policy_unresolved|calibration_support_below_50|calibration_wilson95_below_0_95` |
| `NQ=F` | `1h` | `Bull` | `false` | 157 | 0.976116 | 36 | 0.903581 | `false` | `crosswalk_relation_policy_unresolved|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `NQ=F` | `1h` | `Crisis` | `false` | 0 | 0.000000 | 18 | 0.824121 | `false` | `crosswalk_relation_policy_unresolved|calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_support_below_50|heldout_time_wilson95_below_0_95` |
| `NQ=F` | `1h` | `Sideways` | `false` | 23 | 0.856883 | 52 | 0.931208 | `false` | `crosswalk_relation_policy_unresolved|calibration_support_below_50|calibration_wilson95_below_0_95|heldout_time_wilson95_below_0_95` |

## Target Data

| Instrument | Local Symbol | 15m Bars | 15m Sessions | 1h Sessions From 15m | Date Range | Raw Committed |
|---|---|---:|---:|---:|---|---|
| `ES=F` | `ES` | 39881 | 1408 | 990 | `2012-04-23` to `2025-08-04` | `false` |
| `NQ=F` | `NQ` | 28975 | 738 | 575 | `2012-07-06` to `2023-10-26` | `false` |

## Next

- Resolve NQ with a Nasdaq-100-grade source label or explicit owner-approved ^IXIC policy.
- Add broader exact-source Crisis/Bear/Sideways support; ES Bull alone does not close the full matrix.
- Keep ETF/futures/index crosswalks, Kraken/full-species rows, and direct Manipulation acquisition as separate lanes.
