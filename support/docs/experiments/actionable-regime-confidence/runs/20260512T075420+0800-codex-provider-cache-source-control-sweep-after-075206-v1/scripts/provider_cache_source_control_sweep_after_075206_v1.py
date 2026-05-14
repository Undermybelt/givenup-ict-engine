#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "provider-cache-source-control-sweep-after-075206-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

R6_REQUIRED = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]

TARGET_ROOTS = {
    "r6_owner_export": [
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    ],
    "r5_recency": [
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    ],
    "r3_native_subhour": [
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
    ],
    "source_label_equivalence_target": [
        Path("/tmp/ict-engine-source-label-equivalence-v1"),
        Path("/private/tmp/ict-engine-source-label-equivalence-v1"),
    ],
    "source_label_equivalence_intake": [
        Path("/tmp/ict-engine-source-label-equivalence-intake"),
        Path("/private/tmp/ict-engine-source-label-equivalence-intake"),
    ],
}

PROVIDER_ROOTS = [
    Path("/Users/thrill3r/Auto-Quant/user_data/data"),
    Path("/Users/thrill3r/Auto-Quant/user_data/strategies"),
    Path("/Users/thrill3r/Auto-Quant/user_data/strategies_external"),
    Path("/Users/thrill3r/Downloads/Tomac"),
    Path("/Users/thrill3r/tradingview-mcp"),
    Path("/Users/thrill3r/Library/Application Support/TradingView"),
    Path("/Users/thrill3r/Jts"),
    Path("/Users/thrill3r/.ibkr"),
    Path("/Users/thrill3r/.kraken"),
    Path("/Users/thrill3r/projects-ict-engine/ict-engine/state"),
    Path("/tmp/ict-engine-board-a-064259-runtime-v1"),
]

