import csv, json, math
from pathlib import Path
from datetime import datetime, timezone

run_root = Path('docs/experiments/actionable-regime-confidence/runs/20260512T193511+0800-codex-long-horizon-provider-window-inventory-v1')
out_dir = run_root / 'long-horizon-provider-window-inventory-v1'
out_dir.mkdir(parents=True, exist_ok=True)
source_175651 = Path('docs/experiments/actionable-regime-confidence/runs/20260512T175651+0800-codex-high-density-rsi-bb-ema-six-provider-aq-v1')
source_191941 = Path('docs/experiments/actionable-regime-confidence/runs/20260512T191941+0800-codex-independent-market-timeframe-downstream-smoke-v1')
prov_csv = source_175651 / 'summaries/provider_provenance_matrix.csv'
market_csv = source_191941 / 'independent-market-timeframe-downstream-smoke-v1/market_timeframe_inventory_v1.csv'
summary_191941 = source_191941 / 'independent-market-timeframe-downstream-smoke-v1/independent_market_timeframe_downstream_smoke_v1.json'

def parse_dt(s):
    if not s:
        return None
    s = s.strip().replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z') if dt else ''

def read_csv(p):
    with p.open(newline='') as f:
        return list(csv.DictReader(f))

providers = read_csv(prov_csv)
market_rows = {r['provider']: r for r in read_csv(market_csv)}
smoke = json.loads(summary_191941.read_text())
rows = []
for r in providers:
    provider = r['provider']
    m = market_rows.get(provider, {})
    first = parse_dt(r.get('first',''))
    last = parse_dt(r.get('last',''))
    span_days = (last - first).total_seconds() / 86400 if first and last else 0.0
    rows_1h = int(float(m.get('source_rows_1h') or r.get('rows') or 0))
    rows_full = int(float(m.get('source_rows_full') or r.get('rows') or 0))
    rows_4h = int(float(m.get('derived_rows_4h') or 0))
    rows_1d = int(float(m.get('derived_rows_1d') or 0))
    source_native_timeframe = r.get('timeframe','') or 'unknown'
    # Board correction: long horizon is not a magic 15y rule, but one-month/short windows are only smoke.
    long_span_candidate = span_days >= 365 or rows_1h >= 8000
    adequate_for_training = long_span_candidate and rows_4h >= 200 and rows_1d >= 90
    native_cross_timeframe = False  # current artifacts derive 4h/1d from 1h; no provider-native 4h/1d fetch evidence.
    if provider == 'yfinance/YF':
        market = 'equity'
    elif provider == 'IBKR':
        market = 'equity'
    else:
        market = 'crypto'
    blockers = []
    if not long_span_candidate:
        blockers.append('short_provider_span_or_low_1h_rows')
    if not native_cross_timeframe:
        blockers.append('no_provider_native_cross_timeframe_fetch')
    if rows_1d < 90:
        blockers.append('daily_rows_below_90')
    if provider in ('Bybit','TradingViewRemix/TVR','IBKR') and span_days < 180:
        blockers.append('provider_window_under_180_days')
    rows.append({
        'provider': provider,
        'market': market,
        'provider_symbol': r.get('provider_symbol',''),
        'aq_symbol': r.get('aq_symbol',''),
        'requested_span': r.get('requested_span',''),
        'actual_first': iso(first),
        'actual_last': iso(last),
        'actual_span_days': round(span_days, 3),
        'source_native_timeframe': source_native_timeframe,
        'source_rows_full': rows_full,
        'source_rows_1h': rows_1h,
        'derived_rows_4h': rows_4h,
        'derived_rows_1d': rows_1d,
        'provider_authority_state': r.get('provider_authority_state',''),
        'local_cache_replay': r.get('local_cache_replay',''),
        'material_path': r.get('material_path',''),
        'normalized_path': r.get('normalized_path',''),
        'native_cross_timeframe_provider_fetch': native_cross_timeframe,
        'long_span_candidate': long_span_candidate,
        'adequate_for_board_a_training_support': adequate_for_training and native_cross_timeframe,
        'blockers': ';'.join(blockers) if blockers else 'none',
    })

