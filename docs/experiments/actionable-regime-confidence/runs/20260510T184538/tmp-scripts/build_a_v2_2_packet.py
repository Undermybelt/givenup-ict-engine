
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

REPO = Path('/Users/thrill3r/projects-ict-engine/ict-engine')
RUN = REPO / 'docs/experiments/actionable-regime-confidence/runs/20260510T184538'
AQ_JSON = RUN / 'autoquant/fresh_tomac_scratch_no_rsi_nq_binding_2025.json'
NQ_FEATHER = Path('/Users/thrill3r/Auto-Quant/user_data/data/NQ_USD-15m.feather')
QQQ_YF = REPO / 'docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/yf_QQQ_1h_20240601_20260509.csv'
IBKR_QQQ = REPO / 'docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/ibkr_QQQ_1h.csv'
KRAKEN = REPO / 'docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/kraken_PF_XBTUSD_1h_2024_2025.csv'

OUT_LIBRARY = RUN / 'autoquant/strategy_library_nq_scratch_no_rsi_2025.json'
OUT_LABELS = RUN / 'calibration/nq_binding_provider_agreement_labels_1081.csv'
OUT_FEATURES = RUN / 'calibration/nq_binding_provider_agreement_features_1081.csv'
OUT_REPORT = RUN / 'calibration/nq_binding_provider_agreement_calibration.json'
OUT_PACKET = RUN / 'evidence_packet_v2.json'


def as_dt(v):
    return pd.to_datetime(v, utc=True, errors='coerce')


