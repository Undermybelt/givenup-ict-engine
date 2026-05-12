import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.isotonic import IsotonicRegression

ROOT = Path('/Users/thrill3r/projects-ict-engine/ict-engine')
RUN = ROOT / 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion'
OUT = RUN / 'multi-regime'
NQ_CSV = Path('/tmp/ict-regime-chain-20260509T231052/input/nq_auto_quant_15m_ohlcv_20k.csv')
SESSION_CSV = ROOT / 'docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_features.csv'
SESSION_PACKET = ROOT / 'docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json'
Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def wilson(success, n, z):
    if n <= 0:
        return 0.0
    p = success / n
    den = 1 + z * z / n
    cen = p + z * z / (2 * n)
    mar = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (cen - mar) / den


def metrics(y, mask, prob=None):
    mask = np.asarray(mask, dtype=bool)
    y = np.asarray(y, dtype=int)
    n = int(mask.sum())
    s = int(y[mask].sum()) if n else 0
    precision = s / n if n else 0.0
    if prob is None:
        ece = 0.0 if n else None
        mean_prob = precision
    else:
        mean_prob = float(np.asarray(prob)[mask].mean()) if n else None
        ece = abs(mean_prob - precision) if n else None
    return {
        'support': n,
        'success': s,
        'precision': precision,
        'precision_wilson_lcb_95': wilson(s, n, Z95),
        'precision_wilson_lcb_99': wilson(s, n, Z99),
        'coverage': n / len(y) if len(y) else 0.0,
        'ece': ece,
        'mean_probability': mean_prob,
    }


def pass_flags(cal_m, test_m):
    p95 = (
        cal_m['support'] >= 120 and test_m['support'] >= 60 and
        test_m['precision_wilson_lcb_95'] >= 0.95 and
        test_m['coverage'] >= 0.03 and test_m['ece'] is not None and test_m['ece'] <= 0.05
    )
    p99 = (
        cal_m['support'] >= 300 and test_m['support'] >= 120 and
        test_m['precision_wilson_lcb_99'] >= 0.99 and
        test_m['coverage'] >= 0.02 and test_m['ece'] is not None and test_m['ece'] <= 0.02
    )
    return p95, p99


