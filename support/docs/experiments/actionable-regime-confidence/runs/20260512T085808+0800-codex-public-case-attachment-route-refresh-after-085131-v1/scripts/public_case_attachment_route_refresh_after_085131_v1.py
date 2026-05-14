#!/usr/bin/env python3
"""Public case attachment route refresh after 085131.

This is a source/control acquisition readback only. It records current public
case/source routes and keeps promotion gates closed unless row-level positives,
matched normal controls, and provenance are actually present.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "public-case-attachment-route-refresh-after-085131-v1"
CHECKS_DIR = RUN_ROOT / "checks"

BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

RUN_ID = "20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1"
GATE = (
    "public_case_attachment_route_refresh_after_085131_v1="
    "public_case_narrative_only_no_row_level_source_control_no_unlock"
)

ROOTS = {
    "r6_owner_export_tmp": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r6_owner_export_private_tmp": Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_tmp": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r5_recency_private_tmp": Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour_tmp": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r3_native_subhour_private_tmp": Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
    "missing_085042_run_root": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085042+0800-codex-current-objective-audit-after-083703-v1",
}

CURRENT_R6_REQUIRED = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

LEGACY_R6_REQUIRED = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]

PUBLIC_ROUTES = [
    {
        "route_id": "cftc_release_7264_15",
        "owner": "CFTC",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7264-15",
        "route_type": "official_public_case_context",
        "observed_signal": (
            "Official CFTC release confirms alleged spoofing/layering across "
            "CME, NYMEX, COMEX, and CFE products with flip/cancel pattern context."
        ),
        "limitation": "Narrative case context only; no row-level positives or matched normal controls.",
        "gate_disposition": "no_source_control_unlock",
    },
    {
        "route_id": "cftc_order_122016",
        "owner": "CFTC",
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfoystacherorder122016.pdf",
        "route_type": "official_public_case_order",
        "observed_signal": (
            "Administrative order text discusses book imbalance, trade-side/cancel-side behavior, "
            "and product coverage."
        ),
        "limitation": "PDF/order text only; no verifier-native row export package or matched controls.",
        "gate_disposition": "no_source_control_unlock",
    },
    {
        "route_id": "justia_doc_195",
        "owner": "N.D. Ill. / Justia mirror",
        "url": "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1%3A2015cv09196/316889/195/",
        "route_type": "public_court_order_context",
        "observed_signal": (
            "Public opinion says data illustrated order imbalance, cancellation speed, iceberg usage, "
            "fill/cancellation rates, and market reaction categories."
        ),
        "limitation": "Court opinion summarizes data categories; underlying row-level data/exhibits are not exposed.",
        "gate_disposition": "no_source_control_unlock",
    },
    {
        "route_id": "justia_doc_237",
        "owner": "N.D. Ill. / Justia mirror",
        "url": "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1%3A2015cv09196/316889/237/",
        "route_type": "public_court_order_context",
        "observed_signal": (
            "Public opinion confirms CFTC allegations rely on examples, flip behavior, cancellation speeds, "
            "and market reaction summaries."
        ),
        "limitation": "Opinion-level data description only; no source-owned positive/control rows.",
        "gate_disposition": "no_source_control_unlock",
    },
    {
        "route_id": "cftc_release_7515_16",
        "owner": "CFTC",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7515-16",
        "route_type": "official_public_case_resolution",
        "observed_signal": "Official settlement/resolution route for the Oystacher matter.",
        "limitation": "Resolution context only; no row-level source/control package acquired locally.",
        "gate_disposition": "no_source_control_unlock",
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def board_hash(path: Path) -> str:
    return sha256_file(path) if path.exists() else ""


def root_status(name: str, root: Path) -> dict:
    files = []
    if root.exists():
        for item in sorted(root.rglob("*")):
            if item.is_file():
                try:
                    files.append(
                        {
                            "path": str(item),
                            "size": item.stat().st_size,
                            "mtime": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        }
                    )
                except OSError:
                    files.append({"path": str(item), "size": None, "mtime": None})
    current_present = [name for name in CURRENT_R6_REQUIRED if (root / name).is_file()]
    legacy_present = [name for name in LEGACY_R6_REQUIRED if (root / name).is_file()]
    return {
        "name": name,
        "path": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "sample_files": files[:20],
        "current_r6_required_present": current_present,
        "legacy_r6_required_present": legacy_present,
        "current_r6_complete": len(current_present) == len(CURRENT_R6_REQUIRED),
        "legacy_r6_complete": len(legacy_present) == len(LEGACY_R6_REQUIRED),
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone(timedelta(hours=8))).isoformat()
    root_rows = [root_status(name, path) for name, path in ROOTS.items()]

    r6_owner_export_unlock = any(
        row["current_r6_complete"] or row["legacy_r6_complete"]
        for row in root_rows
        if row["name"].startswith("r6_owner_export")
    )
    r5_recency_unlock = any(
        row["exists"] and row["file_count"] > 0
        for row in root_rows
        if row["name"].startswith("r5_recency")
    )
    r3_native_subhour_present = any(
        row["exists"] and row["file_count"] > 0
        for row in root_rows
        if row["name"].startswith("r3_native_subhour")
    )
    missing_085042_run_root_present = next(
        row["exists"] for row in root_rows if row["name"] == "missing_085042_run_root"
    )

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "generated_at": generated_at,
        "board_a_sha256_before_artifact": board_hash(BOARD_A),
        "board_b_sha256_before_artifact": board_hash(BOARD_B),
        "public_routes_checked": len(PUBLIC_ROUTES),
        "row_level_positive_rows_acquired": False,
        "matched_normal_controls_acquired": False,
        "ticket_export_license_provenance_present": False,
        "r6_owner_export_unlock": r6_owner_export_unlock,
        "r5_recency_unlock": r5_recency_unlock,
        "r3_native_subhour_present": r3_native_subhour_present,
        "r3_native_subhour_unlock": False,
        "missing_085042_run_root_present": missing_085042_run_root_present,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    write_csv(
        ARTIFACT_DIR / "public_case_attachment_routes_after_085131_v1.csv",
        PUBLIC_ROUTES,
        [
            "route_id",
            "owner",
            "url",
            "route_type",
            "observed_signal",
            "limitation",
            "gate_disposition",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "source_control_target_roots_after_085131_v1.csv",
        [
            {
                "name": row["name"],
                "path": row["path"],
                "exists": row["exists"],
                "file_count": row["file_count"],
                "current_r6_complete": row["current_r6_complete"],
                "legacy_r6_complete": row["legacy_r6_complete"],
                "sample_files_json": json.dumps(row["sample_files"], sort_keys=True),
            }
            for row in root_rows
        ],
        [
            "name",
            "path",
            "exists",
            "file_count",
            "current_r6_complete",
            "legacy_r6_complete",
            "sample_files_json",
        ],
    )

    json_path = ARTIFACT_DIR / "public_case_attachment_route_refresh_after_085131_v1.json"
    json_path.write_text(
        json.dumps({"summary": summary, "routes": PUBLIC_ROUTES, "root_status": root_rows}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    report = f"""# Public Case Attachment Route Refresh After 085131 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Scope

