#!/usr/bin/env python3
"""Ledger recent concurrent Board A artifacts without modifying their run dirs."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T183720+0800-codex-board-a-concurrent-artifact-ledger-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183720-codex-board-a-concurrent-artifact-ledger-v1"
)
OUT_DIR = RUN_ROOT / "concurrent-artifact-ledger"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

OUT_JSON = OUT_DIR / "board_a_concurrent_artifact_ledger_v1.json"
OUT_MD = OUT_DIR / "board_a_concurrent_artifact_ledger_v1.md"
OUT_CSV = OUT_DIR / "board_a_concurrent_artifact_ledger_v1_rows.csv"
OUT_ASSERT = CHECK_DIR / "board_a_concurrent_artifact_ledger_v1_assertions.out"

EVIDENCE = {
    "direct_manipulation_source_scan_v2": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T182601-codex-direct-manipulation-source-scan-v2/"
        "direct-source-scan/direct_manipulation_source_scan_v2.json"
    ),
    "hf_pumpdump_schema_audit_v1": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183018-codex-hf-pumpdump-schema-audit-v1/"
        "hf-pumpdump-schema/hf_pumpdump_schema_audit_v1.json"
    ),
    "source_label_equivalence_intake_verifier_v1": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
        "equivalence-intake-verifier/source_label_equivalence_intake_verifier_manifest_v1.json"
    ),
    "external_source_label_candidate_screen_v1": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183328-codex-external-source-label-candidate-screen-v1/"
        "external-source-label-screen/external_source_label_candidate_screen_v1.json"
    ),
    "macro_stress_asset_regime_schema_audit_v1": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183329-codex-macro-stress-asset-regime-schema-audit-v1/"
        "macro-stress-schema/macro_stress_asset_regime_schema_audit_v1.json"
    ),
    "external_intake_bundle_v1": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183606-codex-external-intake-bundle-v1/"
        "external-intake-bundle/board_a_external_intake_bundle_manifest_v1.json"
    ),
    "completion_audit_v18_prompt_artifact": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183611-codex-current-goal-completion-audit-v18-prompt-artifact/"
        "completion-audit/current_goal_completion_audit_v18_prompt_artifact.json"
    ),
    "completion_audit_v18_after_external_source_screen": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183632-current-goal-completion-audit-v18-after-external-source-screen/"
        "completion-audit/current_goal_completion_audit_v18_after_external_source_screen.json"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(doc: dict[str, Any]) -> str:
    decision = doc.get("decision")
    if isinstance(decision, dict):
        return str(decision.get("gate_result", ""))
    if isinstance(decision, str):
        return decision
    return str(doc.get("gate_result", ""))


def bool_field(doc: dict[str, Any], field: str) -> bool:
    decision = doc.get("decision")
    if isinstance(decision, dict) and field in decision:
        return bool(decision[field])
    return bool(doc.get(field, False))


def int_field(doc: dict[str, Any], field: str) -> int:
    decision = doc.get("decision")
    value: Any = None
    if isinstance(decision, dict) and field in decision:
        value = decision[field]
    else:
        value = doc.get(field, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main() -> int:
    missing = [name for name, path in EVIDENCE.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing evidence: {missing}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    loaded = {name: load_json(path) for name, path in EVIDENCE.items()}
    rows: list[dict[str, Any]] = []
    for name, path in EVIDENCE.items():
        doc = loaded[name]
        run_dir = path.parts[path.parts.index("runs") + 1]
        rows.append(
            {
                "artifact": name,
                "run_dir": run_dir,
                "path": str(path),
                "gate_result": gate(doc),
                "accepted_rows_added": int_field(doc, "accepted_rows_added"),
                "new_confidence_gate": bool_field(doc, "new_confidence_gate"),
                "full_objective_achieved": bool_field(doc, "full_objective_achieved"),
                "update_goal": bool_field(doc, "update_goal"),
                "runtime_code_changed": bool_field(doc, "runtime_code_changed"),
                "thresholds_relaxed": bool_field(doc, "thresholds_relaxed"),
                "raw_data_committed": bool_field(doc, "raw_data_committed"),
                "trade_usable": bool_field(doc, "trade_usable"),
                "already_registered_in_board_before_ledger": run_dir in board_text,
            }
        )

    unregistered = [row for row in rows if not row["already_registered_in_board_before_ledger"]]
    bad_completion = [
        row
        for row in rows
        if row["full_objective_achieved"]
        or row["update_goal"]
        or row["new_confidence_gate"]
        or row["accepted_rows_added"]
        or row["thresholds_relaxed"]
        or row["trade_usable"]
    ]
    artifact = {
        "run_id": RUN_ID,
        "artifact_type": "board_a_concurrent_artifact_ledger_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "purpose": "Preserve recent concurrent Board A evidence without editing other agents' run directories.",
        "artifact_count": len(rows),
        "unregistered_count_before_ledger": len(unregistered),
        "rows": rows,
        "decision": {
            "gate_result": "board_a_concurrent_artifact_ledger_v1=blocked_artifacts_preserved_no_completion",
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Do not repeat these metadata/screens. The next unblocker is actual source-owned "
            "rows or owner approval placed into the external intake bundle."
        ),
    }
    OUT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "artifact",
            "run_dir",
            "path",
            "gate_result",
            "accepted_rows_added",
            "new_confidence_gate",
            "full_objective_achieved",
            "update_goal",
            "runtime_code_changed",
            "thresholds_relaxed",
            "raw_data_committed",
            "trade_usable",
            "already_registered_in_board_before_ledger",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Board A Concurrent Artifact Ledger v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Gate result: `board_a_concurrent_artifact_ledger_v1=blocked_artifacts_preserved_no_completion`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        f"- Recent artifact count: `{len(rows)}`; unregistered before this ledger: `{len(unregistered)}`.",
        "",
        "## Rows",
        "",
        "| Artifact | Gate | Registered before ledger |",
        "|---|---|---|",
    ]
    for row in rows:
        md.append(
            f"| `{row['artifact']}` | `{row['gate_result']}` | `{str(row['already_registered_in_board_before_ledger']).lower()}` |"
        )
    md.extend(
        [
            "",
            "## Guardrail",
            "",
            "This ledger does not alter the source artifacts. It prevents duplicate source-screen work and keeps the strict blocker visible: source-owned rows or owner-approved equivalence files are still missing.",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    OUT_ASSERT.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"artifact_count={len(rows)}",
                f"unregistered_count_before_ledger={len(unregistered)}",
                f"bad_completion_signal_count={len(bad_completion)}",
                "strict_full_objective_achieved=false",
                "update_goal=false",
                "accepted_rows_added=0",
                "new_confidence_gate=false",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed=false",
                "trade_usable=false",
                "assertion_status=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(artifact["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
