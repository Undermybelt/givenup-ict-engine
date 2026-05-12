#!/usr/bin/env python3
"""Check whether the existing source panel can materialize the next strict 1h intake contract."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T192900+0800-codex-strict-1h-contract-panel-exhaustion-v1"
RUN_DIR = "20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_DIR
OUT_DIR = RUN_ROOT / "strict-1h-contract-panel-exhaustion"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

CONTRACT_TARGETS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T192211-codex-strict-1h-next-source-intake-contract-v1/"
    "strict-1h-next-source-intake-contract/strict_1h_next_source_intake_targets_v1.csv"
)
NEAR_MISS_ROWS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T191552-codex-strict-1h-post-future-gap-triage-v1/"
    "strict-1h-post-future-gap-triage/strict_1h_post_future_gap_triage_v1_rows.csv"
)
STRICT_GATE_ROWS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
SOURCE_PANEL_CANDIDATES = [
    Path("/tmp/ict-engine-kaggle-stock-regimes-live-check-20260511T191523/stock_market_regimes_2000_2026.csv"),
    Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def source_panel_path() -> Path:
    for path in SOURCE_PANEL_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("stock_market_regimes_2000_2026.csv not found in known source-panel locations")


def split_year(split_role: str) -> int:
    if split_role == "calibration":
        return 2024
    if split_role == "heldout_time":
        return 2025
    raise ValueError(f"unsupported split_role for this contract: {split_role}")


def support_field(split_role: str) -> str:
    if split_role == "calibration":
        return "calibration_2024_support"
    if split_role == "heldout_time":
        return "heldout_time_2025_support"
    raise ValueError(f"unsupported split_role for this contract: {split_role}")


def count_source_rows(path: Path) -> dict[tuple[str, str, int], dict[str, object]]:
    counts: dict[tuple[str, str, int], dict[str, object]] = defaultdict(
        lambda: {"source_rows_in_split": 0, "first_date": "", "last_date": ""}
    )
    tail_counts: dict[tuple[str, str], int] = defaultdict(int)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            date = row["date"][:10]
            symbol = row["ticker"]
            label = row["regime_label"]
            year = int(date[:4])
            key = (symbol, label, year)
            item = counts[key]
            item["source_rows_in_split"] = int(item["source_rows_in_split"]) + 1
            if not item["first_date"]:
                item["first_date"] = date
            item["last_date"] = date
            if "2026-01-02" <= date <= "2026-01-30":
                tail_counts[(symbol, label)] += 1
    for (symbol, label), count in tail_counts.items():
        counts[(symbol, label, 2026)]["jan2026_tail_rows"] = count
    return counts


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source_path = source_panel_path()
    contract_rows = read_csv(CONTRACT_TARGETS)
    near_rows = {
        (row["instrument"], row["root"], row["repair_split"]): row
        for row in read_csv(NEAR_MISS_ROWS)
    }
    strict_rows = {
        (row["instrument"], row["root"]): row
        for row in read_csv(STRICT_GATE_ROWS)
    }
    source_counts = count_source_rows(source_path)

    target_rows: list[dict[str, object]] = []
    total_extra = 0
    for target in contract_rows:
        symbol = target["symbol"]
        label = target["main_regime_v2_label"]
        role = target["split_role"]
        year = split_year(role)
        repair_split = "calibration_2024" if role == "calibration" else "heldout_2025"
        near = near_rows[(symbol, label, repair_split)]
        strict = strict_rows[(symbol, label)]
        source = source_counts[(symbol, label, year)]
        jan_tail = int(source_counts[(symbol, label, 2026)].get("jan2026_tail_rows", 0))
        existing_support = int(float(strict[support_field(role)]))
        source_rows_in_split = int(source["source_rows_in_split"])
        extra_rows = max(0, source_rows_in_split - existing_support)
        required = int(target["minimum_new_source_sessions"])
        total_extra += extra_rows
        target_rows.append(
            {
                "priority": target["priority"],
                "symbol": symbol,
                "label": label,
                "split_role": role,
                "split_year": year,
                "required_new_source_sessions": required,
                "source_rows_in_split": source_rows_in_split,
                "existing_strict_gate_support": existing_support,
                "extra_source_rows_beyond_existing_gate": extra_rows,
                "can_materialize_from_existing_panel": str(extra_rows >= required).lower(),
                "source_first_date": source["first_date"],
                "source_last_date": source["last_date"],
                "jan2026_tail_rows_for_symbol_label": jan_tail,
                "near_miss_blocker": near["blocker"],
                "acceptable_package_id": target["acceptable_package_id"],
                "market_family": target["market_family"],
            }
        )

    can_materialize_any = any(row["can_materialize_from_existing_panel"] == "true" for row in target_rows)
    decision = {
        "gate_result": "strict_1h_contract_panel_exhaustion_v1=existing_source_panel_has_zero_extra_contract_rows",
        "contract_targets": len(target_rows),
        "targets_materializable_from_existing_panel": sum(
            1 for row in target_rows if row["can_materialize_from_existing_panel"] == "true"
        ),
        "extra_source_rows_beyond_existing_gate_total": total_extra,
        "intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    report = {
        "artifact_type": "strict_1h_contract_panel_exhaustion_v1",
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_observed": sha256(BOARD),
        "inputs": {
            "contract_targets": repo_rel(CONTRACT_TARGETS),
            "near_miss_rows": repo_rel(NEAR_MISS_ROWS),
            "strict_gate_rows": repo_rel(STRICT_GATE_ROWS),
            "source_panel": str(source_path),
            "source_panel_sha256": sha256(source_path),
        },
        "decision": decision,
        "targets": target_rows,
        "interpretation": [
            "The four strict 1h contract targets exactly match source-panel counts already consumed by the current strict gate.",
            "Reformatting the same source-panel rows into /tmp intake would duplicate existing support and cannot supply new source-owned sessions.",
            "The next useful input is a real owner-approved source extension or crosswalk, not another verifier readback against missing files.",
        ],
        "guardrails": [
            "No raw source panel rows were copied into the repo.",
            "No source labels were generated.",
            "No /tmp intake files were created.",
            "Current Cursor was not edited by this script.",
        ],
    }

    json_path = OUT_DIR / "strict_1h_contract_panel_exhaustion_v1.json"
    csv_path = OUT_DIR / "strict_1h_contract_panel_exhaustion_v1_targets.csv"
    md_path = OUT_DIR / "strict_1h_contract_panel_exhaustion_v1.md"
    assertions_path = CHECK_DIR / "strict_1h_contract_panel_exhaustion_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = [
        "priority",
        "symbol",
        "label",
        "split_role",
        "split_year",
        "required_new_source_sessions",
        "source_rows_in_split",
        "existing_strict_gate_support",
        "extra_source_rows_beyond_existing_gate",
        "can_materialize_from_existing_panel",
        "source_first_date",
        "source_last_date",
        "jan2026_tail_rows_for_symbol_label",
        "near_miss_blocker",
        "acceptable_package_id",
        "market_family",
    ]
    write_csv(csv_path, target_rows, fields)

    lines = [
        "# Strict 1h Contract Panel Exhaustion v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This checks whether the existing stock-market-regimes source panel can safely populate the `192211` strict `1h` intake contract without duplicating support already counted by the strict gate.",
        "",
        "## Decision",
        "",
        f"`{decision['gate_result']}`",
        "",
        f"- Contract targets checked: `{decision['contract_targets']}`.",
        f"- Targets materializable from existing panel: `{decision['targets_materializable_from_existing_panel']}`.",
        f"- Extra source rows beyond existing strict-gate support: `{decision['extra_source_rows_beyond_existing_gate_total']}`.",
        "- Intake files created: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Target Readback",
        "",
        "| Target | Split | Needed | Source rows | Existing gate support | Extra | Jan-2026 tail | Materializable |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in target_rows:
        lines.append(
            "| `{symbol}/{label}` | `{split_role}` `{split_year}` | {need} | {source_rows} | {existing} | {extra} | {tail} | `{ok}` |".format(
                symbol=row["symbol"],
                label=row["label"],
                split_role=row["split_role"],
                split_year=row["split_year"],
                need=row["required_new_source_sessions"],
                source_rows=row["source_rows_in_split"],
                existing=row["existing_strict_gate_support"],
                extra=row["extra_source_rows_beyond_existing_gate"],
                tail=row["jan2026_tail_rows_for_symbol_label"],
                ok=row["can_materialize_from_existing_panel"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The existing source panel has no extra rows for the four contract targets beyond what the current strict gate already counted.",
            "- Creating `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv` from this panel would only duplicate evidence and must remain fail-closed.",
            "- The next useful input is an owner-approved extension/crosswalk with new rows, then the existing verifier and unchanged strict chronological gates can be rerun.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_DIR}/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json`",
            f"- Target CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_DIR}/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1_targets.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_DIR}/checks/strict_1h_contract_panel_exhaustion_v1_assertions.out`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={decision['gate_result']}",
        f"contract_targets={decision['contract_targets']}",
        f"targets_materializable_from_existing_panel={decision['targets_materializable_from_existing_panel']}",
        f"extra_source_rows_beyond_existing_gate_total={decision['extra_source_rows_beyond_existing_gate_total']}",
        f"intake_files_created={str(decision['intake_files_created']).lower()}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"source_panel={source_path}",
        f"report_json={repo_rel(json_path)}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if can_materialize_any:
        raise SystemExit("unexpected materializable contract target found; rerun intake verifier instead")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
