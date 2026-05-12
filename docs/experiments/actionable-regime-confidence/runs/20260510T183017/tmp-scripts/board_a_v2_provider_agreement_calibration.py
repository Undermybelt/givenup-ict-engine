
from __future__ import annotations

import csv
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

REPO = Path('/Users/thrill3r/projects-ict-engine/ict-engine')
PREV = REPO / 'docs/experiments/actionable-regime-confidence/runs/20260510T174651'
RUN = REPO / 'docs/experiments/actionable-regime-confidence/runs/20260510T183017'
SELECTED = PREV / 'autoquant/autoquant-entry-windows-512-selected-trades.csv'
LEAKSAFE = PREV / 'catboost/autoquant_entry_release_leaksafe_features_512.csv'
SCAN = PREV / 'execution-tree/entry_scan_512.tsv'
YF_QQQ_BACKTEST = PREV / 'branch-chain/qqq-regime-branch-iteration/candles/yf_QQQ_1h_2024_2025.csv'
YF_NQ_LIVE = RUN / 'provider/yf_nq_15m.csv'
YF_QQQ_LIVE = RUN / 'provider/yf_qqq_1h.csv'
IBKR_QQQ_LIVE = RUN / 'provider/ibkr_qqq_1h.csv'
KRAKEN_LIVE = RUN / 'provider/kraken_pf_xbtusd_15m.csv'
AUTOQUANT_CACHE = Path('/Users/thrill3r/Auto-Quant/user_data/data/NQ_USD-15m.feather')

OUT_LABELS = RUN / 'labels/provider_agreement_v2_labels_512.csv'
OUT_FEATURES = RUN / 'calibration/provider_agreement_v2_features_512.csv'
OUT_REPORT = RUN / 'calibration/provider_agreement_v2_calibration_report.json'
OUT_PROVIDER = RUN / 'provider/provider_status_v2.json'
OUT_PACKET = RUN / 'evidence_packet_v2.json'
OUT_LABELS.parent.mkdir(parents=True, exist_ok=True)
OUT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

BLOCKED_LEAKAGE_SUBSTRINGS = [
    'gate_status', 'branch', 'decision_hint', 'execution_readiness',
    'readiness_gap_to_observe', 'readiness_gap_to_ready',
    'hybrid_transition_hazard', 'duration_remaining_expected_bars',
    'execution_tree', 'target_', 'outcome', 'profit', 'close_', 'exit_',
    'cluster_safe', 'cluster_bad', 'cluster_all_safe', 'cluster_any_win',
    'is_bad_loss', 'is_win', 'is_material_win',
]


def as_dt(series: pd.Series) -> pd.Series:
    values = series.copy()
    if pd.api.types.is_numeric_dtype(values):
        return pd.to_datetime(values, unit='ms', utc=True, errors='coerce')
    return pd.to_datetime(values, utc=True, errors='coerce')


def read_ohlcv(path: Path, provider: str, market: str, timeframe: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    ts_col = 'date' if 'date' in df.columns else 'ts' if 'ts' in df.columns else 'timestamp'
    df['timestamp'] = as_dt(df[ts_col])
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['timestamp', 'open', 'high', 'low', 'close']).sort_values('timestamp')
    df['provider'] = provider
    df['market'] = market
    df['timeframe'] = timeframe
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'provider', 'market', 'timeframe']]


def trend_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['ret_1'] = out['close'].pct_change()
    out['ret_4'] = out['close'].pct_change(4)
    out['ret_8'] = out['close'].pct_change(8)
    out['ret_16'] = out['close'].pct_change(16)
    out['range_pct'] = (out['high'] - out['low']) / out['close'].replace(0, np.nan)
    out['vol_16'] = out['ret_1'].rolling(16, min_periods=4).std()
    out['absret_16'] = out['ret_1'].abs().rolling(16, min_periods=4).sum()
    out['eff_16'] = out['ret_16'].abs() / out['absret_16'].replace(0, np.nan)
    out['trend_dir'] = np.where(out['ret_8'] > 0, 1, np.where(out['ret_8'] < 0, -1, 0))
    vol_thr = out['vol_16'].rolling(96, min_periods=16).quantile(0.55)
    eff_thr = out['eff_16'].rolling(96, min_periods=16).quantile(0.55)
    out['trend_expansion'] = ((out['ret_8'] > 0) & (out['eff_16'] >= eff_thr) & (out['vol_16'] >= vol_thr)).astype(int)
    out['transition_guardrail'] = ((out['trend_dir'] == 0) | (out['eff_16'].fillna(0) < 0.25) | (out['vol_16'].isna())).astype(int)
    return out


