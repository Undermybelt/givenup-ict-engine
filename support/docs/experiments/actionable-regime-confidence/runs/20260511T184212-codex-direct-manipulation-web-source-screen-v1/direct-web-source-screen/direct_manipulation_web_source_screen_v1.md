# Direct Manipulation Web Source Screen v1

Run ID: `20260511T184212+0800-codex-direct-manipulation-web-source-screen-v1`

This is a supplemental public web/GitHub/arXiv screen for direct Manipulation row sources. It does not download raw rows and does not alter the Current Cursor.

## Decision

`direct_manipulation_web_source_screen_v1=no_ready_real_matched_negative_source`

- Candidates screened: `5`.
- Ready source candidates: `0`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`; `update_goal=false`.

## Candidate Disposition

- `kpetridis24/lobsim`: `blocked_simulator_no_source_rows`.
  Source: https://github.com/kpetridis24/lobsim
  Reason: Repository provides simulated LOB machinery/sample data, not real direct manipulation positives with matched normal controls.
- `Spoofing the Limit Order Book: A Strategic Agent-Based Analysis`: `blocked_paper_simulation_no_row_export`.
  Source: https://www.mdpi.com/2073-4336/12/2/46
  Reason: Useful model/background source; it describes an agent-based spoofing simulation, not a real row dataset with positives and matched normal controls.
- `arXiv 2504.15908 spoofability`: `blocked_method_only_no_public_matched_rows`.
  Source: https://ideas.repec.org/p/arx/papers/2504.15908.html
  Reason: Uses Level-3 data and computes spoofability probabilities, but the public record is a method/paper, not an export with accepted positives plus matched normal controls.
- `marvingozo/polymarket-tick-level-orderbook-dataset`: `blocked_raw_lob_no_direct_labels`.
  Source: https://www.kaggle.com/datasets/marvingozo/polymarket-tick-level-orderbook-dataset
  Reason: Tick/orderbook rows may support future feature work, but no source-owned direct Manipulation labels or matched control groups were exposed in the public dataset page.
- `solsticestudioai/dark-pool-pack`: `blocked_synthetic_not_source_owned_market_rows`.
  Source: https://huggingface.co/datasets/solsticestudioai/dark-pool-pack
  Reason: Dataset has fraudulent/benign spoofing-like sequences, but the card states it is 100% synthetic and contains no real transactions or order books.

## Why It Still Blocks

Board A strict direct `Manipulation` still needs real row-level positives, matched normal controls, and provenance. Simulators, papers, raw LOB feeds without direct labels, model-computed probabilities, and synthetic fraud packs can be useful for design or tests, but they cannot satisfy the strict confidence gate.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184212-codex-direct-manipulation-web-source-screen-v1/direct-web-source-screen/direct_manipulation_web_source_screen_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T184212-codex-direct-manipulation-web-source-screen-v1/direct-web-source-screen/direct_manipulation_web_source_screen_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T184212-codex-direct-manipulation-web-source-screen-v1/checks/direct_manipulation_web_source_screen_v1_assertions.out`
