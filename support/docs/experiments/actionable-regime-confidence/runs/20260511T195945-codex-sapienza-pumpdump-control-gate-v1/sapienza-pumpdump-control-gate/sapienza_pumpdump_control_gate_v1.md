# Sapienza Pump/Dump Control Gate v1

- Decision: `sapienza_pumpdump_control_gate_v1=accepted_95_scoped_telegram_pumpdump_positive_control`
- Source commit: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`
- Accepted direct variety: `pump_dump_social_text_or_twitter` scoped to `scoped_telegram_pumpdump_positive_control`
- Accepted positive event groups: `317`
- Accepted feature positive rows: `951`
- Minimum split Wilson95 LCB: `0.970640354706`
- Cross-cycle granularities: `features_5S.csv.gz, features_15S.csv.gz, features_25S.csv.gz`
- Minimum positive symbol count: `85`
- New confidence gate: `true`
- Strict full objective achieved: `false`; `update_goal=false`

## Qualifying Rule

`source commit pinned; labeled_features rows expose gt=1 pump groups and same-schema gt=0 controls for the same pump_index across 5S, 15S, and 25S feature granularities`.

Allowed action: `direct_manipulation_overlay_suppress_or_cooldown_only`. This is a direct Manipulation overlay/suppression signal only, not a trade entry signal.

## Split Evidence

| File | Split | Controlled groups | Positive groups | Wilson95 LCB |
|---|---|---:|---:|---:|
| `features_5S.csv.gz` | `all` | `317` | `317` | `0.988026925090` |
| `features_5S.csv.gz` | `chronological_calibration_first_60pct` | `190` | `190` | `0.980182470540` |
| `features_5S.csv.gz` | `chronological_heldout_last_40pct` | `127` | `127` | `0.970640354706` |
| `features_15S.csv.gz` | `all` | `317` | `317` | `0.988026925090` |
| `features_15S.csv.gz` | `chronological_calibration_first_60pct` | `190` | `190` | `0.980182470540` |
| `features_15S.csv.gz` | `chronological_heldout_last_40pct` | `127` | `127` | `0.970640354706` |
| `features_25S.csv.gz` | `all` | `317` | `317` | `0.988026925090` |
| `features_25S.csv.gz` | `chronological_calibration_first_60pct` | `190` | `190` | `0.980182470540` |
| `features_25S.csv.gz` | `chronological_heldout_last_40pct` | `127` | `127` | `0.970640354706` |

## Remaining Blockers

This closes only a scoped Telegram pump/dump positive-control slice. Strict Board A remains blocked for spoofing/layering, quote stuffing, pinging, bear raid or painting tape, source-label equivalence, native sub-hour source labels, and recency-tail repair.

## Artifacts

- JSON: `sapienza_pumpdump_control_gate_v1.json`
- Feature CSV: `sapienza_pumpdump_control_gate_v1_features.csv`
- Split CSV: `sapienza_pumpdump_control_gate_v1_splits.csv`