def align_provider_features(trades: pd.DataFrame, provider_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    left = trades[['row_id', 'open_dt']].copy()
    left['open_dt'] = pd.to_datetime(left['open_dt'], utc=True).astype('datetime64[ns, UTC]')
    left = left.sort_values('open_dt')
    right = trend_features(provider_df).copy()
    right['timestamp'] = pd.to_datetime(right['timestamp'], utc=True).astype('datetime64[ns, UTC]')
    right = right.sort_values('timestamp')
    merged = pd.merge_asof(left, right, left_on='open_dt', right_on='timestamp', direction='backward', tolerance=pd.Timedelta('7D'))
    keep = ['row_id', 'timestamp', 'ret_1', 'ret_4', 'ret_8', 'ret_16', 'range_pct', 'vol_16', 'eff_16', 'trend_dir', 'trend_expansion', 'transition_guardrail']
    merged = merged[keep]
    rename = {c: f'{prefix}_{c}' for c in keep if c != 'row_id'}
    return merged.rename(columns=rename)


def wilson_lower(successes: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def ece_binary(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    if len(y) == 0:
        return 1.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    err = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi == 1.0:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        if not mask.any():
            continue
        err += mask.mean() * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(err)


def max_drawdown_from_entry(close: pd.Series, entry: float) -> float:
    if close.empty or entry == 0:
        return 0.0
    return float((close / entry - 1.0).min())


def future_return(close: pd.Series, entry: float) -> float:
    if close.empty or entry == 0:
        return 0.0
    return float(close.iloc[-1] / entry - 1.0)


def load_provider_status() -> dict[str, Any]:
    paths = {
        'yfinance_nq_15m': YF_NQ_LIVE,
        'yfinance_qqq_1h': YF_QQQ_LIVE,
        'ibkr_qqq_1h': IBKR_QQQ_LIVE,
        'kraken_pf_xbtusd_15m': KRAKEN_LIVE,
    }
    status: dict[str, Any] = {}
    for key, path in paths.items():
        if path.exists():
            df = read_ohlcv(path, key.split('_')[0], key, 'mixed')
            status[key] = {
                'artifact': str(path.relative_to(RUN)),
                'rows': int(len(df)),
                'first': df['timestamp'].min().isoformat() if len(df) else None,
                'last': df['timestamp'].max().isoformat() if len(df) else None,
                'ready': bool(len(df)),
            }
        else:
            status[key] = {'artifact': str(path.relative_to(RUN)), 'ready': False, 'rows': 0}
    if AUTOQUANT_CACHE.exists():
        try:
            aq = pd.read_feather(AUTOQUANT_CACHE, columns=['date','open','high','low','close','volume'])
            status['auto_quant_cache_nq_15m'] = {
                'source': str(AUTOQUANT_CACHE), 'ready': True, 'rows': int(len(aq)),
                'first': str(pd.to_datetime(aq['date'].iloc[0], unit='ms', utc=True)),
                'last': str(pd.to_datetime(aq['date'].iloc[-1], unit='ms', utc=True)),
            }
        except Exception as exc:
            status['auto_quant_cache_nq_15m'] = {'source': str(AUTOQUANT_CACHE), 'ready': False, 'error': repr(exc)}
    status['tradingview_remix'] = {
        'ready': False,
        'status': 'configured_runtime_unhealthy',
        'reason': 'provider-status probe returned tradingview_mcp_connectivity_probe_failed; durable 2026-only tv_QQQ_1h artifact not chronologically aligned with 2024-2025 replay labels',
    }
    OUT_PROVIDER.write_text(json.dumps({'schema_version':'provider-status-v2','providers':status}, indent=2) + '\n')
    return status


def build_labels() -> tuple[pd.DataFrame, dict[str, Any]]:
    trades = pd.read_csv(SELECTED)
    trades.insert(0, 'row_id', np.arange(1, len(trades) + 1))
    trades['open_dt'] = as_dt(trades['open_timestamp'])
    trades['profit_ratio_num'] = pd.to_numeric(trades['profit_ratio'], errors='coerce')
    trades['is_bad_loss_num'] = trades['profit_ratio_num'] <= -0.0025
    trades['release_allowed_v2'] = ((trades['profit_ratio_num'] > 0.0) & (~trades['is_bad_loss_num'])).astype(int)

    qqq_yf = read_ohlcv(YF_QQQ_BACKTEST, 'yfinance', 'QQQ', '1h')
    nq_aq = pd.read_feather(AUTOQUANT_CACHE)
    nq_aq['timestamp'] = pd.to_datetime(nq_aq['date'], unit='ms', utc=True, errors='coerce')
    nq_aq = nq_aq.rename(columns={'timestamp':'timestamp'})[['timestamp','open','high','low','close','volume']]
    for col in ['open','high','low','close','volume']:
        nq_aq[col] = pd.to_numeric(nq_aq[col], errors='coerce')
    nq_aq['provider'] = 'auto_quant_cache'
    nq_aq['market'] = 'NQ'
    nq_aq['timeframe'] = '15m'
    nq_aq = nq_aq.dropna(subset=['timestamp','open','high','low','close']).sort_values('timestamp')

    labels = trades[['row_id','trade_id','strategy','strategy_family','pair','timeframe','open_date','open_timestamp','open_dt','profit_ratio_num','release_allowed_v2','is_bad_loss_num']].copy()
    labels = labels.merge(align_provider_features(trades, qqq_yf, 'qqq_yf_1h'), on='row_id', how='left')
    labels = labels.merge(align_provider_features(trades, nq_aq, 'nq_autoquant_15m'), on='row_id', how='left')
    labels['provider_observations_aligned'] = labels[['qqq_yf_1h_timestamp','nq_autoquant_15m_timestamp']].notna().sum(axis=1)
    labels['provider_trend_expansion_votes'] = labels[['qqq_yf_1h_trend_expansion','nq_autoquant_15m_trend_expansion']].fillna(0).sum(axis=1)
    labels['provider_transition_guardrail_votes'] = labels[['qqq_yf_1h_transition_guardrail','nq_autoquant_15m_transition_guardrail']].fillna(0).sum(axis=1)
    labels['provider_bull_trend_votes'] = ((labels['qqq_yf_1h_trend_dir'] > 0).astype(int) + (labels['nq_autoquant_15m_trend_dir'] > 0).astype(int))
    labels['provider_agreement_v2'] = ((labels['provider_observations_aligned'] >= 2) & (labels['provider_bull_trend_votes'] >= 2)).astype(int)
    labels['provider_agreement_trend_expansion_event'] = ((labels['provider_agreement_v2'] == 1) & (labels['provider_trend_expansion_votes'] >= 1)).astype(int)
    labels['provider_disagreement_transition_guardrail_event'] = ((labels['provider_observations_aligned'] < 2) | (labels['provider_bull_trend_votes'] < 2) | (labels['provider_transition_guardrail_votes'] >= 1)).astype(int)

    # Future-realized transition stability and path edge are labels, not predictors.
    qqq_tf = trend_features(qqq_yf)
    future_ret_16 = []
    future_dd_16 = []
    stable = []
    for dt, entry in zip(labels['open_dt'], labels['profit_ratio_num']):
        row = qqq_tf[qqq_tf['timestamp'] <= dt].tail(1)
        current_dir = int(row['trend_dir'].iloc[0]) if len(row) else 0
        future = qqq_tf[(qqq_tf['timestamp'] > dt) & (qqq_tf['timestamp'] <= dt + pd.Timedelta(hours=16))]
        entry_close = float(row['close'].iloc[0]) if len(row) else np.nan
        fret = future_return(future['close'], entry_close) if np.isfinite(entry_close) else 0.0
        fdd = max_drawdown_from_entry(future['close'], entry_close) if np.isfinite(entry_close) else 0.0
        future_ret_16.append(fret)
        future_dd_16.append(fdd)
        future_dirs = future['trend_dir'].dropna().astype(int)
        if len(future_dirs) == 0 or current_dir == 0:
            stable.append(0)
        else:
            stable.append(int((future_dirs == current_dir).mean() >= 0.65))
    labels['future_qqq_ret_16h'] = future_ret_16
    labels['future_qqq_max_dd_16h'] = future_dd_16
    labels['transition_stable_v2'] = stable
    labels['path_specific_edge_v2'] = ((labels['profit_ratio_num'] > 0.0) & (labels['future_qqq_ret_16h'] > -0.002)).astype(int)
    labels['release_allowed_v2'] = ((labels['release_allowed_v2'] == 1) & (labels['future_qqq_max_dd_16h'] > -0.015)).astype(int)
    labels['provider_agreement_trend_expansion_release_v2'] = ((labels['provider_agreement_trend_expansion_event'] == 1) & (labels['release_allowed_v2'] == 1) & (labels['transition_stable_v2'] == 1) & (labels['path_specific_edge_v2'] == 1)).astype(int)
    labels['allowed_action'] = np.where(labels['provider_agreement_trend_expansion_release_v2'] == 1, 'release_long', 'observe_only')
    labels['regime_id_v2'] = np.where(labels['provider_agreement_trend_expansion_event'] == 1, 'ProviderAgreementTrendExpansion', 'ProviderDisagreementTransitionGuardrail')
    labels.to_csv(OUT_LABELS, index=False)
    meta = {
        'rows': int(len(labels)),
        'label_counts': {col: {'positive': int(labels[col].sum()), 'negative': int(len(labels)-labels[col].sum())} for col in ['provider_agreement_v2','provider_agreement_trend_expansion_event','provider_disagreement_transition_guardrail_event','release_allowed_v2','transition_stable_v2','path_specific_edge_v2','provider_agreement_trend_expansion_release_v2']},
        'provider_alignment': {
            'observations_ge_2': int((labels['provider_observations_aligned'] >= 2).sum()),
            'provider_bull_trend_votes_2': int((labels['provider_bull_trend_votes'] >= 2).sum()),
        }
    }
    return labels, meta


def build_features(labels: pd.DataFrame) -> pd.DataFrame:
    base = pd.read_csv(LEAKSAFE)
    selected = pd.read_csv(SELECTED)
    selected.insert(0, 'row_id', np.arange(1, len(selected)+1))
    df = pd.DataFrame({'row_id': labels['row_id']})
    # Allowed current features only from Auto-Quant leak-safe columns.
    for col in base.columns:
        low = col.lower()
        if any(block in low for block in BLOCKED_LEAKAGE_SUBSTRINGS):
            continue
        if col.startswith(('aq_5m_', 'aq_15m_', 'aq_1h_', 'aq_4h_', 'aq_1d_', 'aq_entry_', 'aq_is_short_int', 'aq_qqq_', 'aq_nq_', 'aq_vix', 'aq_vvix', 'aq_filter_')):
            df[col] = pd.to_numeric(base[col], errors='coerce')
    provider_cols = [c for c in labels.columns if c.startswith(('qqq_yf_1h_ret','qqq_yf_1h_range','qqq_yf_1h_vol','qqq_yf_1h_eff','qqq_yf_1h_trend_dir','nq_autoquant_15m_ret','nq_autoquant_15m_range','nq_autoquant_15m_vol','nq_autoquant_15m_eff','nq_autoquant_15m_trend_dir','provider_observations_aligned','provider_trend_expansion_votes','provider_transition_guardrail_votes','provider_bull_trend_votes'))]
    for col in provider_cols:
        df[col] = pd.to_numeric(labels[col], errors='coerce')
    for col in ['provider_agreement_trend_expansion_release_v2','release_allowed_v2','transition_stable_v2','path_specific_edge_v2','provider_agreement_v2','provider_agreement_trend_expansion_event']:
        df[f'target_{col}'] = labels[col].astype(int).values
    df['open_dt'] = labels['open_dt'].astype(str).values
    df.to_csv(OUT_FEATURES, index=False)
    return df


def score_target(df: pd.DataFrame, target_col: str) -> dict[str, Any]:
    target = df[target_col].astype(int).to_numpy()
    feature_cols = [c for c in df.columns if c not in {'row_id','open_dt'} and not c.startswith('target_')]
    x = df[feature_cols].apply(pd.to_numeric, errors='coerce').replace([np.inf,-np.inf], np.nan).fillna(0.0)
    n = len(df)
    train_end = n // 2
    cal_end = (n * 3) // 4
    y_train = target[:train_end]
    if len(np.unique(y_train)) < 2 or int(target.sum()) == 0:
        return {'target': target_col, 'skipped': True, 'reason': 'single_class_or_no_positive_train', 'positive': int(target.sum()), 'negative': int(n-target.sum())}
    model = CatBoostClassifier(iterations=180, depth=4, learning_rate=0.035, loss_function='Logloss', verbose=False, random_seed=29, allow_writing_files=False)
    model.fit(x.iloc[:train_end], y_train)
    prob = model.predict_proba(x)[:,1]
    importances = model.get_feature_importance()
    top = [{'feature': f, 'importance': float(v)} for f,v in sorted(zip(feature_cols, importances), key=lambda kv: kv[1], reverse=True)[:15]]
    thresholds = sorted(set(map(float, prob[train_end:cal_end])), reverse=True)
    candidates = []
    for thr in thresholds:
        cal_idx = np.where(prob[train_end:cal_end] >= thr)[0] + train_end
        if len(cal_idx) < 120:
            continue
        cal_success = int(target[cal_idx].sum())
        cal_lcb = wilson_lower(cal_success, len(cal_idx), 1.959963984540054)
        test_idx = np.where(prob[cal_end:] >= thr)[0] + cal_end
        if len(test_idx) < 60:
            continue
        test_success = int(target[test_idx].sum())
        test_lcb95 = wilson_lower(test_success, len(test_idx), 1.959963984540054)
        test_lcb99 = wilson_lower(test_success, len(test_idx), 2.5758293035489004)
        coverage = len(test_idx) / max(1, n - cal_end)
        ece = ece_binary(target[test_idx], prob[test_idx]) if len(test_idx) else 1.0
        candidates.append({
            'threshold': float(thr),
            'calibration_support': int(len(cal_idx)),
            'calibration_success': cal_success,
            'calibration_precision': cal_success / len(cal_idx),
            'calibration_wilson_lcb_95': cal_lcb,
            'test_support': int(len(test_idx)),
            'test_success': test_success,
            'test_precision': test_success / len(test_idx),
            'precision_wilson_lcb_95': test_lcb95,
            'precision_wilson_lcb_99': test_lcb99,
            'ece': ece,
            'coverage': coverage,
            'passes_95': bool(test_lcb95 >= 0.95 and len(cal_idx) >= 120 and len(test_idx) >= 60 and ece <= 0.05 and coverage >= 0.03),
            'passes_99': bool(test_lcb99 >= 0.99 and len(cal_idx) >= 300 and len(test_idx) >= 120 and ece <= 0.02 and coverage >= 0.02),
        })
    candidates.sort(key=lambda r: (r['passes_99'], r['passes_95'], r['precision_wilson_lcb_95'], r['test_support'], r['calibration_wilson_lcb_95']), reverse=True)
    return {
        'target': target_col,
        'skipped': False,
        'positive': int(target.sum()),
        'negative': int(n-target.sum()),
        'train_rows': int(train_end),
        'calibration_rows': int(cal_end-train_end),
        'test_rows': int(n-cal_end),
        'top_importances': top,
        'admissible_rules': len(candidates),
        'accepted_95_rules': sum(1 for c in candidates if c['passes_95']),
        'accepted_99_rules': sum(1 for c in candidates if c['passes_99']),
        'selected_rule': candidates[0] if candidates else None,
    }


def main() -> None:
    provider_status = load_provider_status()
    labels, label_meta = build_labels()
    features = build_features(labels)
    target_cols = [
        'target_provider_agreement_trend_expansion_release_v2',
        'target_release_allowed_v2',
        'target_transition_stable_v2',
        'target_path_specific_edge_v2',
        'target_provider_agreement_v2',
        'target_provider_agreement_trend_expansion_event',
    ]
    target_reports = {col: score_target(features, col) for col in target_cols}
    accepted_95 = [r for r in target_reports.values() if not r.get('skipped') and r.get('accepted_95_rules',0) > 0]
    accepted_99 = [r for r in target_reports.values() if not r.get('skipped') and r.get('accepted_99_rules',0) > 0]
    release_report = target_reports['target_provider_agreement_trend_expansion_release_v2']
    blocker = 'none'
    accepted_gate = 'none'
    board_state = 'abstain'
    if release_report.get('skipped'):
        blocker = str(release_report.get('reason'))
    elif release_report.get('accepted_95_rules', 0) > 0:
        accepted_gate = 'ProviderAgreementTrendExpansionReleaseV2_95'
        board_state = 'accepted_95'
        if release_report.get('accepted_99_rules', 0) > 0:
            accepted_gate = 'ProviderAgreementTrendExpansionReleaseV2_99'
            board_state = 'accepted_99'
    else:
        selected = release_report.get('selected_rule') or {}
        if label_meta['label_counts']['provider_agreement_trend_expansion_release_v2']['positive'] < 120:
            blocker = 'support_too_thin_for_release_packet'
        elif not selected:
            blocker = 'abstain_no_calibrated_release_rule'
        else:
            blocker = 'precision_or_ece_below_acceptance_threshold'
    report = {
        'schema_version': 'board-a-provider-agreement-v2-calibration/v1',
        'loop_id': '20260510T183017+0800-board-a-v2-provider-agreement-calibration',
        'inputs': {
            'selected_trades': str(SELECTED.relative_to(REPO)),
            'leak_safe_features': str(LEAKSAFE.relative_to(REPO)),
            'qqq_yfinance_backtest': str(YF_QQQ_BACKTEST.relative_to(REPO)),
            'nq_autoquant_cache': str(AUTOQUANT_CACHE),
        },
        'leakage_policy': {
            'blocked_substrings': BLOCKED_LEAKAGE_SUBSTRINGS,
            'blocked_fields_not_used_as_predictors': ['gate_status','branch','decision_hint','execution_readiness','readiness_gap_to_observe','readiness_gap_to_ready','hybrid_transition_hazard','duration_remaining_expected_bars'],
        },
        'label_meta': label_meta,
        'target_reports': target_reports,
        'accepted_gate': accepted_gate,
        'board_state': board_state,
        'blocker': blocker,
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, default=str) + '\n')
    packet = {
        'schema_version': 'board-a-actionable-regime-confidence-evidence/v2',
        'loop_id': report['loop_id'],
        'durable_run_root': str(RUN.relative_to(REPO)),
        'provider_packet': provider_status,
        'active_market_timeframe_set': {'primary_chain':['QQQ 1h','NQ 15m'], 'provider_probe_only':['PF_XBTUSD 15m','TradingViewRemix QQQ 1h unavailable for replay']},
        'candidate_regime': {'regime_id':'ProviderAgreementTrendExpansion', 'horizon':'16h replay label', 'allowed_action':'release_long' if accepted_gate != 'none' else 'none'},
        'calibration_result': {
            'accepted_gate': accepted_gate,
            'board_state': board_state,
            'blocker': blocker,
            'release_target': release_report,
            'other_target_summary': {k:v for k,v in target_reports.items() if k != 'target_provider_agreement_trend_expansion_release_v2'},
        },
        'downstream_chain': {
            'pre_bayes': {'artifact': 'bbn/02_pre_bayes_status.out'},
            'bbn': {'dry_run_artifact':'bbn/03_auto_quant_prior_init_dry_run.out','apply_artifact':'bbn/04_auto_quant_prior_init_apply.out'},
            'catboost': {'path_ranker_train':'catboost/03_path_ranker_train.out','blocker':'catboost_support_too_thin: 3 target rows, mature_rows=0'},
            'execution_tree': {'workflow_after_bbn':'execution-tree/04_workflow_status_after_bbn_apply.out','state_snapshot':'state-snapshots/workflow_snapshot.json'},
        },
        'artifacts': {
            'labels': str(OUT_LABELS.relative_to(REPO)),
            'features': str(OUT_FEATURES.relative_to(REPO)),
            'calibration_report': str(OUT_REPORT.relative_to(REPO)),
        },
        'next_action': 'A-v2-2: add replay-aligned second same-market provider or realized covariance/eigenstructure, then rerun ProviderAgreementTrendExpansion release calibration without lowering thresholds.'
    }
    OUT_PACKET.write_text(json.dumps(packet, indent=2, default=str) + '\n')
    print(json.dumps({'ok': True, 'packet': str(OUT_PACKET), 'accepted_gate': accepted_gate, 'board_state': board_state, 'blocker': blocker, 'label_counts': label_meta['label_counts']}, indent=2))

if __name__ == '__main__':
    main()
