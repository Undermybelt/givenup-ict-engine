#!/usr/bin/env python3
"""Read-only Board A source/control arrival poll after the 083618 local sweeps."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T084829+0800-codex-source-control-arrival-poll-after-083618-v1"
SLUG = "source-control-arrival-poll-after-083618-v1"
GATE = "source_control_arrival_poll_after_083618_v1=no_new_required_root_no_unlock"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / SLUG
CHECK_DIR = RUN_ROOT / "checks"

TARGET_ROOTS = [
    (
        "r6_owner_export_tmp",
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    ),
    (
        "r6_owner_export_private_tmp",
        Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    ),
    (
        "r5_recency_tmp",
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
    (
        "r5_recency_private_tmp",
        Path("/private/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
    (
        "r3_native_subhour_tmp",
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
    (
        "r3_native_subhour_private_tmp",
        Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
]

RECENT_STUB_ROOTS = [
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T084654+0800-codex-current-objective-audit-after-083618-v1",
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T084727+0800-codex-local-source-control-wide-header-sweep-after-083618-v1",
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083711+0800-codex-r6-approved-dispatch-channel-readback-after-083108-v1",
]

PRIOR_ASSERTIONS = [
    (
        "083108_arrival_poll",
        "20260512T083108+0800-codex-source-control-arrival-poll-after-082720-v1/checks/source_control_arrival_poll_after_082720_v1_assertions.out",
    ),
    (
        "083545_dispatch_channel",
        "20260512T083545+0800-codex-r6-approved-dispatch-channel-readback-after-083108-v1/checks/r6_approved_dispatch_channel_readback_after_083108_v1_assertions.out",
    ),
    (
        "083559_local_order_lifecycle_sweep",
        "20260512T083559+0800-codex-local-order-lifecycle-source-sweep-after-083108-v1/checks/local_order_lifecycle_source_sweep_after_083108_v1_assertions.out",
    ),
    (
        "083618_tomac_header_inventory",
        "20260512T083618+0800-codex-tomac-futures-header-inventory-after-083108-v1/checks/tomac_futures_header_inventory_after_083108_v1_assertions.out",
    ),
    (
        "083703_zip_header_sweep",
        "20260512T083703+0800-codex-local-order-lifecycle-zip-header-sweep-after-083450-v1/checks/local_order_lifecycle_zip_header_sweep_after_083450_v1_assertions.out",
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {"present": str(path.exists()).lower()}
    if not path.exists():
        return parsed
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("PASS "):
            line = line[5:]
        if line.startswith("FAIL "):
            line = line[5:]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "pass"}


def first(parsed: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        if key in parsed:
            return parsed[key]
    return default


def count_csv_rows(path: Path, limit: int = 1_000_000) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for count, _row in enumerate(reader, start=1):
            if count >= limit:
                break
    return count


def inspect_target_root(name: str, path: Path, required_files: list[str]) -> dict[str, object]:
    required_presence = {file_name: (path / file_name).exists() for file_name in required_files}
    sample_files: list[str] = []
    if path.exists() and path.is_dir():
        for child in sorted(path.iterdir()):
            if child.is_file():
                sample_files.append(str(child))
            if len(sample_files) >= 20:
                break
    elif path.exists() and path.is_file():
        sample_files.append(str(path))

    row: dict[str, object] = {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "required_files_present": required_presence,
        "complete_required_file_set": bool(required_files) and all(required_presence.values()),
        "sampled_files": len(sample_files),
        "sample_files": sample_files,
    }
    if name.startswith("r3_native_subhour") and path.exists():
        row["rows_sampled"] = count_csv_rows(path / "native_subhour_source_label_rows.csv")
    return row


def inspect_stub_root(path: Path) -> dict[str, object]:
    files = sorted(child for child in path.rglob("*") if child.is_file()) if path.exists() else []
    return {
        "path": rel(path),
        "exists": path.exists(),
        "file_count": len(files),
        "terminal_artifacts_present": any(file.suffix in {".json", ".csv", ".md", ".out"} for file in files),
        "sample_files": [rel(file) for file in files[:20]],
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    target_rows = [inspect_target_root(name, path, required) for name, path, required in TARGET_ROOTS]
    stub_rows = [inspect_stub_root(path) for path in RECENT_STUB_ROOTS]

    prior_root = REPO / "docs/experiments/actionable-regime-confidence/runs"
    assertion_rows: list[dict[str, object]] = []
    prior_valid_unlock = False
    prior_source_control = False
    prior_update_goal = False
    for name, relative in PRIOR_ASSERTIONS:
        path = prior_root / relative
        parsed = parse_assertions(path)
        valid_unlock = truthy(first(parsed, "valid_required_root_unlock"))
        source_control = truthy(first(parsed, "source_control_evidence_acquired"))
        update_goal = truthy(first(parsed, "update_goal"))
        prior_valid_unlock = prior_valid_unlock or valid_unlock
        prior_source_control = prior_source_control or source_control
        prior_update_goal = prior_update_goal or update_goal
        assertion_rows.append(
            {
                "name": name,
                "path": rel(path),
                "present": parsed["present"],
                "gate_result": first(parsed, "gate_result", "gate"),
                "accepted_rows_added": first(parsed, "accepted_rows_added", default="0"),
                "valid_required_root_unlock": str(valid_unlock).lower(),
                "source_control_evidence_acquired": str(source_control).lower(),
                "update_goal": str(update_goal).lower(),
            }
        )

    r6_complete = any(row["complete_required_file_set"] for row in target_rows if str(row["name"]).startswith("r6_"))
    r5_complete = any(row["complete_required_file_set"] for row in target_rows if str(row["name"]).startswith("r5_"))
    r3_complete = any(row["complete_required_file_set"] for row in target_rows if str(row["name"]).startswith("r3_"))
    terminal_stub_count = sum(1 for row in stub_rows if row["terminal_artifacts_present"])

    payload = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "gate_result": GATE,
        "target_roots": target_rows,
        "recent_stub_roots": stub_rows,
        "prior_assertion_rows": assertion_rows,
        "r6_owner_export_complete_required_file_set": r6_complete,
        "r5_recency_complete_required_file_set": r5_complete,
        "r3_native_subhour_complete_required_file_set": r3_complete,
        "recent_stub_terminal_artifact_count": terminal_stub_count,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "prior_any_valid_required_root_unlock": prior_valid_unlock,
        "prior_any_source_control_evidence_acquired": prior_source_control,
        "prior_any_update_goal": prior_update_goal,
    }

    json_path = OUT_DIR / "source_control_arrival_poll_after_083618_v1.json"
    target_csv = OUT_DIR / "source_control_target_roots_after_083618_v1.csv"
    stub_csv = OUT_DIR / "recent_nonterminal_run_roots_after_083618_v1.csv"
    prior_csv = OUT_DIR / "prior_assertion_readback_after_083618_v1.csv"
    report_path = OUT_DIR / "source_control_arrival_poll_after_083618_v1.md"
    assertions_path = CHECK_DIR / "source_control_arrival_poll_after_083618_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        target_csv,
        [
            {
                "name": row["name"],
                "path": row["path"],
                "exists": row["exists"],
                "is_dir": row["is_dir"],
                "complete_required_file_set": row["complete_required_file_set"],
                "sampled_files": row["sampled_files"],
                "required_files_present": json.dumps(row["required_files_present"], sort_keys=True),
            }
            for row in target_rows
        ],
        ["name", "path", "exists", "is_dir", "complete_required_file_set", "sampled_files", "required_files_present"],
    )
    write_csv(
        stub_csv,
        stub_rows,
        ["path", "exists", "file_count", "terminal_artifacts_present", "sample_files"],
    )
    write_csv(
        prior_csv,
        assertion_rows,
        [
            "name",
            "path",
            "present",
            "gate_result",
            "accepted_rows_added",
            "valid_required_root_unlock",
            "source_control_evidence_acquired",
            "update_goal",
        ],
    )

    report = [
        "# Source/Control Arrival Poll After 083618 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        "Read-only arrival poll after the 083618 local Tomac header inventory and",
        "after later empty run-root stubs appeared. This artifact checks only whether",
        "the required R6/R5/R3 source/control roots have arrived and whether recent",
        "stub roots have terminal files. It does not approve local root presence,",
        "run direct verifier, run canonical merge, run selected-data AutoQuant, run",
        "filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree",
        "promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Required Roots",
        "",
        "| Name | Exists | Complete required file set | Sampled files |",
        "|---|---:|---:|---:|",
    ]
    for row in target_rows:
        report.append(
            f"| `{row['name']}` | `{row['exists']}` | `{row['complete_required_file_set']}` | `{row['sampled_files']}` |"
        )
    report.extend(
        [
            "",
            "## Recent Stub Roots",
            "",
            "| Path | Exists | File count | Terminal artifacts present |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in stub_rows:
        report.append(
            f"| `{row['path']}` | `{row['exists']}` | `{row['file_count']}` | `{row['terminal_artifacts_present']}` |"
        )
    report.extend(
        [
            "",
            "## Decision",
            "",
            f"- R6 owner-export complete required file set: `{r6_complete}`.",
            f"- R5 recency complete required file set: `{r5_complete}`.",
            f"- R3 native-subhour complete required file set: `{r3_complete}`; still non-unlocking without accepted source/control approval.",
            f"- Recent stub roots with terminal artifacts: `{terminal_stub_count}`.",
            "- Accepted rows added: `0`.",
            "- Valid required-root unlock: `false`.",
            "- Source/control evidence acquired: `false`.",
            "- Canonical merge: `false`.",
            "- Selected-data AutoQuant promotion: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Strict full objective: `false`.",
            "- Trade usable: `false`.",
            "- Promotion allowed: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. The live unblocker remains an",
            "owner-approved/authenticated FINRA, venue-surveillance, CAT-like,",
            "CME/Cboe/CFE order-lifecycle export with positives and matched normal",
            "controls, or explicit same-exhibit `FLIP`-as-control approval.",
            "",
        ]
    )
    report_path.write_text("\n".join(report), encoding="utf-8")

    assertions = [
        f"gate_result={GATE}",
        "accepted_rows_added=0",
        f"r6_owner_export_complete_required_file_set={str(r6_complete).lower()}",
        f"r5_recency_complete_required_file_set={str(r5_complete).lower()}",
        f"r3_native_subhour_complete_required_file_set={str(r3_complete).lower()}",
        f"recent_stub_terminal_artifact_count={terminal_stub_count}",
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
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
