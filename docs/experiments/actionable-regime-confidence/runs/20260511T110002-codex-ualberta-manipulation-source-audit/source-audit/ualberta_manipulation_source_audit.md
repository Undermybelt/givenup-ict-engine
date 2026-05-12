# UAlberta Manipulation Source Audit

Run ID: `20260511T110002+0800-codex-ualberta-manipulation-source-audit`

## Scope

This bounded audit checks whether newly surfaced Golmohammadi/Zaiane manipulation-anomaly materials can fill Board A's active `MainRegimeV2` missing-slot contract.

## Network Probe

- Dataset directory WAF challenge observed: `true`.
- No raw market CSV was committed to the repo.

## Candidate Decisions

| Source | Decision | Reason |
|---|---|---|
| `Golmohammadi-Zaiane DSAA2015 S&P outlier CSV package` | `rejected` | The paper/data framing is synthetic or artificial outlier injection for anomaly-detection benchmarking, not adjudicated timestamped manipulation positives with same-venue negatives and not MainRegimeV2 Bull/Bear/Sideways/Crisis label windows. |
| `Golmohammadi-Zaiane DSAA2014 SEC/Diaz manipulation case study` | `rejected` | Methodology/case-study provenance only; no materialized positive/negative manipulation rows, no exact provider/instrument/timeframe label windows for the Board A missing-slot matrix. |

## Result

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_ualberta_sources_synthetic_or_methodology_only_no_attachable_labels`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Do not spend another loop on synthetic/anomaly-benchmark sources. Continue this branch only if a public row-level ground-truth file for the SEC/Diaz manipulation cases is located.
