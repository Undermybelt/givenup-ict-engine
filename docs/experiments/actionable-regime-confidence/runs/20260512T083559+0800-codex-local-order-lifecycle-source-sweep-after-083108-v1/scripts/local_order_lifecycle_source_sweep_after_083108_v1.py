#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T083559+0800-codex-local-order-lifecycle-source-sweep-after-083108-v1"
RUN_SLUG = "local-order-lifecycle-source-sweep-after-083108-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / RUN_SLUG
CHECK_DIR = RUN_ROOT / "checks"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

ROOTS = [
    Path("/Users/thrill3r/Downloads/Tomac"),
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
    Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
]
MAX_DEPTH = 5
MAX_CANDIDATES = 600
MAX_HEADER_BYTES = 32768

FILENAME_TERMS = [
    "cme",
    "cboe",
    "cfe",
    "databento",
    "dbn",
    "market_depth",
    "market-depth",
    "market by order",
    "market_by_order",
    "mbo",
    "mbp",
    "pitch",
    "order",
    "book",
    "quote",
    "trade",
    "cat",
    "finra",
    "oystacher",
    "coscia",
    "spoof",
    "layer",
]
ORDER_LIFECYCLE_TERMS = [
    "order_id",
    "order id",
    "event_type",
    "event type",
    "add order",
    "modify",
    "cancel",
    "delete",
    "execution",
    "fill",
    "side",
    "bid_px",
    "ask_px",
    "price",
    "size",
    "ts_recv",
    "sequence",
    "mbo",
    "mbp",
    "pitch",
]
REQUIRED_R6_FILES = {
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
}
REQUIRED_R5_FILES = {
    "stock_market_regimes_2026_extension.csv",
    "source_panel_recency_provenance.json",
}
REQUIRED_R3_FILES = {
    "native_subhour_source_label_rows.csv",
    "native_subhour_source_label_provenance.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def depth_from(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 999


def iter_files(root: Path):
    if not root.exists():
        return
    if root.is_file():
        yield root
        return
    for current, dirs, files in os.walk(root):
        cur = Path(current)
        if depth_from(root, cur) >= MAX_DEPTH:
            dirs[:] = []
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "Library", ".Trash"}]
        for name in files:
            yield cur / name


def filename_matches(path: Path) -> bool:
    text = str(path).lower().replace("_", " ")
    return any(term in text for term in FILENAME_TERMS)


def read_head(path: Path) -> str:
    if path.suffix.lower() not in {".csv", ".tsv", ".json", ".jsonl", ".txt", ".md", ".dbn"}:
        return ""
    try:
        return path.read_bytes()[:MAX_HEADER_BYTES].decode("utf-8", errors="replace")
    except OSError:
        return ""


