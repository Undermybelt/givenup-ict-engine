---
license: cc-by-4.0
tags:
- datasets
- finance
- timeseries
- tabular
- classification
- market-regime
- technical-indicators
- bitcoin
pretty_name: Multi‑Timeframe Market Regimes (HMM‑6) (BTCUSD)
---

# Multi‑Timeframe Market Regimes (HMM‑6)

## Dataset Summary

This dataset provides labeled crypto market regimes derived from multi-timeframe (5m, 15m) OHLCV data and technical indicators.
Market regimes are inferred using a 6-state Hidden Markov Model (HMM).

The dataset is suitable for market regime detection, regime-aware modeling, and sequence modeling baselines (LSTM / Transformers).

No future leakage: all indicators are computed using information available up to the timestamp, and labels correspond to the inferred regime at that timestamp only.
## Source & Licensing
* **Asset**: BTC (BTCUSD / BTCUSDT – specify exact symbol)
* **Exchange**: specify exchange (e.g., Binance)
* **Market**: spot or perpetual futures
* **Timezone**: UTC


## Files

```
.
├── README.md
└── data/
    ├── train.csv         # oldest part
    ├── validation.csv    # middle part
    └── test.csv          # most recent data
```

Optionally provide Parquet equivalents:

```
└── data/
    ├── train.parquet
    ├── validation.parquet
    └── test.parquet
```
All splits are chronological.
No shuffling is performed.

## Columns

### Core
- `timestamp` — UTC timestamp (ISO8601 or UNIX ms)

### OHLCV (contextual)
- `open_5m`, `high_5m`, `low_5m`, `close_5m`, `volume_5m`
- `open_15m`, `high_15m`, `low_15m`, `close_15m`, `volume_15m`

OHLCV columns are included for **context and visualization** and are **not required** for training the HMM.

---

### Technical Indicators (5m)
- `log_ret_1_5m`
- `ema_ratio_9_21_5m`
- `macd_hist_5m`
- `adx_5m`
- `atr_norm_5m`
- `bb_width_5m`
- `rsi_14_5m`
- `volume_zscore_50_5m`

### Technical Indicators (15m)
- `log_ret_1_15m`
- `ema_ratio_9_21_15m`
- `macd_hist_15m`
- `adx_15m`
- `atr_norm_15m`
- `bb_width_15m`
- `rsi_14_15m`
- `volume_zscore_50_15m`

---

## Targets

- `state` — integer HMM state label (0–5)
- `regime` — human-readable semantic label mapped from `state`

### Regime Semantics

| State | Regime |
|------:|--------|
| 0 | Choppy High-Vol |
| 1 | Range |
| 2 | Squeeze |
| 3 | Strong Trend |
| 4 | Volatility Spike |
| 5 | Weak Trend |

**Notes**
- `state` IDs are **model-dependent and arbitrary**
- `regime` labels are **post-hoc human interpretations**
- For modeling, use `state` as the target

---
## Columns

### Core
- `timestamp` — UTC timestamp (ISO8601 or UNIX ms)

### OHLCV (contextual)
- `open_5m`, `high_5m`, `low_5m`, `close_5m`, `volume_5m`
- `open_15m`, `high_15m`, `low_15m`, `close_15m`, `volume_15m`

OHLCV columns are included for **context and visualization** and are **not required** for training the HMM.

---

### Technical Indicators (5m)
- `log_ret_1_5m`
- `ema_ratio_9_21_5m`
- `macd_hist_5m`
- `adx_5m`
- `atr_norm_5m`
- `bb_width_5m`
- `rsi_14_5m`
- `volume_zscore_50_5m`

### Technical Indicators (15m)
- `log_ret_1_15m`
- `ema_ratio_9_21_15m`
- `macd_hist_15m`
- `adx_15m`
- `atr_norm_15m`
- `bb_width_15m`
- `rsi_14_15m`
- `volume_zscore_50_15m`

---

## Targets

- `state` — integer HMM state label (0–5)
- `regime` — human-readable semantic label mapped from `state`

### Regime Semantics

| State | Regime |
|------:|--------|
| 0 | Choppy High-Vol |
| 1 | Range |
| 2 | Squeeze |
| 3 | Strong Trend |
| 4 | Volatility Spike |
| 5 | Weak Trend |

**Notes**
- `state` IDs are **model-dependent and arbitrary**
- `regime` labels are **post-hoc human interpretations**
- For modeling, use `state` as the target

---
## Splitting Protocol (Leak-Free)

1. Sort data by `timestamp` (ascending)
2. Split into **contiguous** blocks:
   - train → validation → test
3. Do **not** shuffle
4. Sliding windows for sequence models must be constructed **within each split only**

---

## How to Load

```python
from datasets import load_dataset

ds = load_dataset("akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD")
train = ds["train"]
valid = ds["validation"]
test = ds["test"]
```

## Known Limitations

* Technical‑indicator engineered features; not raw trades.
* Single asset (if BTCUSDT only) may not generalize to alts/FX.
* Regimes are **model‑dependent**; HMM re‑fits may shift boundaries.

## Changelog

* v1.0.0 — Initial release.