providers_required = ['yfinance/YF','IBKR','Binance','Bybit','Kraken','TradingViewRemix/TVR']
providers_present = sorted([r['provider'] for r in rows])
adequate = [r for r in rows if r['adequate_for_board_a_training_support']]
long_span = [r for r in rows if r['long_span_candidate']]
result = {
    'schema_version': 'long_horizon_provider_window_inventory_v1',
    'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
    'source_roots': [str(source_175651), str(source_191941)],
    'providers_required': providers_required,
    'providers_present': providers_present,
    'providers_present_count': len(providers_present),
    'provider_rows': rows,
    'long_span_candidate_count': len(long_span),
    'adequate_for_board_a_training_support_count': len(adequate),
    'native_cross_timeframe_provider_fetch_count': sum(1 for r in rows if r['native_cross_timeframe_provider_fetch']),
    'smoke_191941': {
        'commands_total': smoke.get('commands_total'),
        'commands_exit_zero': smoke.get('commands_exit_zero'),
        'accepted_95_contexts_added': smoke.get('accepted_95_contexts_added'),
        'promotion_allowed': smoke.get('promotion_allowed'),
        'trade_usable': smoke.get('trade_usable'),
    },
    'promotion_allowed': False,
    'trade_usable': False,
    'update_goal': False,
    'accepted_95_contexts_added': 0,
    'gate': 'fail_closed_inventory_only_native_cross_timeframe_and_full_chain_missing',
}
json_path = out_dir / 'long_horizon_provider_window_inventory_v1.json'
json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
fieldnames = list(rows[0].keys())
with (out_dir / 'provider_window_inventory_v1.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(rows)
with (out_dir / 'gate_matrix_v1.csv').open('w', newline='') as f:
    fields = ['gate','status','evidence']
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    gates = [
        ('six_provider_rows_present', len(providers_present)==6, f'{len(providers_present)}/6'),
        ('long_span_candidates_present', len(long_span)>0, f'{len(long_span)}/6'),
        ('native_cross_timeframe_provider_fetch_present', result['native_cross_timeframe_provider_fetch_count']>0, f"{result['native_cross_timeframe_provider_fetch_count']}/6"),
        ('all_rows_training_adequate', len(adequate)==6, f'{len(adequate)}/6'),
        ('accepted_95_contexts_added', False, '0'),
        ('promotion_allowed', False, 'false'),
    ]
    for gate, ok, evidence in gates:
        w.writerow({'gate': gate, 'status': 'pass' if ok else 'fail_closed', 'evidence': evidence})
md = ['# Long-Horizon Provider Window Inventory v1', '', f'- Providers present: `{len(providers_present)}/6`.', f'- Long-span candidates by span/rows: `{len(long_span)}/6`.', f'- Native provider cross-timeframe fetches: `{result["native_cross_timeframe_provider_fetch_count"]}/6`.', f'- Board A training-adequate rows: `{len(adequate)}/6`.', '- Accepted 95 contexts added: `0`.', '- Promotion allowed: `false`.', '', '## Provider Rows', '', '| Provider | Market | Span Days | 1h Rows | 4h Rows | 1d Rows | Long Span | Native XTF | Training Adequate | Blockers |', '|---|---|---:|---:|---:|---:|---|---|---|---|']
for r in rows:
    md.append(f"| `{r['provider']}` | `{r['market']}` | {r['actual_span_days']:.1f} | {r['source_rows_1h']} | {r['derived_rows_4h']} | {r['derived_rows_1d']} | {r['long_span_candidate']} | {r['native_cross_timeframe_provider_fetch']} | {r['adequate_for_board_a_training_support']} | `{r['blockers']}` |")
md += ['', '## Interpretation', '', '- This is inventory only, not a confidence packet.', '- Existing artifacts contain six provider-backed rows, but 4h/1d are derived from 1h artifacts rather than provider-native cross-timeframe fetches.', '- Only yfinance/YF and Binance look long-span enough by current rows/span heuristics; the rest remain short-window or low-row evidence.', '- No full provider/AQ -> Pre-Bayes/BBN -> CatBoost/path-ranker -> execution-tree rerun was performed in this slice.', '- Board A remains fail-closed.']
(out_dir / 'long_horizon_provider_window_inventory_v1.md').write_text('\n'.join(md) + '\n')
assert len(providers_present)==6
assert result['promotion_allowed'] is False
assert result['accepted_95_contexts_added']==0
(Path('docs/experiments/actionable-regime-confidence/runs/20260512T193511+0800-codex-long-horizon-provider-window-inventory-v1/checks/long_horizon_provider_window_inventory_v1_assertions.out')).write_text('\n'.join([
    f"PASS providers_present={len(providers_present)}_of_6",
    f"PASS long_span_candidates={len(long_span)}_of_6",
    f"FAIL_CLOSED native_cross_timeframe_provider_fetch={result['native_cross_timeframe_provider_fetch_count']}_of_6",
    f"FAIL_CLOSED training_adequate_rows={len(adequate)}_of_6",
    'FAIL_CLOSED accepted_95_contexts_added=0',
    'PASS promotion_allowed=false',
]) + '\n')
print(json_path)
