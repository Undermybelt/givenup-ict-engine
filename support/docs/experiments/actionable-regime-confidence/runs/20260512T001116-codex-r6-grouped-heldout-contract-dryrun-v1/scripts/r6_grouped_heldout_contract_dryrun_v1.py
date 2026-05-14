#!/usr/bin/env python3
"""Dry-run a grouped heldout contract for R6 direct Manipulation.

The active exact-symbol/exact-venue contract is structurally blocked by row
debt. This script tests whether a less granular market-family / venue-family
contract would pass on the current live rows. It does not approve the contract
or mutate the shared intake.
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


RUN_ID = "20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-grouped-heldout-contract-dryrun"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LIVE_POSITIVE = LIVE_ROOT / "positive_spoofing_layering_rows.csv"
LIVE_NEGATIVE = LIVE_ROOT / "matched_negative_normal_activity_rows.csv"
LIVE_PROVENANCE = LIVE_ROOT / "provenance_manifest.json"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
DEBT_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000801-codex-r6-exact-split-support-debt-audit-v1"
    / "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)

MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96


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


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def metric(split_family: str, split_name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    positives = [row for row in rows if row["_class"] == "positive"]
    negatives = [row for row in rows if row["_class"] == "negative"]
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(pos_lcb, neg_lcb)
    support_ok = len(positives) >= MIN_SUPPORT and len(negatives) >= MIN_SUPPORT
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "split_family": split_family,
        "split_name": split_name,
        "positive_support": len(positives),
        "negative_support": len(negatives),
        "positive_wilson95_lcb": round(pos_lcb, 12),
        "negative_wilson95_lcb": round(neg_lcb, 12),
        "min_wilson95_lcb": round(min_lcb, 12),
        "support_ok": support_ok,
        "wilson_ok": wilson_ok,
        "pass": support_ok and wilson_ok,
    }


def classify_market_family(symbol: str) -> str:
    s = (symbol or "").lower()
    if any(token in s for token in ["s&p", "nasdaq", "dow", "index", "e-mini"]):
        return "equity_index_futures"
    if any(token in s for token in ["gold", "silver", "platinum", "copper", "lme"]):
        return "metals"
    if any(token in s for token in ["crude", "oil", "gasoline", "natural gas", "brent", "wti", "rbob"]):
        return "energy"
    if any(token in s for token in ["soybean", "wheat", "agriculture"]):
        return "agriculture"
    if "option" in s:
        return "listed_options"
    return "other"


def classify_venue_family(venue: str) -> str:
    v = (venue or "").lower()
    if any(token in v for token in ["cme", "cbot", "comex", "nymex", "globex"]):
        return "cme_group"
    if "lme" in v:
        return "lme_cross_market"
    if "ifeu" in v or "ice" in v:
        return "ice_ifeu"
    if "cftc complaint" in v or "us futures exchange" in v:
        return "us_futures_exchange_unspecified"
    return "other"


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_failed", "stdout_sample": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "payload": parsed,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
    }


def attach_class(rows: list[dict[str, str]], row_class: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        copy = dict(row)
        copy["_class"] = row_class
        copy["_market_family"] = classify_market_family(copy.get("symbol", ""))
        copy["_venue_family"] = classify_venue_family(copy.get("venue_or_market_center", ""))
        out.append(copy)
    return out


def grouped_metrics(rows: list[dict[str, str]], field: str, family_name: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row[field]].append(row)
    return [metric(family_name, name, group_rows) for name, group_rows in sorted(groups.items())]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    required = [BOARD, DIRECT_VERIFIER, LIVE_POSITIVE, LIVE_NEGATIVE, LIVE_PROVENANCE, DEBT_AUDIT]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing,
            "update_goal": False,
        }
        write_json(OUT / "r6_grouped_heldout_contract_dryrun_v1.json", payload)
        return 2

    positive_rows = attach_class(read_csv(LIVE_POSITIVE), "positive")
    negative_rows = attach_class(read_csv(LIVE_NEGATIVE), "negative")
    rows = positive_rows + negative_rows
    verifier = run_verifier()
    debt = json.loads(DEBT_AUDIT.read_text(encoding="utf-8"))

    metrics = [metric("pooled_all_source_rows", "all_rows", rows)]
    metrics.extend(grouped_metrics(rows, "_market_family", "heldout_market_family"))
    metrics.extend(grouped_metrics(rows, "_venue_family", "heldout_venue_family"))
    metrics.extend(grouped_metrics(rows, "session_bucket", "heldout_session_bucket"))
    metrics.extend(grouped_metrics(rows, "_market_family", "candidate_contract_market_family"))
    metrics.extend(grouped_metrics(rows, "_venue_family", "candidate_contract_venue_family"))

    market_family_pass = all(item["pass"] for item in metrics if item["split_family"] == "candidate_contract_market_family")
    venue_family_pass = all(item["pass"] for item in metrics if item["split_family"] == "candidate_contract_venue_family")
    grouped_contract_pass = market_family_pass and venue_family_pass
    verifier_ok = verifier["returncode"] == 0 and verifier["payload"].get("status") == "schema_ready_unscored"

    family_summary = {
        family: {
            "cells": len([item for item in metrics if item["split_family"] == family]),
            "failing_cells": len([item for item in metrics if item["split_family"] == family and not item["pass"]]),
            "min_cell_wilson95_lcb": min(
                (item["min_wilson95_lcb"] for item in metrics if item["split_family"] == family),
                default=0.0,
            ),
            "max_positive_support": max(
                (item["positive_support"] for item in metrics if item["split_family"] == family),
                default=0,
            ),
        }
        for family in sorted({item["split_family"] for item in metrics})
    }

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "live_root": str(LIVE_ROOT),
        "live_hashes": {
            "positive_rows": sha256(LIVE_POSITIVE),
            "matched_negative_rows": sha256(LIVE_NEGATIVE),
            "provenance": sha256(LIVE_PROVENANCE),
        },
        "verifier": verifier,
        "debt_audit_ref": {
            "path": rel(DEBT_AUDIT),
            "gate_result": debt.get("decision", {}).get("gate_result"),
            "exact_symbol_pairwise_debt": debt.get("debt_summary", {}).get("exact_symbol_pairwise_debt_if_current_buckets_must_all_pass"),
            "exact_venue_pairwise_debt": debt.get("debt_summary", {}).get("exact_venue_pairwise_debt_if_current_buckets_must_all_pass"),
        },
        "dryrun_metrics_csv": rel(OUT / "r6_grouped_heldout_contract_dryrun_v1_metrics.csv"),
        "family_summary": family_summary,
        "decision": {
            "gate_result": "r6_grouped_heldout_contract_dryrun_v1=grouped_contract_still_fails_owner_approval_required",
            "owner_approved_contract": False,
            "grouped_market_family_pass": market_family_pass,
            "grouped_venue_family_pass": venue_family_pass,
            "grouped_contract_pass": grouped_contract_pass,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "accepted_rows_added": 0,
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Grouped market-family/venue-family dry-run still fails on current rows; "
            "R6 now needs a large owner-approved row export or explicit user approval "
            "for a different validation contract before another split-acceptance attempt."
        ),
    }

    write_csv(
        OUT / "r6_grouped_heldout_contract_dryrun_v1_metrics.csv",
        metrics,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "positive_wilson95_lcb",
            "negative_wilson95_lcb",
            "min_wilson95_lcb",
            "support_ok",
            "wilson_ok",
            "pass",
        ],
    )
    write_json(OUT / "r6_grouped_heldout_contract_dryrun_v1.json", payload)

    report = f"""# R6 Grouped Heldout Contract Dry-Run v1

