#!/usr/bin/env python3
"""Bounded presence sweep for R6 Oystacher source-owner normal-control exports."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "r6-source-owner-export-presence-sweep"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD_FILE = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

OWNER_EXPORT_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
]

SEARCH_ROOTS = [
    (Path("/Users/thrill3r/Downloads/Tomac"), 5),
    (Path("/Users/thrill3r/Downloads"), 4),
    (Path("/Users/thrill3r/nautilus_trader/tests/test_data"), 8),
    (Path("/tmp"), 3),
    (Path("/private/tmp"), 3),
]

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    "site-packages",
    "target",
    ".venv",
    "venv",
}

OWNER_APPROVAL_FILES = [
    "validation_contract_approval.json",
    "owner_approval_reference.md",
]

VERIFIER_NATIVE_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

PATTERN_TOKENS = [
    "datamine",
    "market-depth",
    "market_depth",
    "depth-of-book",
    "depth_book",
    "mbo",
    "pcap",
    "fix-fast",
    "fix_fast",
    "fixfast",
    "cfe",
    "vix",
    "globex",
    "mdp3",
]

REQUIRED_YEAR_TOKENS = {"2011", "2012", "2013", "2014"}
REQUIRED_PRODUCT_TOKENS = {"cl", "crude", "ng", "natural", "hg", "copper", "es", "s&p", "vix", "cfe"}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_candidate_name(path: Path) -> bool:
    name = path.name.lower()
    if name in OWNER_APPROVAL_FILES or name in VERIFIER_NATIVE_FILES:
        return True
    return any(token in name for token in PATTERN_TOKENS)


def walk_candidates(root: Path, max_depth: int) -> list[Path]:
    if not root.exists():
        return []
    hits: list[Path] = []
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.parts) - root_depth
        dirs[:] = [name for name in dirs if name not in SKIP_DIR_NAMES and depth < max_depth]
        if depth > max_depth:
            continue
        for name in files:
            path = current_path / name
            if is_candidate_name(path):
                hits.append(path)
    return hits


def classify(path: Path) -> tuple[str, str, bool]:
    lower = str(path).lower()
    name = path.name.lower()
    has_required_year = any(token in lower for token in REQUIRED_YEAR_TOKENS)
    has_required_product = any(token in lower for token in REQUIRED_PRODUCT_TOKENS)

    if any(str(path).startswith(str(root)) for root in OWNER_EXPORT_ROOTS):
        if name in OWNER_APPROVAL_FILES or name in VERIFIER_NATIVE_FILES:
            return "owner_export_target_file", "target-root file present; package validity depends on complete set", False
    if name in VERIFIER_NATIVE_FILES:
        return "prior_verifier_native_intake_file", "existing verifier-native file outside owner-export root is not source-owner Oystacher normal-control export", False
    if "symbology" in name:
        return "metadata_only", "symbology metadata is not row-level order-lifecycle normal-control evidence", False
    if name.endswith((".html", ".txt")):
        return "route_page_cache", "route/cache page is useful provenance only, not a control export", False
    if "databento" in lower or "mbo" in lower or "mdp3" in lower:
        if has_required_year and has_required_product:
            return "manual_review_data_like", "data-like file has required date/product tokens but still needs source-owned label/provenance review", True
        return "modern_or_sample_market_data", "market-data sample does not match required Oystacher 2011-2014 cells and lacks source-owned normal labels", False
    if "cfe" in lower or "vix" in lower or "globex" in lower or "datamine" in lower:
        if has_required_year and has_required_product:
            return "manual_review_route_or_data_like", "name matches route/product/year tokens; requires manual provenance review", True
        return "route_or_filename_noise", "route/product filename does not establish source-owned normal-control rows", False
    return "filename_noise", "matched a broad token but is not a usable owner-control export", False


def owner_root_status() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in OWNER_EXPORT_ROOTS:
        for filename in OWNER_APPROVAL_FILES + VERIFIER_NATIVE_FILES:
            path = root / filename
            rows.append(
                {
                    "root": str(root),
                    "filename": filename,
                    "exists": path.exists(),
                    "sha256": sha256_file(path) or "",
                }
            )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    owner_rows = owner_root_status()
    seen: set[Path] = set()
    candidates: list[Path] = []
    for root, depth in SEARCH_ROOTS:
        for path in walk_candidates(root, depth):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                candidates.append(path)

    candidate_rows: list[dict[str, object]] = []
    viable_review_candidates = 0
    strict_owner_package_files_present = sum(1 for row in owner_rows if row["exists"])
    for path in sorted(candidates, key=lambda item: str(item)):
        classification, reason, needs_review = classify(path)
        if needs_review:
            viable_review_candidates += 1
        candidate_rows.append(
            {
                "path": str(path),
                "classification": classification,
                "needs_manual_review": needs_review,
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": sha256_file(path) or "",
                "decision": "manual_review_required" if needs_review else "reject_for_current_contract",
                "reason": reason,
            }
        )

    owner_package_complete = all(row["exists"] for row in owner_rows if row["root"].startswith("/tmp/"))
    gate_result = (
        "r6_source_owner_export_presence_sweep_v1="
        "no_verifier_native_owner_package_or_viable_local_source_owner_export_found"
    )
    summary = {
        "run_id": "20260512T004713-codex-r6-source-owner-export-presence-sweep-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_file_sha256_before_writeback": sha256_file(BOARD_FILE),
        "search_roots": [{"path": str(path), "max_depth": depth, "exists": path.exists()} for path, depth in SEARCH_ROOTS],
        "owner_export_roots": [str(path) for path in OWNER_EXPORT_ROOTS],
        "owner_package_files_present": strict_owner_package_files_present,
        "owner_package_complete": owner_package_complete,
        "candidate_hits": len(candidate_rows),
        "manual_review_candidates": viable_review_candidates,
        "strictly_usable_source_owned_controls_found": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "owner_root_status": owner_rows,
        "candidate_files": candidate_rows,
    }

    json_path = OUT_DIR / "r6_source_owner_export_presence_sweep_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        OUT_DIR / "r6_source_owner_export_presence_owner_root_files_v1.csv",
        owner_rows,
        ["root", "filename", "exists", "sha256"],
    )
    write_csv(
        OUT_DIR / "r6_source_owner_export_presence_candidates_v1.csv",
        candidate_rows,
        ["path", "classification", "needs_manual_review", "size_bytes", "sha256", "decision", "reason"],
    )

    md = f"""# R6 Source-Owner Export Presence Sweep v1

