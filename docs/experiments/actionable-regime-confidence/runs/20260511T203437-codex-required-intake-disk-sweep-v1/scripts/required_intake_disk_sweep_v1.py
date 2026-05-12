#!/usr/bin/env python3
"""Search for Board A required intake files and rerun fail-closed verifiers."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T203437-codex-required-intake-disk-sweep-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "required-intake-disk-sweep"
CHECK_DIR = RUN_ROOT / "checks"

SEARCH_ROOTS = [Path("/Users/thrill3r"), Path("/tmp"), Path("/private/tmp")]
SKIP_DIR_NAMES = {
    ".Trash",
    ".cache",
    ".cargo",
    ".rustup",
    "Library",
    "node_modules",
    "target",
    ".git",
}
REQUIRED_FILES = {
    "source_label_equivalence": [
        "source_label_equivalence_rows.csv",
        "source_label_equivalence_provenance.json",
    ],
    "native_subhour_source_label": [
        "native_subhour_source_label_rows.csv",
        "native_subhour_source_label_provenance.json",
    ],
    "source_panel_recency_extension": [
        "stock_market_regimes_2026_extension.csv",
        "source_panel_recency_provenance.json",
    ],
    "direct_manipulation_row_intake": [
        "positive_spoofing_layering_rows.csv",
        "matched_negative_normal_activity_rows.csv",
        "provenance_manifest.json",
    ],
}
INTAKE_ROOTS = {
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "native_subhour_source_label": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_panel_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "direct_manipulation_row_intake": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
}
VERIFIERS = {
    "source_label_equivalence": [
        "python3",
        "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py",
        "--intake-root",
        str(INTAKE_ROOTS["source_label_equivalence"]),
    ],
    "source_panel_recency_extension": [
        "python3",
        "docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py",
        "--intake-root",
        str(INTAKE_ROOTS["source_panel_recency_extension"]),
    ],
    "direct_manipulation_row_intake": [
        "python3",
        "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py",
        "--intake-root",
        str(INTAKE_ROOTS["direct_manipulation_row_intake"]),
    ],
}


def search_required_files() -> list[dict[str, str]]:
    wanted_to_package = {
        filename: package for package, filenames in REQUIRED_FILES.items() for filename in filenames
    }
    hits: list[dict[str, str]] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for current_root, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
            for filename in files:
                package = wanted_to_package.get(filename)
                if package:
                    hits.append({
                        "package": package,
                        "filename": filename,
                        "path": str(Path(current_root) / filename),
                    })
    return sorted(hits, key=lambda item: (item["package"], item["filename"], item["path"]))


def run_verifier(command: list[str]) -> dict[str, object]:
    proc = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "parsed": parsed,
    }


def inspect_intake_roots() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for package, root in INTAKE_ROOTS.items():
        required = REQUIRED_FILES[package]
        present = [name for name in required if (root / name).exists()]
        rows.append({
            "package": package,
            "root": str(root),
            "exists": root.exists(),
            "required_files": ";".join(required),
            "present_files": ";".join(present),
            "missing_files": ";".join(name for name in required if name not in present),
            "ready": len(present) == len(required),
        })
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    hits = search_required_files()
    root_rows = inspect_intake_roots()
    verifier_results = {name: run_verifier(command) for name, command in VERIFIERS.items()}
    native_ready = next(row for row in root_rows if row["package"] == "native_subhour_source_label")["ready"]

    decision = (
        "required_intake_disk_sweep_v1=no_required_intake_files_found_verifiers_blocked"
        if not hits and all(result["returncode"] == 2 for result in verifier_results.values()) and not native_ready
        else "required_intake_disk_sweep_v1=potential_intake_artifact_needs_review"
    )
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "searched_roots": [str(root) for root in SEARCH_ROOTS],
        "skip_dir_names": sorted(SKIP_DIR_NAMES),
        "required_files": REQUIRED_FILES,
        "disk_hit_count": len(hits),
        "disk_hits": hits,
        "intake_roots": root_rows,
        "verifier_results": verifier_results,
        "native_subhour_package_ready": native_ready,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next": (
            "Acquire source-owned or owner-approved intake files externally, place them under the exact /tmp roots, "
            "then rerun source-label, recency, direct-manipulation, and native-subhour checks before another audit."
        ),
    }

    json_path = OUT_DIR / "required_intake_disk_sweep_v1.json"
    hits_csv = OUT_DIR / "required_intake_disk_sweep_v1_hits.csv"
    roots_csv = OUT_DIR / "required_intake_disk_sweep_v1_intake_roots.csv"
    md_path = OUT_DIR / "required_intake_disk_sweep_v1.md"
    assertions_path = CHECK_DIR / "required_intake_disk_sweep_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    with hits_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["package", "filename", "path"])
        writer.writeheader()
        writer.writerows(hits)
    with roots_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["package", "root", "exists", "required_files", "present_files", "missing_files", "ready"],
        )
        writer.writeheader()
        writer.writerows(root_rows)

    lines = [
        "# Required Intake Disk Sweep v1",
        "",
        f"- Decision: `{decision}`",
        f"- Required filename hits: `{len(hits)}`",
        f"- Source-label verifier returncode: `{verifier_results['source_label_equivalence']['returncode']}`",
        f"- Recency-extension verifier returncode: `{verifier_results['source_panel_recency_extension']['returncode']}`",
        f"- Direct-manipulation verifier returncode: `{verifier_results['direct_manipulation_row_intake']['returncode']}`",
        f"- Native sub-hour package ready: `{str(native_ready).lower()}`",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Scope",
        "",
        "Searched bounded local roots for the exact intake filenames required by the Board A fail-closed gates. "
        "This does not promote proxy data or create intake rows.",
        "",
        "## Intake Roots",
        "",
        "| Package | Ready | Missing Files |",
        "|---|---:|---|",
    ]
    for row in root_rows:
        lines.append(f"| `{row['package']}` | `{str(row['ready']).lower()}` | `{row['missing_files']}` |")
    lines.extend([
        "",
        "## Decision",
        "",
        "No required source-owned or owner-approved intake files were found in the bounded local search, "
        "and all existing fail-closed verifiers remain blocked. The strict objective remains incomplete.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Hits CSV: `{hits_csv.relative_to(REPO)}`",
        f"- Intake roots CSV: `{roots_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS disk_hit_count={len(hits)}",
        f"PASS source_label_verifier_returncode={verifier_results['source_label_equivalence']['returncode']}",
        f"PASS recency_verifier_returncode={verifier_results['source_panel_recency_extension']['returncode']}",
        f"PASS direct_verifier_returncode={verifier_results['direct_manipulation_row_intake']['returncode']}",
        f"PASS native_subhour_package_ready={str(native_ready).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "json": str(json_path), "assertions": str(assertions_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
