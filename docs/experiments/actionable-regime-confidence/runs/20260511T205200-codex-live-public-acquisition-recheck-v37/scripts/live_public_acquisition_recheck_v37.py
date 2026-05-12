#!/usr/bin/env python3
"""Fresh public-acquisition recheck for Board A strict source-owned blockers."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205200-codex-live-public-acquisition-recheck-v37"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "live-public-acquisition-recheck"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

OUTBOX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204131-codex-source-acquisition-outbox-v1/"
    "source-acquisition-outbox/source_acquisition_outbox_v1.json"
)
V35 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204335-codex-current-goal-completion-audit-v35-after-source-outbox/"
    "completion-audit/current_goal_completion_audit_v35_after_source_outbox.json"
)

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
        "verifier": SOURCE_LABEL_VERIFIER,
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
        "verifier": None,
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
        "verifier": RECENCY_VERIFIER,
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "verifier": DIRECT_VERIFIER,
    },
]

KAGGLE_DATASET = "mafaqbhatti/stock-market-regimes-20002026"
KAGGLE_URL = f"https://www.kaggle.com/datasets/{KAGGLE_DATASET}"
KAGGLE_PULL_ROOT = Path("/tmp/ict-engine-kaggle-stock-regimes-live-refresh-v37")
KAGGLE_CSV = KAGGLE_PULL_ROOT / "stock_market_regimes_2000_2026.csv"
LAST_ACCEPTED_SOURCE_DATE = "2026-01-30"
TARGET_CELLS = [
    ("XOM", "Sideways", "heldout_time", 5),
    ("UNH", "Bear", "calibration", 7),
    ("^DJI", "Sideways", "calibration", 7),
    ("AMD", "Bear", "calibration", 10),
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_kaggle_metadata(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return {"raw_metadata": payload}
    return payload if isinstance(payload, dict) else {"raw_metadata": payload}


def run_cmd(args: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def root_status(config: dict[str, Any]) -> dict[str, Any]:
    root = config["root"]
    present = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()) if root.exists() else []
    missing = [name for name in config["required"] if not (root / name).is_file()]
    return {
        "id": config["id"],
        "requirements": config["requirements"],
        "root": str(root),
        "required_files": ";".join(config["required"]),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "exists": root.exists(),
        "ready": not missing,
    }


def run_verifiers() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for config in INTAKE_ROOTS:
        verifier = config["verifier"]
        if verifier is None:
            status = root_status(config)
            results[config["id"]] = {
                "status": "ready_files_present_unscored" if status["ready"] else "blocked",
                "reason": "native_subhour_has_required_files" if status["ready"] else "missing_required_files",
                "returncode": None,
                "stdout": json.dumps(status, sort_keys=True),
                "stderr": "",
            }
            continue
        result = run_cmd(["python3", str(verifier), "--intake-root", str(config["root"])], cwd=REPO)
        parsed: dict[str, Any] | None = None
        try:
            parsed = json.loads(result["stdout"])
        except json.JSONDecodeError:
            parsed = None
        results[config["id"]] = {
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "parsed": parsed,
        }
    return results


def analyze_kaggle_csv(path: Path) -> dict[str, Any]:
    row_count = 0
    dates: list[str] = []
    fieldnames: list[str] = []
    target_rows = {
        f"{symbol}/{label}": {
            "symbol": symbol,
            "main_regime_v2_label": label,
            "split_role": split_role,
            "min_new_source_sessions": min_rows,
            "post_cutoff_rows": 0,
            "total_rows": 0,
        }
        for symbol, label, split_role, min_rows in TARGET_CELLS
    }

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            row_count += 1
            day = (row.get("date") or "")[:10]
            symbol = row.get("ticker") or ""
            label = row.get("regime_label") or ""
            if day:
                dates.append(day)
            key = f"{symbol}/{label}"
            if key in target_rows:
                target_rows[key]["total_rows"] += 1
                if day > LAST_ACCEPTED_SOURCE_DATE:
                    target_rows[key]["post_cutoff_rows"] += 1

    return {
        "exists": path.exists(),
        "sha256": sha256(path),
        "fieldnames": fieldnames,
        "row_count": row_count,
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "target_counts": list(target_rows.values()),
        "post_cutoff_target_rows": sum(int(row["post_cutoff_rows"]) for row in target_rows.values()),
    }


def materialize_recency_extension_if_available(kaggle_stats: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    if not KAGGLE_CSV.exists() or int(kaggle_stats["post_cutoff_target_rows"]) <= 0:
        return {"created": False, "reason": "no_post_cutoff_target_rows"}

    recency_root = Path("/tmp/ict-engine-source-panel-recency-extension")
    recency_root.mkdir(parents=True, exist_ok=True)
    rows_path = recency_root / "stock_market_regimes_2026_extension.csv"
    provenance_path = recency_root / "source_panel_recency_provenance.json"

    with KAGGLE_CSV.open(newline="", encoding="utf-8") as source, rows_path.open(
        "w", newline="", encoding="utf-8"
    ) as dest:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(dest, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        written = 0
        for row in reader:
            if (row.get("date") or "")[:10] > LAST_ACCEPTED_SOURCE_DATE:
                writer.writerow(row)
                written += 1

    provenance = {
        "source": KAGGLE_DATASET,
        "source_url": KAGGLE_URL,
        "source_pull_root": str(KAGGLE_PULL_ROOT),
        "source_csv_sha256": kaggle_stats["sha256"],
        "source_metadata": metadata,
        "materialized_at_utc": datetime.now(timezone.utc).isoformat(),
        "last_accepted_source_date": LAST_ACCEPTED_SOURCE_DATE,
        "rows_file_sha256": sha256(rows_path),
        "attestation": "public Kaggle source rows only; no OHLCV-only generated labels added by this script",
    }
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"created": True, "row_count": written, "rows_file": str(rows_path), "provenance_file": str(provenance_path)}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    if KAGGLE_PULL_ROOT.exists():
        shutil.rmtree(KAGGLE_PULL_ROOT)
    KAGGLE_PULL_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    outbox = read_json(OUTBOX)
    v35 = read_json(V35)
    kaggle_available = shutil.which("kaggle") is not None
    kaggle_commands: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    kaggle_stats: dict[str, Any] = {
        "exists": False,
        "post_cutoff_target_rows": 0,
        "date_max": None,
        "row_count": 0,
        "target_counts": [],
    }

    if kaggle_available:
        kaggle_commands.append(run_cmd(["kaggle", "datasets", "metadata", KAGGLE_DATASET, "-p", str(KAGGLE_PULL_ROOT)]))
        metadata_path = KAGGLE_PULL_ROOT / "dataset-metadata.json"
        if metadata_path.exists():
            metadata = read_kaggle_metadata(metadata_path)
        kaggle_commands.append(run_cmd(["kaggle", "datasets", "files", KAGGLE_DATASET, "-v"]))
        kaggle_commands.append(
            run_cmd(["kaggle", "datasets", "download", KAGGLE_DATASET, "-p", str(KAGGLE_PULL_ROOT), "--unzip"])
        )
        if KAGGLE_CSV.exists():
            kaggle_stats = analyze_kaggle_csv(KAGGLE_CSV)

    recency_materialization = materialize_recency_extension_if_available(kaggle_stats, metadata)
    roots = [root_status(config) for config in INTAKE_ROOTS]
    verifier_results = run_verifiers()
    ready_roots = [row["id"] for row in roots if row["ready"]]

    new_rows_acquired = bool(recency_materialization.get("created"))
    decision = (
        "live_public_acquisition_recheck_v37=public_recency_rows_materialized_needs_verifier_review"
        if new_rows_acquired
        else "live_public_acquisition_recheck_v37=no_new_public_rows_intakes_still_absent_blocked"
    )
    strict_full_objective = False
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "board_hash_before_writeback": board_hash,
        "outbox_decision": outbox.get("decision"),
        "v35_decision": v35.get("decision"),
        "kaggle_available": kaggle_available,
        "kaggle_dataset": KAGGLE_DATASET,
        "kaggle_url": KAGGLE_URL,
        "kaggle_pull_root": str(KAGGLE_PULL_ROOT),
        "kaggle_commands": kaggle_commands,
        "kaggle_metadata_license": metadata.get("licenseName") or metadata.get("license"),
        "kaggle_stats": kaggle_stats,
        "recency_materialization": recency_materialization,
        "intake_roots_checked": roots,
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "verifier_results": verifier_results,
        "request_sent": False,
        "external_authenticated_message_sent": False,
        "rows_acquired": new_rows_acquired,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": strict_full_objective,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "unmet_ids": ["R2", "R3", "R4", "R5", "R6", "R8"],
        "next_action": (
            "Use the source acquisition outbox with explicit user approval, or place real source-owned/"
            "owner-approved intake files under the four /tmp roots and rerun the fail-closed verifiers."
        ),
    }

    (OUT / "live_public_acquisition_recheck_v37.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(
        OUT / "live_public_acquisition_recheck_v37_intake_roots.csv",
        roots,
        ["id", "requirements", "root", "required_files", "present_files", "missing_files", "exists", "ready"],
    )
    write_csv(
        OUT / "live_public_acquisition_recheck_v37_kaggle_targets.csv",
        list(kaggle_stats.get("target_counts") or []),
        ["symbol", "main_regime_v2_label", "split_role", "min_new_source_sessions", "post_cutoff_rows", "total_rows"],
    )

    lines = [
        "# Live Public Acquisition Recheck v37",
        "",
        f"- Decision: `{decision}`",
        f"- Kaggle dataset: `{KAGGLE_DATASET}`",
        f"- Kaggle pull root: `{KAGGLE_PULL_ROOT}`",
        f"- Kaggle date max: `{kaggle_stats.get('date_max')}`",
        f"- Kaggle post-cutoff target rows after `{LAST_ACCEPTED_SOURCE_DATE}`: `{kaggle_stats.get('post_cutoff_target_rows')}`",
        f"- Recency intake materialized: `{str(recency_materialization.get('created')).lower()}`",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        "- External authenticated/request messages sent: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Intake Roots",
        "",
        "| Root | Ready | Missing Files |",
        "|---|---:|---|",
    ]
    for row in roots:
        lines.append(f"| `{row['id']}` | `{str(row['ready']).lower()}` | `{row['missing_files']}` |")
    lines.extend(
        [
            "",
            "## Target Cells",
            "",
            "| Symbol | Label | Split Role | Required New Sessions | Post-Cutoff Rows | Total Rows |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for row in kaggle_stats.get("target_counts") or []:
        lines.append(
            f"| `{row['symbol']}` | `{row['main_regime_v2_label']}` | `{row['split_role']}` | "
            f"{row['min_new_source_sessions']} | {row['post_cutoff_rows']} | {row['total_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            "The public Kaggle refresh did not produce post-cutoff target rows, and no required source-owned "
            "or owner-approved files are present in the four intake roots. The outbox remains the controlling "
            "closure path, but it cannot be sent without explicit user approval.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT / 'live_public_acquisition_recheck_v37.json'}`",
            f"- Intake-root CSV: `{OUT / 'live_public_acquisition_recheck_v37_intake_roots.csv'}`",
            f"- Kaggle target CSV: `{OUT / 'live_public_acquisition_recheck_v37_kaggle_targets.csv'}`",
            f"- Assertions: `{CHECKS / 'live_public_acquisition_recheck_v37_assertions.out'}`",
        ]
    )
    (OUT / "live_public_acquisition_recheck_v37.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS kaggle_available={str(kaggle_available).lower()}",
        f"PASS kaggle_date_max={kaggle_stats.get('date_max')}",
        f"PASS kaggle_post_cutoff_target_rows={kaggle_stats.get('post_cutoff_target_rows')}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS request_sent=false",
        "PASS external_authenticated_message_sent=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "live_public_acquisition_recheck_v37_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "ready_intake_roots": len(ready_roots)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
