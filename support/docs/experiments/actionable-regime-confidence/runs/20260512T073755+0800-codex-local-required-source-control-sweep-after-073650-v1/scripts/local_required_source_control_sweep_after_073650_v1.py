#!/usr/bin/env python3
import csv
import hashlib
import json
import os
import time
from pathlib import Path


RUN_ID = "20260512T073755+0800-codex-local-required-source-control-sweep-after-073650-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "local-required-source-control-sweep-after-073650-v1"
CHECK_DIR = RUN_ROOT / "checks"

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}

APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")

SEARCH_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
    Path("/Users/thrill3r/Documents"),
    Path("/tmp"),
    Path("/private/tmp"),
]

KEYWORDS = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "positive_spoofing_layering_rows",
    "matched_negative_normal_activity_rows",
    "provenance_manifest",
    "MainRegimeV2",
    "mainregimev2",
    "native_subhour_source_label_rows",
    "stock_market_regimes_2026_extension",
    "stock-market-regimes-2026-extension",
    "owner_export",
    "owner-export",
    "databento",
    ".dbn",
    "mbo",
    "mbp",
    "order_lifecycle",
    "order-lifecycle",
    "oystacher",
    "3red",
    "3_red",
]

REQUIRED_FILENAMES = {
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
    "native_subhour_source_label_rows.csv",
    "stock_market_regimes_2026_extension.csv",
}


def sha256_file(path: Path, limit_bytes: int = 16 * 1024 * 1024) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        remaining = limit_bytes
        while remaining > 0:
            chunk = fh.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()


def safe_stat(path: Path) -> dict:
    try:
        st = path.stat()
        return {
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size": st.st_size,
            "mtime": st.st_mtime,
        }
    except FileNotFoundError:
        return {"exists": False, "is_file": False, "is_dir": False, "size": None, "mtime": None}


def list_target_files(root: Path, max_files: int = 200) -> list[dict]:
    if not root.exists():
        return []
    out = []
    for path in sorted(root.rglob("*")):
        if len(out) >= max_files:
            break
        if path.is_file():
            st = path.stat()
            out.append({
                "path": str(path),
                "name": path.name,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "required_filename": path.name in REQUIRED_FILENAMES,
                "keyword_hit": any(k.lower() in str(path).lower() for k in KEYWORDS),
            })
    return out


def approval_readback() -> dict:
    info = safe_stat(APPROVAL_PACKAGE)
    result = {"path": str(APPROVAL_PACKAGE), **info}
    if not info["exists"] or not info["is_file"]:
        result.update({
            "json_parse_ok": False,
            "approval_present": False,
            "canonical_merge_allowed_now": False,
            "downstream_rerun_allowed_now": False,
        })
        return result
    try:
        data = json.loads(APPROVAL_PACKAGE.read_text())
        assertions = data.get("assertions", {})
        result.update({
            "json_parse_ok": True,
            "gate_result": data.get("gate_result"),
            "approval_present": bool(assertions.get("approval_present")),
            "canonical_merge_allowed_now": bool(assertions.get("canonical_merge_allowed_now")),
            "downstream_rerun_allowed_now": bool(assertions.get("downstream_rerun_allowed_now")),
            "flip_controls_accepted_under_current_contract": bool(assertions.get("flip_controls_accepted_under_current_contract")),
            "row_counts": data.get("row_counts", {}),
            "sha256": sha256_file(APPROVAL_PACKAGE),
        })
    except Exception as exc:
        result.update({"json_parse_ok": False, "error": repr(exc)})
    return result


