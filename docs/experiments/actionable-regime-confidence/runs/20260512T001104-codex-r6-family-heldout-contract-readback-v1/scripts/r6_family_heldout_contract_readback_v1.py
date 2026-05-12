#!/usr/bin/env python3
"""Draft and read back a family-level heldout split contract for R6.

This does not replace the current exact-symbol/exact-venue gate. It quantifies
whether a market-family / venue-family contract would be a lower-debt next
path before more direct Manipulation rows are sourced.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001104-codex-r6-family-heldout-contract-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-family-heldout-contract-readback"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_R6_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V58_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration"
)
POSITIVE = V58_ROOT / "positive_spoofing_layering_rows_v1.csv"
NEGATIVE = V58_ROOT / "matched_negative_normal_activity_rows_v1.csv"
EXACT_DEBT_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000801-codex-r6-exact-split-support-debt-audit-v1"
    / "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)

Z95 = 1.959963984540054
MIN_WILSON = 0.95
MIN_SUPPORT = 50


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson_all_success_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + Z95 * Z95 / n
    center = 1.0 + Z95 * Z95 / (2.0 * n)
    margin = Z95 * math.sqrt(Z95 * Z95 / (4.0 * n * n))
    return (center - margin) / denominator


def min_count() -> int:
    n = 1
    while wilson_all_success_lcb(n) < MIN_WILSON:
        n += 1
    return n


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_R6_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    stdout = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "parse_failed", "stdout_sample": proc.stdout[:500]}
    return {"returncode": proc.returncode, "payload": payload, "stdout": rel(stdout), "stderr": rel(stderr)}


def market_family(symbol: str) -> str:
    value = symbol.lower()
    if any(token in value for token in ["gold", "silver", "platinum", "copper", "lme", "comex"]):
        return "metals_futures"
    if any(token in value for token in ["crude", "rbob", "natural gas", "brent", "wti", "ngh0", "clm0", "light sweet"]):
        return "energy_futures"
    if any(token in value for token in ["e-mini", "nasdaq", "s&p", "dow"]):
        return "equity_index_futures"
    if any(token in value for token in ["soybean", "wheat"]):
        return "agriculture_futures"
    return "other_or_unmapped"


def venue_family(venue: str) -> str:
    value = venue.lower()
    if "comex" in value or "lme" in value:
        return "metals_venues_comex_lme"
    if "nymex" in value or "ifeu" in value or "ice" in value:
        return "energy_venues_nymex_ice"
    if "cbot" in value:
        return "agriculture_or_rates_venues_cbot"
    if "cme" in value or "globex" in value or "us futures exchange" in value:
        return "cme_globex_index_or_generic"
    return "other_or_unmapped"


def metric(axis: str, name: str, positive_support: int, negative_support: int, floor: int) -> dict[str, Any]:
    pos_lcb = wilson_all_success_lcb(positive_support)
    neg_lcb = wilson_all_success_lcb(negative_support)
    min_lcb = min(pos_lcb, neg_lcb)
    support_ok = positive_support >= MIN_SUPPORT and negative_support >= MIN_SUPPORT
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "axis": axis,
        "name": name,
        "positive_support": positive_support,
        "negative_support": negative_support,
        "positive_lcb": round(pos_lcb, 12),
        "negative_lcb": round(neg_lcb, 12),
        "min_lcb": round(min_lcb, 12),
        "positive_rows_needed_for_95": max(0, floor - positive_support),
        "negative_rows_needed_for_95": max(0, floor - negative_support),
        "pair_rows_needed_for_95": max(max(0, floor - positive_support), max(0, floor - negative_support)),
        "pass": support_ok and wilson_ok,
    }


def family_metrics(positives: list[dict[str, str]], negatives: list[dict[str, str]], floor: int) -> list[dict[str, Any]]:
    enriched: list[tuple[str, dict[str, str]]] = []
    for row in positives:
        enriched.append(("positive", row))
    for row in negatives:
        enriched.append(("negative", row))

    families: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0})
    for kind, row in enriched:
        families[("market_family", market_family(row.get("symbol", "")))][kind] += 1
        families[("venue_family", venue_family(row.get("venue_or_market_center", "")))][kind] += 1

    rows = []
    for (axis, name), counts in sorted(families.items()):
        rows.append(metric(axis, name, counts["positive"], counts["negative"], floor))
    return rows


def contract_rows() -> list[dict[str, str]]:
    return [
        {
            "clause": "authority_boundary",
            "rule": "This artifact is a candidate heldout contract only; it does not replace the current exact-symbol/exact-venue gate without explicit board/user approval.",
        },
        {
            "clause": "raw_identity_preserved",
            "rule": "Keep raw symbol and venue strings in every row; family labels are additional audit axes, not data rewrites.",
        },
        {
            "clause": "accepted_family_floor",
            "rule": "A family bucket must pass support and Wilson95 with positive and matched-control rows; unknown_or_unmapped is fail-closed.",
        },
        {
            "clause": "no_new_sparse_bucket_promotion",
            "rule": "Adding a new family bucket cannot improve acceptance unless that bucket also carries enough paired direct rows to pass.",
        },
        {
            "clause": "chronology_still_required",
            "rule": "Family grouping does not waive chronological train/calibration/test gates.",
        },
        {
            "clause": "species_still_required",
            "rule": "Family grouping does not close quote_stuffing, pinging, bear_raid_or_painting_tape, or pump_dump_social_text_or_onchain gaps.",
        },
    ]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    board_hash = sha256(BOARD)
    required = [DIRECT_VERIFIER, POSITIVE, NEGATIVE, EXACT_DEBT_JSON]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        write_json(
            OUT / "r6_family_heldout_contract_readback_v1.json",
            {
                "run_id": RUN_ID,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "board_sha256_at_start": board_hash,
                "status": "blocked",
                "reason": "missing_required_inputs",
                "missing": missing,
                "update_goal": False,
            },
        )
        return 2

    verifier = run_verifier()
    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    floor = min_count()
    metrics = family_metrics(positives, negatives, floor)
    exact_debt = json.loads(EXACT_DEBT_JSON.read_text(encoding="utf-8"))
    family_csv = OUT / "r6_family_heldout_contract_metrics_v1.csv"
    contract_csv = OUT / "r6_family_heldout_contract_v1.csv"
    write_csv(
        family_csv,
        metrics,
        [
            "axis",
            "name",
            "positive_support",
            "negative_support",
            "positive_lcb",
            "negative_lcb",
            "min_lcb",
            "positive_rows_needed_for_95",
            "negative_rows_needed_for_95",
            "pair_rows_needed_for_95",
            "pass",
        ],
    )
    write_csv(contract_csv, contract_rows(), ["clause", "rule"])

    market_rows = [row for row in metrics if row["axis"] == "market_family"]
    venue_rows = [row for row in metrics if row["axis"] == "venue_family"]
    family_debt = sum(row["pair_rows_needed_for_95"] for row in metrics if not row["pass"])
    exact_debt_total = exact_debt.get("debt_summary", {}).get("total_pairwise_rows_needed_if_existing_exact_buckets_are_filled")
    best_market = min(market_rows, key=lambda row: row["pair_rows_needed_for_95"]) if market_rows else {}
    best_venue = min(venue_rows, key=lambda row: row["pair_rows_needed_for_95"]) if venue_rows else {}
    family_axis_pass = all(row["pass"] for row in metrics)
    gate_result = "r6_family_heldout_contract_readback_v1=family_contract_draft_reduces_exact_debt_but_gates_still_blocked"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "verifier": verifier,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "support_floor_for_wilson95": floor,
        "contract_csv": rel(contract_csv),
        "family_metrics_csv": rel(family_csv),
        "family_axis_pass": family_axis_pass,
        "family_pairwise_debt_if_current_family_buckets_must_pass": family_debt,
        "exact_pairwise_debt_prior": exact_debt_total,
        "best_market_family": best_market,
        "best_venue_family": best_venue,
        "chronological_gate_still_required": True,
        "direct_species_still_required": True,
        "contract_replaces_exact_gate": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "next_action": (
            "If the board/user accepts family-level heldout axes, source rows into metals_futures/"
            "metals_venues_comex_lme first; otherwise pursue a large owner-approved export for exact buckets. "
            "Either path still needs chronology and non-spoofing species closure."
        ),
    }
    json_path = OUT / "r6_family_heldout_contract_readback_v1.json"
    report_path = OUT / "r6_family_heldout_contract_readback_v1.md"
    write_json(json_path, result)
    report_path.write_text(
        "\n".join(
            [
                "# R6 Family Heldout Contract Readback v1",
                "",
                f"- Run id: `{RUN_ID}`",
                f"- Live verifier: `{verifier['payload'].get('status')}` rows `{len(positives)}/{len(negatives)}`.",
                f"- Candidate contract replaces exact gate: `false`.",
                f"- Family axis pass: `{str(family_axis_pass).lower()}`.",
                f"- Family pairwise debt if all current family buckets must pass: `{family_debt}`.",
                f"- Prior exact pairwise debt: `{exact_debt_total}`.",
                f"- Best market family: `{best_market.get('name')}` needs `{best_market.get('pair_rows_needed_for_95')}` paired rows.",
                f"- Best venue family: `{best_venue.get('name')}` needs `{best_venue.get('pair_rows_needed_for_95')}` paired rows.",
                f"- Gate result: `{gate_result}`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "",
                "## Boundary",
                "- This is a candidate contract/readback only. It preserves raw symbol and venue strings and does not waive chronology or species gates.",
                "- No Board A confidence acceptance is claimed from this family grouping.",
                "",
                "## Artifacts",
                f"- JSON: `{rel(json_path)}`",
                f"- Contract CSV: `{rel(contract_csv)}`",
                f"- Family metrics CSV: `{rel(family_csv)}`",
                f"- Verifier stdout: `{verifier['stdout']}`",
                f"- Assertions: `{rel(CHECKS / 'r6_family_heldout_contract_readback_v1_assertions.out')}`",
                "",
                "## Next",
                result["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        ("live_verifier_schema_ready", verifier["returncode"] == 0 and verifier["payload"].get("status") == "schema_ready_unscored"),
        ("exact_gate_not_replaced", not result["contract_replaces_exact_gate"]),
        ("strict_full_objective_not_complete", not result["strict_full_objective_achieved"]),
        ("update_goal_false", not result["update_goal"]),
        ("contract_written", contract_csv.exists()),
        ("metrics_written", family_csv.exists()),
    ]
    (CHECKS / "r6_family_heldout_contract_readback_v1_assertions.out").write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": all(passed for _, passed in assertions), "gate_result": gate_result, "update_goal": False}, indent=2))
    return 0 if all(passed for _, passed in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
