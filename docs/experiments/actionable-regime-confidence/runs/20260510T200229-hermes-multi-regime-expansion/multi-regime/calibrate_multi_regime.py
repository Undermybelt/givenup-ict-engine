import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path('/Users/thrill3r/projects-ict-engine/ict-engine')
RUN = ROOT / 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion'
OUT = RUN / 'multi-regime'
FEATURES = ROOT / 'docs/experiments/actionable-regime-confidence/runs/20260510T185034-a7-covariance-eigenstructure/covariance-eigenstructure/covariance_eigenstructure_features.csv'
SESSION_REPORT = ROOT / 'docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json'

Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def wilson_lcb(success, n, z):
    if n <= 0:
        return 0.0
    phat = success / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def ece_binary(prob, y, bins=10):
    prob = np.asarray(prob, dtype=float)
    y = np.asarray(y, dtype=int)
    if len(prob) == 0:
        return None
    edges = np.linspace(0, 1, bins + 1)
    total = len(prob)
    err = 0.0
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        if i == bins - 1:
            mask = (prob >= lo) & (prob <= hi)
        else:
            mask = (prob >= lo) & (prob < hi)
        if not mask.any():
            continue
        err += mask.mean() * abs(prob[mask].mean() - y[mask].mean())
    return float(err)


def split_chrono(df):
    n = len(df)
    train_end = n // 2
    cal_end = train_end + (n - train_end) // 2
    return df.iloc[:train_end].copy(), df.iloc[train_end:cal_end].copy(), df.iloc[cal_end:].copy()


def safe_num(df, col):
    return pd.to_numeric(df[col], errors='coerce')


def eval_rule(df, mask_col, target_col, prob_value=None):
    rows = df[[mask_col, target_col]].dropna()
    rows = rows[rows[mask_col].astype(bool)]
    support = int(len(rows))
    success = int(rows[target_col].sum()) if support else 0
    precision = success / support if support else 0.0
    prob = precision if prob_value is None else prob_value
    ece = abs(prob - precision) if support else None
    return {
        'support': support,
        'success': success,
        'precision': precision,
        'precision_wilson_lcb_95': wilson_lcb(success, support, Z95),
        'precision_wilson_lcb_99': wilson_lcb(success, support, Z99),
        'coverage': support / len(df) if len(df) else 0.0,
        'ece': ece,
        'mean_probability': prob,
    }


