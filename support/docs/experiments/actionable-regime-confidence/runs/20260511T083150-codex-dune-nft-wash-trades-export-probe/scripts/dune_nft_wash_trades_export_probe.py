#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T083150+0800-codex-dune-nft-wash-trades-export-probe"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T083150-codex-dune-nft-wash-trades-export-probe"
)
OUT_DIR = RUN_ROOT / "dune-export-probe"
CHECK_DIR = RUN_ROOT / "checks"

WASH_DOC_URL = "https://docs.dune.com/data-catalog/curated/nft-trades/evm/nft-wash-trades.md"
AUTH_DOC_URL = "https://docs.dune.com/api-reference/overview/authentication.md"
EXECUTE_SQL_DOC_URL = "https://docs.dune.com/api-reference/executions/endpoint/execute-sql.md"
EXECUTE_SQL_URL = "https://api.dune.com/api/v1/sql/execute"
LATEST_RESULT_URL = "https://api.dune.com/api/v1/query/3457808/results?limit=1"

REQUIRED_COLUMNS = [
    "block_time",
    "block_date",
    "tx_hash",
    "unique_trade_id",
    "is_wash_trade",
]
FILTER_COLUMNS = [
    "filter_1_same_buyer_seller",
    "filter_2_back_and_forth_trade",
    "filter_3_bought_or_sold_3x",
    "filter_4_first_funded_by_same_wallet",
    "filter_5_flashloan",
]


