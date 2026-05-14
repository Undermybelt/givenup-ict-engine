#!/usr/bin/env python3
"""Materialize current non-R6 Board A source-intake outbound request messages."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T010201-codex-non-r6-source-intake-outbound-request-messages-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "non-r6-source-intake-outbound-request-messages-v1"
CHECKS = RUN_ROOT / "checks"

GATE = (
    "non_r6_source_intake_outbound_request_messages_v1="
    "outbound_messages_ready_not_sent_rows_not_acquired"
)

REQUESTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2/R4 source-label equivalence and strict 1h target support",
        "destination_root": "/tmp/ict-engine-source-label-equivalence-intake",
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
        "message_file": "source_label_equivalence_owner_request_message_v1.md",
        "route": "Kaggle stock-regime owner plus index/exchange/vendor source-label owners",
        "target": (
            "Owner-approved or source-owned cross-market/source-label equivalence rows "
            "for Bull, Bear, Sideways, and Crisis; rows must use accepted MainRegimeV2 "
            "root vocabulary and must not duplicate already-counted panel evidence."
        ),
        "schema": [
            "package_id",
            "source_owner",
            "source_report_or_dataset",
            "source_pull_date",
            "market_family",
            "symbol",
            "source_symbol",
            "equivalence_policy",
            "event_species",
            "timestamp_or_date",
            "timeframe",
            "main_regime_v2_label",
            "direct_label",
            "matched_negative_group_id",
            "split_role",
            "source_row_id",
            "provenance_hash",
        ],
        "verifier": (
            "docs/experiments/actionable-regime-confidence/runs/"
            "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
            "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
        ),
        "blocker": "source-label confidence remains 0/4 without verifier-ready rows.",
    },
    {
        "id": "r3_native_subhour_source_labels",
        "requirements": "R3 native sub-hour cross-timeframe validation",
        "destination_root": "/tmp/ict-engine-native-subhour-source-label-intake",
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "message_file": "r3_native_subhour_source_label_request_message_v1.md",
        "route": "Kaggle stock-regime owner, Yahoo/Nasdaq/CME/Cboe/Polygon source or licensing contacts",
        "target": (
            "Source-native or owner-approved 1m/5m/15m/30m/1h/4h labels, especially "
            "AAPL and ^IXIC 15m/30m focus cells, with per-row source provenance."
        ),
        "schema": [
            "source_row_id",
            "source_name",
            "owner_or_licensor",
            "license_or_permission",
            "instrument",
            "timeframe",
            "timestamp_start_utc",
            "timestamp_end_utc",
            "root_label",
            "source_label",
            "qualifying_condition",
            "confidence_or_quality_flag",
            "validation_instrument_group",
            "validation_period",
            "validation_market_context",
            "provenance_url_or_path",
            "source_version_hash",
            "forbidden_proxy_flag",
        ],
        "verifier": "native-subhour package readback plus unchanged completion audit",
        "blocker": "R3 native-subhour root is absent; daily/monthly projections remain rejected.",
    },
    {
        "id": "r5_source_panel_recency_extension",
        "requirements": "R5 source-panel recency after 2026-01-30",
        "destination_root": "/tmp/ict-engine-source-panel-recency-extension",
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "message_file": "r5_source_panel_recency_extension_request_message_v1.md",
        "route": "Kaggle stock-regime dataset owner/profile/discussion or equivalent source owner",
        "target": (
            "Post-2026-01-30 source-owned extension rows for required cells: "
            "XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear."
        ),
        "schema": [
            "date",
            "ticker",
            "close",
            "returns",
            "volatility",
            "regime_label",
            "regime_confidence",
            "macro_context",
            "unemployment_rate",
            "fed_funds_rate",
            "cpi",
            "10y_treasury",
            "2y_treasury",
            "vix",
        ],
        "verifier": (
            "docs/experiments/actionable-regime-confidence/runs/"
            "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
            "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
        ),
        "blocker": "R5 public Kaggle refresh still stops at 2026-01-30; proxy yfinance labels are rejected.",
    },
]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def message_for(request: dict[str, object]) -> str:
    files = "\n".join(f"- `{name}`" for name in request["required_files"])
    schema = ", ".join(f"`{field}`" for field in request["schema"])
    return f"""# {request['requirements']} Request

