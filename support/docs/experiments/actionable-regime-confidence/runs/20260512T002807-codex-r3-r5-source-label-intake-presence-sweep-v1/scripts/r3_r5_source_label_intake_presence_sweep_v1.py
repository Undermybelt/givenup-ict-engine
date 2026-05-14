#!/usr/bin/env python3
"""Current-state presence sweep for non-R6 Board A blocker intake roots."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T002807-codex-r3-r5-source-label-intake-presence-sweep-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "r3-r5-source-label-intake-presence-sweep"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"

SOURCE_LABEL_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "blocker": "source-label confidence/equivalence",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
        "verifier": SOURCE_LABEL_VERIFIER,
        "acceptance": "schema_ready_unscored first, then Wilson95 >=0.95 per MainRegimeV2 root/split",
    },
    {
        "id": "native_subhour_source_label",
        "blocker": "R3 native-subhour root",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "verifier": None,
        "acceptance": "source-native or owner-approved sub-hour labels plus provenance; no OHLCV/HMM proxy",
    },
    {
        "id": "source_panel_recency_extension",
        "blocker": "R5 post-2026-01-30 source-panel recency",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "verifier": RECENCY_VERIFIER,
        "acceptance": "post-2026-01-30 source-owned rows matching the recency verifier schema",
    },
]

SEARCH_BASES = [Path("/tmp"), Path("/private/tmp"), Path("/Users/thrill3r/Downloads")]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_data_rows(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        for count, _ in enumerate(reader, start=1):
            pass
    return max(count - 1, 0)


def root_snapshot(item: dict) -> dict:
    root = item["root"]
    present = []
    missing = []
    hashes = {}
    row_counts = {}
    for name in item["required"]:
        path = root / name
        if path.exists():
            present.append(name)
            hashes[name] = sha256_file(path)
            if path.suffix.lower() == ".csv":
                row_counts[name] = csv_data_rows(path)
        else:
            missing.append(name)
    return {
        "id": item["id"],
        "blocker": item["blocker"],
        "root": str(root),
        "root_exists": root.exists(),
        "required_files": item["required"],
        "present_files": present,
        "missing_files": missing,
        "all_required_present": not missing,
        "file_hashes": hashes,
        "csv_row_counts": row_counts,
        "acceptance": item["acceptance"],
    }


def run_verifier(item: dict) -> dict | None:
    verifier = item.get("verifier")
    if verifier is None:
        return None
    cmd = ["python3", str(verifier), "--intake-root", str(item["root"])]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    prefix = item["id"]
    (CMD_OUT / f"{prefix}_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_OUT / f"{prefix}_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_OUT / f"{prefix}_verifier.exit").write_text(str(proc.returncode), encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"parse_error": True}
    return {
        "id": f"{prefix}_verifier",
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout_file": str(CMD_OUT / f"{prefix}_verifier.stdout.txt"),
        "stderr_file": str(CMD_OUT / f"{prefix}_verifier.stderr.txt"),
        "exit_file": str(CMD_OUT / f"{prefix}_verifier.exit"),
        "parsed": parsed,
    }


def relative_depth(base: Path, path: Path) -> int:
    try:
        return len(path.relative_to(base).parts)
    except ValueError:
        return 999


def bounded_find(required_names: set[str], max_depth: int = 5) -> list[dict]:
    hits = []
    seen = set()
    for base in SEARCH_BASES:
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            current = Path(dirpath)
            if relative_depth(base, current) >= max_depth:
                dirnames[:] = []
            for filename in filenames:
                if filename not in required_names:
                    continue
                path = current / filename
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "required_file": filename,
                        "path": str(path),
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
    return sorted(hits, key=lambda row: (row["required_file"], row["path"]))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    snapshots = [root_snapshot(item) for item in INTAKE_ROOTS]
    verifiers = [result for item in INTAKE_ROOTS if (result := run_verifier(item)) is not None]
    required_names = {name for item in INTAKE_ROOTS for name in item["required"]}
    candidate_hits = bounded_find(required_names)

    ready_roots = [row["id"] for row in snapshots if row["all_required_present"]]
    present_required_count = sum(len(row["present_files"]) for row in snapshots)
    missing_required_count = sum(len(row["missing_files"]) for row in snapshots)
    source_label_status = next(
        (
            result["parsed"].get("status")
            for result in verifiers
            if result["id"] == "source_label_equivalence_verifier"
        ),
        "not_run",
    )
    recency_status = next(
        (
            result["parsed"].get("status")
            for result in verifiers
            if result["id"] == "source_panel_recency_extension_verifier"
        ),
        "not_run",
    )

    decision = "r3_r5_source_label_intake_presence_sweep_v1=non_r6_intake_roots_absent_or_incomplete"
    summary = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "roots_checked": len(snapshots),
        "ready_roots": ready_roots,
        "ready_root_count": len(ready_roots),
        "required_file_count": present_required_count + missing_required_count,
        "present_required_file_count": present_required_count,
        "missing_required_file_count": missing_required_count,
        "candidate_hits_count": len(candidate_hits),
        "source_label_equivalence_status": source_label_status,
        "source_panel_recency_status": recency_status,
        "native_subhour_root_ready": any(
            row["id"] == "native_subhour_source_label" and row["all_required_present"]
            for row in snapshots
        ),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": (
            "Preserve the active V62 R6 owner-export next action. For non-R6 hardening, "
            "populate the missing source-label equivalence, native-subhour, or R5 recency "
            "intake roots with owner-approved/source-owned files before rerunning the unchanged gates."
        ),
    }

    json_path = OUT / "r3_r5_source_label_intake_presence_sweep_v1.json"
    roots_csv = OUT / "r3_r5_source_label_intake_roots_v1.csv"
    hits_csv = OUT / "r3_r5_source_label_intake_candidate_hits_v1.csv"
    report_path = OUT / "r3_r5_source_label_intake_presence_sweep_v1.md"
    assertions_path = CHECKS / "r3_r5_source_label_intake_presence_sweep_v1_assertions.out"

    json_path.write_text(
        json.dumps(
            {
                **summary,
                "intake_roots": snapshots,
                "verifier_results": verifiers,
                "candidate_hits": candidate_hits,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with roots_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "blocker",
                "root",
                "root_exists",
                "required_files",
                "present_files",
                "missing_files",
                "all_required_present",
                "csv_row_counts",
                "acceptance",
            ],
        )
        writer.writeheader()
        for row in snapshots:
            writer.writerow(
                {
                    "id": row["id"],
                    "blocker": row["blocker"],
                    "root": row["root"],
                    "root_exists": row["root_exists"],
                    "required_files": ";".join(row["required_files"]),
                    "present_files": ";".join(row["present_files"]),
                    "missing_files": ";".join(row["missing_files"]),
                    "all_required_present": row["all_required_present"],
                    "csv_row_counts": json.dumps(row["csv_row_counts"], sort_keys=True),
                    "acceptance": row["acceptance"],
                }
            )

    with hits_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["required_file", "path", "size_bytes", "sha256"])
        writer.writeheader()
        for row in candidate_hits:
            writer.writerow(row)

    md_lines = [
        "# R3/R5 Source-Label Intake Presence Sweep v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Non-R6 intake roots ready: `{len(ready_roots)}/3`.",
        (
            f"- Required files present: `{present_required_count}/"
            f"{present_required_count + missing_required_count}`."
        ),
        f"- Source-label equivalence verifier status: `{source_label_status}`.",
        f"- R5 source-panel recency verifier status: `{recency_status}`.",
        f"- R3 native-subhour root ready: `{str(summary['native_subhour_root_ready']).lower()}`.",
        f"- Bounded local candidate hits in `/tmp`, `/private/tmp`, and `Downloads`: `{len(candidate_hits)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "Intake Roots:",
        "",
        "| Root | Ready | Missing |",
        "|---|---:|---|",
    ]
    for row in snapshots:
        missing = ", ".join(row["missing_files"]) if row["missing_files"] else "none"
        md_lines.append(
            f"| `{row['id']}` | `{str(row['all_required_present']).lower()}` | `{missing}` |"
        )
    md_lines.extend(
        [
            "",
            "Next:",
            (
                "- Preserve the active V62 R6 owner-export next action. For non-R6 hardening, "
                "populate the missing source-label equivalence, native-subhour, or R5 recency "
                "intake roots with owner-approved/source-owned files before rerunning the unchanged gates."
            ),
            "",
            "Artifacts:",
            f"- JSON: `{json_path}`",
            f"- Intake roots CSV: `{roots_csv}`",
            f"- Candidate hits CSV: `{hits_csv}`",
            f"- Command output: `{CMD_OUT}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    report_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS ready_roots={len(ready_roots)}",
        f"PASS present_required_files={present_required_count}",
        f"PASS missing_required_files={missing_required_count}",
        f"PASS source_label_equivalence_status={source_label_status}",
        f"PASS source_panel_recency_status={recency_status}",
        f"PASS native_subhour_root_ready={str(summary['native_subhour_root_ready']).lower()}",
        f"PASS candidate_hits_count={len(candidate_hits)}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
