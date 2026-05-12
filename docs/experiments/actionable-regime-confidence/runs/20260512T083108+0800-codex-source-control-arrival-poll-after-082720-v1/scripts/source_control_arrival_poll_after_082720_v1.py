#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T083108+0800-codex-source-control-arrival-poll-after-082720-v1"
SLUG = "source-control-arrival-poll-after-082720-v1"
GATE = "source_control_arrival_poll_after_082720_v1=no_new_required_root_no_unlock"

REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"

TARGET_ROOTS = [
    ("r6_owner_export_tmp", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r6_owner_export_private_tmp", Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r5_recency_tmp", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("r5_recency_private_tmp", Path("/private/tmp/ict-engine-source-panel-recency-extension")),
    ("r3_native_subhour_tmp", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r3_native_subhour_private_tmp", Path("/private/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r6_approval_decision_package", Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")),
]

ASSERTION_FILES = [
    (
        "082337_required_root_dispatch_gate_corrected",
        "20260512T082337+0800-codex-post-081705-required-root-dispatch-gate-v1/checks/post_081705_required_root_dispatch_gate_v1_assertions.out",
    ),
    (
        "082430_runtime_readiness",
        "20260512T082430+0800-codex-runtime-readiness-after-082215-v1/checks/runtime_readiness_after_082215_v1_assertions.out",
    ),
    (
        "082523_selected_history_correction",
        "20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1/checks/source_control_selected_history_poll_after_082215_v1_correction_assertions.out",
    ),
    (
        "082629_local_databento_archive",
        "20260512T082629+0800-codex-local-databento-archive-readback-after-082240-v1/checks/local_databento_archive_readback_after_082240_v1_assertions.out",
    ),
    (
        "082720_current_objective_audit",
        "20260512T082720+0800-codex-current-objective-audit-after-082458-v1/checks/current_objective_audit_after_082458_v1_assertions.out",
    ),
]

