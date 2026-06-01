#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path('/Users/thrill3r/projects-ict-engine/ict-engine')
BASE = REPO / 'support/docs/experiments/actionable-regime-confidence'
RESEARCH_HELPERS = REPO / 'support/scripts/research'
if str(RESEARCH_HELPERS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_HELPERS))

import instrument_cost_model as cost_model  # noqa: E402

STAMP = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S+0800')
ROOT_OVERRIDE = os.environ.get('ICT_ENGINE_RUN_ROOT_OVERRIDE', '').strip()
ROOT = Path(ROOT_OVERRIDE).expanduser() if ROOT_OVERRIDE else BASE / 'runs' / f'{STAMP}-hermes-ibkr-qqq-intraday-micro-trend-reclaim-density-1m-mtf-v1'
PY = Path('/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python')
FETCH = REPO / 'support/scripts/auto_quant_external/fetch_external.py'
ICT = REPO / '.local-artifacts/cargo-target/debug/ict-engine'
AQ_REPO = Path('/Users/thrill3r/Auto-Quant')
AQ_SYMBOL = 'IBKR_QQQ_INTRADAY_MICRO_TREND_RECLAIM_DENSITY_1M_MTF_V1'
FACTOR_ID = 'ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1'
BRANCH_PATH = 'US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1'
PARTS = [p.strip() for p in BRANCH_PATH.split(' -> ')]

@dataclass(frozen=True)
class Spec:
    tf: str
    bar_size: str
    duration: str
    role: str

SPECS = [
    Spec('1m', '1 min', '7 D', 'training_origin'),
    Spec('5m', '5 mins', '1 M', 'small_cycle_context'),
    Spec('15m', '15 mins', '1 M', 'small_cycle_sibling'),
    Spec('30m', '30 mins', '1 M', 'neutralization_context'),
    Spec('1h', '1 hour', '1 M', 'higher_timeframe_veto'),
    Spec('4h', '4 hours', '1 M', 'attempt_if_provider_supported'),
    Spec('1d', '1 day', '1 Y', 'daily_context'),
]

VARIANTS = {
    'dense': dict(roi=0.0025, stop=-0.0040, trail=0.0010, off=0.0032, vol=0.35, rsi_lo=38, rsi_hi=82, max_ext=3.8, min_slope=-0.12),
    'balanced': dict(roi=0.0032, stop=-0.0048, trail=0.0012, off=0.0040, vol=0.45, rsi_lo=42, rsi_hi=78, max_ext=3.0, min_slope=-0.06),
    'quality': dict(roi=0.0042, stop=-0.0060, trail=0.0016, off=0.0052, vol=0.60, rsi_lo=46, rsi_hi=74, max_ext=2.3, min_slope=0.00),
}

def run_cmd(name: str, argv: list[object], timeout: int = 240) -> dict:
    (ROOT / 'command-output').mkdir(parents=True, exist_ok=True)
    (ROOT / 'checks').mkdir(parents=True, exist_ok=True)
    argv_s = [str(x) for x in argv]
    (ROOT / 'command-output' / f'{name}.cmd').write_text(' '.join(argv_s) + '\n', encoding='utf-8')
    try:
        proc = subprocess.run(argv_s, cwd=REPO, text=True, capture_output=True, timeout=timeout)
        stdout, stderr, rc, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ''
        stderr = (exc.stderr or '') + f'\nTIMEOUT after {timeout}s\n'
        rc, timed_out = 124, True
    if isinstance(stdout, bytes):
        stdout = stdout.decode('utf-8', errors='replace')
    if isinstance(stderr, bytes):
        stderr = stderr.decode('utf-8', errors='replace')
    (ROOT / 'command-output' / f'{name}.out').write_text(stdout, encoding='utf-8')
    (ROOT / 'command-output' / f'{name}.err').write_text(stderr, encoding='utf-8')
    (ROOT / 'checks' / f'{name}.exit').write_text(f'{rc}\n', encoding='utf-8')
    return {'name': name, 'exit': rc, 'timed_out': timed_out}