def list_archive_members(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(path) as zf:
                return zf.namelist()[:200]
        if suffix in {".tar", ".gz", ".tgz"}:
            with tarfile.open(path) as tf:
                return [m.name for m in tf.getmembers()[:200]]
    except Exception:
        return []
    return []


def classify(path: Path) -> dict[str, object]:
    head = read_head(path)
    head_lower = head.lower()
    archive_members = list_archive_members(path)
    member_text = " ".join(archive_members).lower()
    header_hits = [term for term in ORDER_LIFECYCLE_TERMS if term in head_lower]
    member_hits = [term for term in ORDER_LIFECYCLE_TERMS if term in member_text]
    verifier_native_hint = bool(header_hits or member_hits)
    return {
        "path": str(path),
        "directory": str(path.parent),
        "name": path.name,
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256(path) if path.is_file() and path.stat().st_size <= 200 * 1024 * 1024 else "",
        "header_hits": "|".join(header_hits) if header_hits else "none",
        "archive_member_hits": "|".join(member_hits) if member_hits else "none",
        "archive_member_sample": "|".join(archive_members[:20]),
        "verifier_native_hint": verifier_native_hint,
    }


def root_package_status(root: Path, required: set[str]) -> dict[str, object]:
    present = {name: (root / name).is_file() for name in sorted(required)}
    return {
        "root": str(root),
        "exists": root.exists(),
        "required_files_present": present,
        "complete": bool(present) and all(present.values()),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    candidates = []
    seen = set()
    for root in ROOTS:
        for path in iter_files(root) or []:
            if len(candidates) >= MAX_CANDIDATES:
                break
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen or not path.is_file():
                continue
            if not filename_matches(path):
                continue
            seen.add(resolved)
            try:
                candidates.append(classify(path))
            except OSError:
                continue

    r6_status = [
        root_package_status(Path("/tmp/ict-engine-board-a-r6-owner-export-v1"), REQUIRED_R6_FILES),
        root_package_status(Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"), REQUIRED_R6_FILES),
    ]
    r5_status = [
        root_package_status(Path("/tmp/ict-engine-source-panel-recency-extension"), REQUIRED_R5_FILES),
        root_package_status(Path("/private/tmp/ict-engine-source-panel-recency-extension"), REQUIRED_R5_FILES),
    ]
    r3_status = [
        root_package_status(Path("/tmp/ict-engine-native-subhour-source-label-intake"), REQUIRED_R3_FILES),
        root_package_status(Path("/private/tmp/ict-engine-native-subhour-source-label-intake"), REQUIRED_R3_FILES),
    ]

    verifier_native_candidates = [row for row in candidates if row["verifier_native_hint"]]
    exact_required_packages = sum(1 for row in r6_status + r5_status + r3_status if row["complete"])
    accepted_rows_added = 0
    valid_required_root_unlock = False
    source_control_evidence_acquired = False

    metrics = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_b_sha256_before_artifact": sha256(BOARD_B),
        "gate_result": (
            "local_order_lifecycle_source_sweep_after_083108_v1="
            "no_accepted_owner_export_or_required_source_control_package"
        ),
        "roots_scanned": [str(root) for root in ROOTS],
        "max_depth": MAX_DEPTH,
        "candidate_files_scanned": len(candidates),
        "verifier_native_candidate_files": len(verifier_native_candidates),
        "exact_required_packages": exact_required_packages,
        "accepted_rows_added": accepted_rows_added,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    payload = {
        "metrics": metrics,
        "r6_status": r6_status,
        "r5_status": r5_status,
        "r3_status": r3_status,
        "candidates": candidates,
    }

    (OUT_DIR / "local_order_lifecycle_source_sweep_after_083108_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (OUT_DIR / "local_order_lifecycle_source_sweep_candidates_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        fieldnames = [
            "path",
            "directory",
            "name",
            "suffix",
            "size_bytes",
            "sha256",
            "header_hits",
            "archive_member_hits",
            "archive_member_sample",
            "verifier_native_hint",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)

    root_rows = []
    for family, rows in [("r6", r6_status), ("r5", r5_status), ("r3", r3_status)]:
        for row in rows:
            root_rows.append(
                {
                    "family": family,
                    "root": row["root"],
                    "exists": row["exists"],
                    "complete": row["complete"],
                    "required_files_present": json.dumps(row["required_files_present"], sort_keys=True),
                }
            )
    with (OUT_DIR / "local_order_lifecycle_source_sweep_target_roots_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["family", "root", "exists", "complete", "required_files_present"]
        )
        writer.writeheader()
        writer.writerows(root_rows)

    candidate_lines = "\n".join(
        f"| `{row['name']}` | `{row['directory']}` | `{row['suffix']}` | `{row['header_hits']}` | `{row['archive_member_hits']}` | `{row['verifier_native_hint']}` |"
        for row in candidates[:50]
    )
    if not candidate_lines:
        candidate_lines = "| `none` | `n/a` | `n/a` | `none` | `none` | `False` |"
    (OUT_DIR / "local_order_lifecycle_source_sweep_after_083108_v1.md").write_text(
        f"""# Local Order-Lifecycle Source Sweep After 083108 v1

Run id: `{RUN_ID}`

Gate result: `{metrics["gate_result"]}`

## Scope

Read-only bounded local sweep after `083108`. It checks target roots and local
candidate locations for owner-export/order-lifecycle package hints. Filename,
header, archive-member, or local OHLCV hits are not accepted source/control
evidence. This artifact does not copy files, populate target roots, approve
same-exhibit `FLIP` controls, run direct verifier, run canonical merge, run
selected-data AutoQuant, run filter / Pre-Bayes, BBN, CatBoost/path-ranking, or
execution-tree promotion, make a trade claim, or call `update_goal`.

## Candidate Files

| File | Directory | Suffix | Header hits | Archive-member hits | Verifier-native hint |
|---|---|---|---|---|---:|
{candidate_lines}

## Decision

- Candidate files scanned: `{metrics["candidate_files_scanned"]}`.
- Verifier-native candidate files: `{metrics["verifier_native_candidate_files"]}`.
- Exact required target-root packages: `{metrics["exact_required_packages"]}`.
- Accepted rows added: `0`.
- Valid required-root unlock: `false`.
- Source/control evidence acquired: `false`.
- Canonical merge: `false`.
- Selected-data AutoQuant promotion: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Next

Continue source/control acquisition only. The live unblocker remains a complete
owner-approved R6/R5/R3 package with provenance and matched controls, or explicit
same-exhibit `FLIP`-as-control approval before any selected-data AutoQuant or
downstream promotion rerun.
""",
        encoding="utf-8",
    )

    assertions = [
        f"gate_result={metrics['gate_result']}",
        f"candidate_files_scanned={metrics['candidate_files_scanned']}",
        f"verifier_native_candidate_files={metrics['verifier_native_candidate_files']}",
        f"exact_required_packages={metrics['exact_required_packages']}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "local_order_lifecycle_source_sweep_after_083108_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