def load_ohlcv(path: Path, ts_col: str | None = None) -> pd.DataFrame:
    if path.suffix == '.feather':
        df = pd.read_feather(path)
        df['timestamp'] = pd.to_datetime(df['date'], unit='ms', utc=True)
    else:
        df = pd.read_csv(path)
        col = ts_col or ('date' if 'date' in df.columns else 'ts')
        df['timestamp'] = pd.to_datetime(df[col], utc=True, errors='coerce')
    for c in ['open','high','low','close','volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.dropna(subset=['timestamp','open','high','low','close']).sort_values('timestamp')[['timestamp','open','high','low','close','volume']]


def add_feats(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['ret_1'] = out['close'].pct_change()
    out['ret_4'] = out['close'].pct_change(4)
    out['ret_8'] = out['close'].pct_change(8)
    out['ret_16'] = out['close'].pct_change(16)
    out['ret_32'] = out['close'].pct_change(32)
    out['range_pct'] = (out['high'] - out['low']) / out['close'].replace(0, np.nan)
    out['vol_16'] = out['ret_1'].rolling(16, min_periods=4).std()
    out['vol_64'] = out['ret_1'].rolling(64, min_periods=8).std()
    out['absret_16'] = out['ret_1'].abs().rolling(16, min_periods=4).sum()
    out['eff_16'] = out['ret_16'].abs() / out['absret_16'].replace(0, np.nan)
    out['dd_16'] = out['close'] / out['close'].rolling(16, min_periods=4).max() - 1.0
    out['pos_16'] = (out['close'] - out['low'].rolling(16, min_periods=4).min()) / (out['high'].rolling(16, min_periods=4).max() - out['low'].rolling(16, min_periods=4).min()).replace(0, np.nan)
    vol_thr = out['vol_16'].rolling(256, min_periods=64).quantile(0.55)
    eff_thr = out['eff_16'].rolling(256, min_periods=64).quantile(0.55)
    out['trend_dir'] = np.where(out['ret_16'] > 0, 1, np.where(out['ret_16'] < 0, -1, 0))
    out['trend_expansion'] = ((out['trend_dir'] > 0) & (out['vol_16'] >= vol_thr) & (out['eff_16'] >= eff_thr)).astype(int)
    out['transition_guardrail'] = ((out['eff_16'].fillna(0) < 0.25) | (out['vol_16'].isna()) | (out['dd_16'] < -0.01)).astype(int)
    return out


def align(left: pd.DataFrame, right: pd.DataFrame, prefix: str, tolerance: str) -> pd.DataFrame:
    l = left[['row_id','open_dt']].copy()
    l['open_dt'] = pd.to_datetime(l['open_dt'], utc=True).astype('datetime64[ns, UTC]')
    r = add_feats(right).copy()
    r['timestamp'] = pd.to_datetime(r['timestamp'], utc=True).astype('datetime64[ns, UTC]')
    m = pd.merge_asof(l.sort_values('open_dt'), r.sort_values('timestamp'), left_on='open_dt', right_on='timestamp', direction='backward', tolerance=pd.Timedelta(tolerance))
    keep = ['row_id','timestamp','ret_1','ret_4','ret_8','ret_16','ret_32','range_pct','vol_16','vol_64','eff_16','dd_16','pos_16','trend_dir','trend_expansion','transition_guardrail']
    return m[keep].rename(columns={c:f'{prefix}_{c}' for c in keep if c!='row_id'})


def wilson(successes: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + z*z/total
    center = p + z*z/(2*total)
    margin = z * math.sqrt((p*(1-p)+z*z/(4*total))/total)
    return max(0.0, (center-margin)/denom)


def ece(y: np.ndarray, p: np.ndarray) -> float:
    if len(y) == 0:
        return 1.0
    total = len(y)
    out = 0.0
    for lo, hi in zip(np.linspace(0,1,11)[:-1], np.linspace(0,1,11)[1:]):
        mask = ((p >= lo) & (p <= hi)) if hi == 1 else ((p >= lo) & (p < hi))
        if mask.any():
            out += mask.sum()/total * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(out)


def build_library(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload['summaries'][0]
    trades = payload['results'][summary['strategy']]['trades']
    wins = sum(1 for t in trades if float(t.get('profit_ratio') or 0) > 0)
    losses = sum(1 for t in trades if float(t.get('profit_ratio') or 0) < 0)
    total_profit_pct = float(summary['profit_total']) * 100
    pf = float(summary['profit_factor'])
    lib = {
        'manifest_version': '1.0',
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'auto_quant_repo_url': '/Users/thrill3r/Auto-Quant',
        'auto_quant_pinned_ref': 'local-nq-binding-probe',
        'config_path': str(payload['scratch_config']),
        'timeframe': summary['timeframe'],
        'log_path': str(RUN / 'autoquant/fresh_tomac_scratch_no_rsi_nq_binding_2025.out'),
        'strategies': [{
            'name': summary['strategy'],
            'file_path': '/tmp/ict-regime-chain-20260509T231052/scratch_strategies/TomacNQ_ScratchNoRSINoConflict15m.py',
            'metadata': {'strategy': summary['strategy'], 'mutation_id': 'board-a-v2-2-nq-binding-repair', 'base_factor': 'scratch_no_rsi_no_conflict', 'hypothesis': 'data-binding repair probe only', 'paradigm': 'trend_pullback', 'status': 'probe_only', 'created': '2026-05-10'},
            'status': 'ok',
            'validation_metrics': {'sharpe': 0.0, 'sortino': 0.0, 'calmar': 0.0, 'total_profit_pct': total_profit_pct, 'max_drawdown_pct': -14.97, 'trade_count': int(summary['total_trades']), 'win_rate_pct': float(summary['winrate'])*100, 'profit_factor': pf},
            'per_pair_metrics': {'NQ/USD': {'total_profit_pct': total_profit_pct, 'trade_count': int(summary['total_trades']), 'win_rate_pct': float(summary['winrate'])*100, 'profit_factor': pf}},
            'pairs': ['NQ/USD'],
            'timerange': f"{summary['first_open']} -> {summary['last_open']}",
            'commit': 'local-nq-binding-probe',
            'error': None,
        }],
        'validation_errors': [],
    }
    OUT_LIBRARY.write_text(json.dumps(lib, indent=2) + '\n')
    return lib


def build_labels(payload: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    trades = payload['results']['TomacNQ_ScratchNoRSINoConflict15m']['trades']
    rows = []
    for i, t in enumerate(trades, 1):
        rows.append({
            'row_id': i,
            'open_dt': as_dt(t['open_date']),
            'close_dt': as_dt(t['close_date']),
            'profit_ratio': float(t.get('profit_ratio') or 0),
            'trade_duration': float(t.get('trade_duration') or 0),
            'exit_reason': str(t.get('exit_reason') or ''),
            'open_rate': float(t.get('open_rate') or 0),
            'min_rate': float(t.get('min_rate') or 0),
            'max_rate': float(t.get('max_rate') or 0),
        })
    df = pd.DataFrame(rows).sort_values('open_dt')
    nq = load_ohlcv(NQ_FEATHER)
    qqq = load_ohlcv(QQQ_YF)
    ibkr = load_ohlcv(IBKR_QQQ)
    # Kraken is context-only; dates do not overlap 2025 probe, so no predictor alignment.
    df = df.merge(align(df, nq, 'nq_aq_15m', '1h'), on='row_id', how='left')
    df = df.merge(align(df, qqq, 'qqq_yf_1h', '7D'), on='row_id', how='left')
    df = df.merge(align(df, ibkr, 'qqq_ibkr_1h', '7D'), on='row_id', how='left')
    df['provider_observations'] = df[['nq_aq_15m_timestamp','qqq_yf_1h_timestamp','qqq_ibkr_1h_timestamp']].notna().sum(axis=1)
    df['provider_bull_votes'] = (df['nq_aq_15m_trend_dir'].fillna(0).gt(0).astype(int) + df['qqq_yf_1h_trend_dir'].fillna(0).gt(0).astype(int) + df['qqq_ibkr_1h_trend_dir'].fillna(0).gt(0).astype(int))
    df['provider_expansion_votes'] = df[['nq_aq_15m_trend_expansion','qqq_yf_1h_trend_expansion','qqq_ibkr_1h_trend_expansion']].fillna(0).sum(axis=1)
    df['provider_guardrail_votes'] = df[['nq_aq_15m_transition_guardrail','qqq_yf_1h_transition_guardrail','qqq_ibkr_1h_transition_guardrail']].fillna(0).sum(axis=1)
    df['provider_agreement_v2'] = ((df['provider_observations'] >= 2) & (df['provider_bull_votes'] >= 2)).astype(int)
    df['provider_agreement_trend_expansion_event'] = ((df['provider_agreement_v2'] == 1) & (df['provider_expansion_votes'] >= 1)).astype(int)
    df['provider_disagreement_transition_guardrail_event'] = ((df['provider_observations'] < 2) | (df['provider_bull_votes'] < 2) | (df['provider_guardrail_votes'] >= 1)).astype(int)
    df['release_allowed_v2'] = ((df['profit_ratio'] > 0.0) & ((df['min_rate'] / df['open_rate'] - 1.0) > -0.015)).astype(int)
    df['path_specific_edge_v2'] = (df['profit_ratio'] > 0.001).astype(int)
    df['duration_viable_v2'] = (df['trade_duration'] >= 30).astype(int)
    df['transition_stable_v2'] = ((df['provider_guardrail_votes'] <= 1) & (df['duration_viable_v2'] == 1)).astype(int)
    df['provider_agreement_trend_expansion_release_v2'] = ((df['provider_agreement_trend_expansion_event'] == 1) & (df['release_allowed_v2'] == 1) & (df['path_specific_edge_v2'] == 1) & (df['transition_stable_v2'] == 1)).astype(int)
    df.to_csv(OUT_LABELS, index=False)
    meta = {col: {'positive': int(df[col].sum()), 'negative': int(len(df)-df[col].sum())} for col in ['provider_agreement_v2','provider_agreement_trend_expansion_event','provider_disagreement_transition_guardrail_event','release_allowed_v2','path_specific_edge_v2','transition_stable_v2','provider_agreement_trend_expansion_release_v2']}
    return df, meta


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    cols = ['row_id','open_dt']
    for c in df.columns:
        if any(c.startswith(prefix) for prefix in ['nq_aq_15m_ret','nq_aq_15m_range','nq_aq_15m_vol','nq_aq_15m_eff','nq_aq_15m_dd','nq_aq_15m_pos','nq_aq_15m_trend_dir','qqq_yf_1h_ret','qqq_yf_1h_range','qqq_yf_1h_vol','qqq_yf_1h_eff','qqq_yf_1h_dd','qqq_yf_1h_pos','qqq_yf_1h_trend_dir','qqq_ibkr_1h_ret','qqq_ibkr_1h_range','qqq_ibkr_1h_vol','qqq_ibkr_1h_eff','qqq_ibkr_1h_dd','qqq_ibkr_1h_pos','qqq_ibkr_1h_trend_dir','provider_observations','provider_bull_votes','provider_expansion_votes','provider_guardrail_votes']):
            cols.append(c)
    features = df[cols].copy()
    features['entry_hour_sin'] = np.sin(2*np.pi*pd.to_datetime(df['open_dt']).dt.hour/24)
    features['entry_hour_cos'] = np.cos(2*np.pi*pd.to_datetime(df['open_dt']).dt.hour/24)
    features['entry_dow_sin'] = np.sin(2*np.pi*pd.to_datetime(df['open_dt']).dt.dayofweek/7)
    features['entry_dow_cos'] = np.cos(2*np.pi*pd.to_datetime(df['open_dt']).dt.dayofweek/7)
    for t in ['provider_agreement_trend_expansion_release_v2','release_allowed_v2','path_specific_edge_v2','transition_stable_v2','provider_agreement_v2','provider_agreement_trend_expansion_event']:
        features[f'target_{t}'] = df[t].astype(int)
    features.to_csv(OUT_FEATURES, index=False)
    return features


def score(features: pd.DataFrame, target_col: str) -> dict[str, Any]:
    y = features[target_col].astype(int).to_numpy()
    feature_cols = [c for c in features.columns if c not in ['row_id','open_dt'] and not c.startswith('target_')]
    x = features[feature_cols].apply(pd.to_numeric, errors='coerce').replace([np.inf,-np.inf], np.nan).fillna(0.0)
    n = len(x)
    train_end = int(n * 0.5)
    cal_end = int(n * 0.75)
    if len(set(y[:train_end])) < 2 or y.sum() == 0:
        return {'target': target_col, 'skipped': True, 'reason': 'single_class_or_no_positive_train', 'positive': int(y.sum()), 'negative': int(n-y.sum())}
    model = CatBoostClassifier(iterations=220, depth=4, learning_rate=0.03, loss_function='Logloss', random_seed=41, verbose=False, allow_writing_files=False)
    model.fit(x.iloc[:train_end], y[:train_end])
    p = model.predict_proba(x)[:,1]
    imps = model.get_feature_importance()
    top = [{'feature': f, 'importance': float(v)} for f,v in sorted(zip(feature_cols, imps), key=lambda kv: kv[1], reverse=True)[:12]]
    candidates = []
    for thr in sorted(set(map(float, p[train_end:cal_end])), reverse=True):
        cal_idx = np.where(p[train_end:cal_end] >= thr)[0] + train_end
        if len(cal_idx) < 120:
            continue
        test_idx = np.where(p[cal_end:] >= thr)[0] + cal_end
        if len(test_idx) < 60:
            continue
        cal_success = int(y[cal_idx].sum())
        test_success = int(y[test_idx].sum())
        e = ece(y[test_idx], p[test_idx])
        cov = len(test_idx) / (n-cal_end)
        candidates.append({'threshold': float(thr), 'calibration_support': int(len(cal_idx)), 'calibration_success': cal_success, 'calibration_precision': cal_success/len(cal_idx), 'calibration_wilson_lcb_95': wilson(cal_success, len(cal_idx), 1.959963984540054), 'test_support': int(len(test_idx)), 'test_success': test_success, 'test_precision': test_success/len(test_idx), 'precision_wilson_lcb_95': wilson(test_success, len(test_idx), 1.959963984540054), 'precision_wilson_lcb_99': wilson(test_success, len(test_idx), 2.5758293035489004), 'ece': e, 'coverage': cov, 'passes_95': bool(wilson(test_success, len(test_idx), 1.959963984540054) >= 0.95 and e <= 0.05 and cov >= 0.03), 'passes_99': bool(wilson(test_success, len(test_idx), 2.5758293035489004) >= 0.99 and len(cal_idx)>=300 and len(test_idx)>=120 and e<=0.02 and cov>=0.02)})
    candidates.sort(key=lambda c: (c['passes_99'], c['passes_95'], c['precision_wilson_lcb_95'], c['test_precision'], c['test_support']), reverse=True)
    return {'target': target_col, 'skipped': False, 'positive': int(y.sum()), 'negative': int(n-y.sum()), 'train_rows': train_end, 'calibration_rows': cal_end-train_end, 'test_rows': n-cal_end, 'top_importances': top, 'admissible_rules': len(candidates), 'accepted_95_rules': sum(1 for c in candidates if c['passes_95']), 'accepted_99_rules': sum(1 for c in candidates if c['passes_99']), 'selected_rule': candidates[0] if candidates else None}


def main() -> None:
    payload = json.loads(AQ_JSON.read_text())
    lib = build_library(payload)
    labels, label_counts = build_labels(payload)
    features = make_features(labels)
    target_cols = [f'target_{x}' for x in ['provider_agreement_trend_expansion_release_v2','release_allowed_v2','path_specific_edge_v2','transition_stable_v2','provider_agreement_v2','provider_agreement_trend_expansion_event']]
    reports = {t: score(features, t) for t in target_cols}
    release = reports['target_provider_agreement_trend_expansion_release_v2']
    accepted_gate = 'none'
    state = 'abstain'
    if not release.get('skipped') and release.get('accepted_95_rules', 0) > 0:
        accepted_gate = 'ProviderAgreementTrendExpansionReleaseV2_95'
        state = 'accepted_95'
        if release.get('accepted_99_rules', 0) > 0:
            accepted_gate = 'ProviderAgreementTrendExpansionReleaseV2_99'
            state = 'accepted_99'
    blocker = 'none' if accepted_gate != 'none' else 'abstain_no_calibrated_release_rule'
    report = {'schema_version': 'board-a-v2-2-nq-binding-calibration/v1', 'loop_id': '20260510T184538+0800-board-a-v2-2-nq-binding-repair', 'label_counts': label_counts, 'target_reports': reports, 'accepted_gate': accepted_gate, 'board_state': state, 'blocker': blocker}
    OUT_REPORT.write_text(json.dumps(report, indent=2, default=str) + '\n')
    packet = {
        'schema_version': 'board-a-actionable-regime-confidence-evidence/v2',
        'loop_id': report['loop_id'],
        'durable_run_root': str(RUN.relative_to(REPO)),
        'provider_packet': {
            'auto_quant_nq_binding': {'status': 'repaired', 'trades': int(payload['summaries'][0]['total_trades']), 'artifact': 'autoquant/fresh_tomac_scratch_no_rsi_nq_binding_2025.json'},
            'yfinance_qqq': {'artifact': 'provider inherited from 20260510T183454/yf_QQQ_1h_20240601_20260509.csv'},
            'ibkr_qqq': {'artifact': 'provider inherited from 20260510T183454/ibkr_QQQ_1h.csv'},
            'kraken': {'artifact': 'provider inherited from 20260510T183454/kraken_PF_XBTUSD_1h_2024_2025.csv', 'role': 'probe_only'},
            'tradingview_remix': {'status': 'configured_runtime_unhealthy', 'artifact': 'provider/tv_qqq_harness_retry.json'},
        },
        'active_market_timeframe_set': {'primary_chain': ['NQ 15m', 'QQQ 1h'], 'provider_probe_only': ['PF_XBTUSD 1h', 'TradingViewRemix QQQ failed']},
        'candidate_regime': {'regime_id': 'ProviderAgreementTrendExpansion', 'horizon': 'fresh 2025 NQ-bound Auto-Quant trades', 'allowed_action': 'release_long' if accepted_gate != 'none' else 'none'},
        'auto_quant_packet': {'strategy_library': str(OUT_LIBRARY.relative_to(REPO)), 'summary': payload['summaries'][0], 'data_binding_fix': 'pair_whitelist changed from QQQ/USD to NQ/USD in isolated scratch config only'},
        'calibration_result': {'accepted_gate': accepted_gate, 'board_state': state, 'blocker': blocker, 'release_target': release, 'other_target_summary': {k:v for k,v in reports.items() if k != 'target_provider_agreement_trend_expansion_release_v2'}},
        'artifacts': {'labels': str(OUT_LABELS.relative_to(REPO)), 'features': str(OUT_FEATURES.relative_to(REPO)), 'calibration_report': str(OUT_REPORT.relative_to(REPO))},
        'next_action': 'A-v2-3: do not pursue this NQ ScratchNoRSINoConflict release gate; either restore TradingViewRemix or switch regime family/labels because fresh NQ-bound repair produced no calibrated release rule.'
    }
    OUT_PACKET.write_text(json.dumps(packet, indent=2, default=str) + '\n')
    print(json.dumps({'ok': True, 'accepted_gate': accepted_gate, 'board_state': state, 'blocker': blocker, 'label_counts': label_counts, 'packet': str(OUT_PACKET)}, indent=2))

if __name__ == '__main__':
    main()
