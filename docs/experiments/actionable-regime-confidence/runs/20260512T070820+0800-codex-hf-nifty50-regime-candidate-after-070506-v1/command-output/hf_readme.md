---
license: mit
task_categories:
- tabular-classification
- time-series-forecasting
tags:
- finance
- trading
- market-data
- nifty50
- india
- technical-indicators
pretty_name: NIFTY 50 Market Regime Dataset
size_categories:
- n<1K
---

# 📊 NIFTY 50 Market Regime Dataset

Dataset for training machine learning models to predict market regimes (RISK_ON/RISK_OFF) in Indian financial markets.

## 📋 Dataset Description

This dataset contains technical indicators and corresponding market regime labels for NIFTY 50, used to train binary classification models for regime prediction.

### Market Regimes

- **RISK_ON (1)**: Favorable market conditions - lower volatility, bullish momentum
- **RISK_OFF (0)**: Cautious conditions - higher volatility, defensive positioning

## 📊 Features

| Feature | Type | Description | Range |
|---------|------|-------------|-------|
| **india_vix** | float | India VIX volatility index | 0-100+ |
| **rsi_14** | float | 14-day Relative Strength Index | 0-100 |
| **ma_50** | float | 50-day moving average | > 0 |
| **ma_200** | float | 200-day moving average | > 0 |
| **regime** | int | Target label (0=RISK_OFF, 1=RISK_ON) | 0 or 1 |

### Feature Descriptions

1. **India VIX**: Measures expected volatility in NIFTY 50
   - Low values (< 15): Low fear, potentially RISK_ON
   - High values (> 25): High fear, potentially RISK_OFF

2. **RSI-14**: Momentum indicator
   - < 30: Oversold (potentially bullish)
   - > 70: Overbought (potentially bearish)
   - 40-60: Neutral

3. **MA-50**: Short-term trend indicator
4. **MA-200**: Long-term trend indicator

## 📈 Statistics

Load the dataset to see:
- Total samples
- Class distribution (RISK_ON vs RISK_OFF)
- Feature correlations
- Summary statistics

## 💻 Usage

### Load with Pandas

```python
import pandas as pd

# Load from local file
df = pd.read_csv("market_regime_data_nifty50.csv")

# View first few rows
print(df.head())

# Check class distribution
print(df['regime'].value_counts())
```

### Load from Hugging Face

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("AAdevloper/nifty50-market-regime")

# Convert to pandas
df = dataset['train'].to_pandas()
```

### Example Training Code

```python
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Prepare data
X = df[['india_vix', 'rsi_14', 'ma_50', 'ma_200']]
y = df['regime']

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train
model = XGBClassifier(max_depth=6, learning_rate=0.1, n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
score = model.score(X_test, y_test)
print(f"Accuracy: {score:.2%}")
```

## 🎯 Use Cases

1. **Market Regime Classification**: Train models to predict current regime
2. **Trading Strategy Development**: Use regime predictions for position sizing
3. **Risk Management**: Adjust portfolio based on predicted regime
4. **Feature Engineering Research**: Experiment with technical indicators
5. **MLOps Pipeline Development**: Practice model deployment and monitoring

## 🔧 Data Collection

The dataset includes:
- Historical technical indicators for NIFTY 50
- Calculated from OHLCV (Open, High, Low, Close, Volume) data
- Regime labels based on market behavior patterns

## 📊 Data Quality

- ✅ No missing values
- ✅ Features normalized/scaled appropriately
- ✅ Balanced class distribution (or document imbalance)
- ✅ No data leakage in feature engineering
- ✅ Temporally consistent

## 🏗️ Related Projects

This dataset is part of a complete MLOps pipeline:

- **Model**: [market-regime-classifier](https://huggingface.co/AAdevloper/market-regime-classifier)
- **Live Demo**: [MLOps Finance Pipeline Space](https://huggingface.co/spaces/AAdevloper/mlops-finance-pipeline)
- **Source Code**: [GitHub Repository](https://github.com/AAdevloper/mlops-finance-pipeline)

## 📄 Citation

If you use this dataset, please cite:

```bibtex
@misc{nifty50_market_regime,
  author = {AAdevloper},
  title = {NIFTY 50 Market Regime Dataset},
  year = {2025},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/datasets/AAdevloper/nifty50-market-regime}}
}
```

## 📄 License

MIT License - Free to use for research and commercial applications

---

**Part of the MLOps Finance Pipeline project** 🚀

For questions or improvements, visit the [GitHub repository](https://github.com/AAdevloper/mlops-finance-pipeline)
