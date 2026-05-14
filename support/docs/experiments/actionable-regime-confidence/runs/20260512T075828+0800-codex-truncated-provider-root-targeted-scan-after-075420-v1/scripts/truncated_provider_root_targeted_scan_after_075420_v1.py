#!/usr/bin/env python3
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RUN_ROOT = Path(os.environ["RUN_ROOT"])
OUT = RUN_ROOT / "truncated-provider-root-targeted-scan-after-075420-v1"
CHECKS = RUN_ROOT / "checks"
ROOTS = [
    "/Users/thrill3r/tradingview-mcp",
    "/Users/thrill3r/Library/Application Support/TradingView",
    "/tmp/ict-engine-board-a-064259-runtime-v1",
]
REQUIRED_NAMES = {
    "native_subhour_source_label_rows.csv",
    "stock_market_regimes_2026_extension.csv",
    "main_regime_v2_source_panel_rows.csv",
    "source_panel_recency_extension.csv",
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
    "r6_oystacher_approval_decision_package_v1.json.valid",
}
SCHEMA_TERMS = [
    "main_regime_v2_label",
    "MainRegimeV2",
    "source_confidence",
    "source_panel",
    "matched_negative_group_id",
    "direct_label",
    "order_lifecycle",
    "Crisis",
]
TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".txt", ".yaml", ".yml", ".toml"}
MAX_BYTES = 2_000_000
rows = []
summary = {
    "run_id": RUN_ROOT.name,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "roots": ROOTS,
    "files_scanned": 0,
    "required_filename_hits": 0,
    "schema_hits": 0,
    "read_errors": 0,
    "oversize_skips": 0,
    "r6_owner_export_complete": False,
    "r5_source_panel_candidate": False,
    "r3_crisis_capable_candidate": False,
    "valid_required_root_unlock": False,
    "source_control_evidence_acquired": False,
    "accepted_rows_added": 0,
    "canonical_merge": False,
    "selected_data_autoquant_promotion": False,
    "downstream_promotion_rerun": False,
    "strict_full_objective": False,
    "trade_usable": False,
    "update_goal": False,
}
required_by_root = {root: set() for root in ROOTS}
schema_by_root = {root: set() for root in ROOTS}