OWNER_ENV_NEEDLES = [
    "CME",
    "CBOE",
    "CFE",
    "FINRA",
    "CAT",
    "DATABENTO",
    "BARCHART",
    "POLYGON",
    "NASDAQ",
    "IBKR",
    "TRADINGVIEW",
    "KRAKEN",
    "ALPACA",
    "OPRA",
    "CFTC",
    "COURTLISTENER",
    "PACER",
    "RECAP",
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


def parse_kv_assertions(path: Path) -> dict[str, str]:
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


def sample_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    if root.is_file():
        return [str(root)]
    return [str(path) for path in sorted(root.iterdir()) if path.is_file()][:20]


def inspect_r3_labels(root: Path) -> dict[str, object]:
    csv_path = root / "native_subhour_source_label_rows.csv"
    if not csv_path.exists():
        return {"rows": 0, "labels": [], "main_regime_v2_hits": 0}
    labels: set[str] = set()
    main_hits = 0
    rows = 0
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        label_fields = [name for name in fieldnames if "label" in name.lower() or "regime" in name.lower()]
        for row in reader:
            rows += 1
            for field in label_fields:
                value = (row.get(field) or "").strip()
                if value:
                    labels.add(value)
                    if value == "MainRegimeV2":
                        main_hits += 1
            if rows >= 20000:
                break
    return {"rows": rows, "labels": sorted(labels), "main_regime_v2_hits": main_hits}


def root_row(name: str, path: Path) -> dict[str, object]:
    files = sample_files(path)
    row: dict[str, object] = {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "file_count_sampled": len(files),
        "sample_files": files,
    }
    if name.startswith("r3_native_subhour") and path.exists():
        row.update(inspect_r3_labels(path))
    return row


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    root_rows = [root_row(name, path) for name, path in TARGET_ROOTS]
    assertion_root = REPO / "docs/experiments/actionable-regime-confidence/runs"
    assertion_rows: list[dict[str, object]] = []
    any_valid_unlock = False
    any_source_control = False
    any_downstream = False
    any_update_goal = False
    for name, relative in ASSERTION_FILES:
        path = assertion_root / relative
        parsed = parse_kv_assertions(path)
        valid_unlock = truthy(first(parsed, "valid_required_root_unlock"))
        source_control = truthy(first(parsed, "source_control_evidence_acquired"))
        downstream = truthy(first(parsed, "downstream_promotion_rerun", "downstream_rerun_allowed_now"))
        update_goal = truthy(first(parsed, "update_goal"))
        any_valid_unlock = any_valid_unlock or valid_unlock
        any_source_control = any_source_control or source_control
        any_downstream = any_downstream or downstream
        any_update_goal = any_update_goal or update_goal
        assertion_rows.append(
            {
                "name": name,
                "path": rel(path),
                "present": parsed["present"],
                "gate_result": first(parsed, "gate_result", "gate"),
                "accepted_rows_added": first(parsed, "accepted_rows_added", default="0"),
                "valid_required_root_unlock": str(valid_unlock).lower(),
                "source_control_evidence_acquired": str(source_control).lower(),
                "downstream_promotion_rerun": str(downstream).lower(),
                "update_goal": str(update_goal).lower(),
            }
        )

    owner_env_names = sorted(
        name
        for name in os.environ
        if any(needle in name.upper() for needle in OWNER_ENV_NEEDLES)
    )
    r6_roots_present = any(row["exists"] for row in root_rows if str(row["name"]).startswith("r6_owner_export"))
    r5_roots_present = any(row["exists"] for row in root_rows if str(row["name"]).startswith("r5_recency"))
    r3_rows = [row for row in root_rows if str(row["name"]).startswith("r3_native_subhour") and row["exists"]]

    payload = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "gate_result": GATE,
        "target_roots": root_rows,
        "assertion_rows": assertion_rows,
        "owner_env_names_present_count": len(owner_env_names),
        "owner_env_names_present": owner_env_names,
        "r6_owner_export_roots_present": r6_roots_present,
        "r5_recency_roots_present": r5_roots_present,
        "r3_native_subhour_roots_present": bool(r3_rows),
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
        "prior_assertion_any_valid_unlock": any_valid_unlock,
        "prior_assertion_any_source_control": any_source_control,
        "prior_assertion_any_downstream": any_downstream,
        "prior_assertion_any_update_goal": any_update_goal,
    }

    json_path = OUT_ROOT / "source_control_arrival_poll_after_082720_v1.json"
    root_csv = OUT_ROOT / "source_control_target_roots_after_082720_v1.csv"
    assertion_csv = OUT_ROOT / "counted_assertion_readback_after_082720_v1.csv"
    report_path = OUT_ROOT / "source_control_arrival_poll_after_082720_v1.md"
    assertion_path = CHECK_ROOT / "source_control_arrival_poll_after_082720_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        root_csv,
        root_rows,
        [
            "name",
            "path",
            "exists",
            "is_dir",
            "file_count_sampled",
            "sample_files",
            "rows",
            "labels",
            "main_regime_v2_hits",
        ],
    )
    write_csv(
        assertion_csv,
        assertion_rows,
        [
            "name",
            "path",
            "present",
            "gate_result",
            "accepted_rows_added",
            "valid_required_root_unlock",
            "source_control_evidence_acquired",
            "downstream_promotion_rerun",
            "update_goal",
        ],
    )

    root_lines = "\n".join(
        f"| `{row['name']}` | `{row['path']}` | `{row['exists']}` | `{row['file_count_sampled']}` |"
        for row in root_rows
    )
    assertion_lines = "\n".join(
        f"| `{row['name']}` | `{row['gate_result']}` | `{row['valid_required_root_unlock']}` | `{row['source_control_evidence_acquired']}` | `{row['downstream_promotion_rerun']}` | `{row['update_goal']}` |"
        for row in assertion_rows
    )
    report_path.write_text(
        "\n".join(
            [
                "# Source/Control Arrival Poll After 082720 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only poll after the terminal `082720` objective audit and count-once corrections. This artifact inventories approved R6/R5/R3 target roots, owner-route env-name presence, and latest counted assertions. It does not mutate target roots, approve local bars or route metadata as source/control evidence, run verifier/split calibration, run canonical merge, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Target Roots",
                "",
                "| Name | Path | Exists | Sampled files |",
                "|---|---|---:|---:|",
                root_lines,
                "",
                "## Counted Assertion Readback",
                "",
                "| Root | Gate | Valid root unlock | Source/control | Downstream rerun | update_goal |",
                "|---|---|---:|---:|---:|---:|",
                assertion_lines,
                "",
                "## Decision",
                "",
                f"- Owner-route env-name hints present: `{len(owner_env_names)}`; values are not printed.",
                f"- R6 owner/export target roots present: `{str(r6_roots_present).lower()}`.",
                f"- R5 recency target roots present: `{str(r5_roots_present).lower()}`.",
                f"- R3 native-subhour roots present: `{str(bool(r3_rows)).lower()}`, but presence remains non-promoting without a required source/control package.",
                "- Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only. The live unblocker remains an owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE exchange order-lifecycle export with positives and matched normal controls, or explicit same-exhibit `FLIP`-as-control approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"gate_result={GATE}",
        f"r6_owner_export_roots_present={str(r6_roots_present).lower()}",
        f"r5_recency_roots_present={str(r5_roots_present).lower()}",
        f"r3_native_subhour_roots_present={str(bool(r3_rows)).lower()}",
        f"owner_env_names_present_count={len(owner_env_names)}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
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
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