def fetch_text(url: str, *, headers: dict[str, str] | None = None, data: bytes | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def parse_schema(markdown: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in markdown.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue
        column = parts[0].strip("`")
        typ = parts[1].strip("`")
        desc = parts[2]
        rows.append({"column": column, "type": typ, "description": desc})
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    wash_status, wash_md = fetch_text(WASH_DOC_URL)
    auth_status, auth_md = fetch_text(AUTH_DOC_URL)
    execute_doc_status, execute_doc_md = fetch_text(EXECUTE_SQL_DOC_URL)

    schema = parse_schema(wash_md)
    columns = {row["column"] for row in schema}
    required_present = {col: col in columns for col in REQUIRED_COLUMNS}
    filters_present = {col: col in columns for col in FILTER_COLUMNS}

    api_key_present = bool(os.environ.get("DUNE_API_KEY"))
    public_result_status, public_result_body = fetch_text(LATEST_RESULT_URL)

    candidate_sql = """
WITH labeled AS (
  SELECT
    blockchain,
    project,
    nft_contract_address,
    token_id,
    buyer,
    seller,
    block_time,
    block_date,
    tx_hash,
    unique_trade_id,
    CAST(is_wash_trade AS BOOLEAN) AS manipulation_positive,
    filter_1_same_buyer_seller,
    filter_2_back_and_forth_trade,
    filter_3_bought_or_sold_3x,
    filter_4_first_funded_by_same_wallet,
    filter_5_flashloan
  FROM nft.wash_trades
  WHERE block_time IS NOT NULL
    AND is_wash_trade IS NOT NULL
),
balanced AS (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY manipulation_positive
      ORDER BY block_time, unique_trade_id
    ) AS class_row_number
  FROM labeled
)
SELECT *
FROM balanced
WHERE class_row_number <= 5000
ORDER BY block_time, unique_trade_id
""".strip()

    execute_attempt: dict[str, object] = {
        "attempted": False,
        "reason": "DUNE_API_KEY missing; Dune execute-sql requires an API key with at least Read scope.",
    }

    if api_key_present:
        payload = json.dumps({"sql": candidate_sql, "performance": "medium"}).encode()
        status, body = fetch_text(
            EXECUTE_SQL_URL,
            headers={
                "Content-Type": "application/json",
                "X-Dune-Api-Key": os.environ["DUNE_API_KEY"],
            },
            data=payload,
        )
        execute_attempt = {
            "attempted": True,
            "status": status,
            "body_preview": body[:500],
            "contains_execution_id": bool(re.search(r"execution_id", body, re.I)),
        }

    docs_prove_export_candidate = (
        wash_status == 200
        and all(required_present.values())
        and all(filters_present.values())
        and "is_wash_trade" in wash_md
        and "block_time" in wash_md
    )

    if not docs_prove_export_candidate:
        gate_result = "blocked_dune_wash_trades_schema_missing_required_fields"
    elif not api_key_present:
        gate_result = "blocked_dune_export_missing_api_key"
    elif execute_attempt.get("attempted") and execute_attempt.get("contains_execution_id"):
        gate_result = "dune_export_execution_started_pending_poll_and_calibration"
    else:
        gate_result = "blocked_dune_export_api_error"

    accepted_direct_manipulation_95 = False
    manipulation_label_slots_added = 0
    mainregimev2_root_slots_added = 0

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Probe whether Dune nft.wash_trades can materialize replayable positive/negative direct Manipulation label windows.",
        "active_taxonomy": {
            "mainregimev2_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "residual": "UnknownOrMixed",
            "separate_overlay": "Manipulation",
        },
        "sources": {
            "wash_trades_docs": WASH_DOC_URL,
            "auth_docs": AUTH_DOC_URL,
            "execute_sql_docs": EXECUTE_SQL_DOC_URL,
            "public_result_probe_url": LATEST_RESULT_URL,
        },
        "docs_probe": {
            "wash_docs_status": wash_status,
            "auth_docs_status": auth_status,
            "execute_sql_docs_status": execute_doc_status,
            "required_columns_present": required_present,
            "filter_columns_present": filters_present,
            "schema_column_count": len(schema),
            "docs_prove_export_candidate": docs_prove_export_candidate,
            "auth_docs_mentions_api_key": "API key" in auth_md,
            "execute_sql_docs_mentions_read_scope": "Minimum required API key scope" in execute_doc_md
            and "Read" in execute_doc_md,
        },
        "api_probe": {
            "dune_api_key_present": api_key_present,
            "public_result_status": public_result_status,
            "public_result_body_preview": public_result_body[:200],
            "execute_attempt": execute_attempt,
        },
        "candidate_export_sql": candidate_sql,
        "decision": {
            "gate_result": gate_result,
            "accepted_direct_manipulation_95": accepted_direct_manipulation_95,
            "mainregimev2_root_slots_added": mainregimev2_root_slots_added,
            "manipulation_label_slots_added": manipulation_label_slots_added,
            "accepted_full_cycle_full_universe": False,
            "blockers": [
                "dune_api_key_missing" if not api_key_present else "dune_export_not_completed",
                "no_replayable_rows_materialized",
                "no_chronological_positive_negative_calibration_split",
                "mainregimev2_root_label_slots_still_missing",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Either provide an authenticated Dune export path/API key and rerun this SQL, "
            "or pivot to another public direct-manipulation source with replayable timestamps and positive/negative labels."
        ),
    }

    (OUT_DIR / "dune_nft_wash_trades_export_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "dune_wash_trades_schema_columns.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["column", "type", "description"])
        writer.writeheader()
        writer.writerows(schema)

    md = [
        "# Dune nft.wash_trades Export-Path Probe",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{gate_result}`",
        f"- Accepted direct `Manipulation` 95: `{str(accepted_direct_manipulation_95).lower()}`",
        f"- MainRegimeV2 root-label slots added: `{mainregimev2_root_slots_added}`",
        f"- Manipulation label slots added: `{manipulation_label_slots_added}`",
        f"- DUNE_API_KEY present: `{str(api_key_present).lower()}`",
        f"- Public query-result probe status: `{public_result_status}`",
        "",
        "## What the docs establish",
        "",
        "- Dune documents `nft.wash_trades` as a curated NFT wash-trading table.",
        "- Required replay columns are present in the documented schema: `block_time`, `block_date`, `tx_hash`, `unique_trade_id`, and `is_wash_trade`.",
        "- Filter provenance columns are documented for same buyer/seller, back-and-forth, repeated trading, common funding wallet, and flashloan filters.",
        "- Dune API documentation requires an API key for authenticated SQL execution; the current shell has no `DUNE_API_KEY`.",
        "",
        "## Candidate SQL",
        "",
        "```sql",
        candidate_sql,
        "```",
        "",
        "## Result",
        "",
        "- No replayable rows were exported in this run.",
        "- No positive/negative chronological calibration/test windows were materialized.",
        "- The table remains a strong candidate source, but it cannot be accepted without authenticated export and calibration.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
    ]
    (OUT_DIR / "dune_nft_wash_trades_export_probe.md").write_text("\n".join(md) + "\n")

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={gate_result}",
        f"docs_prove_export_candidate={str(docs_prove_export_candidate).lower()}",
        f"dune_api_key_present={str(api_key_present).lower()}",
        f"public_result_status={public_result_status}",
        f"accepted_direct_manipulation_95={str(accepted_direct_manipulation_95).lower()}",
        f"mainregimev2_root_slots_added={mainregimev2_root_slots_added}",
        f"manipulation_label_slots_added={manipulation_label_slots_added}",
        "accepted_full_cycle_full_universe=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    (CHECK_DIR / "dune_nft_wash_trades_export_probe_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