def recent_candidate_files(window_minutes: int = 180, max_depth: int = 5, max_files: int = 500) -> list[dict]:
    cutoff = time.time() - window_minutes * 60
    matches = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        stack = [(root, 0)]
        while stack and len(matches) < max_files:
            current, depth = stack.pop()
            try:
                entries = list(current.iterdir())
            except (PermissionError, FileNotFoundError, NotADirectoryError):
                continue
            for entry in entries:
                try:
                    st = entry.stat()
                except (PermissionError, FileNotFoundError):
                    continue
                if entry.is_dir() and depth < max_depth:
                    stack.append((entry, depth + 1))
                if not entry.is_file() or st.st_mtime < cutoff:
                    continue
                s = str(entry).lower()
                keyword_hits = [k for k in KEYWORDS if k.lower() in s]
                required_filename = entry.name in REQUIRED_FILENAMES
                if keyword_hits or required_filename:
                    matches.append({
                        "path": str(entry),
                        "name": entry.name,
                        "root": str(root),
                        "size": st.st_size,
                        "mtime": st.st_mtime,
                        "required_filename": required_filename,
                        "keyword_hits": keyword_hits,
                    })
    return sorted(matches, key=lambda x: (x["mtime"], x["path"]), reverse=True)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    target_roots = {}
    target_files = {}
    for label, root in TARGET_ROOTS.items():
        target_roots[label] = {"path": str(root), **safe_stat(root)}
        target_files[label] = list_target_files(root)

    approval = approval_readback()
    recent = recent_candidate_files()

    required_in_targets = [
        f for files in target_files.values() for f in files if f["required_filename"]
    ]
    required_recent = [f for f in recent if f["required_filename"]]
    unlock_like_recent = [
        f for f in recent
        if f["required_filename"] or any(
            k in f["keyword_hits"]
            for k in [
                "direct_manipulation_positive_rows",
                "direct_manipulation_matched_controls",
                "direct_manipulation_provenance",
                "positive_spoofing_layering_rows",
                "matched_negative_normal_activity_rows",
                "provenance_manifest",
                "native_subhour_source_label_rows",
                "stock_market_regimes_2026_extension",
            ]
        )
    ]

    result = {
        "run_id": RUN_ID,
        "gate_result": "local_required_source_control_sweep_after_073650_v1=no_new_required_root_no_unlock",
        "target_roots": target_roots,
        "target_file_counts": {k: len(v) for k, v in target_files.items()},
        "approval_package": approval,
        "recent_candidate_count": len(recent),
        "recent_required_filename_count": len(required_recent),
        "recent_unlock_like_count": len(unlock_like_recent),
        "required_files_in_target_roots": required_in_targets,
        "recent_candidates": recent[:200],
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    r6_present = target_roots["r6_owner_export"]["exists"]
    r5_present = target_roots["r5_recency_extension"]["exists"]
    r3_present = target_roots["r3_native_subhour"]["exists"]
    approval_present = approval.get("approval_present", False)
    canonical_merge_allowed = approval.get("canonical_merge_allowed_now", False)

    if r6_present and approval_present and canonical_merge_allowed:
        result["gate_result"] = "local_required_source_control_sweep_after_073650_v1=possible_r6_unlock_requires_manual_review"
        result["r6_owner_export_unlock"] = True
        result["valid_required_root_unlock"] = True
        result["source_control_evidence_acquired"] = True
    elif r5_present:
        result["gate_result"] = "local_required_source_control_sweep_after_073650_v1=possible_r5_unlock_requires_manual_review"
        result["r5_recency_unlock"] = True
        result["valid_required_root_unlock"] = True
        result["source_control_evidence_acquired"] = True
    elif r3_present and required_in_targets:
        result["known_r3_required_file_present"] = True
        result["known_r3_disposition"] = "present_but_prior_settled_board_evidence_keeps_tsie_derived_root_quarantined_and_non_promoting"
        result["manual_r3_review"] = {
            "decision": "known_tsie_root_non_promoting",
            "dataset_id": "sujinwo/tsie-market-regime-dataset",
            "crisis_absent": True,
            "trap_labels_fail_closed": True,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
        }

    (OUT_DIR / "local_required_source_control_sweep_after_073650_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    with (OUT_DIR / "local_required_source_control_sweep_after_073650_v1.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value"])
        writer.writerow(["gate_result", result["gate_result"]])
        for label, info in target_roots.items():
            writer.writerow([f"{label}_exists", info["exists"]])
            writer.writerow([f"{label}_file_count", len(target_files[label])])
        writer.writerow(["approval_present", approval.get("approval_present", False)])
        writer.writerow(["canonical_merge_allowed_now", approval.get("canonical_merge_allowed_now", False)])
        writer.writerow(["downstream_rerun_allowed_now", approval.get("downstream_rerun_allowed_now", False)])
        writer.writerow(["recent_candidate_count", len(recent)])
        writer.writerow(["recent_required_filename_count", len(required_recent)])
        writer.writerow(["recent_unlock_like_count", len(unlock_like_recent)])
        writer.writerow(["valid_required_root_unlock", result["valid_required_root_unlock"]])
        writer.writerow(["source_control_evidence_acquired", result["source_control_evidence_acquired"]])
        writer.writerow(["update_goal", result["update_goal"]])

    report = [
        "# Local Required Source/Control Sweep After 073650 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Scope",
        "",
        "Read-only local sweep for newly arrived required R3/R5/R6 source/control files after the `073650` tail registration. This does not mutate target roots, approve `.valid` decision packages, run verifier/calibration/merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Target Roots",
        "",
    ]
    for label, info in target_roots.items():
        report.append(f"- `{label}`: `{info['path']}` exists=`{str(info['exists']).lower()}` files=`{len(target_files[label])}`")
    report.extend([
        "",
        "## Approval Package",
        "",
        f"- package present: `{str(approval.get('exists', False)).lower()}`",
        f"- approval_present: `{str(approval.get('approval_present', False)).lower()}`",
        f"- canonical_merge_allowed_now: `{str(approval.get('canonical_merge_allowed_now', False)).lower()}`",
        f"- downstream_rerun_allowed_now: `{str(approval.get('downstream_rerun_allowed_now', False)).lower()}`",
        "",
        "## Recent Local Candidates",
        "",
        f"- recent candidate count: `{len(recent)}`",
        f"- recent required filename count: `{len(required_recent)}`",
        f"- recent unlock-like count: `{len(unlock_like_recent)}`",
        f"- known R3 disposition: `{result.get('known_r3_disposition', 'none')}`",
        "- manual R3 review: the required filenames are the already-known TSIE native-subhour root; `Crisis` is absent, trap labels are fail-closed, canonical merge was not run, and downstream provider/AutoQuant/Pre-Bayes/BBN/CatBoost/execution-tree was not rerun.",
        "",
        "## Decision",
        "",
        f"- accepted rows added: `{result['accepted_rows_added']}`",
        f"- R6 owner/export unlock: `{str(result['r6_owner_export_unlock']).lower()}`",
        f"- R5 recency unlock: `{str(result['r5_recency_unlock']).lower()}`",
        f"- R3 native-subhour unlock: `{str(result['r3_native_subhour_unlock']).lower()}`",
        f"- valid required-root unlock: `{str(result['valid_required_root_unlock']).lower()}`",
        f"- source/control evidence acquired: `{str(result['source_control_evidence_acquired']).lower()}`",
        f"- canonical merge: `{str(result['canonical_merge']).lower()}`",
        f"- downstream promotion rerun: `{str(result['downstream_promotion_rerun']).lower()}`",
        f"- strict full objective: `{str(result['strict_full_objective']).lower()}`",
        f"- trade usable: `{str(result['trade_usable']).lower()}`",
        f"- `update_goal={str(result['update_goal']).lower()}`",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
        "",
    ])
    (OUT_DIR / "local_required_source_control_sweep_after_073650_v1.md").write_text("\n".join(report))

    assertions = [
        f"gate_result={result['gate_result']}",
        f"r6_owner_export_root_present={str(target_roots['r6_owner_export']['exists']).lower()}",
        f"r5_recency_root_present={str(target_roots['r5_recency_extension']['exists']).lower()}",
        f"r3_native_subhour_root_present={str(target_roots['r3_native_subhour']['exists']).lower()}",
        f"source_label_equivalence_root_present={str(target_roots['source_label_equivalence']['exists']).lower()}",
        f"approval_present={str(approval.get('approval_present', False)).lower()}",
        f"canonical_merge_allowed_now={str(approval.get('canonical_merge_allowed_now', False)).lower()}",
        f"downstream_rerun_allowed_now={str(approval.get('downstream_rerun_allowed_now', False)).lower()}",
        f"recent_candidate_count={len(recent)}",
        f"recent_required_filename_count={len(required_recent)}",
        f"recent_unlock_like_count={len(unlock_like_recent)}",
        f"known_r3_required_file_present={str(result.get('known_r3_required_file_present', False)).lower()}",
        f"known_r3_disposition={result.get('known_r3_disposition', 'none')}",
        f"accepted_rows_added={result['accepted_rows_added']}",
        f"r6_owner_export_unlock={str(result['r6_owner_export_unlock']).lower()}",
        f"r5_recency_unlock={str(result['r5_recency_unlock']).lower()}",
        f"r3_native_subhour_unlock={str(result['r3_native_subhour_unlock']).lower()}",
        f"valid_required_root_unlock={str(result['valid_required_root_unlock']).lower()}",
        f"source_control_evidence_acquired={str(result['source_control_evidence_acquired']).lower()}",
        f"canonical_merge={str(result['canonical_merge']).lower()}",
        f"downstream_promotion_rerun={str(result['downstream_promotion_rerun']).lower()}",
        f"strict_full_objective={str(result['strict_full_objective']).lower()}",
        f"trade_usable={str(result['trade_usable']).lower()}",
        f"update_goal={str(result['update_goal']).lower()}",
    ]
    (CHECK_DIR / "local_required_source_control_sweep_after_073650_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
