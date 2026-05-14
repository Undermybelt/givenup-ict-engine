# NIFTY Source Confidence Screen v1

- Decision: `nifty_source_confidence_screen_v1=partial_source_confidence_scored_no_acceptance`.
- Live intake rows observed: `248441`; live labels: `{'': 1, 'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899}`; live missing roots: `[]`.
- NIFTY subset labels scored: `['Bull', 'Crisis', 'Sideways']`; NIFTY missing roots: `['Bear']`.
- Source confidence threshold checked: `0.95`.
- High-confidence source rows counted: `1441`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Confidence Summaries

| Label | Source State | Rows | Rows >=0.95 | Share >=0.95 | Median | Mean | Max | Date Range |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `Bull` | `macro_state=Durable` | `1213` | `837` | `0.690025` | `0.991190` | `0.930209` | `0.999997` | `2012-02-02..2025-07-17` |
| `Sideways` | `fast_state=Calm` | `1231` | `328` | `0.266450` | `0.860260` | `0.816182` | `0.995873` | `2012-02-02..2026-02-03` |
| `Crisis` | `fast_state=Stress` | `991` | `276` | `0.278507` | `0.880530` | `0.827549` | `0.997706` | `2013-03-19..2026-03-20` |

## Interpretation

This scores source-provided posterior/confidence fields for the already-ingested NIFTY source-label subset. The live shared intake may include Bear rows from a concurrent US-panel extension, but this NIFTY-only screen does not create Bear rows and does not convert source posterior confidence into a Board A accepted confidence gate.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213820-codex-nifty-source-confidence-screen-v1/nifty-source-confidence-screen/nifty_source_confidence_screen_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213820-codex-nifty-source-confidence-screen-v1/nifty-source-confidence-screen/nifty_source_confidence_screen_v1.md`
- Counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213820-codex-nifty-source-confidence-screen-v1/nifty-source-confidence-screen/nifty_source_confidence_screen_v1_counts.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213820-codex-nifty-source-confidence-screen-v1/nifty-source-confidence-screen/nifty_source_confidence_screen_v1_gates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213820-codex-nifty-source-confidence-screen-v1/checks/nifty_source_confidence_screen_v1_assertions.out`
