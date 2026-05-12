#!/usr/bin/env python3
import csv
import hashlib
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "source-control-arrival-refresh-after-061521-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]
DISPATCH_FILES = {
    "cme_group": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cme_group_owner_export_v5_dispatch_v1.eml",
    "cboe_cfe": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cboe_cfe_owner_export_v5_dispatch_v1.eml",
}
LOCAL_SCAN_ROOTS = [
    Path("/tmp"),
    Path("/private/tmp"),
    Path("/Users/thrill3r/Downloads"),
]
KEYWORDS = (
    "ict-engine-board-a-r6-owner-export-v1",
    "native-subhour-source-label",
    "source-panel-recency-extension",
    "oystacher",
    "market depth",
    "market_depth",
    "market-by-order",
    "market_by_order",
    "mbo",
    "databento",
    "cboe",
    "cfe",
    "vix",
    "mainregimev2",
    "source_label",
    "owner_export",
)
EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".parquet",
    ".dbn",
    ".zip",
    ".gz",
    ".eml",
    ".xlsx",
    ".xls",
    ".txt",
    ".md",
}


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(root: Path, limit: int = 80) -> list[str]:
    if not root.exists():
        return []
    files: list[str] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        rel_depth = len(Path(current).relative_to(root).parts)
        if rel_depth >= 2:
            dirs[:] = []
        for name in sorted(names):
            files.append(str(Path(current, name)))
            if len(files) >= limit:
                return files
    return files


def count_csv_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        rows = sum(1 for _ in reader)
    return max(rows - 1, 0)


def scan_local_candidates(limit: int = 120) -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()
    for root in LOCAL_SCAN_ROOTS:
        if not root.exists():
            continue
        root_depth = len(root.parts)
        for current, dirs, names in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            if depth >= 4:
                dirs[:] = []
            dirs[:] = [
                d
                for d in sorted(dirs)
                if d not in {".git", "node_modules", "target", ".venv", "venv"}
            ]
            for name in sorted(names):
                path = current_path / name
                lower = str(path).lower()
                if path.suffix.lower() not in EXTENSIONS:
                    continue
                if not any(k in lower for k in KEYWORDS):
                    continue
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stat = path.stat()
                except OSError:
                    continue
                candidates.append(
                    {
                        "path": key,
                        "size": stat.st_size,
                        "mtime": int(stat.st_mtime),
                        "is_required_root_member": any(
                            str(path).startswith(str(required) + os.sep)
                            for required in REQUIRED_ROOTS
                        ),
                    }
                )
                if len(candidates) >= limit:
                    return candidates
    return candidates


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    required_status = []
    for root in REQUIRED_ROOTS:
        required_status.append(
            {
                "path": str(root),
                "present": root.exists(),
                "files": list_files(root),
            }
        )

    equiv_rows = count_csv_rows(EQUIV_ROOT / "source_label_equivalence_rows.csv")
    equivalence_status = {
        "path": str(EQUIV_ROOT),
        "present": EQUIV_ROOT.exists(),
        "rows": equiv_rows,
        "files": list_files(EQUIV_ROOT),
    }

    dispatch_status = {}
    for owner, path in DISPATCH_FILES.items():
        dispatch_status[owner] = {
            "path": str(path),
            "present": path.is_file(),
            "sha256": sha256(path),
        }

    local_candidates = scan_local_candidates()
    required_roots_present = all(item["present"] for item in required_status)
    any_required_root_present = any(item["present"] for item in required_status)
    local_required_members = [
        item for item in local_candidates if item["is_required_root_member"]
    ]

    gate_result = (
        "source_control_arrival_refresh_after_061521_v1="
        "no_required_root_no_approval_no_promotion"
    )
    result = {
        "run_id": RUN_ROOT.name,
        "gate_result": gate_result,
        "board_sha256_before_artifact": board_hash,
        "required_roots": required_status,
        "source_label_equivalence": equivalence_status,
        "dispatch_drafts": dispatch_status,
        "local_candidate_count": len(local_candidates),
        "local_candidate_sample": local_candidates[:40],
        "required_roots_present_all": required_roots_present,
        "required_roots_present_any": any_required_root_present,
        "local_required_root_member_count": len(local_required_members),
        "external_requests_sent": False,
        "approval_present": False,
        "source_control_evidence_acquired": False,
        "accepted_rows_added": 0,
        "target_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "source_control_arrival_refresh_after_061521_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    md_lines = [
        "# Source Control Arrival Refresh After 061521 v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Scope",
        "",
        "This is a bounded read-only refresh after the 061505 source-label calibration and the 061521 current-objective audit. It does not send mail, approve controls, copy files into target roots, mutate canonical intake, run downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Required Roots",
        "",
        "| Root | Present | File Count Sampled |",
        "|---|---:|---:|",
    ]
    for item in required_status:
        md_lines.append(
            f"| `{item['path']}` | `{str(item['present']).lower()}` | `{len(item['files'])}` |"
        )
    md_lines.extend(
        [
            "",
            "## Non-Target Equivalence Root",
            "",
            f"- Present: `{str(equivalence_status['present']).lower()}`",
            f"- Rows: `{equivalence_status['rows']}`",
            "- Boundary: this root remains non-target source-label-equivalence evidence and is not R3 native sub-hour, R5 recency, or R6 owner/export control evidence.",
            "",
            "## Dispatch Drafts",
            "",
            "| Owner | Present | SHA256 |",
            "|---|---:|---|",
        ]
    )
    for owner, item in dispatch_status.items():
        md_lines.append(
            f"| `{owner}` | `{str(item['present']).lower()}` | `{item['sha256']}` |"
        )
    md_lines.extend(
        [
            "",
            "## Local Arrival Scan",
            "",
            f"- Candidate files sampled: `{len(local_candidates)}`",
            f"- Files inside required roots: `{len(local_required_members)}`",
            "- Candidate files are discovery hints only. None are promoted unless they appear in a required target root with source/control approval and verifier-native schema.",
            "",
            "## Decision",
            "",
            "No required promotion root is present. The v5 dispatch drafts remain available but there is no evidence they were sent, no ticket/export/license identifier, no approval, and no verifier-native owner/export rows. The source-label equivalence root remains present but non-promoting.",
            "",
            "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
            "",
            "## Next",
            "",
            "Use the v5 drafts through an approved operator dispatch path, or supply explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels. Only after a required root unlocks should direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback rerun in order.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Assertions: `{(CHECK_DIR / 'source_control_arrival_refresh_after_061521_v1_assertions.out').relative_to(REPO)}`",
        ]
    )
    (OUT_DIR / "source_control_arrival_refresh_after_061521_v1.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assertions = [
        f"gate_result={gate_result}",
        f"required_roots_present_any={str(any_required_root_present).lower()}",
        f"required_roots_present_all={str(required_roots_present).lower()}",
        f"source_label_equivalence_present={str(equivalence_status['present']).lower()}",
        f"source_label_equivalence_rows={equivalence_status['rows']}",
        f"operator_dispatch_drafts_present={str(all(item['present'] for item in dispatch_status.values())).lower()}",
        "external_requests_sent=false",
        "approval_present=false",
        "source_control_evidence_acquired=false",
        "accepted_rows_added=0",
        "target_root_mutated=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "source_control_arrival_refresh_after_061521_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    (CMD_DIR / "source_control_arrival_refresh_after_061521_v1.exit").write_text("0\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
