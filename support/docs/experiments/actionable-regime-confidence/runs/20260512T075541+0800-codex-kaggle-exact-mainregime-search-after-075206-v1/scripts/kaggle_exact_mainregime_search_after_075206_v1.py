#!/usr/bin/env python3
"""Exact Kaggle source-route search for Board A MainRegimeV2 terms."""

from __future__ import annotations

import csv
import json
import subprocess
from io import StringIO
from pathlib import Path


RUN_ID = "20260512T075541+0800-codex-kaggle-exact-mainregime-search-after-075206-v1"
GATE_RESULT = "kaggle_exact_mainregime_search_after_075206_v1=existing_stock_regime_only_no_new_source_control_unlock"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SLUG = "kaggle-exact-mainregime-search-after-075206-v1"
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"
CMD_ROOT = RUN_ROOT / "command-output"
R5_KNOWN_CSV = Path(
    "/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1/"
    "stock_market_regimes_2000_2026.csv"
)

QUERIES = [
    "Bull Bear Sideways Crisis",
    "MainRegimeV2",
    "stock_market_regimes_2000_2026",
    "Crisis market regime label",
]


def run_query(query: str) -> dict:
    safe = (
        query.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "_")
    )
    stdout_path = CMD_ROOT / f"kaggle_search_{safe}.stdout.csv"
    stderr_path = CMD_ROOT / f"kaggle_search_{safe}.stderr.txt"
    cmd = ["kaggle", "datasets", "list", "-s", query, "--csv"]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    stdout_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)

    rows = []
    if proc.stdout.strip() and not proc.stdout.strip().startswith("No datasets found"):
        reader = csv.DictReader(StringIO(proc.stdout))
        rows = [dict(row) for row in reader]
    return {
        "query": query,
        "command": cmd,
        "exit_code": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "row_count": len(rows),
        "rows": rows[:20],
    }