- Run id: `20260512T004713-codex-r6-source-owner-export-presence-sweep-v1`.
- Gate result: `{gate_result}`.
- Owner/export roots checked: `{len(OWNER_EXPORT_ROOTS)}`.
- Owner package files present across target roots: `{strict_owner_package_files_present}`.
- Bounded candidate filename hits: `{len(candidate_rows)}`.
- Manual-review data-like candidates: `{viable_review_candidates}`.
- Strictly usable source-owned normal controls found: `0`.
- Canonical merge allowed: `false`; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; external requests sent: `false`; trade usable: `false`.

## Interpretation

The sweep found no complete verifier-native owner package under `/tmp/ict-engine-board-a-r6-owner-export-v1` or `/private/tmp/ict-engine-board-a-r6-owner-export-v1`, and no local CME/Cboe/DataMine/MBO/PCAP/FIX-FAST file that can be accepted as source-owned Oystacher normal-control rows. The hits are prior verifier intakes, route/cache pages, metadata files, or modern/sample market-data files without the required source-owned normal labels and provenance.

## Next

Keep the active V69 next action: acquire source-owned normal controls for the `17` Oystacher cells from the mapped CME/Cboe routes, or explicitly approve the same-exhibit `FLIP`-as-control exception. Only after that should the isolated verifier-native intake be copied under a shared lock and the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback be rerun.

## Artifacts

- JSON: `{compact_path(json_path)}`
- Owner-root files CSV: `{compact_path(OUT_DIR / "r6_source_owner_export_presence_owner_root_files_v1.csv")}`
- Candidate files CSV: `{compact_path(OUT_DIR / "r6_source_owner_export_presence_candidates_v1.csv")}`
- Assertions: `{compact_path(CHECKS_DIR / "r6_source_owner_export_presence_sweep_v1_assertions.out")}`
"""
    (OUT_DIR / "r6_source_owner_export_presence_sweep_v1.md").write_text(md, encoding="utf-8")

    assertions = [
        f"run_id={summary['run_id']}",
        f"owner_package_files_present={strict_owner_package_files_present}",
        f"candidate_hits={len(candidate_rows)}",
        f"manual_review_candidates={viable_review_candidates}",
        "strictly_usable_source_owned_controls_found=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "shared_intake_mutated=false",
        f"gate_result={gate_result}",
    ]
    if owner_package_complete or viable_review_candidates:
        assertions.append("ASSERTION_FAILED=unexpected_owner_package_or_manual_review_candidate")
        (CHECKS_DIR / "r6_source_owner_export_presence_sweep_v1_assertions.out").write_text(
            "\n".join(assertions) + "\n", encoding="utf-8"
        )
        return 1

    assertions.append("ASSERTIONS_PASSED=true")
    (CHECKS_DIR / "r6_source_owner_export_presence_sweep_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