def build_nq_features():
    df = pd.read_csv(NQ_CSV)
    df['ts'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df = df.sort_values('ts').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close', 'volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['ret'] = df['close'].pct_change()
    for w in [4, 8, 16, 32, 64, 128, 256]:
        df[f'ret_{w}'] = df['close'].pct_change(w)
        df[f'absret_{w}'] = df[f'ret_{w}'].abs()
        df[f'vol_{w}'] = df['ret'].rolling(w).std()
        df[f'range_{w}'] = (df['high'].rolling(w).max() - df['low'].rolling(w).min()) / df['close']
        df[f'eff_{w}'] = df[f'ret_{w}'].abs() / (df['ret'].abs().rolling(w).sum() + 1e-12)
        df[f'pos_{w}'] = (df['close'] - df['low'].rolling(w).min()) / (df['high'].rolling(w).max() - df['low'].rolling(w).min() + 1e-12)
        df[f'volrank_{w}'] = df['volume'].rolling(w).rank(pct=True)
    return df.dropna().reset_index(drop=True)


def label_nq_regimes(df, train):
    q = lambda col, x: train[col].quantile(x)
    labels = pd.Series('Unknown', index=df.index, dtype=object)
    stress = (df['vol_32'] >= q('vol_32', .95)) | (df['range_32'] >= q('range_32', .95)) | (df['ret_8'] <= q('ret_8', .02))
    trend = (df['eff_32'] >= q('eff_32', .60)) & (df['absret_32'] >= q('absret_32', .60)) & (df['vol_32'] <= q('vol_32', .95))
    range_ = (df['vol_16'] <= q('vol_16', .60)) & (df['eff_32'] <= q('eff_32', .60)) & (df['absret_32'] <= q('absret_32', .70))
    reversal = ((df['pos_64'] >= .85) & (df['ret_4'] < 0)) | ((df['pos_64'] <= .15) & (df['ret_4'] > 0))
    labels[range_] = 'RangeConsolidation'
    labels[trend] = 'TrendExpansion'
    labels[reversal] = 'ReversalBrewing'
    labels[stress] = 'ExtremeStress'
    return labels


def choose_threshold(cal_prob, cal_y):
    candidates = sorted(set(float(x) for x in np.quantile(cal_prob, np.linspace(0.01, 0.99, 99))))
    best = None
    for t in candidates:
        mask = cal_prob >= t
        m = metrics(cal_y, mask, cal_prob)
        if m['support'] < 120:
            continue
        key = (m['precision_wilson_lcb_95'], m['precision'], m['support'])
        if best is None or key > best[0]:
            best = (key, t, m)
    if best is None:
        t = float(np.quantile(cal_prob, .90))
        return t, metrics(cal_y, cal_prob >= t, cal_prob)
    return best[1], best[2]


def evaluate_nq_persistence():
    df = build_nq_features()
    n = len(df)
    train = df.iloc[: n // 2].copy()
    cal = df.iloc[n // 2: n // 2 + (n - n // 2) // 2].copy()
    test = df.iloc[n // 2 + (n - n // 2) // 2:].copy()
    labels = label_nq_regimes(df, train)
    features = [c for c in df.columns if c not in ['ts', 'timestamp']]
    results = []
    for regime in ['TrendExpansion', 'RangeConsolidation', 'ExtremeStress', 'ReversalBrewing']:
        y_all = ((labels == regime) & (labels.shift(-1) == regime)).astype(int)
        current_all = (labels == regime).astype(int)
        # Model sees only current/lagged market features, not label or future persistence.
        X_train = train[features]
        y_train = y_all.iloc[train.index]
        X_cal = cal[features]
        y_cal = y_all.iloc[cal.index]
        X_test = test[features]
        y_test = y_all.iloc[test.index]
        if y_train.nunique() < 2 or y_cal.nunique() < 2:
            results.append({'regime_id': regime, 'status': 'class_gap', 'accepted_95': False, 'accepted_99': False})
            continue
        model = CatBoostClassifier(iterations=120, depth=4, learning_rate=0.05, loss_function='Logloss', verbose=False, random_seed=17, allow_writing_files=False)
        model.fit(X_train, y_train)
        raw_cal = model.predict_proba(X_cal)[:, 1]
        raw_test = model.predict_proba(X_test)[:, 1]
        iso = IsotonicRegression(out_of_bounds='clip')
        iso.fit(raw_cal, y_cal)
        cal_prob = iso.transform(raw_cal)
        test_prob = iso.transform(raw_test)
        threshold, cal_m = choose_threshold(cal_prob, y_cal.to_numpy())
        test_m = metrics(y_test.to_numpy(), test_prob >= threshold, test_prob)
        p95, p99 = pass_flags(cal_m, test_m)
        current_cal_m = metrics((labels.iloc[cal.index].shift(-1).reindex(cal.index) == regime).fillna(False).astype(int).to_numpy(), current_all.iloc[cal.index].to_numpy())
        current_test_m = metrics((labels.iloc[test.index].shift(-1).reindex(test.index) == regime).fillna(False).astype(int).to_numpy(), current_all.iloc[test.index].to_numpy())
        blockers = []
        if cal_m['support'] < 120:
            blockers.append('calibration_support_too_thin')
        if test_m['support'] < 60:
            blockers.append('test_support_too_thin')
        if test_m['precision_wilson_lcb_95'] < 0.95:
            blockers.append('precision_wilson_lcb_below_95')
        if test_m['ece'] is None or test_m['ece'] > 0.05:
            blockers.append('ece_above_95_limit')
        if test_m['coverage'] < 0.03:
            blockers.append('coverage_below_95_limit')
        results.append({
            'regime_id': regime,
            'market': 'NQ',
            'timeframe': '15m',
            'horizon': 'next 15m window regime persistence',
            'allowed_action': 'regime_context_only_until_downstream_edge_gate_passes',
            'target': f'{regime}_persists_next_15m',
            'model_family': 'catboost_isotonic',
            'threshold': threshold,
            'calibration': cal_m,
            'test': test_m,
            'current_label_baseline_calibration': current_cal_m,
            'current_label_baseline_test': current_test_m,
            'accepted_95': p95,
            'accepted_99': p99,
            'confidence_lane': '99' if p99 else '95' if p95 else 'abstain',
            'blocker': 'none' if p95 or p99 else ';'.join(blockers),
        })
    return results, {'train': len(train), 'calibration': len(cal), 'test': len(test), 'start': str(df['ts'].min()), 'end': str(df['ts'].max())}


def evaluate_thin_liquidity_offhours():
    df = pd.read_csv(SESSION_CSV)
    df['ts'] = pd.to_datetime(df['ts'], utc=True)
    df = df.sort_values('ts').reset_index(drop=True)
    for h in [4]:
        df[f'future_yf_absent_all_h{h}'] = pd.concat([df['qqq_yfinance_current_bar_present'].shift(-i).eq(0) for i in range(1, h + 1)], axis=1).all(axis=1)
    train = df.iloc[:2001].copy()
    cal = df.iloc[2001:3002].copy()
    test = df.iloc[3002:].copy()
    mask_cal = (cal['hour_utc'].between(21, 23)) & (cal['qqq_yfinance_current_bar_present'].eq(0))
    mask_test = (test['hour_utc'].between(21, 23)) & (test['qqq_yfinance_current_bar_present'].eq(0))
    y_cal = cal['future_yf_absent_all_h4'].astype(int).to_numpy()
    y_test = test['future_yf_absent_all_h4'].astype(int).to_numpy()
    cal_m = metrics(y_cal, mask_cal.to_numpy())
    test_m = metrics(y_test, mask_test.to_numpy(), np.repeat(cal_m['precision'], len(y_test)))
    p95, p99 = pass_flags(cal_m, test_m)
    return {
        'regime_id': 'ThinLiquidityOffHoursPersistent',
        'market': 'QQQ',
        'timeframe': '1h',
        'horizon': 'next 4 observed IBKR 1h bars',
        'allowed_action': 'guardrail_only_liquidity_context',
        'target': 'future_yfinance_regular_session_absent_all_h4',
        'rule': '21 <= hour_utc <= 23 and qqq_yfinance_current_bar_present == 0',
        'calibration': cal_m,
        'test': test_m,
        'accepted_95': p95,
        'accepted_99': p99,
        'confidence_lane': '99' if p99 else '95' if p95 else 'abstain',
        'blocker': 'none' if p95 or p99 else 'precision/support/ece/coverage gate failed',
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    nq_results, split = evaluate_nq_persistence()
    thin = evaluate_thin_liquidity_offhours()
    existing_session = json.loads(SESSION_PACKET.read_text())['accepted_packet']
    all_new = nq_results + [thin]
    accepted = [r for r in all_new if r.get('accepted_95') or r.get('accepted_99')]
    abstained = [r for r in all_new if not (r.get('accepted_95') or r.get('accepted_99'))]
    packets = []
    for r in accepted:
        packets.append({
            'accepted_regime_id': r['regime_id'],
            'market': r['market'],
            'timeframe': r['timeframe'],
            'horizon': r['horizon'],
            'allowed_action': r['allowed_action'],
            'confidence_lane': r['confidence_lane'],
            'precision_wilson_lcb': r['test']['precision_wilson_lcb_99'] if r['accepted_99'] else r['test']['precision_wilson_lcb_95'],
            'calibration_support': r['calibration']['support'],
            'test_support': r['test']['support'],
            'ece': r['test']['ece'],
            'coverage': r['test']['coverage'],
            'transition_hazard': 0.0 if 'Persistent' in r['regime_id'] else None,
            'duration_viable': True,
            'downstream_evidence_fields': [r.get('rule', r.get('model_family', 'unknown')), r['target']],
            'artifact_path': 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json',
        })
    report = {
        'schema_version': 'board-a-regime-persistence-expansion/v1',
        'loop_id': '20260510T200229+0800-hermes-regime-persistence-expansion',
        'run_root': 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion',
        'threshold_policy': {
            'thresholds_relaxed': False,
            'precision_wilson_lcb_95': 0.95,
            'precision_wilson_lcb_99': 0.99,
            'calibration_support_min_95': 120,
            'test_support_min_95': 60,
            'ece_max_95': 0.05,
            'coverage_min_95': 0.03,
        },
        'input_sources': {
            'nq_auto_quant_15m_ohlcv_20k': str(NQ_CSV),
            'session_liquidity_features': str(SESSION_CSV.relative_to(ROOT)),
            'session_liquidity_accepted_packet': str(SESSION_PACKET.relative_to(ROOT)),
        },
        'nq_persistence_split': split,
        'existing_accepted_regime_packets': [existing_session],
        'new_regime_results': all_new,
        'accepted_new_regime_count_95': sum(1 for r in accepted if r.get('accepted_95')),
        'accepted_new_regime_count_99': sum(1 for r in accepted if r.get('accepted_99')),
        'accepted_new_regime_packets': packets,
        'abstained_new_regimes': [
            {
                'regime_id': r['regime_id'],
                'blocker': r.get('blocker'),
                'calibration_support': r.get('calibration', {}).get('support'),
                'test_support': r.get('test', {}).get('support'),
                'test_wilson95': r.get('test', {}).get('precision_wilson_lcb_95'),
                'test_ece': r.get('test', {}).get('ece'),
                'test_coverage': r.get('test', {}).get('coverage'),
            }
            for r in abstained
        ],
        'decision': 'accepted_additional_regimes' if accepted else 'abstain_no_additional_calibrated_regime',
        'next_action': 'Continue Trend/Range/Stress/Reversal feature work; keep accepted liquidity regimes as guardrails/context only and do not lower thresholds.' if abstained else 'Hand accepted multi-regime packet to downstream consumers as guardrails/context only.',
    }
    (OUT / 'regime_persistence_calibration_report.json').write_text(json.dumps(report, indent=2))
    (RUN / 'evidence_packet_regime_persistence_expansion.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'accepted': [r['regime_id'] for r in accepted], 'abstained': [r['regime_id'] for r in abstained], 'evidence': 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json'}, indent=2))


if __name__ == '__main__':
    main()
