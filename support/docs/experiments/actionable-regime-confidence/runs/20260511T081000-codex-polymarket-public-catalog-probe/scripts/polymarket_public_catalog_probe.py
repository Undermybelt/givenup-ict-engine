#!/usr/bin/env python3
"""Summarize the Polymarket public catalog probe for Board A."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T081000+0800-codex-polymarket-public-catalog-probe"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T081000-codex-polymarket-public-catalog-probe"
OUT_DIR = RUN_ROOT / "polymarket-catalog"
CHECK_DIR = RUN_ROOT / "checks"
RAW_JSON = Path("/private/tmp/ict-regime-polymarket-public-catalog-20260511T081000/polymarket_markets.json")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_raw_rows() -> list[dict[str, Any]]:
    if not RAW_JSON.exists():
        return []
    payload = json.loads(RAW_JSON.read_text())
    return payload if isinstance(payload, list) else []


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_raw_rows()
    active_rows = [row for row in rows if row.get("active") is True]
    closed_rows = [row for row in rows if row.get("closed") is True]
    tokenized_rows = [row for row in rows if row.get("clob_token_ids")]
    sample = [
        {
            "id": row.get("id"),
            "slug": row.get("slug"),
            "question": row.get("question"),
            "active": row.get("active"),
            "closed": row.get("closed"),
            "end_date": row.get("end_date"),
            "has_clob_token_ids": bool(row.get("clob_token_ids")),
        }
        for row in rows[:10]
    ]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Probe the Polymarket public catalog cell from the expanded Board A provider universe.",
        "source": {
            "fetch_command": "uv run --with requests --with pandas python scripts/auto_quant_external/fetch_external.py polymarket-markets --limit 20 --active true --closed false --format json --output /private/tmp/ict-regime-polymarket-public-catalog-20260511T081000/polymarket_markets.json",
            "raw_json": str(RAW_JSON),
            "raw_data_committed": False,
        },
        "catalog_rows": len(rows),
        "active_rows": len(active_rows),
        "closed_rows": len(closed_rows),
        "rows_with_clob_token_ids": len(tokenized_rows),
        "sample_rows": sample,
        "completion_accounting": {
            "catalog_materialized": len(rows) > 0,
            "accepted_full_cycle_full_universe": False,
            "accepted_confidence": False,
            "why_not_accepted": [
                "Polymarket catalog rows are alternative-data market discovery, not MainRegimeV2 price-root labels.",
                "No provider/instrument/timeframe Bull/Bear/Sideways/Crisis source-label panel is attached.",
                "No Polymarket CLOB price-history token was promoted to root confidence in this slice.",
            ],
        },
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "polymarket_catalog_materialized_root_confidence_pending",
        "next_action": "Keep Polymarket as alternative-data sidecar unless a concrete CLOB token history can be mapped to an independent MainRegimeV2 source-label panel.",
        "artifacts": {
            "summary_json": rel(OUT_DIR / "polymarket_public_catalog_probe.json"),
            "summary_md": rel(OUT_DIR / "polymarket_public_catalog_probe.md"),
            "assertions": rel(CHECK_DIR / "polymarket_public_catalog_probe_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "polymarket_public_catalog_probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    md_lines = [
        "# Polymarket Public Catalog Probe",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- Catalog rows: `{len(rows)}`",
        f"- Active rows: `{len(active_rows)}`",
        f"- Closed rows: `{len(closed_rows)}`",
        f"- Rows with CLOB token ids: `{len(tokenized_rows)}`",
        "- Raw data committed: `false`",
        "",
        "Gate result: `polymarket_catalog_materialized_root_confidence_pending`",
        "",
        "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
    ]
    (OUT_DIR / "polymarket_public_catalog_probe.md").write_text("\n".join(md_lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"catalog_rows={len(rows)}",
        f"active_rows={len(active_rows)}",
        f"closed_rows={len(closed_rows)}",
        f"rows_with_clob_token_ids={len(tokenized_rows)}",
        "accepted_full_cycle_full_universe=false",
        "raw_data_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "gate_result=polymarket_catalog_materialized_root_confidence_pending",
    ]
    (CHECK_DIR / "polymarket_public_catalog_probe_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    print(rel(OUT_DIR / "polymarket_public_catalog_probe.json"))


if __name__ == "__main__":
    main()
