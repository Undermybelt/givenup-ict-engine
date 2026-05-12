import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/thrill3r/Downloads/Tomac')
RUN = Path(__file__).resolve().parents[1]
SLICE = RUN / 'local-databento-multi-futures-nonqualifying-source-screen-v1'
CHECKS = RUN / 'checks'
TARGETS = [
    ('ES', 'es future 2021-2025'),
    ('6E', 'eur future 2015-2025'),
    ('GC', 'gc future 2021-2025'),
    ('NQ', 'nq future 2021-2025'),
    ('YM', 'ym future 2021-2025'),
]

def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def ns_to_date(ns):
    return datetime.fromtimestamp(int(ns) / 1_000_000_000, tz=timezone.utc).date().isoformat()

def load_json(path: Path):
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)

rows = []
for symbol_key, dirname in TARGETS:
    d = ROOT / dirname
    metadata_path = d / 'metadata.json'
    manifest_path = d / 'manifest.json'
    metadata = load_json(metadata_path) or {}
    manifest = load_json(manifest_path) or {}
    query = metadata.get('query', {})
    local_data_files = sorted(p.name for p in d.glob('*.ohlcv-1m.csv'))
    manifest_data_files = [x.get('filename') for x in manifest.get('files', []) if str(x.get('filename', '')).endswith('.ohlcv-1m.csv')]
    manifest_data_hashes = [str(x.get('hash', '')).replace('sha256:', '') for x in manifest.get('files', []) if str(x.get('filename', '')).endswith('.ohlcv-1m.csv')]
    rows.append({
        'symbol_key': symbol_key,
        'source_dir': str(d),
        'dataset': query.get('dataset'),
        'schema': query.get('schema'),
        'symbols': ';'.join(query.get('symbols', [])),
        'stype_in': query.get('stype_in'),
        'stype_out': query.get('stype_out'),
        'start': ns_to_date(query.get('start')) if query.get('start') else None,
        'end': ns_to_date(query.get('end')) if query.get('end') else None,
        'encoding': query.get('encoding'),
        'delivery': (metadata.get('customizations') or {}).get('delivery'),
        'local_data_files': ';'.join(local_data_files),
        'local_data_file_count': len(local_data_files),
        'manifest_data_files': ';'.join(manifest_data_files),
        'manifest_data_hashes': ';'.join(manifest_data_hashes),
        'manifest_sha256': sha256(manifest_path),
        'metadata_sha256': sha256(metadata_path),
        'schema_is_ohlcv_1m': query.get('schema') == 'ohlcv-1m',
        'dataset_is_glbx_mdp3': query.get('dataset') == 'GLBX.MDP3',
        'has_local_ohlcv_file': bool(local_data_files),
        'qualifies_r6_owner_controls': False,
        'qualifies_flip_control_approval': False,
        'qualifies_r3_native_subhour_source_labels': False,
        'qualifies_r5_recency_extension': False,
        'accepted_rows_added': 0,
        'new_confidence_gate': False,
        'canonical_merge_allowed': False,
        'downstream_promotion_rerun_allowed': False,
        'strict_full_objective_achieved': False,
        'update_goal': False,
    })

csv_path = SLICE / 'local_databento_multi_futures_nonqualifying_source_screen_v1.csv'
with csv_path.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

payload = {
    'run_id': RUN.name,
    'gate_result': 'local_databento_multi_futures_nonqualifying_source_screen_v1=databento_ohlcv_multi_futures_found_not_r6_r3_r5_qualifying_no_promotion',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_root': str(ROOT),
    'rows': rows,
    'summary': {
        'symbols': [r['symbol_key'] for r in rows],
        'datasets': sorted(set(r['dataset'] for r in rows if r['dataset'])),
        'schemas': sorted(set(r['schema'] for r in rows if r['schema'])),
        'local_ohlcv_file_count': sum(r['local_data_file_count'] for r in rows),
        'qualifying_r6_owner_controls': False,
        'qualifying_r3_source_labels': False,
        'qualifying_r5_recency_extension': False,
    },
    'promotion': {
        'accepted_rows_added': 0,
        'new_confidence_gate': False,
        'canonical_merge_allowed': False,
        'downstream_rerun_allowed': False,
        'strict_full_objective_achieved': False,
        'update_goal': False,
        'trade_usable': False,
    },
    'non_mutations': {
        'runtime_code_changed': False,
        'shared_intake_mutated': False,
        'r3_r5_r6_roots_mutated': False,
        'thresholds_relaxed': False,
        'raw_data_committed': False,
    },
    'decision': 'Local Databento futures breadth is real OHLCV provider evidence only. It lacks owner/control order-lifecycle rows, explicit FLIP approval, accepted source labels, and per-regime qualifying-condition labels, so it cannot unlock canonical merge or downstream promotion.'
}
json_path = SLICE / 'local_databento_multi_futures_nonqualifying_source_screen_v1.json'
json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')

