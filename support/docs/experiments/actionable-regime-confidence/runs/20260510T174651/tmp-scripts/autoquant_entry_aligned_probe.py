import csv
import json
import math
from pathlib import Path

ROOT = Path('/tmp/ict-regime-chain-20260509T231052')
SCAN = ROOT / 'autoquant-entry-execution-tree-scan-512-compatible' / 'scan.tsv'
SELECTED = ROOT / 'autoquant-entry-windows-512-selected-trades.csv'
OUT_DIR = ROOT / 'autoquant-entry-release-probe-512'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FEATURES = OUT_DIR / 'autoquant_entry_release_features_512.csv'
REPORT = OUT_DIR / 'autoquant_entry_release_probe_512.json'

TARGETS = [
    'AvoidBadLossCluster',
    'AnyWinCluster',
    'ExecutionObserveOrBetter',
    'LowTransitionHazard',
    'DurationViable',
    'ReadinessObserveOrReady',
]

EXCLUDE_SUBSTRINGS = [
    'profit', 'close_', 'exit_', 'trade_duration', 'outcome', 'win', 'loss', 'safe',
    'cluster_safe', 'cluster_bad', 'cluster_all_safe', 'cluster_any_win',
]


def parse_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == '' or text.lower() in {'none', 'nan', 'null'}:
        return None
    try:
        x = float(text)
    except ValueError:
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def wilson_lower(successes, total, z=1.959963984540054):
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def load_rows():
    selected_rows = []
    with SELECTED.open() as f:
        for row in csv.DictReader(f):
            selected_rows.append(row)
    scan_rows = []
    with SCAN.open() as f:
        for row in csv.DictReader(f, delimiter='\t'):
            scan_rows.append(row)
    if len(selected_rows) != len(scan_rows):
        raise SystemExit(f'row mismatch: selected={len(selected_rows)} scan={len(scan_rows)}')
    rows = []
    for idx, (trade, scan) in enumerate(zip(selected_rows, scan_rows), start=1):
        row = {}
        row['row_id'] = idx
        row['open_timestamp'] = trade.get('open_timestamp')
        row['pair'] = trade.get('pair')
        row['strategy'] = trade.get('strategy')
        row['strategy_family'] = trade.get('strategy_family')
        row['enter_tag'] = trade.get('enter_tag')
        row['timeframe'] = trade.get('timeframe')
        row['weekday'] = parse_float(trade.get('weekday'))
        row['is_short_numeric'] = 1.0 if str(trade.get('is_short')).lower() == 'true' else 0.0
        # Entry-known Auto-Quant features only.
        for key, value in trade.items():
            low = key.lower()
            if any(s in low for s in EXCLUDE_SUBSTRINGS):
                continue
            if key in {'archive', 'archive_name', 'trade_id', 'pair', 'strategy', 'strategy_family', 'timeframe', 'timerange', 'trade_index', 'open_date', 'enter_tag', 'is_short', 'selected_window_file'}:
                continue
            val = parse_float(value)
            if val is not None:
                row[f'aq_{key}'] = val
        # ICT execution-tree scan metrics.
        for key, value in scan.items():
            val = parse_float(value)
            if val is not None:
                row[f'ict_{key}'] = val
        # Categorical scan states as simple indicators.
        for key in ['gate_status', 'branch', 'decision_hint', 'path_ranker_runtime_source']:
            value = (scan.get(key) or '').strip()
            if value:
                row[f'ict_{key}__{value}'] = 1.0
        cluster_count = int(float(trade.get('cluster_trade_count') or 0))
        cluster_bad = int(float(trade.get('cluster_bad_count') or 0))
        cluster_safe = int(float(trade.get('cluster_safe_count') or 0))
        row['target_AvoidBadLossCluster'] = 1 if cluster_count > 0 and cluster_bad == 0 else 0
        row['target_AnyWinCluster'] = 1 if str(trade.get('cluster_any_win')).lower() == 'true' else 0
        gate = (scan.get('gate_status') or '').lower()
        row['target_ExecutionObserveOrBetter'] = 1 if gate in {'observe', 'pass', 'ready', 'actionable'} else 0
        hazard = parse_float(scan.get('hybrid_transition_hazard'))
        row['target_LowTransitionHazard'] = 1 if hazard is not None and hazard <= 0.60 else 0
        duration = parse_float(scan.get('duration_remaining_expected_bars'))
        row['target_DurationViable'] = 1 if duration is not None and duration > 0.0 else 0
        readiness = parse_float(scan.get('execution_readiness'))
        row['target_ReadinessObserveOrReady'] = 1 if readiness is not None and readiness >= 0.45 else 0
        rows.append(row)
    return rows