def passes(cal, test):
    p95 = (
        cal['support'] >= 120 and test['support'] >= 60 and
        test['precision_wilson_lcb_95'] >= 0.95 and
        test['coverage'] >= 0.03 and test['ece'] is not None and test['ece'] <= 0.05
    )
    p99 = (
        cal['support'] >= 300 and test['support'] >= 120 and
        test['precision_wilson_lcb_99'] >= 0.99 and
        test['coverage'] >= 0.02 and test['ece'] is not None and test['ece'] <= 0.02
    )
    return p95, p99


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(FEATURES)
    df['ts'] = pd.to_datetime(df['ts'], errors='coerce', utc=True)
    df = df.sort_values('ts').reset_index(drop=True)

    # Targets are execution-native regime events: action may be release_candidate_only or guardrail_only.
    df['future_ret_nq_h8'] = safe_num(df, 'future_ret_nq_h8')
    df['future_absret_nq_h8'] = safe_num(df, 'future_absret_nq_h8')
    df['future_max_down_h8'] = safe_num(df, 'future_max_down_h8')
    df['provider_return_disagreement'] = safe_num(df, 'provider_return_disagreement')
    df['realized_vol_nq_pct_rank_32'] = safe_num(df, 'realized_vol_nq_pct_rank_32')
    df['qqq_hv_pct_rank_252'] = safe_num(df, 'qqq_hv_pct_rank_252')
    df['nq_vs_200d_pct'] = safe_num(df, 'nq_vs_200d_pct')
    df['ret_nq'] = safe_num(df, 'ret_nq')
    df['ret_qqq_avg'] = safe_num(df, 'ret_qqq_avg')
    df['corr_nq_qqq_yf_32'] = safe_num(df, 'corr_nq_qqq_yf_32')
    df['corr_nq_qqq_ibkr_32'] = safe_num(df, 'corr_nq_qqq_ibkr_32')
    df['eigen_top_share_pct_rank_32'] = safe_num(df, 'eigen_top_share_pct_rank_32')

    valid = df.dropna(subset=['future_ret_nq_h8', 'future_absret_nq_h8', 'future_max_down_h8']).copy()
    train, cal, test = split_chrono(valid)

    # Thresholds are derived on train only, then frozen for cal/test.
    thr = {
        'ret_up_70': float(train['future_ret_nq_h8'].quantile(0.70)),
        'absret_low_40': float(train['future_absret_nq_h8'].quantile(0.40)),
        'max_down_mild_65': float(train['future_max_down_h8'].quantile(0.65)),
        'max_down_bad_10': float(train['future_max_down_h8'].quantile(0.10)),
        'future_absret_high_90': float(train['future_absret_nq_h8'].quantile(0.90)),
        'ret_reversal_pos_65': float(train['future_ret_nq_h8'].quantile(0.65)),
    }

    def add_masks(x):
        y = x.copy()
        y['target_trend_expansion_h8'] = ((y['future_ret_nq_h8'] >= thr['ret_up_70']) & (y['future_max_down_h8'] >= thr['max_down_mild_65'])).astype(int)
        y['target_range_consolidation_h8'] = ((y['future_absret_nq_h8'] <= thr['absret_low_40']) & (y['future_max_down_h8'] >= thr['max_down_mild_65'])).astype(int)
        y['target_extreme_stress_h8_v2'] = ((y['future_absret_nq_h8'] >= thr['future_absret_high_90']) | (y['future_max_down_h8'] <= thr['max_down_bad_10'])).astype(int)
        y['target_reversal_brewing_h8_v2'] = ((y['ret_nq'] < 0) & (y['future_ret_nq_h8'] >= thr['ret_reversal_pos_65'])).astype(int)
        y['target_thin_liquidity_guardrail_h8'] = ((y['provider_return_disagreement'].fillna(0) <= train['provider_return_disagreement'].quantile(0.25)) & (y['future_absret_nq_h8'] <= thr['absret_low_40'])).astype(int)

        y['rule_trend_expansion'] = (
            (y['nq_vs_200d_pct'] > train['nq_vs_200d_pct'].quantile(0.50)) &
            (y['ret_nq'].rolling(4, min_periods=1).mean() > 0) &
            (y['ret_qqq_avg'].rolling(4, min_periods=1).mean() > 0) &
            (y['qqq_hv_pct_rank_252'] < train['qqq_hv_pct_rank_252'].quantile(0.80))
        )
        y['rule_range_consolidation'] = (
            (y['realized_vol_nq_pct_rank_32'] <= 0.40) &
            (y['qqq_hv_pct_rank_252'] <= train['qqq_hv_pct_rank_252'].quantile(0.50)) &
            (y['provider_return_disagreement'].fillna(1) <= train['provider_return_disagreement'].quantile(0.60))
        )
        y['rule_extreme_stress'] = (
            (y['realized_vol_nq_pct_rank_32'] >= 0.90) |
            (y['qqq_hv_pct_rank_252'] >= 0.95) |
            (y['eigen_top_share_pct_rank_32'] >= 0.90)
        )
        y['rule_reversal_brewing'] = (
            (y['ret_nq'] < train['ret_nq'].quantile(0.20)) &
            (y['provider_return_disagreement'].fillna(0) >= train['provider_return_disagreement'].quantile(0.75))
        )
        y['rule_thin_liquidity'] = (
            (y['provider_return_disagreement'].isna()) |
            (y['corr_nq_qqq_yf_32'].abs() < 0.20) |
            (y['corr_nq_qqq_ibkr_32'].abs() < 0.20)
        )
        return y

    train = add_masks(train)
    cal = add_masks(cal)
    test = add_masks(test)
    full = pd.concat([train.assign(split='train'), cal.assign(split='calibration'), test.assign(split='test')], ignore_index=True)
    full.to_csv(OUT / 'multi_regime_features_and_labels.csv', index=False)

    specs = [
        ('TrendExpansion', 'target_trend_expansion_h8', 'rule_trend_expansion', 'release_candidate_only_when_other_gates_pass', '8 15m NQ bars'),
        ('RangeConsolidation', 'target_range_consolidation_h8', 'rule_range_consolidation', 'observe_or_mean_reversion_candidate_only_when_other_gates_pass', '8 15m NQ bars'),
        ('ExtremeStress', 'target_extreme_stress_h8_v2', 'rule_extreme_stress', 'guardrail_only_reduce_or_block_release', '8 15m NQ bars'),
        ('ReversalBrewing', 'target_reversal_brewing_h8_v2', 'rule_reversal_brewing', 'observe_or_reversal_candidate_only_when_other_gates_pass', '8 15m NQ bars'),
        ('ThinLiquidity', 'target_thin_liquidity_guardrail_h8', 'rule_thin_liquidity', 'guardrail_only_liquidity_context', '8 15m NQ bars'),
    ]

    regimes = []
    accepted = []
    abstained = []
    for regime_id, target, rule, action, horizon in specs:
        cal_metrics = eval_rule(cal, rule, target)
        test_metrics = eval_rule(test, rule, target, prob_value=cal_metrics['precision'])
        p95, p99 = passes(cal_metrics, test_metrics)
        lane = '99' if p99 else '95' if p95 else 'abstain'
        target_counts = {
            'train_positive': int(train[target].sum()),
            'calibration_positive': int(cal[target].sum()),
            'test_positive': int(test[target].sum()),
            'total_positive': int(full[target].sum()),
        }
        blocker_parts = []
        if cal_metrics['support'] < 120:
            blocker_parts.append('calibration_support_too_thin')
        if test_metrics['support'] < 60:
            blocker_parts.append('test_support_too_thin')
        if test_metrics['precision_wilson_lcb_95'] < 0.95:
            blocker_parts.append('precision_wilson_lcb_below_95')
        if test_metrics['ece'] is None or test_metrics['ece'] > 0.05:
            blocker_parts.append('ece_above_95_limit')
        if test_metrics['coverage'] < 0.03:
            blocker_parts.append('coverage_below_95_limit')
        result = {
            'regime_id': regime_id,
            'market': 'NQ with QQQ provider context',
            'timeframe': 'NQ 15m, QQQ 1h context',
            'horizon': horizon,
            'allowed_action': action,
            'target': target,
            'rule': rule,
            'target_counts': target_counts,
            'calibration': cal_metrics,
            'test': test_metrics,
            'accepted_95': p95,
            'accepted_99': p99,
            'confidence_lane': lane,
            'blocker': 'none' if p95 or p99 else ';'.join(blocker_parts),
        }
        regimes.append(result)
        if p95 or p99:
            accepted.append(result)
        else:
            abstained.append(result)

    session = json.loads(SESSION_REPORT.read_text())
    session_packet = session['accepted_packet']
    report = {
        'schema_version': 'board-a-multi-regime-expansion/v1',
        'loop_id': '20260510T200229+0800-hermes-multi-regime-expansion',
        'run_root': 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion',
        'input_sources': {
            'covariance_eigenstructure_features': str(FEATURES.relative_to(ROOT)),
            'session_liquidity_report': str(SESSION_REPORT.relative_to(ROOT)),
        },
        'threshold_policy': {
            'thresholds_relaxed': False,
            'precision_wilson_lcb_95': 0.95,
            'precision_wilson_lcb_99': 0.99,
            'calibration_support_min_95': 120,
            'test_support_min_95': 60,
            'ece_max_95': 0.05,
            'coverage_min_95': 0.03,
            'training_only_thresholds': thr,
        },
        'split': {
            'train': len(train),
            'calibration': len(cal),
            'test': len(test),
            'train_time_range': {'start': str(train['ts'].min()), 'end': str(train['ts'].max())},
            'calibration_time_range': {'start': str(cal['ts'].min()), 'end': str(cal['ts'].max())},
            'test_time_range': {'start': str(test['ts'].min()), 'end': str(test['ts'].max())},
        },
        'existing_accepted_regime_packets': [session_packet],
        'new_regime_results': regimes,
        'accepted_new_regime_count_95': sum(1 for r in accepted if r['accepted_95']),
        'accepted_new_regime_count_99': sum(1 for r in accepted if r['accepted_99']),
        'accepted_new_regime_packets': [
            {
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
                'transition_hazard': None,
                'duration_viable': True,
                'downstream_evidence_fields': [r['rule'], r['target']],
                'artifact_path': 'docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_multi_regime_expansion.json',
            }
            for r in accepted
        ],
        'abstained_new_regimes': [
            {
                'regime_id': r['regime_id'],
                'blocker': r['blocker'],
                'calibration_support': r['calibration']['support'],
                'test_support': r['test']['support'],
                'test_wilson95': r['test']['precision_wilson_lcb_95'],
                'test_ece': r['test']['ece'],
                'test_coverage': r['test']['coverage'],
            }
            for r in abstained
        ],
        'decision': 'accepted_additional_regimes' if accepted else 'abstain_no_additional_calibrated_regime',
        'next_action': 'Continue regime-family expansion with new features/targets for abstained regimes; do not lower thresholds.' if abstained else 'Hand accepted multi-regime packet to downstream consumers as guardrails/context only.',
    }
    (OUT / 'multi_regime_calibration_report.json').write_text(json.dumps(report, indent=2))
    (RUN / 'evidence_packet_multi_regime_expansion.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({
        'accepted': [r['regime_id'] for r in accepted],
        'abstained': [r['regime_id'] for r in abstained],
        'report': str((OUT / 'multi_regime_calibration_report.json').relative_to(ROOT)),
        'evidence': str((RUN / 'evidence_packet_multi_regime_expansion.json').relative_to(ROOT)),
    }, indent=2))


if __name__ == '__main__':
    main()
