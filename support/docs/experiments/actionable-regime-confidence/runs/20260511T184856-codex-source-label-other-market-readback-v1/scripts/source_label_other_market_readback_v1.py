#!/usr/bin/env python3
"""Read back other-market source-label coverage from existing artifacts."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T184856+0800-codex-source-label-other-market-readback-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184856-codex-source-label-other-market-readback-v1"
)
OUT_DIR = RUN_ROOT / "source-label-readback"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "source_label_other_market_readback_v1.json"
OUT_MD = OUT_DIR / "source_label_other_market_readback_v1.md"
OUT_CSV = OUT_DIR / "source_label_other_market_readback_v1_rows.csv"
OUT_ASSERT = CHECK_DIR / "source_label_other_market_readback_v1_assertions.out"

ATTACHABILITY_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T073430-codex-source-label-attachability-audit/"
    "source-label-attachability/source_label_attachability_audit.json"
)
TSIE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T074300-codex-hf-tsie-source-label-mapping-audit/"
    "hf-tsie-mapping/hf_tsie_source_label_mapping_audit.json"
)
PUBLIC_SWEEP_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081200-codex-public-source-label-candidate-sweep/"
    "source-candidate-sweep/public_source_label_candidate_sweep.json"
)
CRYSTALBULL_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T115235-codex-crystalbull-source-label-attachability/"
    "source-label-attachability/crystalbull_source_label_attachability.json"
)
EXTERNAL_SCREEN_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183328-codex-external-source-label-candidate-screen-v1/"
    "external-source-label-screen/external_source_label_candidate_screen_v1.json"
)
INTAKE_VERIFIER_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_missing_result_v1.json"
)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows(
    attach: dict[str, Any],
    tsie: dict[str, Any],
    sweep: dict[str, Any],
    crystal: dict[str, Any],
    external: dict[str, Any],
    intake: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "source": "existing_source_label_attachability",
            "artifact": repo_rel(ATTACHABILITY_JSON),
            "attached_or_overlap": attach.get("cells_with_any_existing_root_packet_overlap", 0),
            "accepted_factor_or_gate": 0,
            "blocking_reason": f"full four-root attached cells={attach.get('full_main_roots_attached_cells', 0)}; unsupported cells={attach.get('unsupported_full_root_label_cells', 0)}",
            "decision": attach.get("gate_result", ""),
        },
        {
            "source": "public_source_label_candidate_sweep",
            "artifact": repo_rel(PUBLIC_SWEEP_JSON),
            "attached_or_overlap": sweep.get("current_blocker", {}).get("attached_direct_source_label_slots", 0),
            "accepted_factor_or_gate": 0,
            "blocking_reason": f"missing slots={sweep.get('current_blocker', {}).get('missing_slots', '')}; public HMM/HF/OHLCV labels rejected as proxy or sidecar",
            "decision": sweep.get("sweep_result", {}).get("gate_result", "new_accepted_source_label_slots=0"),
        },
        {
            "source": "hf_tsie_market_regime_dataset",
            "artifact": repo_rel(TSIE_JSON),
            "attached_or_overlap": 0,
            "accepted_factor_or_gate": 0,
            "blocking_reason": "candidate Bull/Bear/Sideways mapping only; Crisis and Manipulation missing; no owner-approved MainRegimeV2 equivalence",
            "decision": tsie.get("gate_result", ""),
        },
        {
            "source": "crystalbull_qqq_daily_labels",
            "artifact": repo_rel(CRYSTALBULL_JSON),
            "attached_or_overlap": crystal.get("decision", {}).get("attached_source_label_slots_added", 0),
            "accepted_factor_or_gate": crystal.get("decision", {}).get("accepted_calibrated_root_factors_added", 0),
            "blocking_reason": "QQQ daily Bull/Bear/Sideways only; no Crisis root, no intraday/weekly/monthly crosswalk, factor gate still blocked",
            "decision": crystal.get("decision", {}).get("gate_result", ""),
        },
        {
            "source": "external_source_label_candidate_screen",
            "artifact": repo_rel(EXTERNAL_SCREEN_JSON),
            "attached_or_overlap": 0,
            "accepted_factor_or_gate": 0,
            "blocking_reason": f"promising but blocked={','.join(external.get('promising_but_blocked_candidates', []))}; no promotable MainRegimeV2 equivalence",
            "decision": external.get("decision", ""),
        },
        {
            "source": "source_label_equivalence_intake",
            "artifact": repo_rel(INTAKE_VERIFIER_JSON),
            "attached_or_overlap": 0,
            "accepted_factor_or_gate": 0,
            "blocking_reason": f"missing files={len(intake.get('missing_files', []))}; status={intake.get('status')}; reason={intake.get('reason')}",
            "decision": "source_label_equivalence_intake_verifier_v1=ready_rows_not_acquired",
        },
    ]


def write_csv(rows: list[dict[str, Any]]) -> None:
    fields = ["source", "artifact", "attached_or_overlap", "accepted_factor_or_gate", "blocking_reason", "decision"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Source Label Other-Market Readback v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This readback merges existing source-label and other-market artifacts. It does not fetch raw rows and does not edit the shared Current Cursor.",
        "",
        "## Decision",
        "",
        f"`{payload['decision']['gate_result']}`",
        "",
        f"- Source artifacts read: `{payload['source_artifact_count']}`.",
        f"- Public/partial attached source-label slots: `{payload['partial_attached_or_overlap_total']}`.",
        f"- Accepted calibrated root factors added: `{payload['accepted_factor_or_gate_total']}`.",
        "- Full other-market/source-label equivalence: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Rows",
        "",
        "| Source | Attached/Overlap | Accepted Gate | Decision | Blocking Reason |",
        "|---|---:|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['source']}` | `{row['attached_or_overlap']}` | `{row['accepted_factor_or_gate']}` | `{row['decision']}` | {row['blocking_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Readback",
            "",
            "- Existing accepted packets and CrystalBull add sparse or daily-only provenance, not a complete other-market/full-cycle panel.",
            "- HF TSIE and other public candidates remain sidecar/candidate mappings unless a source owner supplies an approved MainRegimeV2 crosswalk.",
            "- The external intake verifier is still missing source-owned rows/provenance, so no new confidence gate can be claimed.",
            "- This does not close QQQ/NQ/crypto/FX/rates/commodities equivalence or native sub-hour validation.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    attach = load_json(ATTACHABILITY_JSON)
    tsie = load_json(TSIE_JSON)
    sweep = load_json(PUBLIC_SWEEP_JSON)
    crystal = load_json(CRYSTALBULL_JSON)
    external = load_json(EXTERNAL_SCREEN_JSON)
    intake = load_json(INTAKE_VERIFIER_JSON)
    rows = build_rows(attach, tsie, sweep, crystal, external, intake)
    accepted_total = sum(int(row.get("accepted_factor_or_gate") or 0) for row in rows)
    partial_total = sum(int(row.get("attached_or_overlap") or 0) for row in rows)
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "source_label_other_market_readback_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_cursor_edited": False,
        "source_artifact_count": len(rows),
        "partial_attached_or_overlap_total": partial_total,
        "accepted_factor_or_gate_total": accepted_total,
        "rows": rows,
        "decision": {
            "gate_result": "source_label_other_market_readback_v1=partial_sources_no_full_equivalence",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_other_market_source_label_equivalence": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(rows)
    write_markdown(payload)
    assertions = [
        "PASS source_artifact_count=6" if len(rows) == 6 else "FAIL source_artifact_count",
        "PASS accepted_factor_or_gate_total=0" if accepted_total == 0 else "FAIL accepted_factor_or_gate_total",
        "PASS intake_missing_files" if len(intake.get("missing_files", [])) >= 2 else "FAIL intake_missing_files",
        "PASS full_other_market_source_label_equivalence=false" if not payload["decision"]["full_other_market_source_label_equivalence"] else "FAIL full_other_market_source_label_equivalence",
        "PASS full_objective=false" if not payload["decision"]["full_objective_achieved"] else "FAIL full_objective",
        "PASS current_cursor_edited=false" if not payload["current_cursor_edited"] else "FAIL current_cursor_edited",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if any(line.startswith("FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
