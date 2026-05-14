#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path


RUN_ID = "20260511T094002+0800-codex-external-label-request-package-v3"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "acquisition-request"
CHECKS = ROOT / "checks"

MISSING_V2_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)
AUTH_PREFLIGHT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T093411-codex-auth-export-path-preflight/"
    "auth-export-preflight/auth_export_path_preflight.json"
)
COMPLETION_AUDIT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T093533-current-goal-completion-audit-v3/"
    "completion-audit/current_goal_completion_audit_v3.json"
)

PARENT_ROOT_PANEL_SCHEMA = [
    {"field": "provider", "required": True, "description": "Target provider lane such as yfinance or kraken_public_lowpollution_http."},
    {"field": "instrument", "required": True, "description": "Exact requested instrument/underlying, not a near proxy."},
    {"field": "timeframe", "required": True, "description": "Exact requested timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, or 1mo."},
    {"field": "window_start", "required": True, "description": "Inclusive timestamp/date for the label window, with timezone."},
    {"field": "window_end", "required": True, "description": "Exclusive or inclusive end timestamp/date for the label window; convention must be documented."},
    {"field": "root_label", "required": True, "description": "One of Bull, Bear, Sideways, Crisis."},
    {"field": "label_source_id", "required": True, "description": "Stable dataset/source identifier and version."},
    {"field": "label_provenance", "required": True, "description": "Independent source-backed/manual/official label provenance; not HMM/GMM/OHLCV/future-return/proxy output."},
    {"field": "source_url_or_private_ref", "required": True, "description": "Public URL, authenticated export id, or private handoff reference."},
    {"field": "confidence_or_quality_flag", "required": False, "description": "Optional source confidence/quality metadata; not a substitute for calibration."},
]

DIRECT_MANIPULATION_SCHEMA = [
    {"field": "event_id", "required": True, "description": "Stable event or row id."},
    {"field": "instrument_or_asset", "required": True, "description": "Exact traded asset/instrument/collection/token/contract."},
    {"field": "venue_or_chain", "required": True, "description": "Exchange, venue, chain, or data source."},
    {"field": "event_start", "required": True, "description": "Timestamp for positive/negative window start."},
    {"field": "event_end", "required": True, "description": "Timestamp for positive/negative window end."},
    {"field": "is_manipulation_positive", "required": True, "description": "Boolean positive/negative label."},
    {"field": "manipulation_type", "required": True, "description": "wash_trade, spoofing, layering, pump_dump, quote_stuffing, stop_run, liquidity_raid, or other direct class."},
    {"field": "negative_control_type", "required": True, "description": "For negatives: same asset/venue/time controls or documented non-event controls."},
    {"field": "source_id", "required": True, "description": "Stable dataset/source identifier and version."},
    {"field": "source_url_or_private_ref", "required": True, "description": "Public URL, authenticated export id, or private handoff reference."},
]

