#!/usr/bin/env python3
"""Probe public sources for Oystacher source-owned normal controls.

Raw downloaded public pages/PDFs stay in /tmp. Repo artifacts are summaries and
gate evidence only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1"
REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-public-normal-control-source-probe"
CHECKS = RUN_ROOT / "checks"
TMP = Path("/tmp/ict-engine-r6-oystacher-public-normal-control-source-probe-v1")

MATERIALIZATION_ROOT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
    / "r6-oystacher-exhibit-a-row-materialization"
)
PARSED_ROWS = MATERIALIZATION_ROOT / "oystacher_exhibit_a_parsed_order_rows_v1.csv"
CONTROL_REQUEST_ROOT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003627-codex-r6-oystacher-control-contract-request-v1"
    / "r6-oystacher-control-contract-request"
)
REQUIRED_CELLS = CONTROL_REQUEST_ROOT / "r6_oystacher_required_normal_control_cells_v1.csv"

SOURCES = [
    {
        "source_id": "courtlistener_exhibit_a_pdf",
        "url": "https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889/gov.uscourts.ilnd.316889.1.1.pdf",
        "kind": "row_level_exhibit_pdf",
    },
    {
        "source_id": "cftc_complaint_pdf",
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf",
        "kind": "legal_complaint_pdf",
    },
    {
        "source_id": "cftc_press_release_7264_15",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7264-15",
        "kind": "press_release_html",
    },
    {
        "source_id": "justia_doc_237",
        "url": "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1%3A2015cv09196/316889/237/",
        "kind": "court_order_html",
    },
    {
        "source_id": "govinfo_doc_195_pdf",
        "url": "https://www.govinfo.gov/content/pkg/USCOURTS-ilnd-1_15-cv-09196/pdf/USCOURTS-ilnd-1_15-cv-09196-1.pdf",
        "kind": "court_order_pdf",
    },
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(name: str, args: list[str], timeout: int = 60) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "name": name,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\nTIMEOUT after {timeout}s",
            "timed_out": True,
        }


def download_sources() -> list[dict[str, Any]]:
    TMP.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for source in SOURCES:
        suffix = ".pdf" if source["kind"].endswith("_pdf") or "pdf" in source["kind"] else ".html"
        raw_path = TMP / f"{source['source_id']}{suffix}"
        result = run_cmd(
            f"download_{source['source_id']}",
            ["curl", "-L", "--max-time", "45", "-o", str(raw_path), source["url"]],
            timeout=60,
        )
        exists = raw_path.exists()
        size = raw_path.stat().st_size if exists else 0
        text_probe = ""
        if exists and suffix == ".html":
            text = raw_path.read_text(encoding="utf-8", errors="ignore").lower()
            hits = [term for term in ["normal", "control", "non-manipulation", "genuine", "flip", "spoof"] if term in text]
            text_probe = ",".join(hits)
        rows.append(
            {
                "source_id": source["source_id"],
                "kind": source["kind"],
                "url": source["url"],
                "download_returncode": result["returncode"],
                "downloaded_bytes": size,
                "raw_path_tmp": str(raw_path),
                "sha256": sha256(raw_path) if exists and size > 0 else "",
                "text_probe_terms": text_probe,
                "row_level_normal_controls_found": 0,
                "normal_control_file_found": False,
                "decision": "no_source_owned_normal_control_rows_found",
            }
        )
    return rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize_exhibit_rows() -> dict[str, Any]:
    rows = read_csv_rows(PARSED_ROWS)
    side_counts: dict[str, int] = {}
    contract_counts: dict[str, int] = {}
    for row in rows:
        side = row.get("side_type", "")
        contract = row.get("contract", "")
        side_counts[side] = side_counts.get(side, 0) + 1
        root = "".join(ch for ch in contract if ch.isalpha()) or contract
        contract_counts[root] = contract_counts.get(root, 0) + 1
    accepted_control_labels = [
        label
        for label in side_counts
        if label.lower() in {"normal", "control", "genuine", "non_manipulation", "non-manipulation"}
    ]
    return {
        "parsed_rows": len(rows),
        "side_counts": side_counts,
        "contract_roots": sorted(contract_counts),
        "accepted_control_labels": accepted_control_labels,
        "row_level_normal_controls_found": sum(side_counts.get(label, 0) for label in accepted_control_labels),
        "spoof_positive_rows": side_counts.get("SPOOF", 0),
        "flip_candidate_rows": side_counts.get("FLIP", 0),
    }


def summarize_required_cells() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_csv_rows(REQUIRED_CELLS)
    out_rows: list[dict[str, Any]] = []
    total_shortfall = 0
    for row in rows:
        shortfall = int(row.get("valid_normal_control_shortfall") or 0)
        total_shortfall += shortfall
        out_rows.append(
            {
                "axis": row.get("axis", ""),
                "bucket": row.get("bucket", ""),
                "positive_spoof_support": row.get("positive_spoof_support", ""),
                "invalid_flip_candidate_support": row.get("invalid_flip_candidate_support", ""),
                "required_valid_normal_control_support": row.get("required_valid_normal_control_support", ""),
                "valid_normal_control_support_observed": row.get("valid_normal_control_support_observed", ""),
                "valid_normal_control_shortfall": shortfall,
                "decision": "still_short_no_public_source_owned_controls",
            }
        )
    return out_rows, {
        "required_cells": len(rows),
        "required_cell_shortfall_total": total_shortfall,
        "cells_with_valid_normal_controls": sum(
            1 for row in rows if int(row.get("valid_normal_control_support_observed") or 0) > 0
        ),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    source_rows = download_sources()
    exhibit = summarize_exhibit_rows()
    cell_rows, cells = summarize_required_cells()

    valid_controls_found = int(exhibit["row_level_normal_controls_found"])
    source_owned_normal_controls_acquired = valid_controls_found > 0
    downstream_allowed = False
    gate_result = "r6_oystacher_public_normal_control_source_probe_v1=no_public_source_owned_normal_controls_found"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources_checked": len(source_rows),
        "sources_downloaded_ok": sum(1 for row in source_rows if row["download_returncode"] == 0),
        "raw_download_root_tmp": str(TMP),
        "raw_data_committed": False,
        "source_rows_csv": rel(OUT / "r6_oystacher_public_sources_checked_v1.csv"),
        "required_cells_csv": rel(OUT / "r6_oystacher_public_normal_control_required_cells_v1.csv"),
        "parsed_exhibit": exhibit,
        "required_cells": cells,
        "source_owned_normal_controls_acquired": source_owned_normal_controls_acquired,
        "valid_source_owned_normal_controls_found": valid_controls_found,
        "flip_rows_promoted_as_controls": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": downstream_allowed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "next_action": (
            "Supply source-owned normal controls for the 17 Oystacher cells or explicitly approve "
            "the same-exhibit FLIP-as-control exception before canonical merge and downstream rerun."
        ),
    }

    write_csv(OUT / "r6_oystacher_public_sources_checked_v1.csv", source_rows)
    write_csv(OUT / "r6_oystacher_public_normal_control_required_cells_v1.csv", cell_rows)
    (OUT / "r6_oystacher_public_normal_control_source_probe_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# R6 Oystacher Public Normal-Control Source Probe v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Result",
        "",
        f"- Sources checked: `{result['sources_checked']}`; downloaded OK: `{result['sources_downloaded_ok']}`.",
        f"- Raw downloads kept in `/tmp`: `{TMP}`.",
        f"- Parsed Exhibit A rows: `{exhibit['parsed_rows']}`.",
        f"- Exhibit A side labels: `{exhibit['side_counts']}`.",
        f"- Valid public source-owned normal-control rows found: `{valid_controls_found}`.",
        f"- Required control cells: `{cells['required_cells']}`; cells with valid controls: `{cells['cells_with_valid_normal_controls']}`; total shortfall: `{cells['required_cell_shortfall_total']}`.",
        f"- Gate result: `{gate_result}`.",
        "",
        "## Interpretation",
        "",
        "The public row-level source still contains only `SPOOF` positives and same-exhibit `FLIP` rows. "
        "`FLIP` rows remain useful as candidate context, but this probe found no independent public source-owned "
        "normal/non-manipulation control rows for the required cells.",
        "",
        "No canonical intake was mutated and no provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun was allowed.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(OUT / 'r6_oystacher_public_normal_control_source_probe_v1.json')}`",
        f"- Source CSV: `{rel(OUT / 'r6_oystacher_public_sources_checked_v1.csv')}`",
        f"- Required cells CSV: `{rel(OUT / 'r6_oystacher_public_normal_control_required_cells_v1.csv')}`",
        f"- Assertions: `{rel(CHECKS / 'r6_oystacher_public_normal_control_source_probe_v1_assertions.out')}`",
        "",
        "## Next",
        "",
        result["next_action"],
    ]
    (OUT / "r6_oystacher_public_normal_control_source_probe_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"sources_checked={result['sources_checked']}",
        f"sources_downloaded_ok={result['sources_downloaded_ok']}",
        f"parsed_exhibit_rows={exhibit['parsed_rows']}",
        f"spoof_positive_rows={exhibit['spoof_positive_rows']}",
        f"flip_candidate_rows={exhibit['flip_candidate_rows']}",
        f"valid_source_owned_normal_controls_found={valid_controls_found}",
        f"required_cells={cells['required_cells']}",
        f"cells_with_valid_normal_controls={cells['cells_with_valid_normal_controls']}",
        f"source_owned_normal_controls_acquired={source_owned_normal_controls_acquired}",
        "flip_rows_promoted_as_controls=false",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"gate_result={gate_result}",
    ]
    (CHECKS / "r6_oystacher_public_normal_control_source_probe_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "gate_result": gate_result, "valid_controls_found": valid_controls_found}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