Target root: `{request['destination_root']}`

Please provide source-owned or owner-approved rows for:

{request['target']}

Required delivery files:
{files}

Required row schema:
{schema}

Provenance requirements:
- identify the source owner/licensor
- include source dataset, export, ticket, or written approval reference
- include source version/hash or raw export hash
- state license constraints and whether raw rows can be committed
- state why rows are source-native labels rather than generated/HMM/KMeans/future-return/OHLCV proxy labels

Route:
{request['route']}

After delivery:
Place files under `{request['destination_root']}` and rerun `{request['verifier']}`. Schema readiness is not a confidence gate by itself; after verifier readiness, rerun the unchanged chronological/heldout-market/timeframe calibration and completion audit.

Current blocker:
{request['blocker']}
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    index_rows = []
    schema_rows = []
    for request in REQUESTS:
        message_path = OUT / str(request["message_file"])
        message_path.write_text(message_for(request), encoding="utf-8")
        index_rows.append(
            {
                "request_id": request["id"],
                "requirements": request["requirements"],
                "destination_root": request["destination_root"],
                "required_files": ";".join(request["required_files"]),
                "message_file": str(message_path),
                "verifier_or_next_check": request["verifier"],
                "request_sent": False,
                "rows_acquired": False,
                "accepted_rows_added": 0,
            }
        )
        for field in request["schema"]:
            schema_rows.append(
                {
                    "request_id": request["id"],
                    "field": field,
                    "required": True,
                }
            )

    write_csv(
        OUT / "non_r6_source_intake_outbound_request_index_v1.csv",
        index_rows,
        [
            "request_id",
            "requirements",
            "destination_root",
            "required_files",
            "message_file",
            "verifier_or_next_check",
            "request_sent",
            "rows_acquired",
            "accepted_rows_added",
        ],
    )
    write_csv(
        OUT / "non_r6_source_intake_required_schema_v1.csv",
        schema_rows,
        ["request_id", "field", "required"],
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "request_count": len(REQUESTS),
        "roots": [request["destination_root"] for request in REQUESTS],
        "required_files": {
            request["id"]: request["required_files"] for request in REQUESTS
        },
        "external_requests_sent": False,
        "source_rows_acquired": 0,
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT / "non_r6_source_intake_outbound_request_messages_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Non-R6 Source Intake Outbound Request Messages v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{GATE}`.",
        "- Request branches: `3` source-label equivalence, R3 native sub-hour, and R5 recency.",
        "- External requests sent: `false`; source rows acquired: `0`; accepted rows added: `0`.",
        "- Canonical merge allowed: `false`; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.",
        "- Strict full objective achieved: false. `update_goal=false`.",
        "- Runtime code changed: false. Shared intake mutated: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Messages",
    ]
    for request in REQUESTS:
        report.append(f"- `{request['id']}`: `{request['message_file']}`")
    report.extend(
        [
            "",
            "## Required Roots",
        ]
    )
    for request in REQUESTS:
        report.append(
            f"- `{request['destination_root']}` -> `{';'.join(request['required_files'])}`"
        )
    report.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet only materializes outbound-ready messages. It does not send external requests, create `/tmp` intake files, accept rows, rerun promotion gates, or treat provider/OHLCV/generated labels as source-owned evidence.",
            "",
            "## Next",
            "",
            "Send or otherwise satisfy these three non-R6 source-intake requests. After exact files appear under their target roots, rerun the fail-closed verifiers and only then run the unchanged downstream chain in the Board A order.",
        ]
    )
    (OUT / "non_r6_source_intake_outbound_request_messages_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={GATE}",
        "request_count=3",
        "external_requests_sent=false",
        "source_rows_acquired=0",
        "accepted_rows_added=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "shared_intake_mutated=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    (CHECKS / "non_r6_source_intake_outbound_request_messages_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
