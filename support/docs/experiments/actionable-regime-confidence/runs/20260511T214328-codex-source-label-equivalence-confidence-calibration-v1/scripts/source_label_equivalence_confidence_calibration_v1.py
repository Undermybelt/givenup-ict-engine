#!/usr/bin/env python3
"""Fail-closed confidence calibration over the live source-label equivalence root."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260511T214328-codex-source-label-equivalence-confidence-calibration-v1"
OUT = RUN_ROOT / "source-label-equivalence-confidence-calibration"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-public-source-intake-scout/nifty/regime_timeline_history.csv")
NIFTY_METADATA = Path("/tmp/ict-engine-public-source-intake-scout/nifty/dataset-metadata.json")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
CONFIDENCE_THRESHOLD = 0.95
MIN_SUPPORT = 50
WILSON_THRESHOLD = 0.95
Z95 = 1.959963984540054


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2 * total)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * total)) / total)
    return (center - radius) / denom


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "max": max(values),
    }


def run_verifier() -> dict[str, Any]:
    stdout_path = COMMAND_OUT / "source_label_equivalence_verifier.stdout.txt"
    stderr_path = COMMAND_OUT / "source_label_equivalence_verifier.stderr.txt"
    exit_path = COMMAND_OUT / "source_label_equivalence_verifier.exit"
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(str(proc.returncode) + "\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "blocked", "reason": "verifier_stdout_not_json"}
    parsed["return_code"] = proc.returncode
    return parsed


def stock_confidence_map() -> dict[tuple[str, str, str], float]:
    mapping: dict[tuple[str, str, str], float] = {}
    for row in read_csv(STOCK_SOURCE):
        try:
            confidence = float(row.get("regime_confidence", ""))
        except ValueError:
            continue
        mapping[(row["date"], row["ticker"], row["regime_label"])] = confidence
    return mapping


def nifty_confidence_map() -> dict[tuple[str, str, str, str], float]:
    mapping: dict[tuple[str, str, str, str], float] = {}
    for row in read_csv(NIFTY_SOURCE):
        day = row["Date"]
        symbol = "NIFTY500"
        if row.get("macro_state") == "Durable":
            mapping[(day, symbol, "NIFTY500:macro_state", "Bull")] = float(row.get("macro_confidence") or 0.0)
        if row.get("fast_state") == "Calm":
            mapping[(day, symbol, "NIFTY500:fast_state", "Sideways")] = float(row.get("fast_confidence") or 0.0)
        if row.get("fast_state") == "Stress":
            mapping[(day, symbol, "NIFTY500:fast_state", "Crisis")] = float(row.get("fast_confidence") or 0.0)
    return mapping


def confidence_for_row(
    row: dict[str, str],
    stock_map: dict[tuple[str, str, str], float],
    nifty_map: dict[tuple[str, str, str, str], float],
) -> float | None:
    owner = row.get("source_owner", "")
    label = row.get("main_regime_v2_label", "")
    if owner == "source-owned-stock-market-regimes-2000-2026":
        return stock_map.get((row.get("timestamp_or_date", ""), row.get("symbol", ""), label))
    if owner == "ahaanverma00":
        return nifty_map.get(
            (
                row.get("timestamp_or_date", ""),
                row.get("symbol", ""),
                row.get("source_symbol", ""),
                label,
            )
        )
    return None


def metric_row(
    *,
    label: str,
    split: str,
    source_owner: str,
    market_family: str,
    values: list[float],
) -> dict[str, Any]:
    total = len(values)
    high = sum(1 for value in values if value >= CONFIDENCE_THRESHOLD)
    stats = summarize(values)
    return {
        "label": label,
        "split_role": split,
        "source_owner": source_owner,
        "market_family": market_family,
        "support": total,
        "rows_at_or_above_0_95": high,
        "share_at_or_above_0_95": round(high / total, 10) if total else 0.0,
        "wilson95_lcb": round(wilson_lcb(high, total), 10),
        "confidence_min": round(stats["min"], 10),
        "confidence_median": round(stats["median"], 10),
        "confidence_mean": round(stats["mean"], 10),
        "confidence_max": round(stats["max"], 10),
    }


def gate_for_label(label: str, split_rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    by_split = {row["split_role"]: row for row in split_rows if row["label"] == label and row["source_owner"] == "ALL" and row["market_family"] == "ALL"}
    for split in REQUIRED_SPLITS:
        row = by_split.get(split)
        if row is None:
            blockers.append(f"{split}_missing")
            continue
        if int(row["support"]) < MIN_SUPPORT:
            blockers.append(f"{split}_support_below_{MIN_SUPPORT}")
        if float(row["wilson95_lcb"]) < WILSON_THRESHOLD:
            blockers.append(f"{split}_source_confidence_wilson95_below_{WILSON_THRESHOLD}")
    return {
        "label": label,
        "accepted_source_confidence_95": not blockers,
        "blockers": blockers,
        "required_splits": REQUIRED_SPLITS,
        "min_support": MIN_SUPPORT,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "wilson_threshold": WILSON_THRESHOLD,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    required_inputs = [BOARD, INTAKE_ROWS, INTAKE_PROVENANCE, STOCK_SOURCE, NIFTY_SOURCE, NIFTY_METADATA, VERIFIER]
    missing_inputs = [str(path) for path in required_inputs if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError(missing_inputs)

    verifier = run_verifier()
    intake_rows = read_csv(INTAKE_ROWS)
    provenance = load_json(INTAKE_PROVENANCE)
    stock_map = stock_confidence_map()
    nifty_map = nifty_confidence_map()

    values_by_label_split: dict[tuple[str, str], list[float]] = defaultdict(list)
    values_by_owner_label: dict[tuple[str, str], list[float]] = defaultdict(list)
    values_by_market_label: dict[tuple[str, str], list[float]] = defaultdict(list)
    missing_confidence: list[dict[str, str]] = []
    label_counts = Counter()
    split_counts = Counter()
    owner_counts = Counter()
    market_counts = Counter()
    date_values: list[str] = []

    for row in intake_rows:
        label = row.get("main_regime_v2_label", "")
        split = row.get("split_role", "")
        owner = row.get("source_owner", "")
        market = row.get("market_family", "")
        if label:
            label_counts[label] += 1
        if split:
            split_counts[split] += 1
        if owner:
            owner_counts[owner] += 1
        if market:
            market_counts[market] += 1
        if row.get("timestamp_or_date"):
            date_values.append(row["timestamp_or_date"])
        confidence = confidence_for_row(row, stock_map, nifty_map)
        if confidence is None:
            missing_confidence.append(
                {
                    "source_owner": owner,
                    "source_row_id": row.get("source_row_id", ""),
                    "symbol": row.get("symbol", ""),
                    "timestamp_or_date": row.get("timestamp_or_date", ""),
                    "label": label,
                }
            )
            continue
        values_by_label_split[(label, split)].append(confidence)
        values_by_owner_label[(owner, label)].append(confidence)
        values_by_market_label[(market, label)].append(confidence)

    split_rows: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        for split in REQUIRED_SPLITS:
            split_rows.append(
                metric_row(
                    label=label,
                    split=split,
                    source_owner="ALL",
                    market_family="ALL",
                    values=values_by_label_split.get((label, split), []),
                )
            )

    owner_rows = [
        metric_row(label=label, split="ALL", source_owner=owner, market_family="ALL", values=values)
        for (owner, label), values in sorted(values_by_owner_label.items())
    ]
    market_rows = [
        metric_row(label=label, split="ALL", source_owner="ALL", market_family=market, values=values)
        for (market, label), values in sorted(values_by_market_label.items())
    ]
    gates = [gate_for_label(label, split_rows) for label in ROOT_LABELS]
    accepted_labels = [gate["label"] for gate in gates if gate["accepted_source_confidence_95"]]
    missing_labels = sorted(set(ROOT_LABELS) - set(label_counts))
    all_roots_present = not missing_labels
    verifier_ready = verifier.get("status") == "schema_ready_unscored" and verifier.get("return_code") == 0
    source_confidence_available = len(missing_confidence) == 0
    new_confidence_gate = all_roots_present and source_confidence_available and len(accepted_labels) == len(ROOT_LABELS)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256_file(BOARD),
        "decision": "source_label_equivalence_confidence_calibration_v1=source_confidence_scored_no_acceptance",
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "intake_root": str(INTAKE_ROOT),
            "intake_rows_sha256": sha256_file(INTAKE_ROWS),
            "intake_provenance_sha256": sha256_file(INTAKE_PROVENANCE),
            "stock_source": str(STOCK_SOURCE),
            "stock_source_sha256": sha256_file(STOCK_SOURCE),
            "nifty_source": str(NIFTY_SOURCE),
            "nifty_source_sha256": sha256_file(NIFTY_SOURCE),
            "verifier": str(VERIFIER.relative_to(REPO)),
        },
        "verifier": verifier,
        "provenance_row_count": provenance.get("row_count"),
        "provenance_rows_sha256": provenance.get("rows_sha256") or provenance.get("shared_rows_sha256"),
        "row_count": len(intake_rows),
        "label_counts": dict(sorted(label_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "source_owner_counts": dict(sorted(owner_counts.items())),
        "market_family_counts": dict(sorted(market_counts.items())),
        "date_min": min(date_values) if date_values else "",
        "date_max": max(date_values) if date_values else "",
        "all_roots_present": all_roots_present,
        "missing_roots": missing_labels,
        "source_confidence_available_for_all_rows": source_confidence_available,
        "missing_confidence_rows": len(missing_confidence),
        "missing_confidence_examples": missing_confidence[:10],
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "min_support": MIN_SUPPORT,
        "wilson_threshold": WILSON_THRESHOLD,
        "label_split_confidence": split_rows,
        "source_owner_confidence": owner_rows,
        "market_family_confidence": market_rows,
        "gates": gates,
        "accepted_source_confidence_95_labels": accepted_labels,
        "new_confidence_gate": new_confidence_gate,
        "accepted_rows_added": 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "blocker": "Cleaned source-label root has all four labels, but source-owned confidence fields do not clear 0.95 Wilson lower-bound gates across required chronological and heldout splits; R3 native sub-hour, R5 recency, and R6 direct gates remain open.",
    }

    json_path = OUT / "source_label_equivalence_confidence_calibration_v1.json"
    report_path = OUT / "source_label_equivalence_confidence_calibration_v1.md"
    split_csv = OUT / "source_label_equivalence_confidence_calibration_label_split_v1.csv"
    owner_csv = OUT / "source_label_equivalence_confidence_calibration_owner_v1.csv"
    market_csv = OUT / "source_label_equivalence_confidence_calibration_market_v1.csv"
    gates_csv = OUT / "source_label_equivalence_confidence_calibration_gates_v1.csv"
    assertions_path = CHECKS / "source_label_equivalence_confidence_calibration_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with split_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(split_rows[0].keys()))
        writer.writeheader()
        writer.writerows(split_rows)
    with owner_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(owner_rows[0].keys()))
        writer.writeheader()
        writer.writerows(owner_rows)
    with market_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(market_rows[0].keys()))
        writer.writeheader()
        writer.writerows(market_rows)
    with gates_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "label",
                "accepted_source_confidence_95",
                "blockers",
                "required_splits",
                "min_support",
                "confidence_threshold",
                "wilson_threshold",
            ],
        )
        writer.writeheader()
        for gate in gates:
            writer.writerow(
                {
                    **gate,
                    "blockers": ";".join(gate["blockers"]),
                    "required_splits": ";".join(gate["required_splits"]),
                }
            )

    lines = [
        "# Source Label Equivalence Confidence Calibration v1",
        "",
        f"- Decision: `{result['decision']}`.",
        f"- Verifier status: `{verifier.get('status')}`; return code `{verifier.get('return_code')}`; rows `{len(intake_rows)}`.",
        f"- Labels present: `{dict(sorted(label_counts.items()))}`; missing roots `{missing_labels}`.",
        f"- Confidence rule: source-owned confidence field `>= {CONFIDENCE_THRESHOLD}`; Wilson95 lower bound `>= {WILSON_THRESHOLD}`; minimum support `{MIN_SUPPORT}` per required split.",
        f"- Accepted source-confidence labels: `{accepted_labels}`.",
        f"- Missing confidence rows: `{len(missing_confidence)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Label Split Scores",
        "",
        "| Label | Split | Support | Rows >=0.95 | Share >=0.95 | Wilson95 LCB | Mean | Median | Max |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in split_rows:
        lines.append(
            f"| `{row['label']}` | `{row['split_role']}` | `{row['support']}` | "
            f"`{row['rows_at_or_above_0_95']}` | `{row['share_at_or_above_0_95']:.6f}` | "
            f"`{row['wilson95_lcb']:.6f}` | `{row['confidence_mean']:.6f}` | "
            f"`{row['confidence_median']:.6f}` | `{row['confidence_max']:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| Label | Accepted 95 | Blockers |",
            "|---|---|---|",
        ]
    )
    for gate in gates:
        lines.append(
            f"| `{gate['label']}` | `{str(gate['accepted_source_confidence_95']).lower()}` | "
            f"{'; '.join(gate['blockers']) or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a source-confidence calibration screen over the live cleaned source-label equivalence root. It does not promote schema readiness into accepted Board A confidence, does not create native sub-hour or R5 recency-extension rows, and does not alter R6 direct Manipulation evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Label split CSV: `{split_csv.relative_to(REPO)}`",
            f"- Source owner CSV: `{owner_csv.relative_to(REPO)}`",
            f"- Market family CSV: `{market_csv.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Verifier stdout: `{(COMMAND_OUT / 'source_label_equivalence_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS verifier_return_code={verifier.get('return_code')}",
        f"PASS row_count={len(intake_rows)}",
        f"PASS all_roots_present={str(all_roots_present).lower()}",
        f"PASS missing_confidence_rows={len(missing_confidence)}",
        f"PASS accepted_source_confidence_95_labels={','.join(accepted_labels) or 'none'}",
        f"PASS new_confidence_gate={str(new_confidence_gate).lower()}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=false",
        "PASS trade_usable=false",
    ]
    if not verifier_ready:
        raise AssertionError("source-label verifier did not return schema_ready_unscored")
    if new_confidence_gate:
        raise AssertionError("unexpected source-label confidence acceptance")
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "run_id": RUN_ID,
                "row_count": len(intake_rows),
                "accepted_source_confidence_95_labels": accepted_labels,
                "new_confidence_gate": new_confidence_gate,
                "strict_full_objective_achieved": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
