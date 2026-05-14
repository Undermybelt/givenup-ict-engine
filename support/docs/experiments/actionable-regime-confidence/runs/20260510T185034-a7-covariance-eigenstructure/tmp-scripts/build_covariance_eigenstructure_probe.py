from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

ROOT = Path('/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260510T185034-a7-covariance-eigenstructure')
OUT_DIR = ROOT / 'covariance-eigenstructure'
QQQ_YF = Path('/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/yf_QQQ_1h_20240601_20260509.csv')
QQQ_IBKR = Path('/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/ibkr_QQQ_1h.csv')
NQ = Path('/tmp/ict-regime-chain-20260509T231052/input/nq_auto_quant_15m_ohlcv_20k.csv')
AUX = Path('/tmp/ict-regime-chain-20260509T231052/provider-probes/provider_auxiliary_evidence_20k.csv')
FEATURES = OUT_DIR / 'covariance_eigenstructure_features.csv'
REPORT = OUT_DIR / 'covariance_eigenstructure_calibration_report.json'


def wilson_lower(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = success / total
    denom = 1.0 + z * z / total
    centre = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def ece(scores: np.ndarray, labels: np.ndarray, mask: np.ndarray) -> float:
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return 0.0
    s = scores[idx]
    y = labels[idx].astype(float)
    bins = np.linspace(0.0, 1.0, 11)
    total = len(idx)
    out = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        b = (s >= lo) & (s <= hi if hi == 1.0 else s < hi)
        if not b.any():
            continue
        out += (b.sum() / total) * abs(float(s[b].mean()) - float(y[b].mean()))
    return float(out)


def load_qqq_yf() -> pd.DataFrame:
    df = pd.read_csv(QQQ_YF)
    df['ts'] = pd.to_datetime(df['date'], utc=True).dt.floor('h')
    return df[['ts', 'open', 'high', 'low', 'close', 'volume']].rename(columns={c: f'qqq_yf_{c}' for c in ['open', 'high', 'low', 'close', 'volume']})


def load_qqq_ibkr() -> pd.DataFrame:
    df = pd.read_csv(QQQ_IBKR)
    df['ts'] = pd.to_datetime(df['ts'], utc=True).dt.floor('h')
    return df[['ts', 'open', 'high', 'low', 'close', 'volume', 'count']].rename(columns={c: f'qqq_ibkr_{c}' for c in ['open', 'high', 'low', 'close', 'volume', 'count']})


def load_nq_1h() -> pd.DataFrame:
    df = pd.read_csv(NQ)
    df['ts'] = pd.to_datetime(df['timestamp'].astype('int64'), unit='ms', utc=True).dt.floor('h')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    agg = df.groupby('ts', as_index=False).agg(
        nq_open=('open', 'first'),
        nq_high=('high', 'max'),
        nq_low=('low', 'min'),
        nq_close=('close', 'last'),
        nq_volume=('volume', 'sum'),
        nq_15m_count=('close', 'count'),
    )
    return agg


def load_aux_1h() -> pd.DataFrame:
    aux = pd.read_csv(AUX)
    aux['ts'] = pd.to_datetime(aux['timestamp'].astype('int64'), unit='ms', utc=True).dt.floor('h')
    for col in aux.columns:
        if col not in {'timestamp', 'ts'}:
            aux[col] = pd.to_numeric(aux[col], errors='coerce')
    return aux.groupby('ts', as_index=False).last()


def pct_rank(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=max(20, window // 3)).rank(pct=True)


def build_frame() -> pd.DataFrame:
    df = load_nq_1h().merge(load_qqq_yf(), on='ts', how='left').merge(load_qqq_ibkr(), on='ts', how='left').merge(load_aux_1h(), on='ts', how='left')
    df = df.sort_values('ts').reset_index(drop=True)
    for col in df.columns:
        if col != 'ts':
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['ret_nq'] = np.log(df['nq_close']).diff()
    df['ret_qqq_yf'] = np.log(df['qqq_yf_close']).diff()
    df['ret_qqq_ibkr'] = np.log(df['qqq_ibkr_close']).diff()
    df['ret_qqq_avg'] = df[['ret_qqq_yf', 'ret_qqq_ibkr']].mean(axis=1)
    df['provider_return_disagreement'] = (df['ret_qqq_yf'] - df['ret_qqq_ibkr']).abs()
    returns = ['ret_nq', 'ret_qqq_yf', 'ret_qqq_ibkr']
    for window in [16, 32, 64, 128]:
        cov_rows: list[dict[str, float]] = []
        arr = df[returns].to_numpy(dtype=float)
        for i in range(len(df)):
            start = max(0, i - window + 1)
            sample = arr[start:i + 1]
            sample = sample[np.isfinite(sample).all(axis=1)]
            row: dict[str, float] = {}
            if len(sample) < max(8, window // 3):
                cov_rows.append(row)
                continue
            cov = np.cov(sample, rowvar=False)
            corr = np.corrcoef(sample, rowvar=False)
            eigvals = np.linalg.eigvalsh(corr)
            eigvals = np.sort(np.maximum(eigvals, 0.0))[::-1]
            total = float(eigvals.sum()) or 1.0
            row[f'eigen_top_share_{window}'] = float(eigvals[0] / total)
            row[f'eigen_second_share_{window}'] = float(eigvals[1] / total) if len(eigvals) > 1 else 0.0
            row[f'eigen_ratio_1_2_{window}'] = float(eigvals[0] / max(eigvals[1], 1e-12)) if len(eigvals) > 1 else 0.0
            row[f'corr_nq_qqq_yf_{window}'] = float(corr[0, 1])
            row[f'corr_nq_qqq_ibkr_{window}'] = float(corr[0, 2])
            row[f'corr_qqq_yf_ibkr_{window}'] = float(corr[1, 2])
            row[f'realized_vol_nq_{window}'] = float(np.sqrt(max(cov[0, 0], 0.0)))
            row[f'realized_vol_qqq_yf_{window}'] = float(np.sqrt(max(cov[1, 1], 0.0)))
            row[f'realized_vol_qqq_ibkr_{window}'] = float(np.sqrt(max(cov[2, 2], 0.0)))
            cov_rows.append(row)
        cov_df = pd.DataFrame(cov_rows)
        expected_cols = [
            f'eigen_top_share_{window}',
            f'eigen_second_share_{window}',
            f'eigen_ratio_1_2_{window}',
            f'corr_nq_qqq_yf_{window}',
            f'corr_nq_qqq_ibkr_{window}',
            f'corr_qqq_yf_ibkr_{window}',
            f'realized_vol_nq_{window}',
            f'realized_vol_qqq_yf_{window}',
            f'realized_vol_qqq_ibkr_{window}',
        ]
        for col in expected_cols:
            df[col] = cov_df[col] if col in cov_df.columns else np.nan
        df[f'eigen_top_share_pct_rank_{window}'] = pct_rank(df[f'eigen_top_share_{window}'], 256)
        df[f'realized_vol_nq_pct_rank_{window}'] = pct_rank(df[f'realized_vol_nq_{window}'], 256)
        df[f'provider_disagreement_pct_rank_{window}'] = pct_rank(df['provider_return_disagreement'], 256)
    df['future_ret_nq_h8'] = df['nq_close'].shift(-8) / df['nq_close'] - 1.0
    df['future_absret_nq_h8'] = df['future_ret_nq_h8'].abs()
    future_high = pd.concat([df['nq_high'].shift(-i) for i in range(1, 9)], axis=1).max(axis=1)
    future_low = pd.concat([df['nq_low'].shift(-i) for i in range(1, 9)], axis=1).min(axis=1)
    df['future_max_down_h8'] = future_low / df['nq_close'] - 1.0
    df['future_max_up_h8'] = future_high / df['nq_close'] - 1.0
    stress_threshold = df['future_absret_nq_h8'].iloc[: max(1, len(df)//2)].quantile(0.90)
    reversal_threshold = df['future_absret_nq_h8'].iloc[: max(1, len(df)//2)].quantile(0.65)
    df['target_extreme_stress_h8'] = ((df['future_absret_nq_h8'] >= stress_threshold) | (df['future_max_down_h8'] <= -stress_threshold)).astype(int)
    df['target_reversal_brewing_h8'] = ((df['provider_return_disagreement'] > df['provider_return_disagreement'].rolling(256, min_periods=64).quantile(0.80)) & (df['future_ret_nq_h8'].abs() >= reversal_threshold)).astype(int)
    df.loc[df['future_ret_nq_h8'].isna(), ['target_extreme_stress_h8', 'target_reversal_brewing_h8']] = np.nan
    return df


def candidate_thresholds(scores: np.ndarray) -> list[float]:
    finite = scores[np.isfinite(scores)]
    if finite.size == 0:
        return []
    return sorted(set(float(x) for x in np.quantile(finite, np.linspace(0.0, 1.0, 501))), reverse=True)


def run_target(df: pd.DataFrame, features: list[str], target: str) -> dict[str, Any]:
    valid = df[target].notna().to_numpy(dtype=bool)
    valid_idx = np.flatnonzero(valid)
    n = len(valid_idx)
    train_idx = valid_idx[: n // 2]
    cal_idx = valid_idx[n // 2 : (n * 3) // 4]
    test_idx = valid_idx[(n * 3) // 4 :]
    y = df[target].fillna(0).astype(int).to_numpy()
    report: dict[str, Any] = {
        'target': target,
        'positive': int(y[valid_idx].sum()),
        'negative': int(len(valid_idx) - y[valid_idx].sum()),
        'split': {'train': len(train_idx), 'calibration': len(cal_idx), 'test': len(test_idx)},
    }
    if len(set(y[train_idx].tolist())) < 2:
        report.update({'status': 'skipped_single_class_train', 'accepted_95_rules': 0, 'accepted_99_rules': 0, 'selected_rule': None})
        return report
    model = CatBoostClassifier(iterations=220, depth=4, learning_rate=0.045, loss_function='Logloss', verbose=False, random_seed=707, allow_writing_files=False, thread_count=1, auto_class_weights='Balanced')
    x = df[features].replace([np.inf, -np.inf], np.nan).fillna(-999.0)
    model.fit(x.iloc[train_idx], y[train_idx])
    scores = model.predict_proba(x)[:, 1]
    accepted95 = []
    accepted99 = []
    rules = []
    for threshold in candidate_thresholds(scores[cal_idx]):
        cal_mask = scores[cal_idx] >= threshold
        test_mask = scores[test_idx] >= threshold
        cal_n = int(cal_mask.sum())
        test_n = int(test_mask.sum())
        if cal_n < 120 or test_n < 60:
            continue
        cal_s = int(y[cal_idx][cal_mask].sum())
        test_s = int(y[test_idx][test_mask].sum())
        rule = {
            'threshold': threshold,
            'calibration_support': cal_n,
            'calibration_success': cal_s,
            'calibration_precision': cal_s / cal_n,
            'calibration_wilson_lcb_95': wilson_lower(cal_s, cal_n),
            'test_support': test_n,
            'test_success': test_s,
            'test_precision': test_s / test_n,
            'precision_wilson_lcb_95': wilson_lower(test_s, test_n),
            'precision_wilson_lcb_99': wilson_lower(test_s, test_n, z=2.5758293035489004),
            'ece': ece(scores, y, np.isin(np.arange(len(y)), test_idx) & (scores >= threshold)),
            'coverage': test_n / len(test_idx) if len(test_idx) else 0.0,
        }
        rule['passes_95'] = rule['calibration_wilson_lcb_95'] >= 0.95 and rule['precision_wilson_lcb_95'] >= 0.95 and rule['ece'] <= 0.05 and rule['coverage'] >= 0.03
        rule['passes_99'] = rule['calibration_support'] >= 300 and rule['test_support'] >= 120 and rule['precision_wilson_lcb_99'] >= 0.99 and rule['ece'] <= 0.02 and rule['coverage'] >= 0.02
        rules.append(rule)
        if rule['passes_95']:
            accepted95.append(rule)
        if rule['passes_99']:
            accepted99.append(rule)
    rules.sort(key=lambda r: (r['passes_95'], r['precision_wilson_lcb_95'], r['test_precision'], r['test_support']), reverse=True)
    top = sorted(zip(features, model.get_feature_importance()), key=lambda item: item[1], reverse=True)[:20]
    report.update({
        'status': 'ran_catboost',
        'feature_count': len(features),
        'top_importances': [{'feature': name, 'importance': float(value)} for name, value in top],
        'admissible_rules': len(rules),
        'accepted_95_rules': len(accepted95),
        'accepted_99_rules': len(accepted99),
        'selected_rule': rules[0] if rules else None,
    })
    return report


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_frame()
    feature_cols = []
    blocked = {'future_ret_nq_h8', 'future_absret_nq_h8', 'future_max_down_h8', 'future_max_up_h8', 'target_extreme_stress_h8', 'target_reversal_brewing_h8'}
    for col in df.columns:
        if col == 'ts' or col in blocked:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].notna().any():
            feature_cols.append(col)
    df.to_csv(FEATURES, index=False)
    targets = {
        'target_extreme_stress_h8': run_target(df, feature_cols, 'target_extreme_stress_h8'),
        'target_reversal_brewing_h8': run_target(df, feature_cols, 'target_reversal_brewing_h8'),
    }
    accepted = sum(t['accepted_95_rules'] for t in targets.values())
    report = {
        'schema_version': 'board-a-a7-covariance-eigenstructure/v1',
        'rows': int(len(df)),
        'features_csv': str(FEATURES.relative_to(ROOT)),
        'input_sources': {
            'qqq_yfinance_1h': str(QQQ_YF),
            'qqq_ibkr_1h': str(QQQ_IBKR),
            'nq_auto_quant_15m_cache': str(NQ),
            'auxiliary_evidence_20k': str(AUX),
        },
        'feature_count': len(feature_cols),
        'covariance_features': [c for c in feature_cols if c.startswith(('eigen_', 'corr_', 'realized_vol_', 'provider_disagreement'))],
        'targets': targets,
        'accepted_95_rule_count': accepted,
        'accepted_99_rule_count': sum(t['accepted_99_rules'] for t in targets.values()),
        'decision': 'accepted_95_candidate' if accepted else 'abstain_no_calibrated_release_rule',
        'thresholds_relaxed': False,
    }
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(REPORT), 'rows': len(df), 'feature_count': len(feature_cols), 'accepted_95_rule_count': report['accepted_95_rule_count'], 'accepted_99_rule_count': report['accepted_99_rule_count'], 'decision': report['decision']}, indent=2))


if __name__ == '__main__':
    main()