def skipped_cmd(name: str, reason: str) -> dict:
    (ROOT / 'command-output').mkdir(parents=True, exist_ok=True)
    (ROOT / 'checks').mkdir(parents=True, exist_ok=True)
    (ROOT / 'command-output' / f'{name}.cmd').write_text(f'skipped: {reason}\n', encoding='utf-8')
    (ROOT / 'command-output' / f'{name}.out').write_text('', encoding='utf-8')
    (ROOT / 'command-output' / f'{name}.err').write_text(f'skipped: {reason}\n', encoding='utf-8')
    (ROOT / 'checks' / f'{name}.exit').write_text('0\n', encoding='utf-8')
    return {'name': name, 'exit': 0, 'timed_out': False, 'skipped': True, 'reason': reason}

def provider_acquisition_status(provider_rows: list[dict]) -> str:
    if any(int(row.get('rows') or 0) > 0 for row in provider_rows):
        return 'nonzero_rows_acquired'
    if any(int(row.get('exit') or 0) != 0 for row in provider_rows):
        return 'blocked_no_provider_rows_fetch_failed'
    return 'blocked_no_provider_rows'

def classify_decision(provider_rows: list[dict], downstream_allowed: bool, promotion_cost_verified: bool) -> tuple[str, str]:
    status = provider_acquisition_status(provider_rows)
    if status != 'nonzero_rows_acquired':
        return 'provider_acquisition_blocked_no_gate1_verdict', status
    if not promotion_cost_verified:
        return 'blocked_cost_model_unverified_no_downstream', status
    if downstream_allowed:
        return 'gate1_ibkr_native_candidate_downstream_allowed', status
    return 'drop_gate1_no_ibkr_cost_density', status

def normalize(src: Path, dst: Path) -> int:
    if not src.exists() or src.stat().st_size == 0:
        return 0
    with src.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((k for k in ('timestamp', 'time', 'datetime', 'date', 'ts') if k in headers), None)
        if not time_key:
            return 0
        rows = []
        for row in reader:
            if all(row.get(k) not in (None, '') for k in ('open', 'high', 'low', 'close')):
                rows.append({'timestamp': row.get(time_key, ''), 'open': row.get('open', ''), 'high': row.get('high', ''), 'low': row.get('low', ''), 'close': row.get('close', ''), 'volume': row.get('volume') or '0'})
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        writer.writeheader(); writer.writerows(rows)
    return len(rows)

def timerange(path: Path) -> str:
    dates = []
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            raw = (row.get('timestamp') or '').strip()
            if raw:
                dates.append(raw[:10].replace('-', ''))
    return f'{min(dates)}-{max(dates)}' if dates else ''

def suffix(tf: str) -> str:
    return tf.replace('m', 'Min').replace('h', 'Hour').replace('d', 'Day')

def cls(tf: str, variant: str) -> str:
    return f'IbkrQqqIntradayMicroTrendReclaimDensity{variant.title()}{suffix(tf)}V1'

def strategy_source(class_name: str, tf: str, cfg: dict, variant: str) -> str:
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame

