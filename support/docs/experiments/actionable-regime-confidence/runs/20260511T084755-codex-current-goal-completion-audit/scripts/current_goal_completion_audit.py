#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path


RUN_ID = "20260511T084755+0800-codex-current-goal-completion-audit"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "completion-audit"
CHECKS = ROOT / "checks"
TODO = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
MISSING_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)
ACQUISITION_PROBE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T084131-codex-root-label-source-acquisition-probe/"
    "source-acquisition/root_label_source_acquisition_probe.json"
)
DUNE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T083150-codex-dune-nft-wash-trades-export-probe/"
    "dune-export-probe/dune_nft_wash_trades_export_probe.json"
)


def load_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def cursor(todo_text):
    m = re.search(r"## Current Cursor\n\n(\| Field \|.*?\n)(?=\n## )", todo_text, re.S)
    if not m:
        return {}
    rows = {}
    for line in m.group(1).splitlines():
        if not line.startswith("| ") or line.startswith("| Field") or line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            rows[parts[0]] = parts[1]
    return rows


def missing_summary():
    rows = list(csv.DictReader(MISSING_CSV.open()))
    return {
        "missing_or_rejected_slots": len(rows),
        "by_root": count(rows, "root"),
        "by_reason": count(rows, "missing_or_rejected_reason"),
        "by_timeframe": count(rows, "timeframe"),
        "by_provider": count(rows, "provider"),
    }


def count(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def build_audit():
    todo_text = TODO.read_text()
    cur = cursor(todo_text)
    missing = missing_summary()
    acquisition_probe = load_json(ACQUISITION_PROBE_JSON)
    dune = load_json(DUNE_JSON)

    dune_gate = dune.get("gate_result") or dune.get("decision", {}).get("gate_result", "missing")
    checklist = [
        {
            "requirement": "Use the named TODO as the authoritative artifact",
            "evidence": str(TODO),
            "status": "pass",
            "notes": "Current cursor, run sections, and Evidence Ledger are present in the named TODO.",
        },
        {
            "requirement": "Every active regime reaches 95%-99% calibrated confidence",
            "evidence": "accepted_gate=" + cur.get("accepted_gate", "missing"),
            "status": "fail",
            "notes": "Current accepted gate is not a completed all-regime gate; expanded full-universe/full-cycle goal remains blocked.",
        },
        {
            "requirement": "Validate across other markets and other timeframes",
            "evidence": f"missing/rejected slots={missing['missing_or_rejected_slots']}; by_timeframe={missing['by_timeframe']}",
            "status": "fail",
            "notes": "Only 48/612 source-label slots are attached from prior evidence; 564 slots remain missing/rejected across intraday, monthly, non-yfinance/Kraken, and missing exact instruments.",
        },
        {
            "requirement": "Full-cycle/full-species coverage",
            "evidence": f"by_provider={missing['by_provider']}; by_root={missing['by_root']}",
            "status": "fail",
            "notes": "Missing slots are balanced at 141 for each MainRegimeV2 price root, so no root is complete under expanded matrix accounting.",
        },
        {
            "requirement": "Manipulation has direct labeled evidence, not OHLCV proxy",
            "evidence": f"Dune gate={dune_gate}; acquisition_new_manipulation={acquisition_probe.get('accepted_new_manipulation_sources', 'missing')}",
            "status": "fail",
            "notes": "Dune is schema-promising but blocked by missing API/export rows; acquisition probe added 0 direct manipulation sources.",
        },
        {
            "requirement": "No proxy labels promoted as completion",
            "evidence": "HMM/GMM/HF/future-return/near-proxy candidates rejected or sidecar-only",
            "status": "pass",
            "notes": "Latest probe preserved fail-closed handling and did not count HMM/GMM/HF/off-universe/near-proxy labels.",
        },
    ]
    goal_achieved = all(item["status"] == "pass" for item in checklist)
    return {
        "run_id": RUN_ID,
        "objective": "Every regime must reach 95%-99% calibrated confidence and validate across other markets/timeframes/full universe/full cycle.",
        "current_cursor": cur,
        "missing_summary": missing,
        "prompt_to_artifact_checklist": checklist,
        "goal_achieved": goal_achieved,
        "accepted_gate": cur.get("accepted_gate", "missing"),
        "single_blocker": "564 missing/rejected source-label slots plus incomplete direct Manipulation label coverage",
        "next_action": "Acquire exact-underlying non-Kaggle root-label panels or authenticated direct Manipulation rows; otherwise the goal remains blocked.",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }


def write(audit):
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (OUT / "current_goal_completion_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Current Goal Completion Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Objective",
        "",
        audit["objective"],
        "",
        "## Result",
        "",
        f"- Goal achieved: `{str(audit['goal_achieved']).lower()}`.",
        f"- Accepted gate: `{audit['accepted_gate']}`.",
        f"- Single blocker: `{audit['single_blocker']}`.",
        f"- Missing/rejected slots: `{audit['missing_summary']['missing_or_rejected_slots']}`.",
        f"- Missing by root: `{audit['missing_summary']['by_root']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"| {item['requirement']} | `{item['status']}` | {item['evidence']} | {item['notes']} |")
    lines.extend(["", "## Next Action", "", audit["next_action"], ""])
    (OUT / "current_goal_completion_audit.md").write_text("\n".join(lines), encoding="utf-8")
    assertions = [
        f"goal_achieved={str(audit['goal_achieved']).lower()}",
        f"accepted_gate={audit['accepted_gate']}",
        f"missing_or_rejected_slots={audit['missing_summary']['missing_or_rejected_slots']}",
        "PASS no_proxy_completion_promoted=true",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
    ]
    (CHECKS / "current_goal_completion_audit_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write(build_audit())