md = f"""# Local Databento Multi-Futures Nonqualifying Source Screen v1

Run id: `{RUN.name}`

Gate result: `{payload['gate_result']}`

Source root: `{ROOT}`

Readback:
- Symbols screened: `{', '.join(payload['summary']['symbols'])}`
- Dataset(s): `{', '.join(payload['summary']['datasets'])}`
- Schema(s): `{', '.join(payload['summary']['schemas'])}`
- Local OHLCV files found: `{payload['summary']['local_ohlcv_file_count']}`
- CSV artifact: `{csv_path}`

Decision:
- This is real local Databento/Tomac futures breadth for ES, NQ, YM, 6E, and GC.
- It is OHLCV `1m` bar evidence, not CME Market Depth / Market by Order / full order-lifecycle evidence.
- It does not provide source-owned normal controls, explicit same-exhibit `FLIP` control approval, accepted source labels, or per-regime qualifying-condition labels.
- It does not close R6 owner/control, R3 native-subhour source-label, or R5 source-panel recency-extension gates.
- It does not justify canonical merge or downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion.

Promotion guards:
- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion rerun allowed: `false`
- Strict full objective achieved: `false`
- `update_goal=false`
- Runtime code changed: `false`
- Shared intake mutated: `false`
- R3/R5/R6 roots mutated: `false`
- Thresholds relaxed: `false`
- Raw data committed: `false`
- Trade usable: `false`

Next:
- Preserve the Current Cursor next action for R6. Continue only from licensed owner/operator R6 controls, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` labels before canonical merge and downstream promotion.
"""
(SLICE / 'local_databento_multi_futures_nonqualifying_source_screen_v1.md').write_text(md)

checks = []
def check(name, cond):
    checks.append((name, bool(cond)))

check('all_targets_scanned', len(rows) == len(TARGETS))
check('all_dataset_glbx_mdp3', all(r['dataset_is_glbx_mdp3'] for r in rows))
check('all_schema_ohlcv_1m', all(r['schema_is_ohlcv_1m'] for r in rows))
check('all_have_local_ohlcv_file', all(r['has_local_ohlcv_file'] for r in rows))
check('not_r6_owner_controls', not any(r['qualifies_r6_owner_controls'] for r in rows))
check('not_flip_approval', not any(r['qualifies_flip_control_approval'] for r in rows))
check('not_r3_source_labels', not any(r['qualifies_r3_native_subhour_source_labels'] for r in rows))
check('not_r5_recency_extension', not any(r['qualifies_r5_recency_extension'] for r in rows))
check('accepted_rows_added_0', payload['promotion']['accepted_rows_added'] == 0)
check('canonical_merge_allowed_false', payload['promotion']['canonical_merge_allowed'] is False)
check('downstream_promotion_rerun_allowed_false', payload['promotion']['downstream_rerun_allowed'] is False)
check('strict_full_objective_achieved_false', payload['promotion']['strict_full_objective_achieved'] is False)
check('update_goal_false', payload['promotion']['update_goal'] is False)
check('raw_data_not_committed', payload['non_mutations']['raw_data_committed'] is False)

assertion_path = CHECKS / 'local_databento_multi_futures_nonqualifying_source_screen_v1_assertions.out'
assertion_path.write_text('\n'.join(f'{name}={"PASS" if ok else "FAIL"}' for name, ok in checks) + '\n')
if not all(ok for _, ok in checks):
    raise SystemExit(1)
print(RUN)
