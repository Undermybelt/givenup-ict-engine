#!/usr/bin/env python3
"""Probe whether local assets contain Nasdaq-100 source labels for NQ crosswalks."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T140846+0800-codex-ndx-source-label-availability-probe-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140846-codex-ndx-source-label-availability-probe-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
PRIOR_ATTACHABILITY = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081210-codex-underlying-source-label-attachability/"
    "source-label-attachability/underlying_source_label_attachability.csv"
)
PRIOR_ACQUISITION = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)
LOCAL_NDX_PRICE_FILES = [
    Path("/private/tmp/ict-crosswalk-tracking-source-attachment-v1/_NDX_1d.csv"),
    Path("/private/tmp/ict-crosswalk-tracking-probe-20260511T1355/_NDX_1d.csv"),
    Path("/private/tmp/ict-engine-ibkr-probe/ndx.1d.10y.csv"),
]
OUT_JSON = RUN_ROOT / "ndx-source-label-probe/ndx_source_label_availability_probe_v1.json"
OUT_MD = RUN_ROOT / "ndx-source-label-probe/ndx_source_label_availability_probe_v1.md"
OUT_CSV = RUN_ROOT / "ndx-source-label-probe/ndx_source_label_availability_probe_v1_files.csv"
OUT_ASSERT = RUN_ROOT / "checks/ndx_source_label_availability_probe_v1_assertions.out"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_csv(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "classification": "missing",
            "rows": 0,
            "columns": "",
            "sha256": "",
            "raw_data_committed": False,
        }
    frame = pd.read_csv(path, nrows=5)
    columns = list(frame.columns)
    has_label = any(col.lower() in {"regime_label", "root", "label", "source_label"} for col in columns)
    full_rows = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1
    return {
        "path": str(path),
        "exists": True,
        "classification": "source_label_candidate" if has_label else "price_only_not_source_label",
        "rows": max(full_rows, 0),
        "columns": ",".join(columns),
        "sha256": sha256(path),
        "raw_data_committed": False,
    }


def main() -> int:
    board_sha = sha256(BOARD)
    source = pd.read_csv(SOURCE_PANEL, usecols=["ticker"])
    source_tickers = sorted(source["ticker"].drop_duplicates().tolist())
    has_ndx_source_label = "^NDX" in source_tickers or "NDX" in source_tickers

    prior_rows = {
        "attachability_ndx_rows": 0,
        "attachability_rejected_near_proxy_rows": 0,
        "acquisition_ndx_rows": 0,
        "acquisition_rejected_near_proxy_rows": 0,
    }
    if PRIOR_ATTACHABILITY.exists():
        attach = pd.read_csv(PRIOR_ATTACHABILITY)
        ndx_attach = attach[attach["instrument"].astype(str).str.contains("NDX", na=False)].copy()
        prior_rows["attachability_ndx_rows"] = int(len(ndx_attach))
        prior_rows["attachability_rejected_near_proxy_rows"] = int(
            ndx_attach.fillna("").astype(str).apply(lambda row: " ".join(row.values), axis=1).str.contains(
                "rejected_near_underlying_proxy", na=False
            ).sum()
        )
    if PRIOR_ACQUISITION.exists():
        acq = pd.read_csv(PRIOR_ACQUISITION)
        ndx_acq = acq[acq["instrument"].astype(str).str.contains("NDX", na=False)].copy()
        prior_rows["acquisition_ndx_rows"] = int(len(ndx_acq))
        prior_rows["acquisition_rejected_near_proxy_rows"] = int(
            ndx_acq["missing_or_rejected_reason"].astype(str).str.contains("rejected_near_underlying_proxy", na=False).sum()
        )

    file_rows = [classify_csv(path) for path in LOCAL_NDX_PRICE_FILES]
    price_only_count = sum(1 for row in file_rows if row["classification"] == "price_only_not_source_label")
    source_label_file_count = sum(1 for row in file_rows if row["classification"] == "source_label_candidate")
    ixic_near_proxy_previously_rejected = (
        prior_rows["attachability_rejected_near_proxy_rows"] > 0
        or prior_rows["acquisition_rejected_near_proxy_rows"] > 0
    )
    relation_resolved = has_ndx_source_label or source_label_file_count > 0

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "source_panel": {
            "path": str(SOURCE_PANEL),
            "ticker_count": len(source_tickers),
            "has_ndx_or_nasdaq100_source_label": has_ndx_source_label,
            "available_index_tickers": [ticker for ticker in source_tickers if ticker.startswith("^")],
        },
        "local_ndx_files": file_rows,
        "prior_rejection_evidence": {
            "underlying_source_label_attachability": str(PRIOR_ATTACHABILITY),
            "source_label_acquisition_package_v2": str(PRIOR_ACQUISITION),
            **prior_rows,
            "ixic_near_proxy_previously_rejected": ixic_near_proxy_previously_rejected,
        },
        "decision": {
            "ndx_source_label_available": relation_resolved,
            "local_ndx_price_files_found": price_only_count,
            "local_ndx_source_label_files_found": source_label_file_count,
            "nq_crosswalk_relation_resolved": False,
            "accepted_rows_added": 0,
            "gate_result": "ndx_source_label_availability_probe_v1_no_ndx_source_label_ixic_proxy_rejected",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Acquire a Nasdaq-100-grade source-label panel for ^NDX/NDX, or get explicit owner approval "
            "that ^IXIC source labels are acceptable for NQ=F; otherwise keep NQ crosswalk rows blocked."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(file_rows).to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# NDX Source Label Availability Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This probe checks whether NQ=F can be unblocked with a Nasdaq-100-grade source-label relation. "
        "It treats local ^NDX/NDX price files as price-only evidence, not source labels.",
        "",
        "## Result",
        "",
        f"- Source panel has ^NDX/NDX source labels: `{str(has_ndx_source_label).lower()}`.",
        f"- Local NDX price-only files found: `{price_only_count}`.",
        f"- Local NDX source-label files found: `{source_label_file_count}`.",
        f"- Prior ^IXIC near-proxy rejection found: `{str(ixic_near_proxy_previously_rejected).lower()}`.",
        "- Accepted rows added: `0`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "- Gate result: `ndx_source_label_availability_probe_v1_no_ndx_source_label_ixic_proxy_rejected`.",
        "",
        "## Local File Classification",
        "",
        "| Path | Exists | Rows | Classification | Columns |",
        "|---|---:|---:|---|---|",
    ]
    for row in file_rows:
        lines.append(
            f"| `{row['path']}` | `{str(row['exists']).lower()}` | {row['rows']} | `{row['classification']}` | `{row['columns']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- NQ=F remains blocked for accepted source-label crosswalk attachment.",
            "- The available source panel has `^IXIC` but not `^NDX`; prior artifacts rejected `^IXIC` as a near-underlying proxy for `^NDX`, `QQQ`, and `NQ=F`.",
            "- Local ^NDX/NDX files are price bars only, so they cannot be used as MainRegimeV2 source labels.",
            "",
            "## Next",
            "",
            "- Acquire a Nasdaq-100-grade source-label panel for `^NDX`/`NDX`, or get explicit owner approval that `^IXIC` source labels are acceptable for `NQ=F`.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        "source_panel_has_ndx_or_nasdaq100_source_label=false"
        if not has_ndx_source_label
        else "FAIL source_panel_has_ndx_or_nasdaq100_source_label=true",
        "local_ndx_source_label_files_found=0" if source_label_file_count == 0 else f"FAIL local_ndx_source_label_files_found={source_label_file_count}",
        "ixic_near_proxy_previously_rejected=true"
        if ixic_near_proxy_previously_rejected
        else "FAIL ixic_near_proxy_previously_rejected=false",
        "accepted_rows_added=0",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    if any(line.startswith("FAIL") for line in assertions):
        assertions[-1] = "assertion_status=FAIL"
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0 if assertions[-1].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
