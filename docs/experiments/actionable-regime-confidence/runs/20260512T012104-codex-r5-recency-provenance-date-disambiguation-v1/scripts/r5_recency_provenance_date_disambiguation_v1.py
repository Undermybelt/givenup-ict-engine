#!/usr/bin/env python3
"""Disambiguate composite source-label date max from the R5 recency source."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


RUN_ID = "20260512T012104-codex-r5-recency-provenance-date-disambiguation-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "r5-recency-provenance-date-disambiguation-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_LABEL_ROWS = SOURCE_LABEL_ROOT / "source_label_equivalence_rows.csv"
SOURCE_LABEL_PROVENANCE = SOURCE_LABEL_ROOT / "source_label_equivalence_provenance.json"
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R5_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
STOCK_SOURCE = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
R5_CUTOFF = "2026-01-30"
TARGETS = [
    ("XOM", "Sideways"),
    ("UNH", "Bear"),
    ("^DJI", "Sideways"),
    ("AMD", "Bear"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_stock_source() -> dict:
    result = {
        "path": str(STOCK_SOURCE),
        "present": STOCK_SOURCE.exists(),
        "sha256": sha256_file(STOCK_SOURCE) if STOCK_SOURCE.exists() else "",
        "row_count": 0,
        "date_min": "",
        "date_max": "",
        "post_cutoff_rows": 0,
        "target_rows": [],
    }
    target_counts = {target: 0 for target in TARGETS}
    target_post_counts = {target: 0 for target in TARGETS}
    target_latest = {target: "" for target in TARGETS}

    if not STOCK_SOURCE.exists():
        return result

    with STOCK_SOURCE.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            result["row_count"] += 1
            date_value = row.get("date", "")
            ticker = row.get("ticker", "")
            label = row.get("regime_label", "")
            if date_value:
                if not result["date_min"] or date_value < result["date_min"]:
                    result["date_min"] = date_value
                if date_value > result["date_max"]:
                    result["date_max"] = date_value
                if date_value > R5_CUTOFF:
                    result["post_cutoff_rows"] += 1
            target = (ticker, label)
            if target in target_counts:
                target_counts[target] += 1
                if date_value > target_latest[target]:
                    target_latest[target] = date_value
                if date_value > R5_CUTOFF:
                    target_post_counts[target] += 1

    for symbol, label in TARGETS:
        target = (symbol, label)
        result["target_rows"].append(
            {
                "symbol": symbol,
                "required_label": label,
                "raw_source_rows_total": target_counts[target],
                "raw_source_latest_date": target_latest[target],
                "raw_source_post_cutoff_rows": target_post_counts[target],
                "r5_recency_satisfied_by_raw_stock_source": target_post_counts[target] > 0,
            }
        )
    return result


def scan_source_label_root() -> dict:
    result = {
        "root": str(SOURCE_LABEL_ROOT),
        "rows_present": SOURCE_LABEL_ROWS.exists(),
        "provenance_present": SOURCE_LABEL_PROVENANCE.exists(),
        "rows_sha256": sha256_file(SOURCE_LABEL_ROWS) if SOURCE_LABEL_ROWS.exists() else "",
        "provenance_sha256": sha256_file(SOURCE_LABEL_PROVENANCE)
        if SOURCE_LABEL_PROVENANCE.exists()
        else "",
        "provenance_date_max": "",
        "rows_date_min": "",
        "rows_date_max": "",
        "post_cutoff_rows_by_source_owner": {},
        "post_cutoff_rows_by_market_family": {},
        "target_rows": [],
    }
    target_counts = {target: 0 for target in TARGETS}
    target_post_counts = {target: 0 for target in TARGETS}
    target_latest = {target: "" for target in TARGETS}

    if SOURCE_LABEL_PROVENANCE.exists():
        provenance = json.loads(SOURCE_LABEL_PROVENANCE.read_text(encoding="utf-8"))
        result["provenance_date_max"] = provenance.get("date_max", "")

    if SOURCE_LABEL_ROWS.exists():
        with SOURCE_LABEL_ROWS.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                date_value = row.get("timestamp_or_date", "")
                if date_value:
                    if not result["rows_date_min"] or date_value < result["rows_date_min"]:
                        result["rows_date_min"] = date_value
                    if date_value > result["rows_date_max"]:
                        result["rows_date_max"] = date_value
                    if date_value > R5_CUTOFF:
                        owner = row.get("source_owner", "")
                        family = row.get("market_family", "")
                        result["post_cutoff_rows_by_source_owner"][owner] = (
                            result["post_cutoff_rows_by_source_owner"].get(owner, 0) + 1
                        )
                        result["post_cutoff_rows_by_market_family"][family] = (
                            result["post_cutoff_rows_by_market_family"].get(family, 0) + 1
                        )
                target = (row.get("symbol", ""), row.get("main_regime_v2_label", ""))
                if target in target_counts:
                    target_counts[target] += 1
                    if date_value > target_latest[target]:
                        target_latest[target] = date_value
                    if date_value > R5_CUTOFF:
                        target_post_counts[target] += 1

    for symbol, label in TARGETS:
        target = (symbol, label)
        result["target_rows"].append(
            {
                "symbol": symbol,
                "required_label": label,
                "source_label_rows_total": target_counts[target],
                "source_label_latest_date": target_latest[target],
                "source_label_post_cutoff_rows": target_post_counts[target],
                "r5_recency_satisfied_by_source_label_root": target_post_counts[target] > 0,
            }
        )
    return result


def run_r5_verifier() -> dict:
    command = [sys.executable, str(R5_VERIFIER), "--intake-root", str(R5_ROOT)]
    proc = subprocess.run(command, check=False, text=True, capture_output=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    (CMD_DIR / "r5_recency_verifier_stdout.json").write_text(proc.stdout, encoding="utf-8")
    (CMD_DIR / "r5_recency_verifier_stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_DIR / "r5_recency_verifier_exit_code.txt").write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "command": command,
        "returncode": proc.returncode,
        "parsed_stdout": parsed,
    }


def write_target_csv(path: Path, stock_scan: dict, source_label_scan: dict) -> None:
    stock_by_key = {
        (row["symbol"], row["required_label"]): row for row in stock_scan["target_rows"]
    }
    label_by_key = {
        (row["symbol"], row["required_label"]): row
        for row in source_label_scan["target_rows"]
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "symbol",
                "required_label",
                "raw_source_rows_total",
                "raw_source_latest_date",
                "raw_source_post_cutoff_rows",
                "source_label_rows_total",
                "source_label_latest_date",
                "source_label_post_cutoff_rows",
                "r5_recency_satisfied",
            ],
        )
        writer.writeheader()
        for symbol, label in TARGETS:
            key = (symbol, label)
            stock_row = stock_by_key[key]
            label_row = label_by_key[key]
            writer.writerow(
                {
                    "symbol": symbol,
                    "required_label": label,
                    "raw_source_rows_total": stock_row["raw_source_rows_total"],
                    "raw_source_latest_date": stock_row["raw_source_latest_date"],
                    "raw_source_post_cutoff_rows": stock_row["raw_source_post_cutoff_rows"],
                    "source_label_rows_total": label_row["source_label_rows_total"],
                    "source_label_latest_date": label_row["source_label_latest_date"],
                    "source_label_post_cutoff_rows": label_row["source_label_post_cutoff_rows"],
                    "r5_recency_satisfied": stock_row["raw_source_post_cutoff_rows"] > 0
                    and label_row["source_label_post_cutoff_rows"] > 0,
                }
            )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    stock_scan = scan_stock_source()
    source_label_scan = scan_source_label_root()
    verifier = run_r5_verifier()

    target_satisfied = all(
        row["raw_source_post_cutoff_rows"] > 0 for row in stock_scan["target_rows"]
    )
    gate_result = (
        "r5_recency_provenance_date_disambiguation_v1="
        "composite_date_max_not_r5_stock_recency_rows_root_still_missing"
    )
    summary = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "r5_cutoff_exclusive": R5_CUTOFF,
        "stock_source": stock_scan,
        "source_label_root": source_label_scan,
        "r5_recency_root": str(R5_ROOT),
        "r5_recency_root_exists": R5_ROOT.exists(),
        "r5_verifier": verifier,
        "interpretation": (
            "The composite source-label root date_max comes from non-R5 rows. "
            "The stock-regime source required for R5 still ends at 2026-01-30, "
            "and the required R5 intake root/files are absent."
        ),
        "all_r5_targets_satisfied": target_satisfied,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r5_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    write_target_csv(
        OUT_DIR / "r5_recency_provenance_date_disambiguation_targets_v1.csv",
        stock_scan,
        source_label_scan,
    )
    (OUT_DIR / "r5_recency_provenance_date_disambiguation_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    post_cutoff_owners = ", ".join(
        f"{owner}={count}"
        for owner, count in sorted(
            source_label_scan["post_cutoff_rows_by_source_owner"].items()
        )
    ) or "none"
    report_lines = [
        "# R5 Recency Provenance Date Disambiguation v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{gate_result}`.",
        f"- Composite source-label provenance `date_max`: `{source_label_scan['provenance_date_max']}`.",
        f"- Raw stock-regime source date range: `{stock_scan['date_min']}` to `{stock_scan['date_max']}`.",
        f"- Raw stock-regime post-cutoff rows after `{R5_CUTOFF}`: `{stock_scan['post_cutoff_rows']}`.",
        f"- Source-label post-cutoff rows by owner: `{post_cutoff_owners}`.",
        f"- R5 verifier: status `{verifier['parsed_stdout'].get('status', '')}`, reason `{verifier['parsed_stdout'].get('reason', '')}`, exit `{verifier['returncode']}`.",
        "- Accepted rows added: `0`; new confidence gate: false; downstream chain rerun allowed: false.",
        "- Strict full objective achieved: false. `update_goal=false`.",
        "",
        "## Target Cells",
        "",
    ]
    label_by_key = {
        (row["symbol"], row["required_label"]): row
        for row in source_label_scan["target_rows"]
    }
    for row in stock_scan["target_rows"]:
        label_row = label_by_key[(row["symbol"], row["required_label"])]
        report_lines.append(
            f"- `{row['symbol']}` / `{row['required_label']}`: raw stock latest "
            f"`{row['raw_source_latest_date']}`, raw post-cutoff "
            f"`{row['raw_source_post_cutoff_rows']}`, source-label latest "
            f"`{label_row['source_label_latest_date']}`, source-label post-cutoff "
            f"`{label_row['source_label_post_cutoff_rows']}`."
        )
    report_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Do not use the composite `2026-03-20` date max to populate R5. It is not post-cutoff stock-regime source evidence for the required R5 cells. Keep `/tmp/ict-engine-source-panel-recency-extension` absent until source-owned extension rows and provenance are delivered.",
        ]
    )
    (OUT_DIR / "r5_recency_provenance_date_disambiguation_v1.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={gate_result}",
        f"stock_source_date_max={stock_scan['date_max']}",
        f"stock_source_post_cutoff_rows={stock_scan['post_cutoff_rows']}",
        f"source_label_provenance_date_max={source_label_scan['provenance_date_max']}",
        f"r5_verifier_status={verifier['parsed_stdout'].get('status', '')}",
        f"r5_verifier_reason={verifier['parsed_stdout'].get('reason', '')}",
        f"r5_verifier_exit_code={verifier['returncode']}",
        f"all_r5_targets_satisfied={str(target_satisfied).lower()}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "downstream_chain_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "r5_recency_provenance_date_disambiguation_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