class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{tf}"
    can_short = False
    minimal_roi = {{"0": {cfg['roi']}}}
    stoploss = {cfg['stop']}
    trailing_stop = True
    trailing_stop_positive = {cfg['trail']}
    trailing_stop_positive_offset = {cfg['off']}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = dataframe["close"].ewm(span=9, adjust=False).mean()
        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["atr50"] = tr.rolling(50).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 0.000001)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        dataframe["vol40"] = dataframe["volume"].rolling(40).mean()
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        regular = (minute >= 13 * 60 + 30) & (minute < 20 * 60)
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        dataframe["session_vwap"] = ((typical * dataframe["volume"]).where(regular).groupby(day_key).cumsum() / dataframe["volume"].where(regular).groupby(day_key).cumsum().replace(0, 1))
        dataframe["regular_session"] = regular
        dataframe["entry_window"] = (minute >= 13 * 60 + 42) & (minute < 19 * 60 + 20)
        dataframe["force_exit_window"] = minute >= 19 * 60 + 50
        dataframe["ema_slope"] = dataframe["ema21"] - dataframe["ema21"].shift(5)
        dataframe["vwap_distance_atr"] = (dataframe["close"] - dataframe["session_vwap"]) / dataframe["atr14"]
        dataframe["rv_expansion"] = dataframe["atr14"] / dataframe["atr50"]
        dataframe["micro_reclaim"] = (dataframe["close"] > dataframe["ema9"]) & (dataframe["close"].shift(1) <= dataframe["ema9"].shift(1) * 1.0008)
        dataframe["vwap_reclaim_soft"] = dataframe["close"] > dataframe["session_vwap"] * 0.9985
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["ema9"] > dataframe["ema21"] - dataframe["atr14"] * 0.08) & (dataframe["ema21"] > dataframe["ema55"] - dataframe["atr14"] * 0.35)
        density_reclaim = dataframe["micro_reclaim"] | ((dataframe["close"] > dataframe["ema9"]) & dataframe["vwap_reclaim_soft"])
        slope_ok = dataframe["ema_slope"].fillna(0) >= dataframe["atr14"] * {cfg['min_slope']}
        vol_ok = dataframe["volume"] >= dataframe["vol40"] * {cfg['vol']}
        rsi_ok = dataframe["rsi14"].between({cfg['rsi_lo']}, {cfg['rsi_hi']})
        extension_ok = dataframe["vwap_distance_atr"].between(-0.60, {cfg['max_ext']})
        volatility_ok = dataframe["rv_expansion"].between(0.55, 2.70)
        signal = dataframe["entry_window"] & trend & density_reclaim & slope_ok & vol_ok & rsi_ok & extension_ok & volatility_ok
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{FACTOR_ID}_{variant}_{tf}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        fail = (dataframe["close"] < dataframe["ema21"] - dataframe["atr14"] * 0.20) | (dataframe["close"] < dataframe["session_vwap"] - dataframe["atr14"] * 0.45)
        exit_signal = dataframe["force_exit_window"] | fail | (dataframe["rsi14"] > 86)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''

def latest_rank_rows() -> list[dict]:
    files = sorted((ROOT / f'state/auto-quant/{AQ_SYMBOL}').glob('auto_quant_agent_material_rank.*.json'))
    if not files:
        return []
    return json.loads(files[-1].read_text(encoding='utf-8')).get('ranking', [])

def safe_float(v: object) -> float:
    try:
        return float(str(v))
    except Exception:
        return 0.0

def row_label(row: dict) -> str:
    package_id = str(row.get('package_id') or '')
    variant = next((v for v in VARIANTS if f'-{v}-' in package_id), 'unknown')
    timeframe = next((spec.tf for spec in SPECS if package_id.endswith(f'-{spec.tf}-v1')), str(row.get('timeframe') or 'unknown'))
    return f'{variant}/QQQ/{timeframe}'

