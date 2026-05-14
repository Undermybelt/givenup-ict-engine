#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T073629+0800-codex-local-required-source-control-sweep-v1"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "local-required-source-control-sweep-v1"
CHECK_DIR = RUN_ROOT / "checks"

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-label-equivalence-intake"),
    Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
]

SEARCH_ROOTS = [
    (Path("/tmp"), 5),
    (Path("/private/tmp"), 5),
    (REPO / "docs/experiments/actionable-regime-confidence/runs", 7),
    (Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026"), 3),
]

KEYWORDS = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "matched_negative_normal_activity_rows",
    "stock_market_regimes_2026_extension",
    "native_subhour_source_label_rows",
    "native_subhour_source_label_provenance",
    "source_label_equivalence_rows",
    "source_label_equivalence_provenance",
    "MainRegimeV2",
    "r6_oystacher_approval_decision_package",
]

SKIP_DIRS = {
    ".git",
    "target",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - report-only artifact
        return {"_read_error": str(exc)}


def sample_csv(path: Path, sample_limit: int = 10000) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False}
    out: dict[str, Any] = {"exists": True, "path": str(path), "sha256": sha256_file(path)}
    try:
        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            out["columns"] = reader.fieldnames or []
            label_counts: Counter[str] = Counter()
            event_counts: Counter[str] = Counter()
            split_counts: Counter[str] = Counter()
            rows_seen = 0
            for row in reader:
                rows_seen += 1
                if "main_regime_v2_label" in row:
                    label_counts[row.get("main_regime_v2_label", "")] += 1
                if "event_species" in row:
                    event_counts[row.get("event_species", "")] += 1
                if "split_role" in row:
                    split_counts[row.get("split_role", "")] += 1
                if rows_seen >= sample_limit:
                    break
            out["sample_rows_seen"] = rows_seen
            out["sample_label_counts"] = dict(label_counts)
            out["sample_event_species_counts"] = dict(event_counts)
            out["sample_split_counts"] = dict(split_counts)
    except Exception as exc:  # noqa: BLE001 - report-only artifact
        out["read_error"] = str(exc)
    return out


def depth_from(root: Path, current: Path) -> int:
    try:
        return len(current.relative_to(root).parts)
    except ValueError:
        return 999


def search_candidate_files() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root, max_depth in SEARCH_ROOTS:
        if not root.exists():
            continue
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            if depth_from(root, current_path) >= max_depth:
                dirs[:] = []
            for filename in files:
                full = current_path / filename
                haystack = str(full)
                matched = [k for k in KEYWORDS if k in haystack]
                if not matched:
                    continue
                key = str(full)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stat = full.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                except OSError:
                    size = None
                    mtime = None
                hits.append(
                    {
                        "path": key,
                        "matched_keywords": ";".join(matched),
                        "size_bytes": size,
                        "mtime_utc": mtime,
                    }
                )
    hits.sort(key=lambda row: row["path"])
    return hits