for root in ROOTS:
    rp = Path(root)
    if not rp.exists():
        rows.append({"root": root, "path": "", "kind": "root_absent", "matches": "", "header": "", "size": "0", "mtime": ""})
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "target", "__pycache__"}]
        for name in filenames:
            p = Path(dirpath) / name
            summary["files_scanned"] += 1
            try:
                st = p.stat()
            except OSError:
                summary["read_errors"] += 1
                continue
            lower_name = name.lower()
            required_hit = name in REQUIRED_NAMES or lower_name in {x.lower() for x in REQUIRED_NAMES}
            schema_matches = []
            header = ""
            if p.suffix.lower() in TEXT_SUFFIXES and st.st_size <= MAX_BYTES:
                try:
                    with p.open("r", encoding="utf-8", errors="ignore") as fh:
                        sample = fh.read(8192)
                    header = sample.splitlines()[0][:240] if sample.splitlines() else ""
                    schema_matches = [term for term in SCHEMA_TERMS if term in sample]
                except OSError:
                    summary["read_errors"] += 1
            elif p.suffix.lower() in TEXT_SUFFIXES and st.st_size > MAX_BYTES:
                summary["oversize_skips"] += 1
            if required_hit or schema_matches:
                kind = []
                if required_hit:
                    kind.append("required_filename_hit")
                    required_by_root[root].add(name)
                if schema_matches:
                    kind.append("schema_term_hit")
                    schema_by_root[root].update(schema_matches)
                rows.append({
                    "root": root,
                    "path": str(p),
                    "kind": "+".join(kind),
                    "matches": "|".join(([name] if required_hit else []) + schema_matches),
                    "header": header,
                    "size": str(st.st_size),
                    "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                })

summary["required_filename_hits"] = sum(1 for row in rows if "required_filename_hit" in row["kind"])
summary["schema_hits"] = sum(1 for row in rows if "schema_term_hit" in row["kind"])
# Conservative gate: only exact complete required files can unlock R6; schema terms alone are inventory.
for root, names in required_by_root.items():
    r6 = {"direct_manipulation_positive_rows.csv", "direct_manipulation_matched_controls.csv", "direct_manipulation_provenance.json"}
    if r6.issubset(names):
        summary["r6_owner_export_complete"] = True
    if any(n in names for n in {"stock_market_regimes_2026_extension.csv", "main_regime_v2_source_panel_rows.csv", "source_panel_recency_extension.csv"}):
        summary["r5_source_panel_candidate"] = True
    if "native_subhour_source_label_rows.csv" in names and "Crisis" in schema_by_root[root]:
        summary["r3_crisis_capable_candidate"] = True

summary["valid_required_root_unlock"] = False
summary["source_control_evidence_acquired"] = False
csv_path = OUT / "truncated_provider_root_targeted_scan_after_075420_v1.csv"
with csv_path.open("w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["root", "path", "kind", "matches", "header", "size", "mtime"])
    writer.writeheader()
    writer.writerows(rows)
json_path = OUT / "truncated_provider_root_targeted_scan_after_075420_v1.json"
json_path.write_text(json.dumps({"summary": summary, "required_by_root": {k: sorted(v) for k,v in required_by_root.items()}, "schema_by_root": {k: sorted(v) for k,v in schema_by_root.items()}}, indent=2), encoding="utf-8")
report = OUT / "truncated_provider_root_targeted_scan_after_075420_v1.md"
report.write_text("\n".join([
    "# Truncated Provider Root Targeted Scan After 075420 v1",
    "",
    f"Run id: `{RUN_ROOT.name}`",
    "",
    "Gate result: `truncated_provider_root_targeted_scan_after_075420_v1=no_valid_required_root_no_unlock`",
    "",
    "## Scope",
    "",
    "Targeted scan of the three provider/cache roots that were truncated in `075420`: TradingView MCP, TradingView application cache, and `/tmp/ict-engine-board-a-064259-runtime-v1`. This scan checks exact R3/R5/R6 filenames and source/control schema terms only. It does not mutate target roots, derive labels, run calibration, run AutoQuant, run downstream promotion, or call `update_goal`.",
    "",
    "## Readback",
    "",
    f"- Files scanned: `{summary['files_scanned']}`.",
    f"- Required filename hits: `{summary['required_filename_hits']}`.",
    f"- Schema term hits: `{summary['schema_hits']}`.",
    f"- Oversize text skips: `{summary['oversize_skips']}`.",
    f"- Read errors: `{summary['read_errors']}`.",
    f"- R6 owner/export complete: `{summary['r6_owner_export_complete']}`.",
    f"- R5 source-panel candidate: `{summary['r5_source_panel_candidate']}`.",
    f"- R3 Crisis-capable native-subhour candidate: `{summary['r3_crisis_capable_candidate']}`.",
    "",
    "## Decision",
    "",
    "No valid required source/control root is unlocked by the previously truncated provider roots. Any schema-term hits are inventory only unless a later manual review proves source-owned post-cutoff `MainRegimeV2` labels, verifier-native Crisis-capable R3 rows, or R6 owner-export positives with matched controls and provenance.",
    "",
    "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
    "",
    "## Next",
    "",
    "Continue source/control acquisition only before any split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
    "",
]), encoding="utf-8")
checks = CHECKS / "truncated_provider_root_targeted_scan_after_075420_v1_assertions.out"
checks.write_text("\n".join([
    "gate_result=truncated_provider_root_targeted_scan_after_075420_v1=no_valid_required_root_no_unlock",
    f"files_scanned={summary['files_scanned']}",
    f"required_filename_hits={summary['required_filename_hits']}",
    f"schema_hits={summary['schema_hits']}",
    f"r6_owner_export_complete={str(summary['r6_owner_export_complete']).lower()}",
    f"r5_source_panel_candidate={str(summary['r5_source_panel_candidate']).lower()}",
    f"r3_crisis_capable_candidate={str(summary['r3_crisis_capable_candidate']).lower()}",
    "accepted_rows_added=0",
    "valid_required_root_unlock=false",
    "source_control_evidence_acquired=false",
    "canonical_merge=false",
    "selected_data_autoquant_promotion=false",
    "downstream_promotion_rerun=false",
    "strict_full_objective=false",
    "trade_usable=false",
    "update_goal=false",
    "",
]), encoding="utf-8")
print(report)