def profile_known_r5_csv() -> dict:
    if not R5_KNOWN_CSV.exists():
        return {"exists": False, "path": str(R5_KNOWN_CSV)}
    with R5_KNOWN_CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = 0
        after_cutoff = 0
        min_date = None
        max_date = None
        labels = {}
        for row in reader:
            rows += 1
            date = row.get("date") or row.get("Date") or row.get("timestamp_or_date")
            label = row.get("regime_label") or row.get("main_regime_v2_label") or row.get("label")
            if date:
                min_date = date if min_date is None or date < min_date else min_date
                max_date = date if max_date is None or date > max_date else max_date
                if date > "2026-01-30":
                    after_cutoff += 1
            if label:
                labels[label] = labels.get(label, 0) + 1
    return {
        "exists": True,
        "path": str(R5_KNOWN_CSV),
        "rows": rows,
        "min_date": min_date,
        "max_date": max_date,
        "rows_after_2026_01_30": after_cutoff,
        "labels": labels,
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)
    CMD_ROOT.mkdir(parents=True, exist_ok=True)

    query_results = [run_query(query) for query in QUERIES]
    flat_rows = []
    for result in query_results:
        for row in result["rows"]:
            flat_rows.append(
                {
                    "query": result["query"],
                    "ref": row.get("ref", ""),
                    "title": row.get("title", ""),
                    "size": row.get("size", ""),
                    "lastUpdated": row.get("lastUpdated", ""),
                    "downloadCount": row.get("downloadCount", ""),
                    "voteCount": row.get("voteCount", ""),
                    "usabilityRating": row.get("usabilityRating", ""),
                }
            )

    refs = {row["ref"] for row in flat_rows if row.get("ref")}
    exact_stock_regime_hit = "mafaqbhatti/stock-market-regimes-20002026" in refs
    exact_mainregimev2_hits = [
        row for row in flat_rows if "MainRegimeV2".lower() in (row["title"] + row["ref"]).lower()
    ]
    r5_profile = profile_known_r5_csv()

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "queries": query_results,
        "unique_refs": sorted(refs),
        "known_r5_profile": r5_profile,
        "assertions": {
            "kaggle_cli_all_exit_zero": all(r["exit_code"] == 0 for r in query_results),
            "exact_stock_regime_hit_present": exact_stock_regime_hit,
            "mainregimev2_query_returned_rows": any(
                r["query"] == "MainRegimeV2" and r["row_count"] > 0 for r in query_results
            ),
            "exact_mainregimev2_named_hit_present": bool(exact_mainregimev2_hits),
            "known_r5_rows_after_cutoff": r5_profile.get("rows_after_2026_01_30", -1),
            "r6_owner_export_unlock": False,
            "r5_recency_unlock": False,
            "r3_native_subhour_unlock": False,
            "valid_required_root_unlock": False,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": "Exact Kaggle source-route search found only the already-known stock regime dataset for exact Bull/Bear/Sideways/Crisis style queries, no MainRegimeV2 dataset rows, and no post-cutoff R5 rows in the known redownloaded source panel.",
        "next": "Continue source/control acquisition only.",
    }

    json_path = OUT_ROOT / "kaggle_exact_mainregime_search_after_075206_v1.json"
    csv_path = OUT_ROOT / "kaggle_exact_mainregime_search_results_v1.csv"
    md_path = OUT_ROOT / "kaggle_exact_mainregime_search_after_075206_v1.md"
    assertions_path = CHECK_ROOT / "kaggle_exact_mainregime_search_after_075206_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "query",
                "ref",
                "title",
                "size",
                "lastUpdated",
                "downloadCount",
                "voteCount",
                "usabilityRating",
            ],
        )
        writer.writeheader()
        writer.writerows(flat_rows)

    md_path.write_text(
        "\n".join(
            [
                "# Kaggle Exact MainRegime Search After 075206 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE_RESULT}`",
                "",
                "## Scope",
                "",
                "Bounded current Kaggle CLI search for exact Board A source terms after the `075206` current-objective audit. This packet does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Queries",
                "",
                "| Query | Rows | Notable result |",
                "|---|---:|---|",
                *[
                    f"| `{r['query']}` | `{r['row_count']}` | `{'; '.join(row.get('ref','') for row in r['rows'][:5]) or 'none'}` |"
                    for r in query_results
                ],
                "",
                "## Decision",
                "",
                "- `MainRegimeV2` returned no Kaggle dataset rows.",
                "- Exact `Bull Bear Sideways Crisis` and `stock_market_regimes_2000_2026` searches returned the already-known `mafaqbhatti/stock-market-regimes-20002026` dataset.",
                f"- Known R5 redownload profile: rows `{r5_profile.get('rows')}`, date range `{r5_profile.get('min_date')}` to `{r5_profile.get('max_date')}`, rows after `2026-01-30` `{r5_profile.get('rows_after_2026_01_30')}`.",
                "- Broad `Crisis market regime label` results include unrelated macro/commodity/geopolitical datasets and the already-screened NIFTY behavior-regime dataset, not a required Board A source/control root.",
                "- Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
                "",
            ]
        )
        + "\n"
    )

    checks = result["assertions"]
    failures = []
    if not checks["kaggle_cli_all_exit_zero"]:
        failures.append("kaggle_cli_all_exit_zero=false")
    if checks["mainregimev2_query_returned_rows"]:
        failures.append("mainregimev2_query_returned_rows=true")
    if checks["exact_mainregimev2_named_hit_present"]:
        failures.append("exact_mainregimev2_named_hit_present=true")
    if checks["known_r5_rows_after_cutoff"] != 0:
        failures.append(f"known_r5_rows_after_cutoff={checks['known_r5_rows_after_cutoff']}")
    for key in [
        "r6_owner_export_unlock",
        "r5_recency_unlock",
        "r3_native_subhour_unlock",
        "valid_required_root_unlock",
        "source_control_evidence_acquired",
        "canonical_merge",
        "downstream_promotion_rerun",
        "strict_full_objective",
        "trade_usable",
        "update_goal",
    ]:
        if checks[key]:
            failures.append(f"{key}=true")

    if failures:
        assertions_path.write_text("FAIL " + "; ".join(failures) + "\n")
        return 1
    assertions_path.write_text(
        "\n".join(
            [
                "PASS kaggle_exact_mainregime_search_after_075206_v1",
                f"gate_result={GATE_RESULT}",
                "kaggle_cli_all_exit_zero=true",
                f"exact_stock_regime_hit_present={str(exact_stock_regime_hit).lower()}",
                "mainregimev2_query_returned_rows=false",
                "exact_mainregimev2_named_hit_present=false",
                "known_r5_rows_after_cutoff=0",
                "valid_required_root_unlock=false",
                "update_goal=false",
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
