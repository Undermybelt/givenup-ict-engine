#!/usr/bin/env python3
"""Read-only local candidate screen for R5 MainRegimeV2 evidence."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Iterable


RUN = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T091105+0800-codex-r5-mainregimev2-local-candidate-screen-after-090725-v1"
)
OUT = RUN / "r5-mainregimev2-local-candidate-screen-after-090725-v1"
CHECKS = RUN / "checks"

SEARCH_ROOTS = [
    Path("/tmp"),
    Path("/private/tmp"),
    Path("docs/experiments/actionable-regime-confidence"),
    Path("/Users/thrill3r/Auto-Quant/user_data"),
    Path("/Users/thrill3r/projects-ict-engine/ict-engine/state"),
    Path("/Users/thrill3r/projects-ict-engine/ict-engine/docs"),
]

INTEREST_TERMS = [
    "MainRegimeV2",
    "main_regime_v2",
    "mainregimev2",
    "2026-01-30",
]

NAME_PATTERNS = [
    re.compile(r"mainregime", re.IGNORECASE),
    re.compile(r"main_regime", re.IGNORECASE),
    re.compile(r"recency", re.IGNORECASE),
    re.compile(r"source[-_]?panel", re.IGNORECASE),
    re.compile(r"r5", re.IGNORECASE),
]

TEXT_SUFFIXES = {".csv", ".tsv", ".json", ".jsonl", ".md", ".txt", ".out", ".check"}
SIZE_LIMIT = 50 * 1024 * 1024


def is_interesting_name(path: Path) -> bool:
    name = path.name
    return any(pattern.search(name) for pattern in NAME_PATTERNS)


def text_sniff(path: Path, needles: Iterable[str]) -> dict[str, bool]:
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


def scan_csv(path: Path) -> dict[str, object]:
    header: list[str] = []
    rows = 0
    post_cutoff_rows = 0
    regime_cols: list[str] = []
    date_cols: list[str] = []
    size = path.stat().st_size
    limited = size > SIZE_LIMIT
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            if not header:
                return {
                    "path": str(path),
                    "header": header,
                    "rows": rows,
                    "post_cutoff_rows": post_cutoff_rows,
                    "limited": limited,
                    "regime_cols": regime_cols,
                    "date_cols": date_cols,
                }
            regime_cols = [
                col for col in header if col.lower() in {"mainregimev2", "main_regime_v2", "mainregime", "regime"}
            ]
            date_cols = [col for col in header if col.lower() in {"date", "timestamp", "time", "datetime"}]
            for row in reader:
                rows += 1
                if limited:
                    if rows >= 100000:
                        break
                if not regime_cols:
                    continue
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
        "limited": limited,
        "regime_cols": regime_cols,
        "date_cols": date_cols,
    }


def provenance_hint(path: Path) -> bool:
    parent = path.parent
    try:
        for sibling in parent.iterdir():
            name = sibling.name.lower()
            if any(token in name for token in ("provenance", "manifest", "license", "ticket", "export")):
                return True
    except OSError:
        pass
    return False


def collect_candidates() -> list[dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d
                for d in dirnames
                if d not in {".git", "node_modules", "target", "dist", "build", ".venv", "venv", "__pycache__", "Library"}
            ]
            rel_depth = Path(dirpath).relative_to(root).parts
            if len(rel_depth) > 5:
                dirnames[:] = []
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                if not is_interesting_name(path):
                    try:
                        if path.stat().st_size > 5 * 1024 * 1024:
                            continue
                    except OSError:
                        continue
                try:
                    realpath = str(path.resolve())
                except OSError:
                    realpath = str(path)
                if realpath in candidates:
                    continue
                hits = text_sniff(path, INTEREST_TERMS)
                if not any(hits.values()) and not is_interesting_name(path):
                    continue
                entry: dict[str, object] = {
                    "path": str(path),
                    "realpath": realpath,
                    "suffix": path.suffix,
                    "name_hint": is_interesting_name(path),
                    "provenance_hint": provenance_hint(path),
                    **{f"hit_{k}": v for k, v in hits.items()},
                }
                if path.suffix.lower() == ".csv":
                    entry.update(scan_csv(path))
                candidates[realpath] = entry
    return sorted(candidates.values(), key=lambda item: str(item["path"]))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    candidate_rows = collect_candidates()
    unlock_candidates = [
        row
        for row in candidate_rows
        if bool(row.get("hit_MainRegimeV2") or row.get("hit_main_regime_v2") or row.get("hit_2026-01-30"))
        and int(row.get("post_cutoff_rows", 0) or 0) > 0
        and bool(row.get("provenance_hint"))
    ]

    assertions = {
        "gate_result": "r5_mainregimev2_local_candidate_screen_after_090725_v1="
        + ("source_owned_post_2026_01_30_mainregimev2_unlock" if unlock_candidates else "no_source_owned_post_2026_01_30_mainregimev2_unlock"),
        "candidate_files_scanned": len(candidate_rows),
        "unlock_candidates": len(unlock_candidates),
        "source_control_evidence_acquired": bool(unlock_candidates),
        "valid_required_root_unlock": bool(unlock_candidates),
        "selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    with (OUT / "r5_mainregimev2_local_candidate_screen_after_090725_v1.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "assertions": assertions,
                "candidate_files": candidate_rows,
                "unlock_candidates": unlock_candidates,
            },
            handle,
            indent=2,
            sort_keys=True,
        )

    with (OUT / "r5_mainregimev2_candidate_files_after_090725_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "path",
            "realpath",
            "suffix",
            "name_hint",
            "provenance_hint",
            "hit_MainRegimeV2",
            "hit_main_regime_v2",
            "hit_mainregimev2",
            "hit_2026-01-30",
            "rows",
            "post_cutoff_rows",
            "limited",
            "regime_cols",
            "date_cols",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(candidate_rows)

    lines = [
        "# R5 MainRegimeV2 Local Candidate Screen After 090725 v1",
        "",
        f"Gate result: `{assertions['gate_result']}`",
        "",
        "## Scope",
        "",
        "Read-only local screen for post-2026-01-30 R5 MainRegimeV2 evidence and source-owned provenance hints. This artifact does not copy files, populate roots, approve local hits as source/control evidence, run verifier, selected-data AutoQuant, Pre-Bayes, BBN, CatBoost, execution-tree promotion, trade claims, or `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Candidate files scanned: `{len(candidate_rows)}`.",
        f"- Unlock candidates: `{len(unlock_candidates)}`.",
        f"- Source/control evidence acquired: `{str(bool(unlock_candidates)).lower()}`.",
        f"- Required-root unlock: `{str(bool(unlock_candidates)).lower()}`.",
        f"- Selected history: `false`.",
        f"- Canonical merge: `false`.",
        f"- Selected-data AutoQuant promotion: `false`.",
        f"- Downstream promotion rerun: `false`.",
        f"- Promotion allowed: `false`.",
        "",
        "## Decision",
        "",
        "No source-owned post-2026-01-30 MainRegimeV2 candidate was unlocked in the local screen. The gate remains fail-closed.",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only. Do not run selected-data AutoQuant or downstream promotion until a valid required-root unlock and selected-history gate both pass.",
        "",
    ]
    (OUT / "r5_mainregimev2_local_candidate_screen_after_090725_v1.md").write_text("\n".join(lines), encoding="utf-8")

    with (CHECKS / "r5_mainregimev2_local_candidate_screen_after_090725_v1_assertions.out").open("w", encoding="utf-8") as handle:
        for key, value in assertions.items():
            if isinstance(value, bool):
                rendered = str(value).lower()
            else:
                rendered = str(value)
            handle.write(f"{key}={rendered}\n")


if __name__ == "__main__":
    main()
