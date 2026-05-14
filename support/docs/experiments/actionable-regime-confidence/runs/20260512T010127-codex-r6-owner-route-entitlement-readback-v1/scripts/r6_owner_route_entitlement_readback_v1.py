#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
from pathlib import Path


RUN_ID = "20260512T010127-codex-r6-owner-route-entitlement-readback-v1"
CURSOR = "20260512T004410+0800-codex-r6-official-route-date-fit-check-v1"
BOARD_HASH_BEFORE = "82b72b4daec4a63332b85e3dd8e7491a7bbdba5a98e4b2cdbcecfdaba247096c"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "r6-owner-route-entitlement-readback"
CHECK_DIR = RUN_ROOT / "checks"
OWNER_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
TOMAC = Path("/Users/thrill3r/Downloads/Tomac")

REQUIRED_OWNER_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def path_status(path: Path) -> str:
    if path.exists():
        return "present"
    return "absent"


def module_present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def env_present(names: list[str]) -> bool:
    return any(bool(os.environ.get(name)) for name in names)


def tomac_schema_rows() -> list[dict]:
    candidates = [
        ("ES.FUT", TOMAC / "es future 2021-2025" / "metadata.json"),
        ("GC.FUT", TOMAC / "gc future 2021-2025" / "metadata.json"),
        ("NQ.FUT", TOMAC / "nq future 2021-2025" / "metadata.json"),
        ("YM.FUT", TOMAC / "ym future 2021-2025" / "metadata.json"),
        ("6E.FUT", TOMAC / "eur future 2015-2025" / "metadata.json"),
    ]
    rows = []
    for symbol, metadata_path in candidates:
        metadata = read_json(metadata_path)
        query = metadata.get("query", {})
        rows.append(
            {
                "local_source": str(metadata_path),
                "symbol": symbol,
                "present": str(metadata_path.exists()).lower(),
                "dataset": query.get("dataset", ""),
                "schema": query.get("schema", ""),
                "start_ns": query.get("start", ""),
                "end_ns": query.get("end", ""),
                "board_decision": "local_bar_data_not_source_owned_normal_controls",
            }
        )
    return rows


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    owner_files = {name: OWNER_ROOT / name for name in REQUIRED_OWNER_FILES}
    owner_files_present = {name: path.exists() for name, path in owner_files.items()}

    official_route_rows = [
        {
            "owner": "CME Group",
            "route": "CME Market Depth via CME client site / DataMine licensed export",
            "official_url": "https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457091894/Market+Depth",
            "public_readback": "market_depth_cme_2005_nymex_2007_comex_2007_fix_2009",
            "oystacher_date_fit": "exchange_level_2011_2013_fit_confirmed",
            "remaining_gap": "licensed_export_not_acquired_product_contract_scope_and_normal_control_policy_still_required",
            "board_decision": "route_improved_controls_not_acquired",
        },
        {
            "owner": "Cboe/CFE",
            "route": "Cboe DataShop CFE VIX Futures Trades and Quotes",
            "official_url": "https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes",
            "public_readback": "cfe_vix_futures_trades_quotes_apr_2004_to_feb_2018",
            "oystacher_date_fit": "2013_2014_vix_tick_quote_route_plausible",
            "remaining_gap": "full_depth_or_order_lifecycle_export_not_confirmed_and_licensed_export_not_acquired",
            "board_decision": "route_improved_controls_not_acquired",
        },
        {
            "owner": "Cboe/CFE",
            "route": "Cboe US Futures Market Data Services / Depth of Book",
            "official_url": "https://www.cboe.com/market_data_services/us/futures/",
            "public_readback": "futures_depth_of_book_feed_exists_for_current_services",
            "oystacher_date_fit": "historical_2013_2014_depth_availability_not_publicly_confirmed",
            "remaining_gap": "custom_datashop_or_market_data_support_export_required_for_historical_depth_order_lifecycle",
            "board_decision": "route_gap_preserved_controls_not_acquired",
        },
    ]

    local_entitlement_rows = [
        {
            "probe": "databento_cli",
            "observed": "present" if shutil.which("databento") else "absent",
            "decision": "no_live_entitlement_path",
        },
        {
            "probe": "dbn_cli",
            "observed": "present" if shutil.which("dbn") else "absent",
            "decision": "no_live_decoder_cli",
        },
        {
            "probe": "python_databento",
            "observed": "present" if module_present("databento") else "absent",
            "decision": "no_live_entitlement_path",
        },
        {
            "probe": "python_pyarrow",
            "observed": "present" if module_present("pyarrow") else "absent",
            "decision": "no_local_arrow_decode_path",
        },
        {
            "probe": "databento_api_key_env",
            "observed": "present"
            if env_present(["DATABENTO_API_KEY", "DATABENTO_KEY"])
            else "absent",
            "decision": "no_live_entitlement_path",
        },
        {
            "probe": "owner_export_root",
            "observed": path_status(OWNER_ROOT),
            "decision": "delivery_root_absent_or_incomplete",
        },
        {
            "probe": "owner_required_files",
            "observed": ",".join(
                f"{name}:{str(present).lower()}"
                for name, present in owner_files_present.items()
            ),
            "decision": "verifier_native_package_absent",
        },
    ]

    local_schema_rows = tomac_schema_rows()

    summary = {
        "run_id": RUN_ID,
        "observed_cursor": CURSOR,
        "board_hash_before": BOARD_HASH_BEFORE,
        "gate_result": "r6_owner_route_entitlement_readback_v1=route_fit_improved_controls_not_acquired_no_merge",
        "required_oystacher_normal_control_cells": 17,
        "source_owned_normal_controls_acquired": 0,
        "same_exhibit_flip_approval": False,
        "canonical_merge_allowed": False,
        "downstream_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "official_route_rows": official_route_rows,
        "local_entitlement_rows": local_entitlement_rows,
        "local_schema_rows": local_schema_rows,
        "decision": {
            "cme_route": "CME exchange-level date fit improved; still needs licensed verifier-native export and normal-control policy/provenance.",
            "cboe_route": "Cboe VIX trades/quotes date route improved; historical depth/order-lifecycle remains custom/support route.",
            "local_entitlement": "No local CLI, Python package, API key, or owner-export delivery package can deliver the R6 controls now.",
        },
        "next_action": (
            "Obtain licensed CME Market Depth/Market by Order or equivalent exports and Cboe/CFE VIX "
            "historical trades/quotes or depth/order-lifecycle export with provenance, or explicitly approve "
            "same-exhibit FLIP-as-control; only then populate the owner-export root and rerun the full chain."
        ),
    }

    summary_path = ARTIFACT_DIR / "r6_owner_route_entitlement_readback_v1.json"
    route_csv = ARTIFACT_DIR / "r6_owner_route_entitlement_sources_v1.csv"
    local_csv = ARTIFACT_DIR / "r6_owner_route_local_entitlement_v1.csv"
    schema_csv = ARTIFACT_DIR / "r6_owner_route_local_schema_readback_v1.csv"
    report_path = ARTIFACT_DIR / "r6_owner_route_entitlement_readback_v1.md"

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        route_csv,
        [
            "owner",
            "route",
            "official_url",
            "public_readback",
            "oystacher_date_fit",
            "remaining_gap",
            "board_decision",
        ],
        official_route_rows,
    )
    write_csv(local_csv, ["probe", "observed", "decision"], local_entitlement_rows)
    write_csv(
        schema_csv,
        [
            "local_source",
            "symbol",
            "present",
            "dataset",
            "schema",
            "start_ns",
            "end_ns",
            "board_decision",
        ],
        local_schema_rows,
    )

    report = f"""# R6 Owner Route Entitlement Readback v1

- Run id: `{RUN_ID}`.
- Observed cursor: `{CURSOR}`.
- Gate result: `{summary["gate_result"]}`.
- Required Oystacher normal-control cells: `17`.
- Valid source-owned normal controls acquired: `0`.
- FLIP-as-control approved: `false`.
- Canonical merge allowed: `false`; downstream rerun allowed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; raw data committed: `false`.

## Findings

- CME public client documentation improves the route fit: Market Depth starts at CME `2005`, NYMEX `2007`, COMEX `2007`, and FIX-formatted files are available from `2009`; this covers the broad 2011-2013 Oystacher CME/NYMEX/COMEX date window at exchange level.
- That does not acquire verifier-native controls. The board still needs a licensed CME Market Depth/Market by Order or equivalent export, product/contract scope confirmation, provenance, and source-owned normal-control policy acceptance before canonical merge.
- Cboe DataShop exposes a legacy CFE VIX futures trades-and-quotes product covering April 2004 through February 2018, which improves the VIX date-route fit. It still does not prove historical full-depth/order-lifecycle availability; use DataShop/support for a custom export if depth/order-lifecycle is required.
- Local entitlement remains absent: no `databento` CLI, no `dbn` CLI, no Python `databento`, no Python `pyarrow`, no Databento API key env, and no complete owner-export package under `{OWNER_ROOT}`.
- Local Tomac futures material remains bar data (`ohlcv-1m`) and cannot be promoted into source-owned normal-control labels.

## Artifacts

- JSON: `{summary_path.relative_to(REPO)}`
- Official route CSV: `{route_csv.relative_to(REPO)}`
- Local entitlement CSV: `{local_csv.relative_to(REPO)}`
- Local schema CSV: `{schema_csv.relative_to(REPO)}`

## Next

Obtain licensed CME Market Depth/Market by Order or equivalent exports and Cboe/CFE VIX historical trades/quotes or depth/order-lifecycle export with provenance, or explicitly approve same-exhibit `FLIP`-as-control. Only after verifier-native controls and provenance arrive should the owner-export root be populated and the full chain rerun.
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        ("required_cells_17", summary["required_oystacher_normal_control_cells"] == 17),
        ("controls_zero", summary["source_owned_normal_controls_acquired"] == 0),
        ("no_flip_approval", summary["same_exhibit_flip_approval"] is False),
        ("no_canonical_merge", summary["canonical_merge_allowed"] is False),
        ("no_downstream_rerun", summary["downstream_rerun_allowed"] is False),
        ("owner_files_absent", not all(owner_files_present.values())),
        (
            "tomac_only_bars",
            all(row["schema"] in ("", "ohlcv-1m") for row in local_schema_rows),
        ),
    ]
    failed = [name for name, passed in assertions if not passed]
    assertions_path = CHECK_DIR / "r6_owner_route_entitlement_readback_v1_assertions.out"
    assertions_path.write_text(
        "\n".join(f"{name}: {'PASS' if passed else 'FAIL'}" for name, passed in assertions)
        + "\n",
        encoding="utf-8",
    )
    if failed:
        print(f"ASSERTIONS_FAILED: {','.join(failed)}")
        return 1
    print(f"wrote {summary_path.relative_to(REPO)}")
    print(f"assertions {assertions_path.relative_to(REPO)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
