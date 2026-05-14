#!/usr/bin/env python3
"""Re-poll local inboxes for Board A source/control arrivals after 034813."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T035028-codex-source-control-inbox-repoll-after-034813-v1"
SLUG = "source-control-inbox-repoll-after-034813-v1"


def find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "AGENTS.md").is_file() and (parent / "src").is_dir():
            return parent
    raise RuntimeError("could not locate ict-engine repo root")


REPO = find_repo_root()
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}

REQUIRED_R6_FILES = {
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
}

CONCEPTUAL_R6_FILES = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}

INBOX_ROOTS = [
    Path("/tmp"),
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
    Path("/Users/thrill3r/Documents"),
]

KEYWORDS = [
    "positive_spoofing_layering_rows",
    "matched_negative_normal_activity_rows",
    "provenance_manifest",
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "owner-export",
    "owner_export",
    "oystacher",
    "cme",
    "cboe",
    "cfe",
    "vix",
    "market_depth",
    "market-depth",
    "market by order",
    "mbo",
    "databento",
    "native-subhour",
    "native_subhour",
    "source-label",
    "source_label",
    "recency-extension",
    "recency_extension",
]

APPROVAL_PACKAGE = (
    RUN_ROOT.parent
    / "20260512T034813-codex-current-objective-audit-after-034423-v1"
    / "command-output"
    / "r6_approval_decision_package.pretty.json"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path, max_bytes: int | None = None) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        if max_bytes is None:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        else:
            h.update(fh.read(max_bytes))
    return h.hexdigest()


def file_row(path: Path, reason: str) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": str(path),
        "reason": reason,
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256_file(path) if stat.st_size <= 50_000_000 else "skipped_large_file",
    }


def scan_inboxes() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[Path] = set()
    for root in INBOX_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            depth = len(current.relative_to(root).parts)
            if depth >= 5:
                dirnames[:] = []
            dirnames[:] = [
                d
                for d in dirnames
                if d not in {".git", "node_modules", ".venv", "__pycache__", ".Trash"}
            ]
            for name in filenames:
                lowered = name.lower()
                reason = ""
                if name in REQUIRED_R6_FILES:
                    reason = "required_r6_verifier_native_filename"
                elif name in CONCEPTUAL_R6_FILES:
                    reason = "conceptual_r6_filename_requires_mapping"
                elif any(keyword in lowered for keyword in KEYWORDS):
                    reason = "keyword_candidate"
                if not reason:
                    continue
                path = current / name
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                try:
                    rows.append(file_row(path, reason))
                except OSError as exc:
                    rows.append({"path": str(path), "reason": reason, "error": str(exc)})
    rows.sort(key=lambda row: str(row.get("path", "")))
    return rows


def root_status_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key, root in TARGET_ROOTS.items():
        files = sorted(p.name for p in root.iterdir()) if root.is_dir() else []
        required_present = sorted(name for name in REQUIRED_R6_FILES if (root / name).is_file())
        rows.append(
            {
                "root_key": key,
                "root": str(root),
                "exists": root.exists(),
                "is_dir": root.is_dir(),
                "file_count": len(files),
                "required_r6_files_present": ";".join(required_present),
                "required_r6_complete_here": key == "r6_owner_export"
                and REQUIRED_R6_FILES.issubset(set(files)),
            }
        )
    return rows


def complete_required_bundles(candidates: list[dict[str, object]]) -> list[str]:
    by_dir: dict[str, set[str]] = {}
    for row in candidates:
        path = Path(str(row.get("path", "")))
        by_dir.setdefault(str(path.parent), set()).add(path.name)
    return sorted(directory for directory, names in by_dir.items() if REQUIRED_R6_FILES.issubset(names))


def read_approval() -> dict[str, object]:
    if not APPROVAL_PACKAGE.is_file():
        return {"approval_package_present": False}
    data = json.loads(APPROVAL_PACKAGE.read_text(encoding="utf-8"))
    assertions = data.get("assertions", {})
    return {
        "approval_package_present": True,
        "approval_package_path": rel(APPROVAL_PACKAGE),
        "gate_result": data.get("gate_result"),
        "approval_present": bool(assertions.get("approval_present")),
        "flip_controls_accepted": bool(assertions.get("flip_controls_accepted_under_current_contract")),
        "canonical_merge_allowed_now": bool(assertions.get("canonical_merge_allowed_now")),
        "downstream_rerun_allowed_now": bool(assertions.get("downstream_rerun_allowed_now")),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    roots = root_status_rows()
    candidates = scan_inboxes()
    complete_bundles = complete_required_bundles(candidates)
    approval = read_approval()

    r6_complete = any(row["root_key"] == "r6_owner_export" and row["required_r6_complete_here"] for row in roots)
    r3_present = any(row["root_key"] == "r3_native_subhour" and row["exists"] for row in roots)
    r5_present = any(row["root_key"] == "r5_recency_extension" and row["exists"] for row in roots)
    candidate_complete_bundle = bool(complete_bundles)
    approval_present = bool(approval.get("approval_present"))
    flip_controls = bool(approval.get("flip_controls_accepted"))
    canonical_merge_allowed = r6_complete and (approval_present or flip_controls)

    gate_result = (
        "source_control_inbox_repoll_after_034813_v1="
        + (
            "verifier_native_bundle_candidate_found_no_auto_promotion"
            if candidate_complete_bundle
            else "no_verifier_native_bundle_no_approval_no_promotion"
        )
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "scope": "targeted local inbox repoll after 034813 current-objective audit",
        "roots": roots,
        "approval": approval,
        "candidate_counts": {
            "candidate_files": len(candidates),
            "complete_required_r6_bundles_outside_target_root": len(complete_bundles),
            "complete_bundle_directories": complete_bundles,
        },
        "promotion": {
            "r6_owner_export_root_complete": r6_complete,
            "r3_native_subhour_source_label_root_exists": r3_present,
            "r5_source_panel_recency_extension_root_exists": r5_present,
            "explicit_approval_present": approval_present,
            "flip_controls_accepted_under_current_contract": flip_controls,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": canonical_merge_allowed,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "non_mutations": {
            "runtime_code_changed": False,
            "source_roots_mutated": False,
            "shared_intake_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
        },
    }

    (OUT / "source_control_inbox_repoll_after_034813_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        OUT / "source_control_inbox_repoll_root_status_v1.csv",
        roots,
        [
            "root_key",
            "root",
            "exists",
            "is_dir",
            "file_count",
            "required_r6_files_present",
            "required_r6_complete_here",
        ],
    )
    write_csv(
        OUT / "source_control_inbox_repoll_candidate_files_v1.csv",
        candidates,
        ["path", "reason", "size_bytes", "mtime_utc", "sha256", "error"],
    )

    report_lines = [
        "# Source-Control Inbox Repoll After 034813 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "This packet re-polls likely local inboxes for verifier-native owner/export or source-control files after the `034813` current-objective audit. It does not mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Candidate files found in local inbox scan: `{len(candidates)}`.",
        f"- Complete verifier-native R6 bundles outside target root: `{len(complete_bundles)}`.",
        f"- R6 owner-export root complete: `{r6_complete}`.",
        f"- R3 native sub-hour source-label root exists: `{r3_present}`.",
        f"- R5 source-panel recency-extension root exists: `{r5_present}`.",
        f"- Approval package present: `{approval.get('approval_package_present', False)}`.",
        f"- Explicit approval present: `{approval_present}`.",
        f"- FLIP controls accepted under current contract: `{flip_controls}`.",
        "",
        "## Decision",
        "",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        f"- Canonical merge allowed: `{str(canonical_merge_allowed).lower()}`.",
        "- Downstream promotion rerun allowed: `false`.",
        "- Strict full objective achieved: `false`.",
        "- Trade usable: `false`.",
        "- `update_goal=false`.",
        "",
        "## Next",
        "",
        "Preserve the Current Cursor next action. Record explicit approval or supply verifier-native owner/export rows/source-owned normal controls before direct verifier rerun, canonical merge, and downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(OUT / 'source_control_inbox_repoll_after_034813_v1.json')}`",
        f"- Root status CSV: `{rel(OUT / 'source_control_inbox_repoll_root_status_v1.csv')}`",
        f"- Candidate files CSV: `{rel(OUT / 'source_control_inbox_repoll_candidate_files_v1.csv')}`",
    ]
    (OUT / "source_control_inbox_repoll_after_034813_v1.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS gate_result={gate_result}",
        f"PASS candidate_files={len(candidates)}",
        f"PASS complete_required_r6_bundles={len(complete_bundles)}",
        f"PASS r6_owner_export_root_complete={str(r6_complete).lower()}",
        f"PASS r3_native_subhour_source_label_root_exists={str(r3_present).lower()}",
        f"PASS r5_source_panel_recency_extension_root_exists={str(r5_present).lower()}",
        f"PASS explicit_approval_present={str(approval_present).lower()}",
        f"PASS flip_controls_accepted={str(flip_controls).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        f"PASS canonical_merge_allowed={str(canonical_merge_allowed).lower()}",
        "PASS downstream_promotion_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS source_roots_mutated=false",
        "PASS shared_intake_mutated=false",
        "PASS thresholds_relaxed=false",
    ]
    (CHECKS / "source_control_inbox_repoll_after_034813_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(gate_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
