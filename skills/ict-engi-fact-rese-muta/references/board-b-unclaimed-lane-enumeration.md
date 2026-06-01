# Board B unclaimed-lane enumeration before factor training

Session pattern: user asked to continue regime-rooted profit-factor training after many Board B/YF/IBKR lanes had already been claimed or terminalized.

Reusable workflow:

1. Read the active Board B/current-state doc only enough to confirm the current contract and claim directory.
2. Inspect `/tmp/ict-engine-agent-claims/board-b-factor-refinement/` before launching a new run.
3. If obvious market/sector lanes collide, enumerate existing runner scripts and compare each `FACTOR_ID` against both claim text and run-root names.
4. Prefer a truly unclaimed full-ladder lane with real provider coverage over rerunning or summarizing a sibling lane.
5. Create a short external claim under `/tmp/ict-engine-agent-claims/board-b-factor-refinement/` before launching the runner.
6. Run the long factor script in background with notify-on-complete; poll the generated run root for `checks/*.exit`, then verify `summaries/terminal_decision_summary.md` and `checks/terminal_metrics.json`.
7. Append terminal fields back to the external claim: `run_root`, `terminal_summary`, `terminal_metrics`, `rank_rows`, `positive_origin_1m`, `positive_higher_timeframes`, `branch_fields_preserved`, `downstream_allowed`, `promotion_allowed`, and `trade_usable`.

Python enumeration sketch:

```python
import glob, pathlib, re
repo = pathlib.Path('<ict-engine-repo>')
claims = '\n'.join(
    pathlib.Path(p).read_text(errors='ignore')
    for p in glob.glob('/tmp/ict-engine-agent-claims/board-b-factor-refinement/*')
    if pathlib.Path(p).is_file()
)
runs = '\n'.join(p.name for p in (repo / 'support/docs/experiments/actionable-regime-confidence/runs').glob('*'))
patterns = [
    'support/docs/experiments/actionable-regime-confidence/scripts/run_yf_*_1m_mtf_1d_v1.py',
    'support/docs/experiments/actionable-regime-confidence/scripts/run_kraken_*full_ladder_v1.py',
    'support/docs/experiments/actionable-regime-confidence/scripts/run_binance_*full_ladder_v1.py',
]
for pattern in patterns:
    for script in repo.glob(pattern):
        text = script.read_text(errors='ignore')
        match = re.search(r'(?:runner\.)?FACTOR_ID\s*=\s*"([^"]+)"', text)
        factor_id = match.group(1) if match else script.stem.removeprefix('run_')
        if factor_id not in claims and factor_id not in runs:
            print(factor_id, script)
```

Decision lesson:

- A full provider/AQ run with branch fields preserved still stops at Gate 1 if `positive_origin_1m=[]` and the only positives are sparse higher-timeframe rows.
- Do not run Pre-Bayes/BBN/CatBoost/execution tree after that result.
- The next candidate should change the 1m entry family, not add an overlay to a zero-trade origin.
