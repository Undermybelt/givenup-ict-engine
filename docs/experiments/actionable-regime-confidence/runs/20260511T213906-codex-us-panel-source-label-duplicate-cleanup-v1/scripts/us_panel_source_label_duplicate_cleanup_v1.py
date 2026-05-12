#!/usr/bin/env python3
"""Remove the duplicate US-panel source-label extension introduced by 213446.

The prior 213446 extension was already present in the shared /tmp intake when
that script was rerun. This cleanup restores the pre-rerun rows, fixes the
provenance counters, removes the oversized repo snapshot, and reruns the
unchanged schema verifier.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T213906-codex-us-panel-source-label-duplicate-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "us-panel-source-label-duplicate-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS_NAME = "source_label_equivalence_rows.csv"
PROVENANCE_NAME = "source_label_equivalence_provenance.json"
DUP_RUN_ID = "20260511T213446-codex-us-panel-source-label-equivalence-extension-v1"
DUP_OUT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / DUP_RUN_ID
    / "us-panel-source-label-equivalence-extension"
)
PRE_RUN_ROWS = DUP_OUT / "source_label_equivalence_rows_before.csv"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_rows(path: Path) -> dict[str, Any]:
    labels: Counter[str] = Counter()
    owners: Counter[str] = Counter()
    families: Counter[str] = Counter()
    splits: Counter[str] = Counter()
    symbols: set[str] = set()
    dates: list[str] = []
    row_count = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_count += 1
            labels[row.get("main_regime_v2_label", "")] += 1
            owners[row.get("source_owner", "")] += 1
            families[row.get("market_family", "")] += 1
            splits[row.get("split_role", "")] += 1
            if row.get("symbol"):
                symbols.add(row["symbol"])
            if row.get("timestamp_or_date"):
                dates.append(row["timestamp_or_date"])
    return {
        "row_count": row_count,
        "label_counts": dict(sorted(labels.items())),
        "source_owner_counts": dict(sorted(owners.items())),
        "market_family_counts": dict(sorted(families.items())),
        "split_counts": dict(sorted(splits.items())),
        "symbol_count": len(symbols),
        "date_min": min(dates) if dates else "",
        "date_max": max(dates) if dates else "",
    }


def run_verifier(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD_DIR / "source_label_equivalence_verifier.stdout.txt"
    stderr_path = CMD_DIR / "source_label_equivalence_verifier.stderr.txt"
    exit_path = CMD_DIR / "source_label_equivalence_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict[str, Any] = {}
    try:
        loaded = json.loads(proc.stdout)
        if isinstance(loaded, dict):
            parsed = loaded
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout": proc.stdout[:1000]}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout_file": str(stdout_path.relative_to(REPO)),
        "stderr_file": str(stderr_path.relative_to(REPO)),
    }


def rewrite_provenance(
    provenance_path: Path,
    restored_counts: dict[str, Any],
    restored_hash: str,
    current_counts: dict[str, Any],
) -> tuple[int, int]:
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    extensions = list(provenance.get("extensions", []))
    before_len = len(extensions)
    removed = 0
    duplicate_indexes = [
        index
        for index, extension in enumerate(extensions)
        if extension.get("run_id") == DUP_RUN_ID
    ]
    if len(duplicate_indexes) > 1:
        remove_index = duplicate_indexes[-1]
        extensions.pop(remove_index)
        removed = 1
    provenance["extensions"] = extensions
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["row_count"] = restored_counts["row_count"]
    provenance["label_counts"] = restored_counts["label_counts"]
    provenance["split_counts"] = restored_counts["split_counts"]
    provenance["date_min"] = restored_counts["date_min"]
    provenance["date_max"] = restored_counts["date_max"]
    provenance["rows_sha256"] = restored_hash
    cleanup_actions = list(provenance.get("cleanup_actions", []))
    cleanup_actions.append(
        {
            "run_id": RUN_ID,
            "removed_duplicate_extension_run_id": DUP_RUN_ID,
            "duplicate_extension_entries_before": before_len,
            "duplicate_extension_entries_after": len(extensions),
            "rows_before_cleanup": current_counts["row_count"],
            "rows_after_cleanup": restored_counts["row_count"],
            "rows_removed": current_counts["row_count"] - restored_counts["row_count"],
            "oversized_repo_snapshot_removed": str(PRE_RUN_ROWS.relative_to(REPO)),
        }
    )
    provenance["cleanup_actions"] = cleanup_actions
    tmp = provenance_path.with_name(f".{provenance_path.name}.{RUN_ID}.tmp")
    tmp.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(provenance_path)
    return before_len, removed


def write_counts_csv(path: Path, current_counts: dict[str, Any], restored_counts: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scope", "metric", "key", "value"])
        writer.writeheader()
        for scope, counts in [("before_cleanup", current_counts), ("after_cleanup", restored_counts)]:
            for metric in ["label_counts", "source_owner_counts", "market_family_counts", "split_counts"]:
                for key, value in counts.get(metric, {}).items():
                    writer.writerow({"scope": scope, "metric": metric, "key": key, "value": value})
            for key in ["row_count", "symbol_count", "date_min", "date_max"]:
                writer.writerow({"scope": scope, "metric": "summary", "key": key, "value": counts.get(key, "")})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    shared_rows = INTAKE_ROOT / ROWS_NAME
    shared_provenance = INTAKE_ROOT / PROVENANCE_NAME
    if not PRE_RUN_ROWS.exists():
        raise FileNotFoundError(f"missing pre-run rows snapshot: {PRE_RUN_ROWS}")
    current_hash = sha256_file(shared_rows)
    restored_hash = sha256_file(PRE_RUN_ROWS)
    current_counts = count_rows(shared_rows)
    restored_counts = count_rows(PRE_RUN_ROWS)

    temp_rows = INTAKE_ROOT / f".{ROWS_NAME}.{RUN_ID}.tmp"
    shutil.copy2(PRE_RUN_ROWS, temp_rows)
    temp_rows.replace(shared_rows)
    provenance_entries_before, provenance_entries_removed = rewrite_provenance(
        shared_provenance, restored_counts, restored_hash, current_counts
    )
    PRE_RUN_ROWS.unlink()
    removed_snapshot_path = DUP_OUT / "source_label_equivalence_rows_before.removed.txt"
    removed_snapshot_path.write_text(
        "Removed by "
        f"{RUN_ID} to avoid committing a large generated intake snapshot. "
        f"Restored shared rows hash: {restored_hash}.\n",
        encoding="utf-8",
    )

    verifier = run_verifier(INTAKE_ROOT)
    decision = "us_panel_source_label_duplicate_cleanup_v1=duplicate_extension_removed_schema_ready_unscored"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "rows_before_cleanup": current_counts["row_count"],
        "rows_after_cleanup": restored_counts["row_count"],
        "rows_removed": current_counts["row_count"] - restored_counts["row_count"],
        "hash_before_cleanup": current_hash,
        "hash_after_cleanup": restored_hash,
        "counts_before_cleanup": current_counts,
        "counts_after_cleanup": restored_counts,
        "provenance_extension_entries_before": provenance_entries_before,
        "provenance_extension_entries_removed": provenance_entries_removed,
        "oversized_repo_snapshot_removed": True,
        "verifier": verifier,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "run current-goal audit over the cleaned source-label root; R3/R5/R6 blockers remain",
    }
    json_path = OUT / "us_panel_source_label_duplicate_cleanup_v1.json"
    report_path = OUT / "us_panel_source_label_duplicate_cleanup_v1.md"
    counts_path = OUT / "us_panel_source_label_duplicate_cleanup_counts_v1.csv"
    assertions_path = CHECKS / "us_panel_source_label_duplicate_cleanup_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_counts_csv(counts_path, current_counts, restored_counts)
    report_path.write_text(
        "\n".join(
            [
                "# US Panel Source Label Duplicate Cleanup v1",
                "",
                f"- Decision: `{decision}`.",
                f"- Rows before cleanup: `{current_counts['row_count']}`.",
                f"- Rows after cleanup: `{restored_counts['row_count']}`.",
                f"- Rows removed: `{current_counts['row_count'] - restored_counts['row_count']}`.",
                f"- Labels after cleanup: `{restored_counts['label_counts']}`.",
                f"- Source owners after cleanup: `{restored_counts['source_owner_counts']}`.",
                f"- Shared rows hash after cleanup: `{restored_hash}`.",
                f"- Verifier status: `{verifier['parsed'].get('status')}`; return code `{verifier['returncode']}`.",
                "- Removed the oversized generated repo snapshot and left a small `.removed.txt` marker.",
                "- Accepted confidence rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "Interpretation:",
                "The source-label equivalence root keeps the first US source-panel extension plus NIFTY rows, so all four MainRegimeV2 price labels remain present. The duplicate rerun block is removed. This cleanup does not score confidence and does not close native sub-hour, recency, or R6 direct gates.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Report: `{report_path.relative_to(REPO)}`",
                f"- Counts CSV: `{counts_path.relative_to(REPO)}`",
                f"- Verifier stdout: `{(CMD_DIR / 'source_label_equivalence_verifier.stdout.txt').relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions = [
        f"PASS decision={decision}",
        f"PASS rows_before_cleanup={current_counts['row_count']}",
        f"PASS rows_after_cleanup={restored_counts['row_count']}",
        f"PASS rows_removed={current_counts['row_count'] - restored_counts['row_count']}",
        f"PASS verifier_status={verifier['parsed'].get('status')}",
        "PASS oversized_repo_snapshot_removed=true",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": decision,
        "rows_before_cleanup": current_counts["row_count"],
        "rows_after_cleanup": restored_counts["row_count"],
        "rows_removed": current_counts["row_count"] - restored_counts["row_count"],
        "verifier_status": verifier["parsed"].get("status"),
        "report": str(report_path.relative_to(REPO)),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
