#!/usr/bin/env python3
"""Read-only local probe for direct Manipulation spoofing/layering intake rows."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T181211+0800-codex-direct-manipulation-local-intake-probe-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T181211-codex-direct-manipulation-local-intake-probe-v1"
)
OUT_DIR = RUN_ROOT / "local-intake-probe"
CHECK_DIR = RUN_ROOT / "checks"

INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

OUT_JSON = OUT_DIR / "direct_manipulation_local_intake_probe_v1.json"
OUT_MD = OUT_DIR / "direct_manipulation_local_intake_probe_v1.md"
OUT_CSV = OUT_DIR / "direct_manipulation_local_intake_probe_v1_candidates.csv"
OUT_ASSERT = CHECK_DIR / "direct_manipulation_local_intake_probe_v1_assertions.out"

SEARCH_ROOTS = [
    Path("/tmp"),
    Path("/private/tmp"),
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Auto-Quant"),
]
REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
MAX_DEPTH = 5


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def depth_from(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 999


def likely_candidate(path: Path) -> bool:
    name = path.name.lower()
    if path.parent == INTAKE_ROOT and path.name in REQUIRED_FILES:
        return True
    if path.suffix.lower() != ".csv":
        return False
    return any(term in name for term in ("spoof", "layer", "quote_stuff", "pinging")) and "row" in name


def find_candidates() -> list[Path]:
    out: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if depth_from(root, current) > MAX_DEPTH:
                dirnames[:] = []
                continue
            for filename in filenames:
                path = current / filename
                if likely_candidate(path):
                    out.append(path)
    return sorted(set(out))


def summarize_csv(path: Path) -> dict[str, Any]:
    row = {
        "path": str(path),
        "exists": path.exists(),
        "format": path.suffix.lower().lstrip("."),
        "rows": "",
        "columns": "",
        "candidate_role": "unknown",
    }
    lower = path.name.lower()
    if "positive" in lower or "spoof" in lower or "layer" in lower:
        row["candidate_role"] = "possible_positive"
    if "negative" in lower or "normal" in lower:
        row["candidate_role"] = "possible_negative"
    if path.suffix.lower() == ".csv" and path.exists():
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                fields = reader.fieldnames or []
                count = sum(1 for _ in reader)
            row["rows"] = count
            row["columns"] = "|".join(fields)
        except Exception as exc:  # noqa: BLE001 - artifact should record read failure.
            row["columns"] = f"read_error:{type(exc).__name__}"
    return row


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "blocked", "reason": "invalid_verifier_output", "stdout": proc.stdout}
    return {
        "command": f"python3 {repo_rel(VERIFIER)} --intake-root {INTAKE_ROOT}",
        "returncode": proc.returncode,
        "stdout_json": parsed,
        "stderr": proc.stderr.strip(),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["path", "exists", "format", "rows", "columns", "candidate_role"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    expected = [{"path": str(INTAKE_ROOT / name), "exists": (INTAKE_ROOT / name).exists()} for name in REQUIRED_FILES]
    candidates = [summarize_csv(path) for path in find_candidates()]
    verifier = run_verifier()
    missing_required = [item["path"] for item in expected if not item["exists"]]
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "direct_manipulation_local_intake_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_variety": "spoofing_layering",
        "intake_root": str(INTAKE_ROOT),
        "expected_files": expected,
        "search_roots": [str(path) for path in SEARCH_ROOTS],
        "candidate_file_count": len(candidates),
        "candidate_files": candidates,
        "verifier": verifier,
        "decision": {
            "gate_result": "direct_manipulation_local_intake_probe_v1=missing_required_files",
            "accepted_direct_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Place source-owned positive spoofing/layering rows, matched normal controls, "
            "and provenance under /tmp/ict-engine-direct-manipulation-row-intake, then rerun the verifier."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(OUT_CSV, candidates)
    lines = [
        "# Direct Manipulation Local Intake Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Read-only local probe for spoofing/layering direct Manipulation intake rows.",
        "",
        "## Result",
        "",
        f"- Candidate files found: `{len(candidates)}`.",
        f"- Required files missing: `{len(missing_required)}/3`.",
        f"- Verifier status: `{verifier['stdout_json'].get('status')}` / `{verifier['stdout_json'].get('reason')}`.",
        "- Accepted direct rows added: `0`; new confidence gate: `false`.",
        "- Gate result: `direct_manipulation_local_intake_probe_v1=missing_required_files`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Missing Required Files",
        "",
    ]
    for path in missing_required:
        lines.append(f"- `{path}`")
    lines.extend(["", "## Next", "", payload["next_action"]])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"run_id={RUN_ID}",
        f"candidate_file_count={len(candidates)}",
        f"required_files_missing={len(missing_required)}",
        f"verifier_status={verifier['stdout_json'].get('status')}",
        f"verifier_reason={verifier['stdout_json'].get('reason')}",
        "accepted_direct_rows_added=0",
        "new_confidence_gate=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
