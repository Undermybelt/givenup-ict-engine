# GitHub Code Source Route Probe After 070315 v1

Run id: `20260512T070506+0800-codex-github-code-source-route-probe-after-070315-v1`

Gate result: `github_code_source_route_probe_after_070315_v1=no_github_code_required_root_unlock_no_downstream`

## Scope

Bounded GitHub code search after `070315` found no public exact source/control packet. This packet checks GitHub's code-search surface for the exact R5/R3 target filenames and schema terms. It does not mutate `/tmp` target roots, approve TSIE, run direct verifier, run canonical merge, run provider/AutoQuant promotion, run filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion, make a trade claim, or call `update_goal`.

## Probes

| Query | Exit | Result |
|---|---:|---|
| `stock_market_regimes_2026_extension.csv` | `0` | `0` GitHub code results. |
| `native_subhour_source_label_rows.csv` | `0` | `0` GitHub code results. |
| `MainRegimeV2 Crisis` | `0` | `0` GitHub code results. |
| `stock_market_regimes_2000_2026` | `0` | `0` GitHub code results. |

## Decision

No GitHub code result supplied a required source/control unlock.

- R6 owner/export root remains unproven by this packet.
- R5 post-`2026-01-30` recency root remains unproven by this packet.
- R3 verifier-native Crisis-capable `MainRegimeV2` native-subhour labels remain unproven by this packet.
- Accepted rows added: `0`.
- Valid required-root unlock: `false`.
- Source/control evidence acquired: `false`.
- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Artifacts

- GitHub code search outputs: `command-output/gh_code_*.json`
- GitHub code search stderr/exit files: `command-output/gh_code_*.stderr`, `command-output/gh_code_*.exit`
- JSON summary: `github-code-source-route-probe-after-070315-v1/github_code_source_route_probe_after_070315_v1.json`
- Assertions: `checks/github_code_source_route_probe_after_070315_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