This source/control acquisition readback records a fresh public case-route probe after `085131`.
It uses official/public CFTC and court-route references to check whether public case attachments
can unlock the R6/R5/R3 source/control gate. It does not mutate target roots, send external
requests, approve same-exhibit `FLIP` controls, select historical data, run selected-data AutoQuant,
run verifier/split calibration, run filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree
promotion, make a trade claim, mark the objective complete, or call `update_goal`.

## Readback

- Board A SHA-256 before artifact: `{summary["board_a_sha256_before_artifact"]}`.
- Board B SHA-256 before artifact: `{summary["board_b_sha256_before_artifact"]}`.
- Public official/court routes checked: `{summary["public_routes_checked"]}`.
- Row-level positive rows acquired: `false`.
- Matched normal controls acquired: `false`.
- Ticket/export/license provenance present: `false`.
- R6 owner/export unlock: `{str(r6_owner_export_unlock).lower()}`.
- R5 recency unlock: `{str(r5_recency_unlock).lower()}`.
- R3 native-subhour present: `{str(r3_native_subhour_present).lower()}`; unlock remains `false`.
- `085042` run root present at this filesystem readback: `{str(missing_085042_run_root_present).lower()}`.

## Route Disposition

The public CFTC and court materials confirm the relevant Oystacher spoofing/layering context,
product coverage, flip/cancel behavior, order-imbalance summaries, and the existence of expert
or complaint data categories. They still do not expose verifier-native row-level positives,
matched normal controls, or source-owned provenance manifests that can satisfy the R6/R5/R3
source/control gate.

## Decision

No public case attachment or official route acquired row-level source/control evidence.
Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false;
explicit user-selected history false; canonical merge false; selected-data AutoQuant promotion false;
downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed
false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/public-case-attachment-route-refresh-after-085131-v1/public_case_attachment_route_refresh_after_085131_v1.json`
- Route CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/public-case-attachment-route-refresh-after-085131-v1/public_case_attachment_routes_after_085131_v1.csv`
- Target-root CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/public-case-attachment-route-refresh-after-085131-v1/source_control_target_roots_after_085131_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/public_case_attachment_route_refresh_after_085131_v1_assertions.out`

## Next

Continue source/control acquisition only. The live unblocker remains an owner-approved/authenticated
FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export with positives and matched
normal controls, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable
R3 native-subhour labels, or explicit same-exhibit `FLIP`-as-control approval before verifier,
split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking,
execution-tree promotion, trade claims, or `update_goal`.
"""
    (ARTIFACT_DIR / "public_case_attachment_route_refresh_after_085131_v1.md").write_text(
        report, encoding="utf-8"
    )

    assertions = [
        f"gate_result={GATE}",
        f"public_routes_checked={len(PUBLIC_ROUTES)}",
        "row_level_positive_rows_acquired=false",
        "matched_normal_controls_acquired=false",
        "ticket_export_license_provenance_present=false",
        f"r6_owner_export_unlock={str(r6_owner_export_unlock).lower()}",
        f"r5_recency_unlock={str(r5_recency_unlock).lower()}",
        f"r3_native_subhour_present={str(r3_native_subhour_present).lower()}",
        "r3_native_subhour_unlock=false",
        f"missing_085042_run_root_present={str(missing_085042_run_root_present).lower()}",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECKS_DIR / "public_case_attachment_route_refresh_after_085131_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