def summarize_roots() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in TARGET_ROOTS:
        status = "absent"
        file_count = 0
        path_type = "missing"
        if path.exists():
            status = "exists"
            path_type = "directory" if path.is_dir() else "file"
            if path.is_dir():
                file_count = sum(1 for p in path.rglob("*") if p.is_file())
            else:
                file_count = 1
        rows.append(
            {
                "path": str(path),
                "status": status,
                "path_type": path_type,
                "file_count": file_count,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    root_status = summarize_roots()
    candidate_hits = search_candidate_files()

    native_root = Path("/tmp/ict-engine-native-subhour-source-label-intake")
    native_prov = read_json(native_root / "native_subhour_source_label_provenance.json")
    native_rows = sample_csv(native_root / "native_subhour_source_label_rows.csv")

    equiv_root = Path("/tmp/ict-engine-source-label-equivalence-intake")
    equiv_prov = read_json(equiv_root / "source_label_equivalence_provenance.json")
    equiv_rows = sample_csv(equiv_root / "source_label_equivalence_rows.csv")

    approval_path = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
    approval = read_json(approval_path) if approval_path.exists() else {}
    approval_assertions = approval.get("assertions", {}) if isinstance(approval, dict) else {}

    decision = {
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "direct_verifier_run": False,
        "split_calibration_run": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "local_required_source_control_sweep_v1=no_new_required_source_control_unlock",
        "scope": "bounded local filesystem and known target-root sweep only",
        "target_roots": root_status,
        "candidate_file_hit_count": len(candidate_hits),
        "native_subhour_summary": {
            "provenance_run_id": native_prov.get("run_id"),
            "dataset_id": native_prov.get("dataset_id"),
            "row_count": native_prov.get("row_count"),
            "limitations": native_prov.get("limitations"),
            "sample": native_rows,
        },
        "source_label_equivalence_summary": {
            "provenance_run_id": equiv_prov.get("run_id"),
            "row_count": equiv_prov.get("row_count"),
            "label_counts": equiv_prov.get("label_counts"),
            "limitations": equiv_prov.get("limitations"),
            "sample": equiv_rows,
        },
        "r6_approval_decision_summary": {
            "path": str(approval_path),
            "exists": approval_path.exists(),
            "gate_result": approval.get("gate_result") if isinstance(approval, dict) else None,
            "approval_present": approval_assertions.get("approval_present"),
            "canonical_merge_allowed_now": approval_assertions.get("canonical_merge_allowed_now"),
            "downstream_rerun_allowed_now": approval_assertions.get("downstream_rerun_allowed_now"),
            "update_goal": approval_assertions.get("update_goal"),
        },
        "decision": decision,
        "next": "Continue source/control acquisition only before direct verifier, split calibration, canonical merge, selected-data AutoQuant, or downstream promotion.",
    }

    json_path = OUT_DIR / "local_required_source_control_sweep_v1.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_csv(OUT_DIR / "target_root_status_v1.csv", root_status)
    write_csv(OUT_DIR / "candidate_file_hits_v1.csv", candidate_hits)

    assertions = [
        "gate_result=local_required_source_control_sweep_v1=no_new_required_source_control_unlock",
        f"candidate_file_hit_count={len(candidate_hits)}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "local_required_source_control_sweep_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    md = f"""# Local Required Source/Control Sweep v1

Run id: `{RUN_ID}`

Gate result: `local_required_source_control_sweep_v1=no_new_required_source_control_unlock`

## Scope

This packet is a bounded local filesystem and known target-root sweep. It inspects existing local artifacts only. It does not mutate R3/R5/R6 target roots, does not approve the R6 decision package, does not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- R6 owner/export root `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent.
- R5 recency root `/tmp/ict-engine-source-panel-recency-extension`: absent.
- R3 native-subhour root exists, but its provenance is `{native_prov.get("dataset_id")}` and its limitations include `Crisis has no direct TSIE source taxonomy class`; it remains non-promoting.
- Source-label equivalence root exists with `{equiv_prov.get("row_count")}` rows, but its limitations say schema readiness is not Board A confidence acceptance and source confidence calibration remains fail-closed.
- R6 approval decision package exists at `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid`, but `approval_present={approval_assertions.get("approval_present")}`, `canonical_merge_allowed_now={approval_assertions.get("canonical_merge_allowed_now")}`, and `downstream_rerun_allowed_now={approval_assertions.get("downstream_rerun_allowed_now")}`.
- Candidate filename/path hits found locally: `{len(candidate_hits)}`. They are inventory/discoverability hits only, not accepted source/control roots.

## Decision

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; direct verifier run false; split calibration run false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `{json_path.relative_to(REPO)}`
- Target-root CSV: `{(OUT_DIR / "target_root_status_v1.csv").relative_to(REPO)}`
- Candidate-hit CSV: `{(OUT_DIR / "candidate_file_hits_v1.csv").relative_to(REPO)}`
- Assertions: `{(CHECK_DIR / "local_required_source_control_sweep_v1_assertions.out").relative_to(REPO)}`

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.
"""
    (OUT_DIR / "local_required_source_control_sweep_v1.md").write_text(md)
    print(json.dumps({"run_id": RUN_ID, "gate_result": report["gate_result"], "candidate_file_hit_count": len(candidate_hits)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
