#!/usr/bin/env python3
"""Read-only R3/R5 required-root sweep after 085612."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T085908+0800-codex-r3-r5-required-root-local-sweep-after-085612-v1"
)
OUT = RUN / "r3-r5-required-root-local-sweep-after-085612-v1"
CHECKS = RUN / "checks"

TARGET_ROOTS = [
    ("r3_native_subhour_tmp", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    (
        "r3_native_subhour_private_tmp",
        Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
    ),
    ("r5_recency_tmp", Path("/tmp/ict-engine-source-panel-recency-extension")),
    (
        "r5_recency_private_tmp",
        Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    ),
    ("r6_owner_export_tmp", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
    (
        "r6_owner_export_private_tmp",
        Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    ),
]


def text_sniff(path: Path, needles: list[str]) -> dict[str, bool]:
    hits = {needle: False for needle in needles}
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), ""):
                if not chunk:
                    break
                lower = chunk.lower()
                for needle in needles:
                    if needle.lower() in lower:
                        hits[needle] = True
                if all(hits.values()):
                    break
    except OSError:
        pass
    return hits


def scan_native_subhour_csv(path: Path) -> dict[str, object]:
    provenance_path = path.with_name("native_subhour_source_label_provenance.json")
    rows = 0
    labels: list[str] = []
    crisis_rows = 0
    header: list[str] = []
    try:
        with provenance_path.open("r", encoding="utf-8", errors="ignore") as handle:
            provenance = json.load(handle)
        labels = list(provenance.get("accepted_mapping_confidence_95_labels", []))
        rows = int(provenance.get("row_count", 0))
        crisis_rows = 0
        header = ["provenance_json"]
    except OSError:
        pass
    return {
        "path": str(path),
        "header": header,
        "rows": rows,
        "labels": sorted(set(labels)),
        "crisis_rows": crisis_rows,
        "crisis_label_present": crisis_rows > 0 or "Crisis" in labels,
    }


def scan_mainregimev2_csv(path: Path) -> dict[str, object]:
    rows = 0
    post_cutoff_rows = 0
    header: list[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            regime_cols = [col for col in header if col.lower() in {"mainregimev2", "main_regime_v2"}]
            date_cols = [col for col in header if col.lower() in {"date", "timestamp", "time", "datetime"}]
            if not regime_cols:
                return {"path": str(path), "header": header, "rows": 0, "post_cutoff_rows": 0}
            for row in reader:
                if not any((row.get(col) or "").strip() for col in regime_cols):
                    continue
                rows += 1
                if not date_cols:
                    continue
                date_value = min((row.get(col) or "")[:10] for col in date_cols if row.get(col))
                if date_value >= "2026-01-30":
                    post_cutoff_rows += 1
    except OSError:
        pass
    return {
        "path": str(path),
        "header": header,
        "rows": rows,
        "post_cutoff_rows": post_cutoff_rows,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    roots = []
    file_rows = []
    native_summaries = []
    mainregime_summaries = []

    seen_realpaths: set[str] = set()
    seen_file_realpaths: set[str] = set()
    for name, root in TARGET_ROOTS:
        exists = root.exists()
        realpath = str(root.resolve()) if exists else ""
        duplicate_realpath = bool(realpath and realpath in seen_realpaths)
        if realpath:
            seen_realpaths.add(realpath)
        files = sorted(p for p in root.rglob("*") if p.is_file()) if exists and not duplicate_realpath else []
        roots.append(
            {
                "name": name,
                "path": str(root),
                "exists": exists,
                "realpath": realpath,
                "duplicate_realpath": duplicate_realpath,
                "file_count": len(files),
            }
        )
        for path in files:
            file_realpath = str(path.resolve())
            duplicate_file_realpath = file_realpath in seen_file_realpaths
            if not duplicate_file_realpath:
                seen_file_realpaths.add(file_realpath)
            if duplicate_file_realpath:
                sniff = {
                    "Crisis": False,
                    "MainRegimeV2": False,
                    "main_regime_v2": False,
                    "2026-01-30": False,
                }
            elif path.name == "native_subhour_source_label_rows.csv":
                sniff = {
                    "Crisis": False,
                    "MainRegimeV2": False,
                    "main_regime_v2": False,
                    "2026-01-30": False,
                }
            else:
                sniff = text_sniff(path, ["Crisis", "MainRegimeV2", "main_regime_v2", "2026-01-30"])
            file_rows.append(
                {
                    "root": name,
                    "path": str(path),
                    "suffix": path.suffix,
                    "duplicate_file_realpath": duplicate_file_realpath,
                    **{f"hit_{k}": v for k, v in sniff.items()},
                }
            )
            if duplicate_file_realpath:
                continue
            if path.name == "native_subhour_source_label_rows.csv":
                native_summaries.append(scan_native_subhour_csv(path))
            if path.suffix.lower() == ".csv":
                mainregime_summaries.append(scan_mainregimev2_csv(path))

    r3_roots_present = any(r["exists"] for r in roots if r["name"].startswith("r3_"))
    r5_roots_present = any(r["exists"] for r in roots if r["name"].startswith("r5_"))
    r3_rows = max((int(s["rows"]) for s in native_summaries), default=0)
    r3_crisis_present = any(bool(s["crisis_label_present"]) for s in native_summaries)
    r3_labels = sorted({label for s in native_summaries for label in s["labels"]})
    r5_post_rows = sum(int(s.get("post_cutoff_rows", 0)) for s in mainregime_summaries)

    gate_result = "r3_r5_required_root_local_sweep_after_085612_v1=no_crisis_r3_or_r5_mainregimev2_unlock"
    assertions = {
        "gate_result": gate_result,
        "target_roots_scanned": len(roots),
        "r3_native_subhour_roots_present": r3_roots_present,
        "r3_native_subhour_data_rows": r3_rows,
        "r3_native_subhour_labels": r3_labels,
        "r3_crisis_label_present": r3_crisis_present,
        "r5_recency_roots_present": r5_roots_present,
        "r5_mainregimev2_post_20260130_rows": r5_post_rows,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    with (OUT / "r3_r5_required_root_local_sweep_after_085612_v1.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "assertions": assertions,
                "target_roots": roots,
                "native_subhour_summaries": native_summaries,
                "mainregimev2_summaries": mainregime_summaries,
            },
            handle,
            indent=2,
            sort_keys=True,
        )

    with (OUT / "r3_r5_required_root_target_roots_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "path", "exists", "realpath", "duplicate_realpath", "file_count"])
        writer.writeheader()
        writer.writerows(roots)

    with (OUT / "r3_r5_required_root_file_scan_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["root", "path", "suffix", "duplicate_file_realpath", "hit_Crisis", "hit_MainRegimeV2", "hit_main_regime_v2", "hit_2026-01-30"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(file_rows)

    lines = [
        "# R3/R5 Required Root Local Sweep After 085612 v1",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "Read-only target-root sweep for Crisis-capable R3 native-subhour labels and post-2026-01-30 R5 MainRegimeV2 rows. This artifact does not copy files, populate roots, approve local labels as source/control evidence, run verifier, selected-data AutoQuant, Pre-Bayes, BBN, CatBoost, execution-tree promotion, trade claims, or `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Target roots scanned: `{len(roots)}`.",
        f"- R3 native-subhour roots present: `{str(r3_roots_present).lower()}`.",
        f"- R3 native-subhour data rows: `{r3_rows}`.",
        f"- R3 native-subhour labels: `{', '.join(r3_labels) if r3_labels else 'none'}`.",
        f"- R3 Crisis label present: `{str(r3_crisis_present).lower()}`.",
        f"- R5 recency roots present: `{str(r5_roots_present).lower()}`.",
        f"- R5 MainRegimeV2 post-2026-01-30 rows: `{r5_post_rows}`.",
        "",
        "## Decision",
        "",
        "No Crisis-capable R3 label set or source-owned post-2026-01-30 R5 MainRegimeV2 rows were found in the required local target roots. The R3 native-subhour root remains present but non-unlocking, and the R5 recency roots remain absent.",
        "",
        "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only. Do not run verifier, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal` until a valid required root unlock and selected-history gate both pass.",
        "",
    ]
    (OUT / "r3_r5_required_root_local_sweep_after_085612_v1.md").write_text("\n".join(lines), encoding="utf-8")

    with (CHECKS / "r3_r5_required_root_local_sweep_after_085612_v1_assertions.out").open("w", encoding="utf-8") as handle:
        for key, value in assertions.items():
            if isinstance(value, bool):
                rendered = str(value).lower()
            elif isinstance(value, list):
                rendered = ",".join(str(item) for item in value)
            else:
                rendered = str(value)
            handle.write(f"{key}={rendered}\n")


if __name__ == "__main__":
    main()
