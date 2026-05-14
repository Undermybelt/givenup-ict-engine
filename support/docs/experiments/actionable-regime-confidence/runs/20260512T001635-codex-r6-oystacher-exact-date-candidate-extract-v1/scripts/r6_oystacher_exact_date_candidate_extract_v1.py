#!/usr/bin/env python3
"""Extract exact-date Oystacher candidate positives from the public CFTC complaint.

The public complaint body lists 51 exact trading dates and aggregate counts for
Oystacher/3 Red flip sequences and spoof orders. This script records those
date-level candidates without promoting them into the live R6 intake, because
matched normal controls and order-time/order-id appendix rows are still absent.
"""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001635-codex-r6-oystacher-exact-date-candidate-extract-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-exact-date-candidate-extract"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

COMPLAINT_URL = (
    "https://www.cftc.gov/sites/default/files/idc/groups/public/"
    "%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf"
)
PRESS_URL = "https://www.cftc.gov/PressRoom/PressReleases/7253-15"
TMP_SOURCE = Path("/tmp/ict-engine-r6-oystacher-exact-date-candidate-extract-v1")


SOURCE_GROUPS = [
    {
        "group_id": "oystacher_copper_2011",
        "source_section": "CFTC complaint paragraph 94, Copper Futures Contracts",
        "symbol": "Copper Futures Contracts",
        "venue_or_market_center": "COMEX/CME Globex",
        "dates": [
            "2011-12-01",
            "2011-12-02",
            "2011-12-05",
            "2011-12-06",
            "2011-12-07",
            "2011-12-08",
            "2011-12-09",
            "2011-12-12",
            "2011-12-13",
            "2011-12-14",
            "2011-12-15",
            "2011-12-16",
            "2011-12-19",
            "2011-12-20",
        ],
        "flip_sequences": 156,
        "spoof_orders": 896,
        "spoof_contracts": 35235,
    },
    {
        "group_id": "oystacher_crude_2012",
        "source_section": "CFTC complaint paragraph 94, Crude Oil Futures Contracts",
        "symbol": "Crude Oil Futures Contracts",
        "venue_or_market_center": "NYMEX/CME Globex",
        "dates": ["2012-05-07", "2012-05-09", "2012-05-10", "2012-05-11"],
        "flip_sequences": 120,
        "spoof_orders": 286,
        "spoof_contracts": 15210,
    },
    {
        "group_id": "oystacher_natural_gas_2012",
        "source_section": "CFTC complaint paragraph 94, Natural Gas Futures Contracts",
        "symbol": "Natural Gas Futures Contracts",
        "venue_or_market_center": "NYMEX/CME Globex",
        "dates": ["2012-11-30", "2012-12-03", "2012-12-04"],
        "flip_sequences": 124,
        "spoof_orders": 369,
        "spoof_contracts": 1630,
    },
    {
        "group_id": "oystacher_vix_2013",
        "source_section": "CFTC complaint paragraph 94, VIX Futures Contracts",
        "symbol": "VIX Futures Contracts",
        "venue_or_market_center": "CFE electronic market",
        "dates": [
            "2013-02-19",
            "2013-02-20",
            "2013-02-21",
            "2013-02-22",
            "2013-02-25",
            "2013-02-26",
            "2013-02-27",
            "2013-02-28",
            "2013-03-01",
            "2013-03-04",
            "2013-03-05",
            "2013-03-06",
            "2013-03-07",
            "2013-03-11",
            "2013-03-12",
            "2013-03-18",
            "2013-03-19",
            "2013-03-20",
            "2013-03-21",
        ],
        "flip_sequences": 692,
        "spoof_orders": 2705,
        "spoof_contracts": 283621,
    },
    {
        "group_id": "oystacher_es_june_2013",
        "source_section": "CFTC complaint paragraph 94, June 2013 E-Mini S&P 500 Futures Contract",
        "symbol": "June 2013 E-Mini S&P 500 Futures Contract",
        "venue_or_market_center": "CME Globex",
        "dates": ["2013-06-11", "2013-06-12"],
        "flip_sequences": 12,
        "spoof_orders": 129,
        "spoof_contracts": 3633,
    },
    {
        "group_id": "oystacher_es_dec_2013_jan_2014",
        "source_section": "CFTC complaint paragraph 94, Dec 2013 and Jan 2014 E-Mini S&P 500 Futures Contracts",
        "symbol": "E-Mini S&P 500 Futures Contracts",
        "venue_or_market_center": "CME Globex",
        "dates": [
            "2013-12-16",
            "2013-12-17",
            "2013-12-18",
            "2013-12-19",
            "2014-01-06",
            "2014-01-07",
            "2014-01-08",
            "2014-01-09",
            "2014-01-10",
        ],
        "flip_sequences": 212,
        "spoof_orders": 822,
        "spoof_contracts": 20461,
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, name: str) -> dict[str, Any]:
    TMP_SOURCE.mkdir(parents=True, exist_ok=True)
    target = TMP_SOURCE / name
    result = {"url": url, "tmp_path": str(target)}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ict-engine-oystacher-source-screen/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read()
            target.write_bytes(payload)
            result.update(
                {
                    "fetch_status": "ok",
                    "http_status": getattr(response, "status", ""),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "content_type": response.headers.get("content-type", ""),
                }
            )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update({"fetch_status": "failed", "error": str(exc)})
    return result


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


def build_candidate_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_rows: list[dict[str, Any]] = []
    source_ranges: list[dict[str, Any]] = []
    for group in SOURCE_GROUPS:
        source_ranges.append(
            {
                "group_id": group["group_id"],
                "source_section": group["source_section"],
                "symbol": group["symbol"],
                "venue_or_market_center": group["venue_or_market_center"],
                "date_count": len(group["dates"]),
                "first_date": group["dates"][0],
                "last_date": group["dates"][-1],
                "flip_sequences": group["flip_sequences"],
                "spoof_orders": group["spoof_orders"],
                "spoof_contracts": group["spoof_contracts"],
                "row_materialization_status": "date_level_positive_only_controls_and_order_times_missing",
            }
        )
        for trade_date in group["dates"]:
            candidate_rows.append(
                {
                    "label": "positive_spoofing_layering",
                    "source_report": "CFTC Complaint: CFTC v. Igor B. Oystacher and 3 Red Trading LLC, filed Oct. 19 2015",
                    "source_section": group["source_section"],
                    "trade_date": trade_date,
                    "symbol": group["symbol"],
                    "venue_or_market_center": group["venue_or_market_center"],
                    "participant_type_code": "CFTC respondent trader",
                    "participant_identifier": "Igor B. Oystacher / 3 Red Trading LLC",
                    "side": "spoof orders opposite aggressive flip sequence; aggregate side varies by date",
                    "earliest_order_received_time": "missing_public_appendix",
                    "latest_order_received_time": "missing_public_appendix",
                    "order_count": "group aggregate only: %s spoof orders / %s flip sequences"
                    % (group["spoof_orders"], group["flip_sequences"]),
                    "total_order_quantity": "group aggregate only: %s spoof contracts" % group["spoof_contracts"],
                    "activity_description": "Public CFTC complaint paragraph 94 gives exact trading date and aggregate spoof/flip counts; Exhibit A/order-time rows are not present in the public complaint body.",
                    "matched_negative_group_id": f"{group['group_id']}_{trade_date}",
                    "session_bucket": "source_time_not_in_public_body",
                    "source_row_id": f"{group['group_id']}_{trade_date}",
                    "candidate_status": "positive_date_candidate_only_controls_missing",
                }
            )
    return candidate_rows, source_ranges


def write_report(payload: dict[str, Any]) -> None:
    report = OUT / "r6_oystacher_exact_date_candidate_extract_v1.md"
    lines = [
        "# R6 Oystacher Exact-Date Candidate Extract v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Official CFTC complaint URL: `{COMPLAINT_URL}`.",
        f"- Exact source dates extracted: `{payload['candidate_positive_dates']}`.",
        f"- Source groups: `{payload['source_group_count']}`.",
        f"- Aggregate source totals: flip sequences `{payload['aggregate_source_totals']['flip_sequences']}`, spoof orders `{payload['aggregate_source_totals']['spoof_orders']}`, spoof contracts `{payload['aggregate_source_totals']['spoof_contracts']}`.",
        "- Candidate status: `positive_date_candidate_only_controls_missing`.",
        "- This does not solve the current R6 gate: the dates are pre-2020, order-time/order-id rows are absent, and matched normal controls are absent.",
        f"- Gate result: `{payload['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: false. `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- Candidate rows: `{rel(OUT / 'r6_oystacher_exact_date_positive_candidates_v1.csv')}`",
        f"- Source date ranges: `{rel(OUT / 'r6_oystacher_exact_date_source_groups_v1.csv')}`",
        f"- JSON: `{rel(OUT / 'r6_oystacher_exact_date_candidate_extract_v1.json')}`",
        f"- Assertions: `{rel(CHECKS / 'r6_oystacher_exact_date_candidate_extract_v1_assertions.out')}`",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    source_fetches = [
        fetch(COMPLAINT_URL, "enfigorcomplnt101915.pdf"),
        fetch(PRESS_URL, "press_7253_15.html"),
    ]
    candidate_rows, source_ranges = build_candidate_rows()

    fields = [
        "label",
        "source_report",
        "source_section",
        "trade_date",
        "symbol",
        "venue_or_market_center",
        "participant_type_code",
        "participant_identifier",
        "side",
        "earliest_order_received_time",
        "latest_order_received_time",
        "order_count",
        "total_order_quantity",
        "activity_description",
        "matched_negative_group_id",
        "session_bucket",
        "source_row_id",
        "candidate_status",
    ]
    write_csv(OUT / "r6_oystacher_exact_date_positive_candidates_v1.csv", candidate_rows, fields)
    write_csv(
        OUT / "r6_oystacher_exact_date_source_groups_v1.csv",
        source_ranges,
        [
            "group_id",
            "source_section",
            "symbol",
            "venue_or_market_center",
            "date_count",
            "first_date",
            "last_date",
            "flip_sequences",
            "spoof_orders",
            "spoof_contracts",
            "row_materialization_status",
        ],
    )

    totals = {
        "flip_sequences": sum(int(row["flip_sequences"]) for row in source_ranges),
        "spoof_orders": sum(int(row["spoof_orders"]) for row in source_ranges),
        "spoof_contracts": sum(int(row["spoof_contracts"]) for row in source_ranges),
    }
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256_path(BOARD),
        "source_fetches": source_fetches,
        "source_group_count": len(source_ranges),
        "candidate_positive_dates": len(candidate_rows),
        "aggregate_source_totals": totals,
        "candidate_rows_path": rel(OUT / "r6_oystacher_exact_date_positive_candidates_v1.csv"),
        "source_groups_path": rel(OUT / "r6_oystacher_exact_date_source_groups_v1.csv"),
        "row_materialization_status": "date_level_positive_only_controls_and_order_times_missing",
        "post_2020_chronology_help": False,
        "matched_controls_present": False,
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "r6_oystacher_exact_date_candidate_extract_v1=exact_dates_extracted_controls_and_order_times_missing_no_acceptance",
    }
    write_json(OUT / "r6_oystacher_exact_date_candidate_extract_v1.json", payload)
    write_report(payload)

    CHECKS.mkdir(parents=True, exist_ok=True)
    (CHECKS / "r6_oystacher_exact_date_candidate_extract_v1_assertions.out").write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"source_fetch_ok_count={sum(1 for row in source_fetches if row.get('fetch_status') == 'ok')}",
                f"candidate_positive_dates={len(candidate_rows)}",
                f"source_group_count={len(source_ranges)}",
                f"aggregate_flip_sequences={totals['flip_sequences']}",
                f"aggregate_spoof_orders={totals['spoof_orders']}",
                f"aggregate_spoof_contracts={totals['spoof_contracts']}",
                "matched_controls_present=false",
                f"gate_result={payload['gate_result']}",
                "accepted_rows_added=0",
                "strict_full_objective_achieved=false",
                "update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
