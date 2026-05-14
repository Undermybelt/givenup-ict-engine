#!/usr/bin/env python3
"""Bounded local scan for R6 owner-export delivery after the 043027 audit."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T043314-codex-r6-owner-export-arrival-scan-after-043027-v1"
SLUG = "r6-owner-export-arrival-scan-after-043027-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

OWNER_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")

OWNER_REQUIRED = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]
LEGACY_REQUIRED = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

SEARCH_ROOTS = [
    Path("/tmp"),
    Path("/private/tmp"),
    Path("/Users/thrill3r/Downloads"),
]
SKIP_DIRS = {
    ".git",
    "target",
    "debug",
    "deps",
    "incremental",
    "node_modules",
    ".venv",
    "site-packages",
    "__pycache__",
}
SKIP_SUFFIXES = {
    ".o",
    ".rlib",
    ".rmeta",
    ".d",
    ".dSYM",
}
HINT_TOKENS = [
    "direct_manipulation",
    "positive_spoofing",
    "matched_negative",
    "provenance_manifest",
    "databento",
    ".dbn",
    "market_depth",
    "market depth",
    "mbo",
    "mbp",
    "cfe-vix",
    "cfe_vix",
    "vix",
    "cme",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def root_row(root_name: str, root: Path, required: list[str]) -> dict[str, Any]:
    files = {name: root / name for name in required}
    present = root.exists()
    present_files = [name for name, path in files.items() if path.exists()]
    return {
        "root_name": root_name,
        "root_path": str(root),
        "root_present": present,
        "required_files": ";".join(required),
        "present_files": ";".join(present_files),
        "complete": present and len(present_files) == len(required),
        "decision": "complete_verifier_native_root_present"
        if present and len(present_files) == len(required)
        else "missing_or_incomplete_no_promotion",
    }


def within_depth(base: Path, current: Path, max_depth: int) -> bool:
    try:
        rel = current.relative_to(base)
    except ValueError:
        return False
    return len(rel.parts) <= max_depth


def hint_reason(path: Path) -> str | None:
    lower = path.name.lower()
    if path.suffix in SKIP_SUFFIXES:
        return None
    if path.name in OWNER_REQUIRED or path.name in LEGACY_REQUIRED:
        return "required_or_legacy_required_filename"
    for token in HINT_TOKENS:
        if token in lower:
            return f"name_contains_{token.replace(' ', '_')}"
    return None


def scan_hints(max_per_root: int = 80) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for base in SEARCH_ROOTS:
        if not base.exists():
            continue
        count = 0
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            dirs[:] = [
                name
                for name in dirs
                if name not in SKIP_DIRS and within_depth(base, current_path / name, 5)
            ]
            for name in files:
                path = current_path / name
                reason = hint_reason(path)
                if not reason:
                    continue
                resolved = str(path)
                if resolved in seen:
                    continue
                seen.add(resolved)
                try:
                    size = path.stat().st_size
                except OSError:
                    size = -1
                rows.append(
                    {
                        "search_root": str(base),
                        "path": resolved,
                        "size_bytes": size,
                        "reason": reason,
                        "decision": "local_hint_not_verifier_native_owner_export",
                    }
                )
                count += 1
                if count >= max_per_root:
                    break
            if count >= max_per_root:
                break
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    target_roots = [
        root_row("r6_owner_export_current_contract", OWNER_ROOT, OWNER_REQUIRED),
        root_row("r6_owner_export_legacy_isolated_names", OWNER_ROOT, LEGACY_REQUIRED),
        root_row("r3_native_subhour", R3_ROOT, []),
        root_row("r5_recency_extension", R5_ROOT, []),
    ]
    for row in target_roots:
        if not row["required_files"]:
            row["complete"] = bool(row["root_present"])
            row["decision"] = "root_present_needs_verifier" if row["root_present"] else "root_absent_no_promotion"

    local_hints = scan_hints()
    owner_current_complete = target_roots[0]["complete"]
    owner_legacy_complete = target_roots[1]["complete"]
    r3_present = target_roots[2]["root_present"]
    r5_present = target_roots[3]["root_present"]
    verifier_native_unlock = bool(owner_current_complete or owner_legacy_complete or r3_present or r5_present)

    gate = (
        "r6_owner_export_arrival_scan_after_043027_v1=verifier_native_target_root_arrived_needs_direct_verifier"
        if verifier_native_unlock
        else "r6_owner_export_arrival_scan_after_043027_v1=no_verifier_native_owner_export_arrival_no_promotion"
    )

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_scan": sha256_file(BOARD),
        "gate_result": gate,
        "target_roots": target_roots,
        "local_hint_count": len(local_hints),
        "local_hints_sample": local_hints[:20],
        "promotion_status": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": verifier_native_unlock,
            "new_confidence_gate": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": (
            "Run direct verifier before any merge because a target root is now present."
            if verifier_native_unlock
            else "Preserve Current Cursor next action: obtain verifier-native R6 controls or explicit approval before canonical merge and downstream rerun."
        ),
    }

    write_csv(
        OUT / "r6_owner_export_arrival_target_roots_v1.csv",
        target_roots,
        [
            "root_name",
            "root_path",
            "root_present",
            "required_files",
            "present_files",
            "complete",
            "decision",
        ],
    )
    write_csv(
        OUT / "r6_owner_export_arrival_local_hints_v1.csv",
        local_hints,
        ["search_root", "path", "size_bytes", "reason", "decision"],
    )
    (OUT / "r6_owner_export_arrival_scan_after_043027_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = [
        "# R6 Owner Export Arrival Scan After 043027 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        "## Result",
        "",
        f"- R6 owner-export root present: `{OWNER_ROOT.exists()}`.",
        f"- R6 current-contract root complete: `{owner_current_complete}`.",
        f"- R6 legacy isolated-name root complete: `{owner_legacy_complete}`.",
        f"- R3 native-subhour root present: `{r3_present}`.",
        f"- R5 recency-extension root present: `{r5_present}`.",
        f"- Local hint files found: `{len(local_hints)}`; treated as hints only unless they are copied into a verifier-native target root with provenance and approval.",
        "- Accepted rows added `0`; canonical merge `false`; downstream promotion rerun `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This scan does not copy files into target roots and does not approve `FLIP` controls. It only checks whether source/control delivery arrived since the latest objective audit.",
    ]
    (OUT / "r6_owner_export_arrival_scan_after_043027_v1.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS gate_result={gate}",
        f"PASS r6_owner_root_present={str(OWNER_ROOT.exists()).lower()}",
        f"PASS r6_current_contract_complete={str(owner_current_complete).lower()}",
        f"PASS r6_legacy_contract_complete={str(owner_legacy_complete).lower()}",
        f"PASS r3_native_subhour_root_present={str(r3_present).lower()}",
        f"PASS r5_recency_extension_root_present={str(r5_present).lower()}",
        "PASS accepted_rows_added=0",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "r6_owner_export_arrival_scan_after_043027_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
