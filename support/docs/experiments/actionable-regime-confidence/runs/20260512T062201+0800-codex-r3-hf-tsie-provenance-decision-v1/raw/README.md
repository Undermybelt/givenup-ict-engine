---
license: mit
task_categories:
- tabular-classification
- time-series-forecasting
tags:
- finance
- trading
- Temporal Fusion Transformer
- time-series
- stock-market
- IDX
- TFT
---

TSIE: Temporal Signal Intelligence Engine — Market Regime Dataset (IDX)

📊 Overview

This dataset provides a multi-class market regime classification for Indonesian stock market (IDX), designed for time-series modeling using architectures such as Temporal Fusion Transformer (TFT).

The dataset includes:

- OHLCV price data
- Engineered technical indicators
- Temporal features
- Session-aware features (IDX trading hours)
- Multi-class regime labels based on rule-based signal logic

---

🎯 Task

Multi-class classification (7 classes)

Each timestep is labeled with a market regime:

Class| Label| Description
0| STRONG SELL| High-confidence bearish breakdown
1| WEAK SELL| Mild bearish movement
2| BEAR TRAP| False breakdown
3| FLAT / NOISE| Sideways / low volatility
4| BULL TRAP| False breakout
5| WEAK BUY| Mild bullish movement
6| STRONG BUY| High-confidence breakout

---

🧠 Feature Groups

🔹 Static Features

- "group_id" → stock identifier

🔹 Time-Varying Known Features

(available in future)

- "time_idx"
- "hour", "day_of_week", "day_of_month"
- "hour_sin", "hour_cos"
- "dow_sin", "dow_cos"
- "session" (IDX session)
- "is_session_1", "is_session_2"
- "is_lunch_break"
- "is_opening", "is_closing"

🔹 Time-Varying Observed Features

(observed at each timestep)

- OHLCV: "open", "high", "low", "volume"
- "log_return"
- "roc_5"
- "volume_ratio"
- "rsi"
- "bb_position"

🔹 Observed Categoricals

- "signal_numeric" → (-1, 0, 1)

---

🏦 Market Session Encoding (IDX)

The dataset includes trading session awareness:

- Session 1: 09:00–11:59
- Lunch Break: 12:00–13:59
- Session 2: 14:00–15:59

Additional flags:

- Opening period
- Closing period

---

⚙️ Labeling Methodology

Labels are generated using:

- Rule-based signal classification
- Price action + volatility + RSI + volume logic
- Inspired by trading heuristics and regime detection

This is not future-leakage-based labeling.

---

📦 Dataset Structure

Columns:

- "time"
- "group_id"
- "time_idx"
- features...
- "target" (main label)
- "is_train" (train/validation split)

---

🚀 Usage

Load dataset

import pandas as pd

df = pd.read_parquet("tft_dataset_ready.parquet")

Example: TFT (PyTorch Forecasting)

from pytorch_forecasting import TimeSeriesDataSet

dataset = TimeSeriesDataSet(
    df,
    time_idx="time_idx",
    target="target",
    group_ids=["group_id"],
)

---

⚠️ Notes

- Dataset is highly imbalanced (dominant "FLAT / NOISE" class)
- Recommended:
  - class weighting
  - focal loss
  - oversampling minority classes

---

📈 Intended Use

- Market regime classification
- Algorithmic trading research
- Time-series deep learning (TFT, LSTM, Transformer)

---