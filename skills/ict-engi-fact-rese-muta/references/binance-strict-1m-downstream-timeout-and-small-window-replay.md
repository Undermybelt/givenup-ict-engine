# Binance strict 1m downstream timeout lesson

Session: 2026-05-18

## Context
- Source branch: `RangeReversion -> CryptoVWAPDeviation -> obv_rsi_vwap_snapback_strict -> binance_vwapdev_obvrsi_1m_strict_iteration_v2`
- Source gate1 survivor: `SOLUSDT z250_obv25_rsi34 1m`
- Source result: `73 trades`, `win_rate=60.274%`, `gross_profit=3.42%`, `net_2bps_side=0.5%`

## Lesson
- A source branch can be gate1-positive and still fail downstream because `analyze` or the downstream replay path stalls on large retained-row windows.
- If a replay script times out on the full 1m matrix, try a smaller retained slice first to isolate whether the blocker is pure input volume or a structural branch failure.
- If the smaller slice also times out, classify it as a replay/runtime blocker, not as promotion evidence.
- Do not promote or lower gates just because the 1m source row survived cost.

## Evidence paths
- Source summary: `.../runs/20260518T125934+0800-codex-binance-vwapdev-obvrsi-1m-strict-iteration-v2/summaries/terminal_decision_summary.md`
- Downstream summary: `.../runs/20260518T125934+0800-codex-binance-vwapdev-obvrsi-1m-strict-iteration-v2/downstream-strict-1m-20260518T182157+0800/summaries/terminal_decision_summary.md`
- Small-window retry attempt: `/tmp/run_binance_vwapdev_obvrsi_1m_strict_iteration_v2_small_downstream.py`

## Use when
- A strict 1m gate1 survivor is ready for downstream but the full replay path times out.
- You need a quick triage: full-window timeout vs. structural fail-closed.