def write_features(rows):
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with FEATURES.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fit_scores_with_catboost(rows, feature_cols, target):
    try:
        from catboost import CatBoostClassifier
        import pandas as pd
    except Exception as exc:
        return None, {'skipped': True, 'reason': f'catboost_unavailable:{type(exc).__name__}'}
    df = pd.DataFrame(rows)
    y = df[f'target_{target}'].astype(int)
    if y.iloc[: max(1, len(y)//2)].nunique() < 2:
        return None, {'skipped': True, 'reason': 'single_class_train_split'}
    x = df[feature_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0)
    n = len(df)
    train_end = n // 2
    model = CatBoostClassifier(iterations=160, depth=4, learning_rate=0.04, loss_function='Logloss', verbose=False, random_seed=17, allow_writing_files=False)
    model.fit(x.iloc[:train_end], y.iloc[:train_end])
    prob = model.predict_proba(x)[:, 1]
    importances = model.get_feature_importance()
    top = sorted(zip(feature_cols, map(float, importances)), key=lambda kv: kv[1], reverse=True)[:12]
    return list(map(float, prob)), {'skipped': False, 'top_importances': [{'feature': k, 'importance': v} for k, v in top]}


def threshold_probe(rows, scores, target, min_cal=30, min_test=20, min_wilson=0.95):
    n = len(rows)
    cal_start = n // 2
    test_start = (n * 3) // 4
    labels = [int(r[f'target_{target}']) for r in rows]
    thresholds = sorted(set(scores[cal_start:test_start]), reverse=True)
    candidates = []
    for thr in thresholds:
        cal_idx = [i for i in range(cal_start, test_start) if scores[i] >= thr]
        if len(cal_idx) < min_cal:
            continue
        cal_ok = sum(labels[i] for i in cal_idx)
        cal_w = wilson_lower(cal_ok, len(cal_idx))
        if cal_w < min_wilson:
            continue
        test_idx = [i for i in range(test_start, n) if scores[i] >= thr]
        if len(test_idx) < min_test:
            continue
        test_ok = sum(labels[i] for i in test_idx)
        test_w = wilson_lower(test_ok, len(test_idx))
        candidates.append({
            'threshold': thr,
            'calibration_success': cal_ok,
            'calibration_total': len(cal_idx),
            'calibration_precision': cal_ok / len(cal_idx),
            'calibration_wilson_lower': cal_w,
            'test_success': test_ok,
            'test_total': len(test_idx),
            'test_precision': test_ok / len(test_idx),
            'test_wilson_lower': test_w,
            'passes': test_w >= min_wilson,
        })
    candidates.sort(key=lambda c: (c['passes'], c['test_wilson_lower'], c['test_total'], c['calibration_wilson_lower']), reverse=True)
    return candidates


def main():
    rows = load_rows()
    write_features(rows)
    numeric_cols = []
    for key in rows[0]:
        if key.startswith('target_') or key in {'row_id'}:
            continue
        vals = [parse_float(r.get(key)) for r in rows]
        if any(v is not None for v in vals):
            numeric_cols.append(key)
    report = {
        'rows': len(rows),
        'features_csv': str(FEATURES),
        'numeric_feature_count': len(numeric_cols),
        'target_counts': {},
        'targets': {},
        'overall_decision': 'no_95_candidate',
    }
    for target in TARGETS:
        labels = [int(r[f'target_{target}']) for r in rows]
        report['target_counts'][target] = {'positive': sum(labels), 'negative': len(labels)-sum(labels)}
        scores, meta = fit_scores_with_catboost(rows, numeric_cols, target)
        if scores is None:
            report['targets'][target] = {**meta, 'accepted_rules': 0, 'selected_rule': None}
            continue
        candidates = threshold_probe(rows, scores, target)
        selected = candidates[0] if candidates else None
        report['targets'][target] = {
            **meta,
            'accepted_rules': len([c for c in candidates if c.get('passes')]),
            'calibration_admissible_rules': len(candidates),
            'selected_rule': selected,
        }
        if selected and selected.get('passes'):
            report['overall_decision'] = 'candidate_found'
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({'report': str(REPORT), 'overall_decision': report['overall_decision'], 'target_counts': report['target_counts']}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
