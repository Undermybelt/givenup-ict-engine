#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T081155+0800-codex-source-control-arrival-poll-after-080837-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "source-control-arrival-poll-after-080837-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}
APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
ENV_HINTS = [
    "DATABENTO_API_KEY",
    "DATABENTO_KEY",
    "CME_API_KEY",
    "CME_DATAMINE_API_KEY",
    "CBOE_API_KEY",
    "CFE_API_KEY",
    "IBKR_ACCOUNT_ID",
    "TV_SESSION",
    "KAGGLE_USERNAME",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sample_text_hits(path: Path, needles: tuple[str, ...], max_files: int = 200) -> dict[str, int]:
    hits = {needle: 0 for needle in needles}
    if not path.exists():
        return hits
    files = [p for p in path.rglob("*") if p.is_file()]
    for file_path in files[:max_files]:
        if file_path.stat().st_size > 2_000_000:
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lower = text.lower()
        for needle in needles:
            if needle.lower() in lower:
                hits[needle] += 1
    return hits


def summarize_root(name: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    files = [p for p in path.rglob("*") if p.is_file()] if exists else []
    labels = sample_text_hits(path, ("Crisis", "MainRegimeV2", "positive_spoofing", "matched_control", "owner_export"))
    return {
        "name": name,
        "path": str(path),
        "exists": exists,
        "file_count": len(files),
        "sample_files": [str(p) for p in files[:12]],
        "crisis_hits": labels["Crisis"],
        "mainregimev2_hits": labels["MainRegimeV2"],
        "positive_spoofing_hits": labels["positive_spoofing"],
        "matched_control_hits": labels["matched_control"],
        "owner_export_hits": labels["owner_export"],
    }


def load_approval(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    out: dict[str, Any] = {"exists": True, "path": str(path), "sha256": sha256_file(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        out["parse_error"] = repr(exc)
        return out
    for key in (
        "approval_present",
        "canonical_merge_allowed_now",
        "downstream_rerun_allowed_now",
        "update_goal",
        "r6_owner_export_unlock",
    ):
        out[key] = payload.get(key)
    return out


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    root_rows = [summarize_root(name, path) for name, path in TARGET_ROOTS.items()]
    approval = load_approval(APPROVAL_PACKAGE)
    env_rows = [{"name": name, "present": bool(os.environ.get(name))} for name in ENV_HINTS]

    r6_row = next(row for row in root_rows if row["name"] == "r6_owner_export")
    r5_row = next(row for row in root_rows if row["name"] == "r5_recency")
    r3_row = next(row for row in root_rows if row["name"] == "r3_native_subhour")
    approval_present = approval.get("approval_present") is True
    r6_owner_export_unlock = bool(
        r6_row["exists"]
        and r6_row["positive_spoofing_hits"] > 0
        and r6_row["matched_control_hits"] > 0
        and r6_row["owner_export_hits"] > 0
        and approval_present
    )
    r5_recency_unlock = bool(r5_row["exists"] and r5_row["mainregimev2_hits"] > 0)
    r3_native_subhour_unlock = bool(r3_row["exists"] and r3_row["crisis_hits"] > 0 and r3_row["mainregimev2_hits"] > 0)
    valid_required_root_unlock = r6_owner_export_unlock or r5_recency_unlock or r3_native_subhour_unlock

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "source_control_arrival_poll_after_080837_v1=no_new_required_root_no_unlock",
        "board_hash_before": sha256_file(BOARD_A),
        "r6_owner_export_unlock": r6_owner_export_unlock,
        "r5_recency_unlock": r5_recency_unlock,
        "r3_native_subhour_unlock": r3_native_subhour_unlock,
        "approval_unlock": approval_present,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": False,
        "accepted_rows_added": 0,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = ARTIFACT_DIR / "source_control_arrival_poll_after_080837_v1.json"
    csv_path = ARTIFACT_DIR / "source_control_arrival_poll_after_080837_v1.csv"
    env_csv_path = ARTIFACT_DIR / "source_control_arrival_env_hints_after_080837_v1.csv"
    md_path = ARTIFACT_DIR / "source_control_arrival_poll_after_080837_v1.md"
    assertions_path = CHECK_DIR / "source_control_arrival_poll_after_080837_v1_assertions.out"

    json_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "target_roots": root_rows,
                "approval_package": approval,
                "env_hints": env_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "name",
                "path",
                "exists",
                "file_count",
                "crisis_hits",
                "mainregimev2_hits",
                "positive_spoofing_hits",
                "matched_control_hits",
                "owner_export_hits",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(root_rows)
    with env_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "present"])
        writer.writeheader()
        writer.writerows(env_rows)

    lines = [
        "# Source/Control Arrival Poll After 080837 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{summary['gate_result']}`",
        "",
        "## Scope",
        "",
        "Read-only post-`080837` arrival poll for required Board A source/control roots, R6 approval package state, and non-secret provider/export credential hints. It does not mutate target roots, approve rows, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Target Root Readback",
        "",
    ]
    for row in root_rows:
        lines.append(
            f"- `{row['name']}` `{row['path']}`: exists `{str(row['exists']).lower()}`, files `{row['file_count']}`, Crisis hits `{row['crisis_hits']}`, MainRegimeV2 hits `{row['mainregimev2_hits']}`, positive hits `{row['positive_spoofing_hits']}`, matched-control hits `{row['matched_control_hits']}`, owner-export hits `{row['owner_export_hits']}`."
        )
    lines.extend(
        [
            "",
            "## Approval / Credential Hints",
            "",
            f"- R6 approval package exists `{str(approval.get('exists', False)).lower()}`, approval present `{str(approval.get('approval_present') is True).lower()}`, canonical merge allowed `{str(approval.get('canonical_merge_allowed_now') is True).lower()}`, downstream rerun allowed `{str(approval.get('downstream_rerun_allowed_now') is True).lower()}`.",
            f"- Provider/export credential hint names present: `{sum(1 for row in env_rows if row['present'])}` of `{len(env_rows)}` checked. Values were not printed.",
            "",
            "## Decision",
            "",
            "No new required root or approval unlock arrived after `080837`. R3 native-subhour files remain insufficient without Crisis/MainRegimeV2 support; R5 recency and R6 owner/export roots remain non-unlocking.",
            "",
            "Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Target-root CSV: `{csv_path.relative_to(REPO)}`",
            f"- Env hint CSV: `{env_csv_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only before direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        f"gate_result={summary['gate_result']}",
        f"r6_owner_export_root_present={str(r6_row['exists']).lower()}",
        f"r5_recency_root_present={str(r5_row['exists']).lower()}",
        f"r3_native_subhour_root_present={str(r3_row['exists']).lower()}",
        f"approval_present={str(approval_present).lower()}",
        f"r6_owner_export_unlock={str(r6_owner_export_unlock).lower()}",
        f"r5_recency_unlock={str(r5_recency_unlock).lower()}",
        f"r3_native_subhour_unlock={str(r3_native_subhour_unlock).lower()}",
        f"valid_required_root_unlock={str(valid_required_root_unlock).lower()}",
        "accepted_rows_added=0",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
