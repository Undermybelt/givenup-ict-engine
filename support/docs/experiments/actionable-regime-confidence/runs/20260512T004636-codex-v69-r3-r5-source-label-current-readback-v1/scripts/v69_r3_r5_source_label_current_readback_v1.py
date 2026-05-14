#!/usr/bin/env python3
"""Read back non-R6 Board A intake roots after the V69 cursor."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T004636-codex-v69-r3-r5-source-label-current-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "v69-r3-r5-source-label-current-readback"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"

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

ROOTS = [
    {
        "root_id": "source_label_equivalence",
        "blocker": "source-label confidence 0/4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
        "verifier": SOURCE_LABEL_VERIFIER,
    },
    {
        "root_id": "r5_source_panel_recency",
        "blocker": "R5 post-2026-01-30 source-panel rows absent",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
        "verifier": RECENCY_VERIFIER,
    },
    {
        "root_id": "r3_native_subhour",
        "blocker": "R3 native-subhour source-label root absent",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
        "verifier": None,
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def count_csv_rows(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        count = sum(1 for _ in csv.reader(handle))
    return max(count - 1, 0)


def run_verifier(root_id: str, verifier: Path | None, root: Path) -> dict[str, object] | None:
    if verifier is None:
        return None
    cmd = ["python3", str(verifier), "--intake-root", str(root)]
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True)
    stdout = CMD_OUT / f"{root_id}_verifier.stdout.txt"
    stderr = CMD_OUT / f"{root_id}_verifier.stderr.txt"
    exit_file = CMD_OUT / f"{root_id}_verifier.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_file.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"parse_error": True}
    return {
        "root_id": root_id,
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": rel(stdout),
        "stderr": rel(stderr),
        "exit": rel(exit_file),
        "parsed": parsed,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    verifiers = []
    for item in ROOTS:
        root = item["root"]
        present = [name for name in item["required_files"] if (root / name).exists()]
        missing = [name for name in item["required_files"] if not (root / name).exists()]
        row_counts = {
            name: count_csv_rows(root / name)
            for name in present
            if (root / name).suffix.lower() == ".csv"
        }
        rows.append(
            {
                "root_id": item["root_id"],
                "blocker": item["blocker"],
                "root": str(root),
                "root_exists": str(root.exists()).lower(),
                "required_files": ";".join(item["required_files"]),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "all_required_present": str(not missing).lower(),
                "csv_row_counts": json.dumps(row_counts, sort_keys=True),
            }
        )
        verifier_result = run_verifier(item["root_id"], item["verifier"], root)
        if verifier_result is not None:
            verifiers.append(verifier_result)

    ready_roots = [row for row in rows if row["all_required_present"] == "true"]
    missing_required = sum(len(row["missing_files"].split(";")) if row["missing_files"] else 0 for row in rows)
    gate = "v69_r3_r5_source_label_current_readback_v1=non_r6_roots_absent_no_confidence_gate"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "roots_checked": len(rows),
        "ready_roots": len(ready_roots),
        "missing_required_files": missing_required,
        "source_label_status": next((v["parsed"].get("status") for v in verifiers if v["root_id"] == "source_label_equivalence"), "not_run"),
        "r5_recency_status": next((v["parsed"].get("status") for v in verifiers if v["root_id"] == "r5_source_panel_recency"), "not_run"),
        "r3_native_subhour_ready": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    roots_csv = OUT / "v69_r3_r5_source_label_roots_v1.csv"
    json_path = OUT / "v69_r3_r5_source_label_current_readback_v1.json"
    report_path = OUT / "v69_r3_r5_source_label_current_readback_v1.md"
    assertions_path = CHECKS / "v69_r3_r5_source_label_current_readback_v1_assertions.out"

    with roots_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps({**result, "roots": rows, "verifiers": verifiers}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# V69 R3/R5 Source-Label Current Readback v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Gate result: `{gate}`.",
                f"- Roots checked: `{len(rows)}`; ready roots: `{len(ready_roots)}`.",
                f"- Missing required files: `{missing_required}`.",
                f"- Source-label equivalence verifier status: `{result['source_label_status']}`.",
                f"- R5 source-panel recency verifier status: `{result['r5_recency_status']}`.",
                "- R3 native-subhour source-label root ready: `false`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "Artifacts:",
                f"- JSON: `{rel(json_path)}`",
                f"- Roots CSV: `{rel(roots_csv)}`",
                f"- Assertions: `{rel(assertions_path)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={gate}",
                f"roots_checked={len(rows)}",
                f"ready_roots={len(ready_roots)}",
                f"missing_required_files={missing_required}",
                f"source_label_status={result['source_label_status']}",
                f"r5_recency_status={result['r5_recency_status']}",
                "r3_native_subhour_ready=False",
                "strict_full_objective_achieved=False",
                "update_goal=False",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