def main() -> int:
    for sub in ['data/provider/raw', 'data/provider/normalized', 'agent-material', 'summaries', 'checks', 'command-output', 'state', 'scripts']:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / 'scripts' / Path(__file__).name)
    commands = [run_cmd('00_provider_status_ibkr', [ICT, 'provider-status', '--provider', 'ibkr', '--agent'], timeout=60)]
    provider_rows = []
    materials = []
    strategies = []
    for index, spec in enumerate(SPECS, start=1):
        raw = ROOT / 'data/provider/raw' / f'ibkr_qqq_{spec.tf}_{spec.duration.replace(" ", "").lower()}.csv'
        norm = ROOT / 'data/provider/normalized' / raw.name
        result = run_cmd(f'{index:02d}_ibkr_fetch_qqq_{spec.tf}_{spec.duration.replace(" ", "").lower()}', [PY, FETCH, 'ibkr-historical', '--symbol', 'QQQ', '--sec-type', 'STK', '--exchange', 'SMART', '--currency', 'USD', '--primary-exchange', 'NASDAQ', '--bar-size', spec.bar_size, '--duration', spec.duration, '--what-to-show', 'TRADES', '--host', '127.0.0.1', '--port', '4002', '--client-id', str(610 + index), '--output', raw], timeout=480)
        commands.append(result)
        rows = normalize(raw, norm)
        provider_rows.append({'provider': 'IBKR', 'symbol': 'QQQ', 'timeframe': spec.tf, 'bar_size': spec.bar_size, 'duration': spec.duration, 'role': spec.role, 'rows': rows, 'path': str(norm) if rows else '', 'exit': result['exit'], 'local_cache_replay': 'false'})
        if rows == 0:
            continue
        for variant, cfg in VARIANTS.items():
            class_name = cls(spec.tf, variant)
            strategy_path = ROOT / 'agent-material' / f'{class_name}.py'
            strategy_path.write_text(strategy_source(class_name, spec.tf, cfg, variant), encoding='utf-8')
            strategies.append(strategy_path)
            material_path = ROOT / 'agent-material' / f'ibkr_qqq_intraday_micro_trend_reclaim_density_{variant}_{spec.tf}_v1.material.json'
            material = {
                'package_id': f'ibkr-qqq-intraday-micro-trend-reclaim-density-{variant}-{spec.tf}-v1',
                'title': f'IBKR QQQ intraday micro trend reclaim density {variant} {spec.tf}',
                'symbol': 'QQQ',
                'timeframe': spec.tf,
                'timerange': timerange(norm),
                'direction': 'long',
                'data_path': str(norm),
                'strategy_source_path': str(strategy_path),
                'strategy_class_name': class_name,
                'strategy_brief': 'IBKR-native QQQ 1m-root intraday micro trend reclaim density candidate using session VWAP, EMA slope, RVOL, and short-hold execution controls.',
                'evaluation_priority': ['ibkr_native_provider', 'one_minute_origin_density', 'real_cost_survival', 'mtf_resonance', 'same_branch_downstream_readiness'],
                'consumer_evidence_profile': {
                    'branch_path': BRANCH_PATH,
                    'regime_profit_branch_path': BRANCH_PATH,
                    'branch_id': FACTOR_ID,
                    'market': PARTS[0],
                    'product': PARTS[1],
                    'root_symbol': PARTS[2],
                    'root_timeframe': PARTS[3],
                    'main_regime': PARTS[4],
                    'sub_regime': PARTS[5],
                    'sub_sub_regime_or_profit_factor': PARTS[6],
                    'profit_factor': PARTS[7],
                    'base_timeframe': '1m',
                    'training_timeframe': '1m',
                    'material_timeframe': spec.tf,
                    'provider': 'IBKR',
                    'provider_window': spec.duration,
                    'provider_provenance': f'IBKR QQQ {spec.tf} {spec.duration}',
                    'asset_class': 'us_equity_etf',
                    'gate_id': 'Gate1IbkrQqqOneMinuteMicroTrendReclaimDensity',
                    'promotion_allowed': False,
                    'trade_usable': False,
                    'update_goal': False,
                },
                'notes': ['ibkr_first=true', 'local_cache_replay=false', 'root_includes_market_product_symbol_timeframe=true', 'profit_factor_only_after_regime_root=true', 'pre_bayes_bbn_catboost_execution_tree_allowed=false_until_gate1_cost_density_passes'],
            }
            material_path.write_text(json.dumps(material, indent=2) + '\n', encoding='utf-8')
            materials.append(material_path)
    compile_result = run_cmd('08_strategy_py_compile', [PY, '-m', 'py_compile', *strategies], timeout=120) if strategies else skipped_cmd('08_strategy_py_compile', 'no provider rows/materialized strategies')
    commands.append(compile_result)
    batch = dispatch = rank = None
    if materials and compile_result['exit'] == 0:
        args = [ICT, 'auto-quant-agent-material-batch', '--symbol', AQ_SYMBOL, '--state-dir', ROOT / 'state', '--max-parallel', '1']
        if AQ_REPO.exists():
            args += ['--repo-url', AQ_REPO]
        for material in materials:
            args += ['--material', material]
        batch = run_cmd('09_auto_quant_agent_material_batch', args, timeout=1800)
        commands.append(batch)
    if batch and batch['exit'] == 0:
        dispatch = run_cmd('10_auto_quant_agent_material_dispatch', [ICT, 'auto-quant-agent-material-dispatch', '--symbol', AQ_SYMBOL, '--state-dir', ROOT / 'state'], timeout=1800)
        commands.append(dispatch)
    if dispatch and dispatch['exit'] == 0:
        rank = run_cmd('11_auto_quant_agent_material_rank', [ICT, 'auto-quant-agent-material-rank', '--symbol', AQ_SYMBOL, '--state-dir', ROOT / 'state'], timeout=360)
        commands.append(rank)
    rank_rows = latest_rank_rows() if rank and rank['exit'] == 0 else []
    representative_price = None
    cost_summary = {'rows': [], 'survivors': [], 'cost_model': cost_model.cost_model_packet('QQQ'), 'promotion_cost_verified': False, 'representative_price': None}
    if rank_rows:
        try:
            representative_price = cost_model.representative_price_from_provider_rows(provider_rows)
        except ValueError:
            representative_price = None
        if representative_price is not None:
            cost_summary = cost_model.rank_rows_real_fee_summary(
                rank_rows,
                symbol='QQQ',
                representative_price=representative_price,
                label_fn=row_label,
            )
    instrument_cost_rows = cost_summary['rows']
    origin = [row for row in instrument_cost_rows if row['label'].endswith('/1m')]
    origin_survivors = [row['label'] for row in origin if int(row.get('trade_count') or 0) >= 6 and row.get('survives_instrument_cost')]
    exact_branch_ok = bool(rank_rows) and all((row.get('branch_path') or row.get('consumer_evidence_profile', {}).get('branch_path')) == BRANCH_PATH for row in rank_rows)
    covered = sorted({row['timeframe'] for row in provider_rows if row['rows'] > 0})
    missing = sorted({row['timeframe'] for row in provider_rows if row['rows'] == 0})
    downstream_allowed = exact_branch_ok and bool(origin_survivors) and bool(cost_summary.get('promotion_cost_verified'))
    decision, provider_status = classify_decision(provider_rows, downstream_allowed, bool(cost_summary.get('promotion_cost_verified')))
    metrics = {
        'run_root': str(ROOT),
        'factor_id': FACTOR_ID,
        'branch_path': BRANCH_PATH,
        'decision': decision,
        'provider_acquisition_status': provider_status,
        'gate1_verdict': 'not_run_no_provider_rows' if provider_status != 'nonzero_rows_acquired' else ('passed_instrument_cost_density_for_downstream' if downstream_allowed else 'failed_or_unverified_instrument_cost_density'),
        'provider_rows': provider_rows,
        'material_count': len(materials),
        'rank_rows': len(rank_rows),
        'representative_price': representative_price,
        'cost_model': cost_summary['cost_model'],
        'promotion_cost_verified': cost_summary['promotion_cost_verified'],
        'instrument_cost_rows': instrument_cost_rows,
        'origin_survivors_instrument_cost': origin_survivors,
        'branch_fields_preserved': exact_branch_ok,
        'covered_timeframes': covered,
        'missing_timeframes': missing,
        'command_exits': {cmd['name']: cmd['exit'] for cmd in commands},
        'pre_bayes_allowed': downstream_allowed,
        'bbn_allowed': downstream_allowed,
        'catboost_allowed': downstream_allowed,
        'execution_tree_allowed': downstream_allowed,
        'promotion_allowed': False,
        'trade_usable': False,
        'update_goal': False,
        'skill_update': 'not_needed',
    }
    (ROOT / 'checks/terminal_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'summaries/terminal_decision_summary.md').write_text('# Terminal Decision Summary\n\n' + json.dumps(metrics, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metrics, indent=2))
    return 0 if rank and rank['exit'] == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
