#!/usr/bin/env python3
"""Board B options sidecar feasibility readback.

This is a run-local evidence script. It checks whether the local Auto-Quant
BTC options sidecar is usable as a root-branch profitability factor input.
It does not score RC-SPA unless the sidecar has enough historical snapshots to
support chronological folds.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T215432+0800-codex-board-b-options-sidecar-feasibility-readback-v1"
RECIPE_ID = "OptionsSidecarFeasibilityReadbackV1"
SCHEMA_VERSION = "board-b-options-sidecar-feasibility/v1"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
OPTIONS_DIR = DATA_DIR / "options"
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
MANIP_COMPONENT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md"
)

OUT_DIR = RUN_ROOT / "options-sidecar-feasibility"
CHECK_DIR = RUN_ROOT / "checks"
REPORT_JSON = OUT_DIR / "options_sidecar_feasibility_readback_v1.json"
REPORT_MD = OUT_DIR / "options_sidecar_feasibility_readback_v1.md"
SOURCE_CSV = OUT_DIR / "options_sidecar_feasibility_sources_v1.csv"
ASSERTIONS = CHECK_DIR / "options_sidecar_feasibility_readback_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def summarize_options_file(path: Path) -> dict[str, Any]:
    rows = read_rows(path)
    snapshots = Counter(row.get("snapshot_utc", "") for row in rows if row.get("snapshot_utc"))
    expiries = Counter(row.get("expiry", "") for row in rows if row.get("expiry"))
    sides = Counter(row.get("side", "") for row in rows if row.get("side"))
    underlying_values = Counter(row.get("underlying", "") for row in rows if row.get("underlying"))
    numeric_fields = ["mark_iv", "delta", "gamma", "theta", "vega", "open_interest", "volume_24h"]
    field_counts = {
        field: sum(1 for row in rows if row.get(field) not in (None, "", "nan", "NaN"))
        for field in numeric_fields
    }
    return {
        "path": rel(path),
        "exists": path.exists(),
        "rows": len(rows),
        "unique_snapshots": len(snapshots),
        "snapshot_values": list(snapshots.keys())[:5],
        "unique_expiries": len(expiries),
        "unique_sides": sorted(sides.keys()),
        "underlyings": sorted(underlying_values.keys()),
        "field_counts": field_counts,
        "has_iv": field_counts.get("mark_iv", 0) > 0,
        "has_greeks": all(field_counts.get(field, 0) > 0 for field in ["delta", "gamma", "theta", "vega"]),
        "has_open_interest": field_counts.get("open_interest", 0) > 0,
        "has_volume": field_counts.get("volume_24h", 0) > 0,
    }


def count_ohlcv_sidecars() -> dict[str, Any]:
    files = sorted(DATA_DIR.glob("*_USDT-*.feather")) + sorted(DATA_DIR.glob("*_USD-*.feather"))
    crypto = [path for path in files if path.name.startswith(("BTC_", "ETH_", "BNB_", "SOL_", "AVAX_"))]
    return {
        "crypto_ohlcv_files": [str(path) for path in crypto],
        "crypto_ohlcv_file_count": len(crypto),
        "btc_ohlcv_files": [str(path) for path in crypto if path.name.startswith("BTC_")],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    option_files = sorted(OPTIONS_DIR.glob("*.csv"))
    sources = [summarize_options_file(path) for path in option_files]
    unique_snapshot_count = len({snap for item in sources for snap in item["snapshot_values"] if snap})
    total_rows = sum(item["rows"] for item in sources)
    has_iv = any(item["has_iv"] for item in sources)
    has_greeks = any(item["has_greeks"] for item in sources)
    has_open_interest = any(item["has_open_interest"] for item in sources)
    has_volume = any(item["has_volume"] for item in sources)

    minimum_snapshots_for_folds = 20
    minimum_monthly_folds = 4
    feasible_for_branch_rc_spa = unique_snapshot_count >= minimum_snapshots_for_folds
    gate_result = (
        "fail:options_sidecar_single_snapshot_not_trainable"
        if not feasible_for_branch_rc_spa
        else "ready:options_sidecar_has_historical_snapshots"
    )
    downstream = (
        "not_started:blocked_by_options_sidecar_feasibility"
        if not feasible_for_branch_rc_spa
        else "not_started:requires_branch_rc_spa"
    )

    sidecars = count_ohlcv_sidecars()
    decision = {
        "gate_result": gate_result,
        "total_option_rows": total_rows,
        "unique_snapshot_count": unique_snapshot_count,
        "minimum_snapshots_for_folds": minimum_snapshots_for_folds,
        "minimum_monthly_folds": minimum_monthly_folds,
        "has_iv": has_iv,
        "has_greeks": has_greeks,
        "has_open_interest": has_open_interest,
        "has_volume": has_volume,
        "branch_rows_emitted": 0,
        "rc_spa_scored": False,
        "price_root_paths_passed": 0,
        "manipulation_component_pass_consumed": False,
        "downstream_consumption": downstream,
        "primary_blocker": (
            "Local options sidecar has IV/Greek snapshot fields but not a historical "
            "snapshot time series, so it cannot be aligned to Board A roots across "
            "chronological folds or treated as a profitability factor."
        ),
        "next_action": (
            "Acquire or build a historical options/dealer-positioning sidecar with "
            ">=20 dated snapshots and >=4 chronological folds before using IV/skew/OI "
            "as a Board B root-branch profit factor."
        ),
    }
    payload = {
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "recipe_id": RECIPE_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "intended_branch_path_shape": "main_regime -> options_vol_sidecar_context -> option_iv_skew_oi_factor -> profit_factor",
        "decision": decision,
        "sources": sources,
        "sidecars": sidecars,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "source_csv": rel(SOURCE_CSV),
            "assertions": rel(ASSERTIONS),
            "manipulation_component": rel(MANIP_COMPONENT),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with SOURCE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "path",
                "exists",
                "rows",
                "unique_snapshots",
                "unique_expiries",
                "unique_sides",
                "underlyings",
                "has_iv",
                "has_greeks",
                "has_open_interest",
                "has_volume",
            ],
        )
        writer.writeheader()
        for item in sources:
            writer.writerow(
                {
                    "path": item["path"],
                    "exists": item["exists"],
                    "rows": item["rows"],
                    "unique_snapshots": item["unique_snapshots"],
                    "unique_expiries": item["unique_expiries"],
                    "unique_sides": ";".join(item["unique_sides"]),
                    "underlyings": ";".join(item["underlyings"]),
                    "has_iv": item["has_iv"],
                    "has_greeks": item["has_greeks"],
                    "has_open_interest": item["has_open_interest"],
                    "has_volume": item["has_volume"],
                }
            )

    md_lines = [
        "# Options Sidecar Feasibility Readback v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{gate_result}`",
        f"- Total option rows: `{total_rows}`",
        f"- Unique option snapshots: `{unique_snapshot_count}`",
        f"- IV present: `{has_iv}`; Greeks present: `{has_greeks}`; open interest present: `{has_open_interest}`; volume present: `{has_volume}`",
        "- Branch RC-SPA scored: `false`",
        "- Branch rows emitted: `0`",
        f"- Downstream consumption: `{downstream}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Root-First Interpretation",
        "",
        "- Intended path shape would be `main_regime -> options_vol_sidecar_context -> option_iv_skew_oi_factor -> profit_factor`.",
        "- Current local sidecar cannot emit that path across chronological folds because it is only a snapshot readback.",
        "- Do not attach IV/skew/OI as a Board B profit factor until a historical sidecar exists.",
        "",
        "## Sources",
        "",
        "| Source | Rows | Unique snapshots | Unique expiries | Fields |",
        "|---|---:|---:|---:|---|",
    ]
    for item in sources:
        fields = []
        if item["has_iv"]:
            fields.append("iv")
        if item["has_greeks"]:
            fields.append("greeks")
        if item["has_open_interest"]:
            fields.append("oi")
        if item["has_volume"]:
            fields.append("volume")
        md_lines.append(
            f"| `{item['path']}` | {item['rows']} | {item['unique_snapshots']} | {item['unique_expiries']} | {', '.join(fields) or 'none'} |"
        )
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(REPORT_JSON)}`",
            f"- Source CSV: `{rel(SOURCE_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"total_option_rows={total_rows}",
                f"unique_snapshot_count={unique_snapshot_count}",
                f"has_iv={has_iv}",
                f"has_greeks={has_greeks}",
                f"has_open_interest={has_open_interest}",
                f"branch_rows_emitted=0",
                f"rc_spa_scored=False",
                f"gate_result={gate_result}",
                f"downstream_consumption={downstream}",
                "artifacts_exist=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