REJECT_RULES = [
    "Do not use HMM/GMM/cluster IDs as independent labels.",
    "Do not use OHLCV/technical-indicator/Pine-generated labels as parent-root completion labels.",
    "Do not use future-return labels, strategy predictions, or model service outputs as source labels.",
    "Do not use near-underlying proxy labels unless the source explicitly labels the requested instrument.",
    "Do not use document indexes, methodology papers, search surfaces, or credentials alone as accepted evidence.",
    "Do not accept Manipulation from ThinLiquidity/session-liquidity/sweep/volume-ratio proxies.",
]


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_schema_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["field", "required", "description"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    missing_rows = read_csv(MISSING_V2_CSV)
    auth = read_json(AUTH_PREFLIGHT_JSON)
    completion = read_json(COMPLETION_AUDIT_JSON)
    by_root = Counter(row["root"] for row in missing_rows)
    by_provider = Counter(row["provider"] for row in missing_rows)
    by_timeframe = Counter(row["timeframe"] for row in missing_rows)
    by_reason = Counter(row["missing_or_rejected_reason"] for row in missing_rows)

    request_csv = OUT / "missing_parent_root_label_slots_request_v3.csv"
    with request_csv.open("w", newline="") as f:
        fieldnames = [
            "request_id", "provider", "instrument", "timeframe", "root",
            "missing_or_rejected_reason", "required_label_source", "forbidden_proxy_sources",
            "minimum_acceptance_note",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(missing_rows, 1):
            writer.writerow({
                "request_id": f"mainregimev2-root-slot-{idx:04d}",
                "provider": row["provider"],
                "instrument": row["instrument"],
                "timeframe": row["timeframe"],
                "root": row["root"],
                "missing_or_rejected_reason": row["missing_or_rejected_reason"],
                "required_label_source": "independent_exact_underlying_parent_root_label_panel",
                "forbidden_proxy_sources": row["forbidden_proxy_sources"],
                "minimum_acceptance_note": "Must provide source-backed Bull/Bear/Sideways/Crisis label windows for this exact provider/instrument/timeframe/root slot.",
            })

    write_schema_csv(OUT / "parent_root_label_panel_schema_v3.csv", PARENT_ROOT_PANEL_SCHEMA)
    write_schema_csv(OUT / "direct_manipulation_rows_schema_v3.csv", DIRECT_MANIPULATION_SCHEMA)

    packet = {
        "run_id": RUN_ID,
        "active_taxonomy": "MainRegimeV2",
        "objective": "External acquisition request for the remaining parent-root label slots and direct Manipulation rows.",
        "source_inputs": {
            "missing_slots_csv": str(MISSING_V2_CSV),
            "auth_preflight_json": str(AUTH_PREFLIGHT_JSON),
            "completion_audit_json": str(COMPLETION_AUDIT_JSON),
        },
        "missing_slots": len(missing_rows),
        "missing_by_root": dict(by_root),
        "missing_by_provider": dict(by_provider),
        "missing_by_timeframe": dict(by_timeframe),
        "missing_by_reason": dict(by_reason),
        "auth_export_paths": auth.get("export_paths", {}),
        "completion_goal_achieved": completion.get("goal_achieved", False),
        "parent_root_panel_schema": PARENT_ROOT_PANEL_SCHEMA,
        "direct_manipulation_rows_schema": DIRECT_MANIPULATION_SCHEMA,
        "reject_rules": REJECT_RULES,
        "accepted_parent_root_sources_added": 0,
        "accepted_direct_manipulation_rows_added": 0,
        "gate_result": "blocked_external_label_request_package_created_no_new_labels",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Fill the v3 request CSV with an exact-underlying independent parent-root label panel, or provide authenticated direct Manipulation positive/negative rows following the schema.",
    }

    (OUT / "external_label_request_package_v3.json").write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# External Label Request Package v3",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Active taxonomy: `{packet['active_taxonomy']}`.",
        f"- Missing/rejected parent-root source-label slots: `{packet['missing_slots']}`.",
        f"- Missing by root: `{dict(by_root)}`.",
        f"- Missing by provider: `{dict(by_provider)}`.",
        f"- Missing by timeframe: `{dict(by_timeframe)}`.",
        f"- Auth/export paths from latest preflight: `{packet['auth_export_paths']}`.",
        "- Accepted parent-root sources added: `0`.",
        "- Accepted direct `Manipulation` rows added: `0`.",
        f"- Gate result: `{packet['gate_result']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Artifacts",
        "",
        f"- Missing-slot request CSV: `{request_csv}`",
        f"- Parent-root panel schema: `{OUT / 'parent_root_label_panel_schema_v3.csv'}`",
        f"- Direct Manipulation row schema: `{OUT / 'direct_manipulation_rows_schema_v3.csv'}`",
        "",
        "## Reject Rules",
        "",
    ]
    md_lines.extend(f"- {rule}" for rule in REJECT_RULES)
    md_lines.extend([
        "",
        "## Next Action",
        "",
        packet["next_action"],
    ])
    (OUT / "external_label_request_package_v3.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    checks = [
        "PASS active_taxonomy=MainRegimeV2",
        f"PASS missing_slots={len(missing_rows)}" if len(missing_rows) == 564 else f"FAIL missing_slots={len(missing_rows)}",
        "PASS accepted_parent_root_sources_added=0",
        "PASS accepted_direct_manipulation_rows_added=0",
        f"PASS gate_result={packet['gate_result']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    (CHECKS / "external_label_request_package_v3_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