TEXT_EXTS = {".csv", ".json", ".md", ".txt", ".out", ".log", ".yaml", ".yml"}
HINT_EXTS = {".csv", ".json", ".md", ".txt", ".out", ".log", ".parquet", ".feather", ".dbn", ".zip", ".rar"}
NEEDLES = [
    "MainRegimeV2",
    "main_regime_v2",
    "main_regime_v2_label",
    "source_confidence",
    "validation_instruments",
    "validation_periods",
    "validation_market_contexts",
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "matched_negative_group_id",
    "approval_present",
    "canonical_merge_allowed_now",
    "downstream_rerun_allowed_now",
    "Crisis",
    "Bull",
    "Bear",
    "Sideways",
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_line(path: Path) -> str:
    try:
        with path.open("rb") as f:
            return f.readline(4096).decode("utf-8", "replace").strip()
    except Exception as exc:
        return f"READ_ERROR:{type(exc).__name__}:{exc}"


def small_text_sample(path: Path) -> str:
    try:
        if path.stat().st_size > 2_000_000:
            return first_line(path)
        return path.read_text(errors="replace")[:200_000]
    except Exception as exc:
        return f"READ_ERROR:{type(exc).__name__}:{exc}"


def path_status(path: Path, required_files: list[str] | None = None) -> dict:
    required_files = required_files or []
    present = []
    missing = list(required_files)
    if path.exists() and path.is_dir():
        names = {p.name for p in path.iterdir()}
        present = [name for name in required_files if name in names]
        missing = [name for name in required_files if name not in names]
    return {
        "root": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "file_count": sum(1 for _ in path.rglob("*") if _.is_file()) if path.exists() and path.is_dir() else (1 if path.is_file() else 0),
        "required_files": required_files,
        "present_required_files": present,
        "missing_required_files": missing,
    }


def inspect_approval_package(path: Path) -> dict:
    out = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return out
    try:
        data = json.loads(path.read_text(errors="replace"))
        for key in [
            "approval_present",
            "canonical_merge_allowed_now",
            "downstream_rerun_allowed_now",
            "flip_controls_accepted_under_current_contract",
            "positive_spoof_rows",
            "flip_rows",
            "matched_groups",
        ]:
            out[key] = data.get(key)
    except Exception as exc:
        out["read_error"] = f"{type(exc).__name__}:{exc}"
    return out


def inspect_r3_root(root: Path) -> dict:
    out = path_status(root)
    labels = set()
    provenance = None
    csv_path = root / "native_subhour_source_label_rows.csv"
    prov_path = root / "native_subhour_source_label_provenance.json"
    if prov_path.exists():
        try:
            pdata = json.loads(prov_path.read_text(errors="replace"))
            provenance = pdata.get("source_dataset") or pdata.get("dataset") or pdata.get("provenance") or pdata
        except Exception as exc:
            provenance = f"READ_ERROR:{type(exc).__name__}:{exc}"
    if csv_path.exists():
        try:
            with csv_path.open(newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    for key in ("main_regime_v2_label", "label", "regime_label", "accepted_mapping_label"):
                        val = (row.get(key) or "").strip()
                        if val:
                            labels.add(val)
                    if i >= 200_000:
                        break
        except Exception as exc:
            out["label_read_error"] = f"{type(exc).__name__}:{exc}"
    out["observed_labels"] = sorted(labels)
    out["crisis_present"] = "Crisis" in labels
    out["provenance"] = provenance
    out["known_tsie"] = "tsie" in json.dumps(provenance, ensure_ascii=False).lower() if provenance is not None else False
    return out


def scan_provider_roots() -> list[dict]:
    hits: list[dict] = []
    max_files_per_root = 2500
    for root in PROVIDER_ROOTS:
        if not root.exists():
            hits.append({
                "root": str(root),
                "path": "",
                "exists": False,
                "kind": "root_absent",
                "matched_terms": "",
                "header": "",
                "size": 0,
                "mtime": "",
            })
            continue
        count = 0
        for path in root.rglob("*") if root.is_dir() else [root]:
            if not path.is_file():
                continue
            count += 1
            if count > max_files_per_root:
                hits.append({
                    "root": str(root),
                    "path": "",
                    "exists": True,
                    "kind": "scan_truncated",
                    "matched_terms": f"max_files_per_root={max_files_per_root}",
                    "header": "",
                    "size": 0,
                    "mtime": "",
                })
                break
            lower_name = path.name.lower()
            if path.suffix.lower() not in HINT_EXTS and not any(n.lower() in lower_name for n in NEEDLES):
                continue
            text = ""
            header = ""
            if path.suffix.lower() in TEXT_EXTS:
                header = first_line(path)
                if path.stat().st_size <= 2_000_000:
                    text = small_text_sample(path)
                else:
                    text = header
            haystack = f"{path.name}\n{header}\n{text}"
            matched = [needle for needle in NEEDLES if needle.lower() in haystack.lower()]
            filename_required = [name for name in R6_REQUIRED if name.lower() == lower_name]
            if matched or filename_required:
                st = path.stat()
                hits.append({
                    "root": str(root),
                    "path": str(path),
                    "exists": True,
                    "kind": "candidate_hit",
                    "matched_terms": "|".join(sorted(set(matched + filename_required))),
                    "header": header[:500],
                    "size": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                })
    return hits


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_path(BOARD)
    target_status = {}
    for name, roots in TARGET_ROOTS.items():
        target_status[name] = []
        for root in roots:
            if name == "r6_owner_export":
                target_status[name].append(path_status(root, R6_REQUIRED))
            elif name == "r3_native_subhour":
                target_status[name].append(inspect_r3_root(root))
            else:
                target_status[name].append(path_status(root))

    approvals = [
        inspect_approval_package(Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")),
        inspect_approval_package(Path("/tmp/r6_oystacher_approval_decision_package_v1.json.valid")),
    ]
    provider_hits = scan_provider_roots()

    r6_unlock = any(s["exists"] and not s["missing_required_files"] for s in target_status["r6_owner_export"]) and any(
        a.get("approval_present") and a.get("canonical_merge_allowed_now") for a in approvals
    )
    r5_unlock = any(False for _ in target_status["r5_recency"])
    r3_unlock = any(s.get("crisis_present") and not s.get("known_tsie") for s in target_status["r3_native_subhour"])
    valid_unlock = bool(r6_unlock or r5_unlock or r3_unlock)

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256": board_hash,
        "gate_result": "provider_cache_source_control_sweep_after_075206_v1=no_valid_required_root_no_unlock",
        "target_status": target_status,
        "approval_packages": approvals,
        "provider_roots_scanned": [str(p) for p in PROVIDER_ROOTS],
        "candidate_hit_count": sum(1 for h in provider_hits if h["kind"] == "candidate_hit"),
        "root_absent_count": sum(1 for h in provider_hits if h["kind"] == "root_absent"),
        "scan_truncated_count": sum(1 for h in provider_hits if h["kind"] == "scan_truncated"),
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": r6_unlock,
        "r5_recency_unlock": r5_unlock,
        "r3_native_subhour_unlock": r3_unlock,
        "valid_required_root_unlock": valid_unlock,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "provider_cache_source_control_sweep_after_075206_v1.json"
    csv_path = OUT_DIR / "provider_cache_source_control_candidates_v1.csv"
    md_path = OUT_DIR / "provider_cache_source_control_sweep_after_075206_v1.md"
    assertions_path = CHECK_DIR / "provider_cache_source_control_sweep_after_075206_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["root", "path", "exists", "kind", "matched_terms", "header", "size", "mtime"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(provider_hits)

    lines = [
        "# Provider Cache Source/Control Sweep After 075206 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Gate result: `provider_cache_source_control_sweep_after_075206_v1=no_valid_required_root_no_unlock`",
        "",
        "## Scope",
        "",
        "Bounded source/control acquisition sweep after the `075206` current-objective audit. It checks exact R3/R5/R6 target roots plus local provider/cache roots associated with Auto-Quant, TradingView, IBKR, Kraken, Tomac/Databento, and the Board A runtime. It does not mutate target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Board hash before artifact: `{board_hash}`.",
        f"- Provider/cache candidate hits: `{summary['candidate_hit_count']}`.",
        f"- Provider/cache absent roots: `{summary['root_absent_count']}`.",
        f"- Provider/cache truncated scans: `{summary['scan_truncated_count']}`.",
        f"- R6 owner/export unlock: `{str(r6_unlock).lower()}`.",
        f"- R5 recency unlock: `{str(r5_unlock).lower()}`.",
        f"- R3 native-subhour unlock: `{str(r3_unlock).lower()}`.",
        f"- Valid required-root unlock: `{str(valid_unlock).lower()}`.",
        "",
        "## Decision",
        "",
        "No provider/cache path supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
        "",
        "Accepted rows added `0`; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Candidate CSV: `{csv_path.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only before direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertion_lines = [
        "gate_result=provider_cache_source_control_sweep_after_075206_v1=no_valid_required_root_no_unlock",
        f"candidate_hit_count={summary['candidate_hit_count']}",
        f"root_absent_count={summary['root_absent_count']}",
        f"scan_truncated_count={summary['scan_truncated_count']}",
        f"r6_owner_export_unlock={str(r6_unlock).lower()}",
        f"r5_recency_unlock={str(r5_unlock).lower()}",
        f"r3_native_subhour_unlock={str(r3_unlock).lower()}",
        f"valid_required_root_unlock={str(valid_unlock).lower()}",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print("\n".join(assertion_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
