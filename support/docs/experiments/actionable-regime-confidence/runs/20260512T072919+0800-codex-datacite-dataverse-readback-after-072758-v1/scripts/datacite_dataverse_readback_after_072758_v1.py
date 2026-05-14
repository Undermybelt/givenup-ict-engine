import csv, json, pathlib, re
src = pathlib.Path('docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1')
root = pathlib.Path(__file__).resolve().parents[1]
outdir = root / 'datacite-dataverse-readback-after-072758-v1'
cmd = src / 'command-output'
required_terms = [
    'mainregimev2',
    'native_subhour_source_label_rows',
    'stock_market_regimes_2026_extension',
    'direct_manipulation_positive_rows',
    'direct_manipulation_matched_controls',
    '3red trading',
    'oystacher',
]
rows = []
failed = 0
required_title_hits = []
for path in sorted(cmd.glob('*.json')):
    exit_path = path.with_suffix('.exit')
    exit_code = exit_path.read_text().strip() if exit_path.exists() else 'missing'
    if exit_code != '0':
        failed += 1
    data = json.loads(path.read_text())
    source = 'datacite' if path.name.startswith('datacite_') else 'dataverse'
    slug = path.name.removeprefix(source + '_').removesuffix('.json')
    items = []
    total = 0
    if source == 'datacite':
        items = data.get('data', [])[:5]
        total = len(data.get('data', []))
        for item in items:
            attrs = item.get('attributes', {})
            title = '; '.join(t.get('title', '') for t in attrs.get('titles', [])[:2])
            ident = attrs.get('doi', '')
            year = attrs.get('publicationYear', '')
            hay = f'{title} {ident}'.lower()
            if any(term in hay for term in required_terms):
                required_title_hits.append({'source': source, 'query': slug, 'title': title, 'identifier': ident})
            rows.append({'source': source, 'query': slug, 'exit_code': exit_code, 'reported_total': total, 'top_title': title, 'identifier': ident, 'published': year})
    else:
        d = data.get('data', {})
        items = d.get('items', [])[:5]
        total = d.get('total_count', 0)
        for item in items:
            title = item.get('name', '')
            ident = item.get('global_id') or item.get('url', '')
            published = item.get('published_at', '')
            hay = f'{title} {ident}'.lower()
            if any(term in hay for term in required_terms):
                required_title_hits.append({'source': source, 'query': slug, 'title': title, 'identifier': ident})
            rows.append({'source': source, 'query': slug, 'exit_code': exit_code, 'reported_total': total, 'top_title': title, 'identifier': ident, 'published': published})
exact_zero_queries = []
for slug in ['mainregimev2', 'native_subhour_source_label_rows', 'stock_market_regimes_2026_extension']:
    dc = json.loads((cmd / f'datacite_{slug}.json').read_text()).get('data', [])
    dv = json.loads((cmd / f'dataverse_{slug}.json').read_text()).get('data', {}).get('items', [])
    exact_zero_queries.append({'query': slug, 'datacite_rows': len(dc), 'dataverse_rows': len(dv)})
summary = {
    'run_id': root.name,
    'source_run_id': src.name,
    'gate_result': 'datacite_dataverse_readback_after_072758_v1=no_required_source_control_unlock',
    'source_run_present': src.exists(),
    'json_files_checked': len(list(cmd.glob('*.json'))),
    'failed_query_count': failed,
    'top_rows_scanned': len(rows),
    'required_title_hits': required_title_hits,
    'exact_zero_queries': exact_zero_queries,
    'accepted_rows_added': 0,
    'valid_required_root_unlock': False,
    'source_control_evidence_acquired': False,
    'r6_owner_export_unlock': False,
    'r5_recency_unlock': False,
    'r3_native_subhour_unlock': False,
    'canonical_merge': False,
    'downstream_promotion_rerun': False,
    'strict_full_objective': False,
    'trade_usable': False,
    'update_goal': False,
}
(outdir / 'datacite_dataverse_readback_after_072758_v1.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
with (outdir / 'datacite_dataverse_readback_after_072758_v1.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['source','query','exit_code','reported_total','top_title','identifier','published'])
    w.writeheader(); w.writerows(rows)
md = f"""# DataCite Dataverse Readback After 072758 v1

Run id: `{root.name}`
Source run id: `{src.name}`

Gate result: `{summary['gate_result']}`

## Scope

Settled readback of the raw `072758` DataCite/Dataverse source-route probe. This packet reads existing command outputs only; it does not rerun DataCite or Dataverse search, mutate target roots, approve proxy labels, run direct verifier, run split calibration, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- JSON files checked: `{summary['json_files_checked']}`.
- Failed query count: `{summary['failed_query_count']}`.
- Top rows scanned across source APIs: `{summary['top_rows_scanned']}`.
- Required title/identifier hits in scanned top rows: `{len(required_title_hits)}`.
- Exact target queries checked: `MainRegimeV2`, `native_subhour_source_label_rows`, and `stock_market_regimes_2026_extension`; DataCite and Dataverse returned zero top-level rows/items for all three.
- Broad Dataverse/Oystacher/3Red/direct-manipulation searches returned unrelated public repository context in top rows, not required R6 owner/export positives, matched normal controls, provenance, source-panel R5 rows, or verifier-native R3 labels.

## Decision

The `072758` readback supplies no accepted source/control unlock. Accepted rows added `0`, R6 owner/export unlock false, R5 recency unlock false, R3 native-subhour unlock false, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `{outdir / 'datacite_dataverse_readback_after_072758_v1.json'}`
- CSV: `{outdir / 'datacite_dataverse_readback_after_072758_v1.csv'}`
- Assertions: `{root / 'checks' / 'datacite_dataverse_readback_after_072758_v1_assertions.out'}`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export.
"""
(outdir / 'datacite_dataverse_readback_after_072758_v1.md').write_text(md)
assert failed == 0, failed
assert len(required_title_hits) == 0, required_title_hits
assert all(x['datacite_rows'] == 0 and x['dataverse_rows'] == 0 for x in exact_zero_queries), exact_zero_queries
(root / 'checks' / 'datacite_dataverse_readback_after_072758_v1_assertions.out').write_text('PASS datacite_dataverse_readback_after_072758_v1 no_required_source_control_unlock\n')
print(outdir / 'datacite_dataverse_readback_after_072758_v1.md')
