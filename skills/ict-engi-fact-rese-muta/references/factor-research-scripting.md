Absorbed from skill: ict-engi-fact-rese-scrp

This reference stores the scripting, parsing, and orchestration patterns for ict-engine factor-research batch work.

Key contents preserved:
- correct top-level JSON extraction for nested stdout payloads
- state isolation rules for parameter comparison studies
- parallel phase / cluster execution patterns
- recovery parsing from archived run logs
- dead scoring weight diagnosis
- experiment refinement logic and plateau diagnosis
- PB/control-matrix rollout and wrapper UX lessons
- cross_market_smt paired-series bug patterns and safe guards

Original narrow scripting skill archived after consolidation.

--- PRESERVED HIGHLIGHTS ---

- Never use naive last-brace extraction on nested JSON output.
- Use isolated `state_dir` per candidate when comparing runs.
- Shared-state positive deltas can be fake due to cumulative promotion drift.
- Once scoring is fair and defaults still win, treat the problem as structural, not parametric.
- For IBKR -> Auto-Quant material, keep provider fetch windows separate from
  Freqtrade timeranges. IBKR accepts duration strings such as `7 D`, `1 M`, and
  `3 M`, but Freqtrade material must use `YYYYMMDD-YYYYMMDD` derived from the
  fetched CSV timestamps; passing the IBKR duration string as `timerange`
  fails with `ConfigurationError: Incorrect syntax for timerange`.
- When maximizing IBKR intraday windows, probe practical limits per timeframe
  before AQ dispatch. On the current local setup, `QQQ 1 min 1 M` returned an
  empty timeout, while `1 min 7 D`, `5 mins 1 M`, `15 mins 1 M`, `30 mins 3 M`,
  and `1 hour 3 M` completed; treat these as observed bounds, not universal
  provider guarantees.
- External papers, open-source strategies, and social strategy snippets are
  hypothesis inputs only. For Board B practical-profit work, turn them into
  rooted Auto-Quant material and re-run IBKR/AQ gates before assigning
  Pre-Bayes, BBN, CatBoost, or execution-tree eligibility.
- If Auto-Quant rank output collapses `provider_provenance` to a generic label
  such as `IBKR`, preserve timeframe/window in `unit_label`, `package_id`, and
  material notes, then derive gate readback from those fields rather than
  assuming provenance includes the full timeframe string.
- For 1m-base strategies with 5m/15m/30m/1h context vetoes, run or embed a
  cheap signal-density diagnostic before treating a zero-trade Auto-Quant result
  as a meaningful strategy verdict. Strict higher-timeframe context gates can
  remove every entry while provider, strategy compile, and AQ dispatch all pass.
