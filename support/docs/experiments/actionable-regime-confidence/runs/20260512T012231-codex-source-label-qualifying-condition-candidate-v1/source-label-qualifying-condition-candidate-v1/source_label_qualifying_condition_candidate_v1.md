# Source Label Qualifying Condition Candidate v1

- Run id: `20260512T012231-codex-source-label-qualifying-condition-candidate-v1`.
- Board hash observed: `e7fc017f0e48a78ebd762b02c83097ac0cccb027b3b00e5e845b7638cfb29254`.
- Triage input: `20260512T011819-codex-source-label-high-confidence-subset-triage-v1`.
- Calibration input: `20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1`.
- Gate result: `source_label_qualifying_condition_candidate_v1=bull_sideways_candidates_no_acceptance`.
- Qualifying-condition candidate: `main_regime_v2_label in {Bull, Sideways} AND source_confidence >= 0.95`.

## Candidate Readback

| Label | Candidate | High-Conf Rows | Market Families | Date Range | Split Support | Conditional Wilson95 LCB |
|---|---|---:|---:|---|---|---|
| `Bull` | true | `10193` | `3` | `2000-01-21..2026-01-30` | `calibration=5460; heldout_market=795; heldout_time=2417; test=1521` | `0.999297; 0.995191; 0.998413; 0.997481` |
| `Sideways` | true | `8686` | `3` | `2000-01-21..2026-01-30` | `calibration=4929; heldout_market=1671; heldout_time=1388; test=698` | `0.999221; 0.997706; 0.997240; 0.994527` |
| `Bear` | false | `52` | `2` | `2000-01-05..2012-05-25` | `calibration=49; heldout_market=3; heldout_time=0; test=0` | `not evaluated` |
| `Crisis` | false | `276` | `1` | `2013-04-16..2026-03-20` | `calibration=130; heldout_market=0; heldout_time=80; test=66` | `not evaluated` |

## Boundary

This is not an acceptance packet. It shows that `Bull` and `Sideways` have enough high-confidence rows to justify a future condition-specific acceptance test if the board accepts `source_confidence >= 0.95` as an explicit qualifying condition. It does not override the failed `011056` full-row source-confidence gate, does not help `Bear` or `Crisis`, does not close R3/R5, and does not touch R6 owner-control blockers.

## Result

- Candidate labels: `Bull`, `Sideways`.
- Blocked labels: `Bear`, `Crisis`.
- Accepted labels now: `0/4`.
- Accepted rows added: `0`; new confidence gate: false; canonical merge allowed: false.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.
- Strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false. Thresholds relaxed: false. Raw data committed: false. External requests sent: false. Trade usable: false.

## Next

If condition-specific source-label gates are allowed, run a formal per-regime qualifying-condition acceptance packet for `Bull` and `Sideways`. `Bear` and `Crisis` need additional high-confidence source rows across missing splits and market families. R6 still needs owner controls or explicit `FLIP` approval before any downstream promotion chain.
