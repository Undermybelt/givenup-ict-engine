#!/usr/bin/env python3
"""Bounded source screen for independent normal controls for Oystacher R6 rows."""

from __future__ import annotations

import csv
import json
import ssl
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-oystacher-independent-normal-control-screen"
CHECKS = RUN_ROOT / "checks"

SOURCE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    / "r6-oystacher-exhibit-a-row-materialization"
)
POLICY_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1/"
    / "r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json"
)
PROVENANCE = SOURCE_RUN / "isolated-oystacher-exhibit-a-intake/provenance_manifest.json"
PARSED = SOURCE_RUN / "oystacher_exhibit_a_parsed_order_rows_v1.csv"
POSITIVE = SOURCE_RUN / "isolated-oystacher-exhibit-a-intake/positive_spoofing_layering_rows.csv"
NEGATIVE = SOURCE_RUN / "isolated-oystacher-exhibit-a-intake/matched_negative_normal_activity_rows.csv"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def probe_url(url: str) -> dict[str, Any]:
    context = ssl.create_default_context()
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "ict-engine-board-a-source-screen/1.0",
            "Range": "bytes=0-65535",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20, context=context) as response:
            payload = response.read(65536)
            text = payload.decode("utf-8", errors="ignore").lower()
            headers = dict(response.headers.items())
            return {
                "url": url,
                "ok": True,
                "status": response.status,
                "content_type": headers.get("Content-Type", ""),
                "content_length": headers.get("Content-Length", ""),
                "bytes_read": len(payload),
                "mentions_normal": "normal" in text,
                "mentions_control": "control" in text,
                "mentions_non_manipulation": "non-manipulation" in text
                or "non manipulation" in text,
                "mentions_spoof": "spoof" in text,
                "mentions_flip": "flip" in text,
                "error": "",
            }
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
        return {
            "url": url,
            "ok": False,
            "status": None,
            "content_type": "",
            "content_length": "",
            "bytes_read": 0,
            "mentions_normal": False,
            "mentions_control": False,
            "mentions_non_manipulation": False,
            "mentions_spoof": False,
            "mentions_flip": False,
            "error": repr(exc),
        }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_RUN.read_text(encoding="utf-8")) if POLICY_RUN.exists() else {}
    parsed_rows = read_csv_rows(PARSED)
    positive_rows = read_csv_rows(POSITIVE)
    negative_rows = read_csv_rows(NEGATIVE)

    parsed_side_counts = Counter(row.get("side_type", "") for row in parsed_rows)
    positive_label_counts = Counter(row.get("label", "") for row in positive_rows)
    negative_label_counts = Counter(row.get("label", "") for row in negative_rows)
    negative_activity_counts = Counter(
        "same_exhibit_flip"
        if "marks this row as FLIP" in row.get("activity_description", "")
        else "other"
        for row in negative_rows
    )
    parsed_non_spoof_flip = [
        row for row in parsed_rows if row.get("side_type") not in {"SPOOF", "FLIP"}
    ]
    independent_normal_rows = [
        row
        for row in parsed_rows
        if row.get("side_type", "").lower()
        in {"normal", "control", "non-manipulation", "non_manipulation"}
    ]

    urls = [
        provenance["source_pdf_url"],
        provenance["courtlistener_docket_url"],
        provenance["cftc_complaint_url_without_exhibit_a"],
        provenance["cftc_press_url"],
    ]
    probes = [probe_url(url) for url in urls]

    independent_normal_controls_found = bool(independent_normal_rows)
    all_negative_candidates_are_flip = (
        len(negative_rows) > 0
        and negative_activity_counts.get("same_exhibit_flip", 0) == len(negative_rows)
    )
    gate_result = (
        "r6_oystacher_independent_normal_control_screen_v1="
        "no_independent_owner_approved_normal_controls_found"
    )
    if independent_normal_controls_found:
        gate_result = (
            "r6_oystacher_independent_normal_control_screen_v1="
            "independent_normal_rows_found_policy_review_required"
        )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_materialization_root": str(SOURCE_RUN.relative_to(REPO)),
        "policy_review": str(POLICY_RUN.relative_to(REPO)) if POLICY_RUN.exists() else None,
        "row_counts": {
            "parsed_order_rows": len(parsed_rows),
            "positive_spoof_candidates": len(positive_rows),
            "matched_control_candidates": len(negative_rows),
            "parsed_side_counts": dict(parsed_side_counts),
            "positive_label_counts": dict(positive_label_counts),
            "negative_label_counts": dict(negative_label_counts),
            "negative_activity_counts": dict(negative_activity_counts),
            "parsed_side_types_not_spoof_or_flip": len(parsed_non_spoof_flip),
            "independent_normal_rows": len(independent_normal_rows),
        },
        "public_source_probes": probes,
        "decision": {
            "gate_result": gate_result,
            "independent_normal_controls_found": independent_normal_controls_found,
            "all_negative_candidates_are_same_exhibit_flip": all_negative_candidates_are_flip,
            "flip_rows_accepted_as_matched_normal_controls": False,
            "canonical_live_intake_merge_approved": False,
            "rerun_downstream_chain": False,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": True,
            "trade_usable": False,
        },
        "next_action": (
            "Source independent owner-approved normal controls for the Oystacher SPOOF positives, "
            "or get explicit board/user approval for same-exhibit FLIP rows as controls and public "
            "RECAP/PACER provenance; only after that merge through the shared lock and rerun the "
            "direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/"
            "path-ranking, and execution-tree chain."
        ),
    }

    json_path = OUT / "r6_oystacher_independent_normal_control_screen_v1.json"
    report_path = OUT / "r6_oystacher_independent_normal_control_screen_v1.md"
    probe_csv = OUT / "r6_oystacher_public_source_probe_v1.csv"
    evidence_csv = OUT / "r6_oystacher_normal_control_evidence_v1.csv"
    assertions_path = CHECKS / "r6_oystacher_independent_normal_control_screen_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(
        probe_csv,
        probes,
        [
            "url",
            "ok",
            "status",
            "content_type",
            "content_length",
            "bytes_read",
            "mentions_normal",
            "mentions_control",
            "mentions_non_manipulation",
            "mentions_spoof",
            "mentions_flip",
            "error",
        ],
    )
    evidence_rows = [
        {
            "evidence": "parsed_side_counts",
            "value": json.dumps(dict(parsed_side_counts), sort_keys=True),
            "decision": "only SPOOF/FLIP labels are materialized from Exhibit A"
            if not parsed_non_spoof_flip
            else "unexpected side labels require review",
        },
        {
            "evidence": "negative_activity_counts",
            "value": json.dumps(dict(negative_activity_counts), sort_keys=True),
            "decision": "candidate controls are same-exhibit FLIP rows",
        },
        {
            "evidence": "independent_normal_rows",
            "value": str(len(independent_normal_rows)),
            "decision": "no independent normal rows found in materialized Exhibit A",
        },
    ]
    write_csv(evidence_csv, evidence_rows, ["evidence", "value", "decision"])

    lines = [
        "# R6 Oystacher Independent Normal-Control Screen v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Source materialization root: `{SOURCE_RUN.relative_to(REPO)}`.",
        f"- Parsed order rows: `{len(parsed_rows)}`; side counts: `{dict(parsed_side_counts)}`.",
        f"- Positive SPOOF candidates: `{len(positive_rows)}`.",
        f"- Same-exhibit FLIP candidate controls: `{len(negative_rows)}`.",
        f"- Independent normal rows found in materialized Exhibit A: `{len(independent_normal_rows)}`.",
        f"- Public source probes sent: `{len(probes)}`.",
        f"- Gate result: `{gate_result}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Result",
        "",
        "The materialized Exhibit A rows contain only `SPOOF` and `FLIP` side labels. No independent source-owned normal/non-manipulation rows were found in the materialized row set. The existing `matched_negative_normal_activity_rows.csv` remains a same-exhibit `FLIP` candidate set and is still blocked without explicit control-policy approval.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Public source probe CSV: `{probe_csv.relative_to(REPO)}`",
        f"- Normal-control evidence CSV: `{evidence_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Next",
        "",
        result["next_action"],
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={gate_result}",
                f"parsed_order_rows={len(parsed_rows)}",
                f"positive_spoof_candidates={len(positive_rows)}",
                f"same_exhibit_flip_candidate_controls={len(negative_rows)}",
                f"independent_normal_controls_found={str(independent_normal_controls_found).lower()}",
                f"all_negative_candidates_are_same_exhibit_flip={str(all_negative_candidates_are_flip).lower()}",
                "canonical_live_intake_merge_approved=false",
                "accepted_rows_added=0",
                "update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "report": str(report_path.relative_to(REPO))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
