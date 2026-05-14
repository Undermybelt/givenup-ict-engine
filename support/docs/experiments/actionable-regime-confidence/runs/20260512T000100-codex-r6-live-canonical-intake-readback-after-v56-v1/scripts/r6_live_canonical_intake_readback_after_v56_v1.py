#!/usr/bin/env python3
"""Read back the live canonical R6 direct-manipulation intake after V56.

This does not mutate the canonical `/tmp` intake. It verifies whether the
volatile canonical root currently exists, compares it with the durable V56
snapshot, and records the remaining split/species blockers.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T000100-codex-r6-live-canonical-intake-readback-after-v56-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-live-canonical-intake-readback-after-v56"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
CANONICAL_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V56_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56"
    / "r6-isolated-reconstruction-snapshot-v56"
)
V56_JSON = V56_ROOT / "r6_isolated_reconstruction_snapshot_v56.json"
V56_SPLITS = V56_ROOT / "r6_isolated_reconstruction_snapshot_v56_split_metrics.csv"
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen"
    / "broad_normal_market_order_lifecycle_controls_v1.csv"
)

Z_95 = 1.96
MIN_WILSON = 0.95


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def run_verifier() -> dict[str, object]:
    result = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(CANONICAL_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    stdout_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"parse_error": True, "raw_stdout": result.stdout[:500]}
    return {
        "returncode": result.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "payload": payload,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    verifier = run_verifier()
    payload = verifier["payload"]
    positives = int(payload.get("positive_rows") or 0)
    negatives = int(payload.get("matched_negative_rows") or 0)
    groups = int(payload.get("matched_group_count") or 0)
    sidecar_controls = len(read_csv(SIDECAR_CONTROLS))
    v56 = json.loads(V56_JSON.read_text(encoding="utf-8")) if V56_JSON.exists() else {}
    split_rows = read_csv(V56_SPLITS)
    chronological_gate = str(v56.get("chronological_split_gate", "false")).lower() == "true"
    heldout_symbol_gate = str(v56.get("heldout_symbol_gate", "false")).lower() == "true"
    heldout_venue_gate = str(v56.get("heldout_venue_gate", "false")).lower() == "true"
    direct_species_closed = bool(v56.get("direct_species_closed", False))
    canonical_files = {
        "positive_rows": CANONICAL_ROOT / "positive_spoofing_layering_rows.csv",
        "matched_negative_rows": CANONICAL_ROOT / "matched_negative_normal_activity_rows.csv",
        "provenance": CANONICAL_ROOT / "provenance_manifest.json",
    }
    canonical_hashes = {
        name: sha256(path) if path.exists() else "missing"
        for name, path in canonical_files.items()
    }
    pooled_lcb = min(wilson_lcb(positives, positives), wilson_lcb(negatives, negatives))
    canonical_schema_ready = verifier["returncode"] == 0 and payload.get("status") == "schema_ready_unscored"
    strict_done = False

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "canonical_root": str(CANONICAL_ROOT),
        "canonical_root_exists": CANONICAL_ROOT.exists(),
        "canonical_schema_ready": canonical_schema_ready,
        "canonical_hashes": canonical_hashes,
        "verifier": verifier,
        "positive_rows": positives,
        "matched_negative_rows": negatives,
        "matched_group_count": groups,
        "sidecar_broad_normal_control_rows": sidecar_controls,
        "pooled_min_wilson95_lcb": round(pooled_lcb, 12),
        "pooled_wilson95_gate": pooled_lcb >= MIN_WILSON,
        "chronological_split_gate": chronological_gate,
        "heldout_symbol_gate": heldout_symbol_gate,
        "heldout_venue_gate": heldout_venue_gate,
        "direct_species_closed": direct_species_closed,
        "split_metrics_source": str(V56_SPLITS),
        "split_metric_rows": len(split_rows),
        "source_v56_json": str(V56_JSON),
        "external_requests_sent": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": pooled_lcb >= MIN_WILSON,
        "strict_full_objective_achieved": strict_done,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "trade_usable": False,
        "gate_result": "r6_live_canonical_intake_readback_after_v56=canonical_live_schema_ready_pooled_wilson_passed_split_species_still_blocked",
        "next_action": (
            "Use the live canonical 73x73 intake plus durable V56 snapshot to extend chronological, "
            "symbol, venue, and non-spoofing species support, then rerun direct plus sidecar calibration."
        ),
    }

    json_path = OUT / "r6_live_canonical_intake_readback_after_v56_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = OUT / "r6_live_canonical_intake_readback_after_v56_v1.md"
    report = f"""# R6 Live Canonical Intake Readback After V56 v1

- Run id: `{RUN_ID}`
- Canonical root: `{CANONICAL_ROOT}`
- Canonical schema ready: `{str(canonical_schema_ready).lower()}`
- Direct rows: positives `{positives}`, matched controls `{negatives}`, matched groups `{groups}`
- Sidecar broad-normal controls: `{sidecar_controls}`
- Pooled Wilson95 min LCB: `{result['pooled_min_wilson95_lcb']}`; pooled gate `{str(result['pooled_wilson95_gate']).lower()}`
- Chronological split gate: `{str(chronological_gate).lower()}`
- Heldout symbol gate: `{str(heldout_symbol_gate).lower()}`
- Heldout venue gate: `{str(heldout_venue_gate).lower()}`
- Direct species closed: `{str(direct_species_closed).lower()}`
- Gate result: `{result['gate_result']}`
- Strict full objective achieved: `false`; `update_goal=false`

## Artifacts
- JSON: `{json_path}`
- Verifier stdout: `{verifier['stdout_path']}`
- Assertions: `{CHECKS / 'r6_live_canonical_intake_readback_after_v56_v1_assertions.out'}`

## Next
{result['next_action']}
"""
    report_path.write_text(report, encoding="utf-8")

    checks = {
        "canonical_schema_ready": canonical_schema_ready,
        "positive_rows_73": positives == 73,
        "matched_negative_rows_73": negatives == 73,
        "pooled_wilson95_passed": pooled_lcb >= MIN_WILSON,
        "chronological_split_still_blocked": not chronological_gate,
        "heldout_symbol_still_blocked": not heldout_symbol_gate,
        "heldout_venue_still_blocked": not heldout_venue_gate,
        "direct_species_not_closed": not direct_species_closed,
        "strict_full_objective_not_complete": not strict_done,
        "no_runtime_code_changed": not result["runtime_code_changed"],
    }
    checks_path = CHECKS / "r6_live_canonical_intake_readback_after_v56_v1_assertions.out"
    checks_path.write_text("\n".join(f"{key}=ok" if ok else f"{key}=FAIL" for key, ok in checks.items()) + "\n", encoding="utf-8")
    if not all(checks.values()):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