- Run id: `{RUN_ID}`.
- Live verifier status: `{verifier["payload"].get("status")}` with positives `{verifier["payload"].get("positive_rows")}` and matched controls `{verifier["payload"].get("matched_negative_rows")}`.
- Exact split debt reference: `{rel(DEBT_AUDIT)}`.
- Grouped market-family pass: `{str(market_family_pass).lower()}`.
- Grouped venue-family pass: `{str(venue_family_pass).lower()}`.
- Grouped contract pass: `{str(grouped_contract_pass).lower()}`.
- Owner-approved contract: `false`.
- Gate result: `{payload["decision"]["gate_result"]}`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Summary

The grouped contract is not enough on the current row set. It reduces exact bucket debt conceptually, but current market-family and venue-family cells still fail support/Wilson gates, and no owner approval exists for replacing the exact split contract.

## Artifacts

- JSON: `{rel(OUT / "r6_grouped_heldout_contract_dryrun_v1.json")}`
- Metrics CSV: `{rel(OUT / "r6_grouped_heldout_contract_dryrun_v1_metrics.csv")}`
- Direct verifier stdout: `{verifier["stdout_path"]}`

## Next

Source a large owner-approved direct row export or obtain explicit approval for a different validation contract before another R6 split-acceptance attempt.
"""
    (OUT / "r6_grouped_heldout_contract_dryrun_v1.md").write_text(report, encoding="utf-8")

    checks = [
        ("live_verifier_schema_ready", verifier_ok),
        ("grouped_market_family_still_fails", not market_family_pass),
        ("grouped_venue_family_still_fails", not venue_family_pass),
        ("owner_approved_contract_false", payload["decision"]["owner_approved_contract"] is False),
        ("new_confidence_gate_false", payload["decision"]["new_confidence_gate"] is False),
        ("strict_full_objective_not_complete", payload["decision"]["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["decision"]["update_goal"] is False),
    ]
    CHECKS.mkdir(parents=True, exist_ok=True)
    (CHECKS / "r6_grouped_heldout_contract_dryrun_v1_assertions.out").write_text(
        "".join(f"{name}={'PASS' if passed else 'FAIL'}\n" for name, passed in checks),
        encoding="utf-8",
    )
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
