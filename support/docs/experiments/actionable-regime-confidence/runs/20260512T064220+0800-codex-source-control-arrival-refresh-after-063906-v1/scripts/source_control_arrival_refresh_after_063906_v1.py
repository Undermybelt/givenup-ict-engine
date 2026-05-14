#!/usr/bin/env python3
"""Read-only source/control arrival refresh after the 063906 Board A audit."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "source-control-arrival-refresh-after-063906-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

REQUIRED_ROOTS = [
    {
        "id": "r6_owner_export",
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "acceptance_note": "verifier-native R6 owner/export rows plus valid controls",
    },
    {
        "id": "r3_native_subhour",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "acceptance_note": "verifier-native R3 MainRegimeV2 labels; TSIE proxy root is quarantined",
    },
    {
        "id": "r5_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "acceptance_note": "source-owned post-2026-01-30 R5 recency rows",
    },
]

KNOWN_DISPATCH_FILES = [
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cme_group_owner_export_v5_dispatch_v1.eml",
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cboe_cfe_owner_export_v5_dispatch_v1.eml",
]

LOCAL_DROP_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
]

EXACT_LOCAL_DROP_NAMES = {
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
    "stock_market_regimes_2026_extension.csv",
    "source_panel_recency_provenance.json",
    "native_subhour_source_label_rows.csv",
    "native_subhour_source_label_provenance.json",
}

FUZZY_LOCAL_DROP_TERMS = (
    "owner-export",
    "owner_export",
    "cme-datamine",
    "cme_datamine",
    "cboe-datashop",
    "cboe_datashop",
    "source-control",
    "source_control",
    "support-id",
    "support_id",
    "export-id",
    "export_id",
    "license-id",
    "license_id",
    "ticket-id",
    "ticket_id",
    "mainregimev2",
    "recency-extension",
    "recency_extension",
)

SKIP_PARTS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    "target",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def board_hash() -> str:
    return sha256_file(BOARD)


def file_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "present": False}
    return {
        "path": str(path),
        "present": True,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path) if path.is_file() and path.stat().st_size < 10_000_000 else "",
    }


def load_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return {"json_error": str(exc)}


def inspect_required_roots() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in REQUIRED_ROOTS:
        root = spec["root"]
        present_files = sorted(p.name for p in root.iterdir()) if root.exists() else []
        missing = [name for name in spec["required_files"] if name not in present_files]
        provenance = {}
        accepted = False
        quarantine_reason = ""
        if spec["id"] == "r3_native_subhour" and not missing:
            provenance = load_json(root / "native_subhour_source_label_provenance.json")
            run_id = str(provenance.get("run_id", "")).lower()
            dataset_id = str(provenance.get("dataset_id", "")).lower()
            limitations = " ".join(str(x).lower() for x in provenance.get("limitations", []))
            if "tsie" in run_id or "tsie" in dataset_id or "crisis" in limitations:
                quarantine_reason = "tsie_proxy_policy_quarantined"
            else:
                accepted = True
        elif spec["id"] == "r6_owner_export" and not missing:
            provenance = load_json(root / "provenance_manifest.json")
            text = json.dumps(provenance, sort_keys=True).lower()
            accepted = all(token in text for token in ("ticket", "export", "source"))
            if not accepted:
                quarantine_reason = "missing_ticket_export_or_source_provenance"
        elif spec["id"] == "r5_recency_extension" and not missing:
            provenance = load_json(root / "source_panel_recency_provenance.json")
            text = json.dumps(provenance, sort_keys=True).lower()
            accepted = "2026-01-30" in text and ("post" in text or "after" in text)
            if not accepted:
                quarantine_reason = "missing_post_cutoff_source_provenance"

        rows.append(
            {
                "id": spec["id"],
                "root": str(root),
                "exists": root.exists(),
                "present_files": ";".join(present_files),
                "missing_files": ";".join(missing),
                "required_files_complete": not missing,
                "accepted_required_unlock": accepted,
                "quarantine_reason": quarantine_reason,
                "acceptance_note": spec["acceptance_note"],
                "provenance_run_id": provenance.get("run_id", "") if provenance else "",
                "provenance_dataset_id": provenance.get("dataset_id", "") if provenance else "",
            }
        )
    return rows


def inspect_dispatch_files() -> list[dict[str, object]]:
    rows = []
    for path in KNOWN_DISPATCH_FILES:
        row = file_summary(path)
        row["asset_kind"] = "v5_dispatch_draft"
        row["sent_evidence"] = False
        row["mentions_ticket_export_fields"] = False
        if path.exists():
            text = path.read_text(errors="replace")
            row["to"] = next((line[3:].strip() for line in text.splitlines() if line.lower().startswith("to:")), "")
            row["has_from"] = any(line.lower().startswith("from:") for line in text.splitlines())
            lower = text.lower()
            row["mentions_ticket_export_fields"] = any(
                marker in lower for marker in ("ticket id", "support id", "export id", "order id")
            )
            row["sent_evidence"] = any(
                marker in lower
                for marker in (
                    "x-operator-sent: true",
                    "x-vendor-ticket:",
                    "x-export-id:",
                    "x-support-id:",
                    "x-order-id:",
                )
            )
        rows.append(row)
    return rows


def scan_local_drops(max_depth: int = 5, max_hits: int = 200) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for root in LOCAL_DROP_ROOTS:
        if not root.exists():
            continue
        root_depth = len(root.parts)
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            dirs[:] = [d for d in dirs if d not in SKIP_PARTS and depth < max_depth]
            if any(part in SKIP_PARTS for part in current_path.parts):
                continue
            for name in files:
                lower = name.lower()
                if name in EXACT_LOCAL_DROP_NAMES or any(term in lower for term in FUZZY_LOCAL_DROP_TERMS):
                    path = current_path / name
                    hits.append(
                        {
                            "path": str(path),
                            "name": name,
                            "size_bytes": path.stat().st_size if path.exists() else 0,
                        }
                    )
                    if len(hits) >= max_hits:
                        return hits
    return hits


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    roots = inspect_required_roots()
    dispatch = inspect_dispatch_files()
    local_hits = scan_local_drops()
    r6 = next(row for row in roots if row["id"] == "r6_owner_export")
    r3 = next(row for row in roots if row["id"] == "r3_native_subhour")
    r5 = next(row for row in roots if row["id"] == "r5_recency_extension")

    valid_required_unlock = any(bool(row["accepted_required_unlock"]) for row in roots)
    gate_result = "source_control_arrival_refresh_after_063906_v1=no_valid_required_unlock_no_downstream"

    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": board_hash(),
        "gate_result": gate_result,
        "required_roots": roots,
        "dispatch_assets": dispatch,
        "local_drop_hits": local_hits,
        "decision": {
            "r6_owner_export_root_exists": r6["exists"],
            "r6_valid_required_unlock": r6["accepted_required_unlock"],
            "r3_native_subhour_root_exists": r3["exists"],
            "r3_valid_required_unlock": r3["accepted_required_unlock"],
            "r3_quarantine_reason": r3["quarantine_reason"],
            "r5_recency_root_exists": r5["exists"],
            "r5_valid_required_unlock": r5["accepted_required_unlock"],
            "valid_required_unlock": valid_required_unlock,
            "external_dispatch_sent_evidence": any(bool(row.get("sent_evidence")) for row in dispatch),
            "local_drop_hits_count": len(local_hits),
            "canonical_merge_allowed_now": False,
            "downstream_rerun_allowed_now": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export rows "
            "with valid controls, source-owned R5 recency rows, verifier-native R3 MainRegimeV2 labels, "
            "or a genuinely new accepted cross-timeframe MainRegimeV2 source export before rerunning "
            "direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, "
            "BBN, CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    json_path = OUT_DIR / "source_control_arrival_refresh_after_063906_v1.json"
    md_path = OUT_DIR / "source_control_arrival_refresh_after_063906_v1.md"
    roots_csv = OUT_DIR / "source_control_arrival_refresh_required_roots_v1.csv"
    dispatch_csv = OUT_DIR / "source_control_arrival_refresh_dispatch_assets_v1.csv"
    local_csv = OUT_DIR / "source_control_arrival_refresh_local_hits_v1.csv"
    assertions_path = CHECK_DIR / "source_control_arrival_refresh_after_063906_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(roots_csv, roots)
    write_csv(dispatch_csv, dispatch)
    write_csv(local_csv, local_hits or [{"path": "", "name": "", "size_bytes": 0}])

    md_lines = [
        "# Source/Control Arrival Refresh After 063906 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "Read-only arrival refresh after the `063906` current-objective audit. This packet checks required R6/R3/R5 roots, existing v5 dispatch drafts, and bounded local drop locations. It does not send mail, use a vendor portal, approve TSIE, mutate target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- R6 owner-export root exists: `{r6['exists']}`; accepted unlock: `{r6['accepted_required_unlock']}`.",
        f"- R3 native-subhour root exists: `{r3['exists']}`; accepted unlock: `{r3['accepted_required_unlock']}`; quarantine reason: `{r3['quarantine_reason']}`.",
        f"- R5 recency root exists: `{r5['exists']}`; accepted unlock: `{r5['accepted_required_unlock']}`.",
        f"- v5 dispatch drafts present: `{sum(1 for row in dispatch if row.get('present'))}/{len(dispatch)}`; sent/ticket/export evidence in drafts: `{result['decision']['external_dispatch_sent_evidence']}`.",
        f"- Bounded local drop hits: `{len(local_hits)}`.",
        "",
        "## Decision",
        "",
        "No valid required root is unlocked. The R3 path is present but remains TSIE-quarantined; R6 owner/export rows are absent; R5 recency rows are absent; no local ticket/export/license/order/support artifact was accepted. Canonical merge and downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion remain blocked.",
        "",
        "Accounting:",
        "",
        "- valid required unlock: `false`",
        "- canonical merge allowed now: `false`",
        "- downstream rerun allowed now: `false`",
        "- strict full objective: `false`",
        "- trade usable: `false`",
        "- `update_goal=false`",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Required roots CSV: `{roots_csv.relative_to(REPO)}`",
        f"- Dispatch assets CSV: `{dispatch_csv.relative_to(REPO)}`",
        f"- Local hits CSV: `{local_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Next",
        "",
        result["next_action"],
        "",
    ]
    md_path.write_text("\n".join(md_lines))

    assertions = [
        f"gate_result={gate_result}",
        f"r6_owner_export_root_exists={str(r6['exists']).lower()}",
        f"r6_valid_required_unlock={str(r6['accepted_required_unlock']).lower()}",
        f"r3_native_subhour_root_exists={str(r3['exists']).lower()}",
        f"r3_valid_required_unlock={str(r3['accepted_required_unlock']).lower()}",
        f"r3_quarantine_reason={r3['quarantine_reason']}",
        f"r5_recency_root_exists={str(r5['exists']).lower()}",
        f"r5_valid_required_unlock={str(r5['accepted_required_unlock']).lower()}",
        f"valid_required_unlock={str(valid_required_unlock).lower()}",
        "canonical_merge_allowed_now=false",
        "downstream_rerun_allowed_now=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
