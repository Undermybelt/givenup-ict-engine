# Local Pine Regime Detector Audit

Run id: `20260511T085659+0800-codex-local-pine-regime-detector-audit`

## Candidate

- Path: `/Users/thrill3r/Downloads/ictscripts/ICT Market Regime Detector`
- SHA-256: `36422875795844de1b29e8cc40d154153de628d81c50f30aabbfdd211e1b6bb7`
- Lines: `999`
- Type: `TradingView Pine Script indicator`

## Result

- Decision: `rejected_proxy_only_no_source_label_attachment`.
- Gate result: `blocked_local_pine_indicator_is_proxy_logic_not_source_labels`.
- Accepted MainRegimeV2 root-label slots added: `0`.
- Accepted direct `Manipulation` label sources added: `0`.
- Runtime code changed: false. Thresholds relaxed: false. Raw source committed: false. Trade usable: false.

## Why It Does Not Close The Gate

The script generates regime names inside classifyRegime() from chart OHLCV/volume, ADX, EMA, RSI, ATR/range, wick, and same-symbol 4h DMI features. It does not contain an independent label table, exact-underlying MainRegimeV2 root labels, or direct Manipulation positive/negative event windows.

The observed labels are generated outputs of a local decision tree, not source labels:

| Observed output labels | Source class |
|---|---|
| `['ACCUMULATION', 'CHOPPY', 'CONSOLIDATION', 'DISTRIBUTION', 'EXPANSION', 'REVERSAL', 'STRONG TREND', 'WEAK TREND']` | `ohlcv_derived_pine_indicator_proxy_logic` |

Decision-tree inputs observed:

- volatility ratio from close-to-close returns
- DMI/ADX from high/low/close
- EMA20/EMA50 structure from close
- RSI divergence from high/low/close
- range high/low/position from high/low/close
- volume spike plus candle body/wick heuristics
- same-symbol 4h request.security DMI alignment

## Direct Label Checks

- Independent MainRegimeV2 root-label panel: `False`.
- Exact-underlying source labels: `False`.
- Direct Manipulation positive/negative windows: `False`.
- `request.*` calls found: `['security']`.

## Next Action

Acquire exact-underlying non-Kaggle root-label panels for the missing intraday/monthly/Kraken/missing-instrument slots or authenticated direct Manipulation rows.
