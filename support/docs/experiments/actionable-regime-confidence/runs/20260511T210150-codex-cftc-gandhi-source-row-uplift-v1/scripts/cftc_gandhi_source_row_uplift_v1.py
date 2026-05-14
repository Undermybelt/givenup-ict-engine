#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


RUN_ID = "20260511T210150+0800-codex-cftc-gandhi-source-row-uplift-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210150-codex-cftc-gandhi-source-row-uplift-v1"
)
OUT_DIR = RUN_ROOT / "cftc-gandhi-source-row-uplift"
CHECKS_DIR = RUN_ROOT / "checks"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_ROWS = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
NEGATIVE_ROWS = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE_ROOT / "provenance_manifest.json"
SOURCE_CACHE = Path("/tmp/ict-engine-cftc-source-row-search")
GANDHI_PDF = SOURCE_CACHE / "enfkamaldeepdandhiorder101118.pdf"
GANDHI_TXT = SOURCE_CACHE / "enfkamaldeepdandhiorder101118.txt"
GANDHI_URL = "https://www.cftc.gov/sites/default/files/2018-10/enfkamaldeepdandhiorder101118.pdf"
VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

FIELDNAMES = [
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
]

SOURCE_REPORT = "CFTC Order: Kamaldeep Gandhi, CFTC Docket No. 19-01"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Findings II.A.i, December 16 2013 March 2014 E-mini S&P example",
        "trade_date": "2013-12-16",
        "symbol": "March 2014 E-mini S&P 500 futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC respondent trader; firm account redacted",
        "participant_identifier": "Kamaldeep Gandhi / Firm A",
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "04:45:57.496 America/Chicago",
        "latest_order_received_time": "04:46:13.240 America/Chicago",
        "order_count": "27 spoof orders in four groups",
        "total_order_quantity": "600 contracts",
        "activity_description": "Public CFTC findings describe four sell-side spoof groups opposite a buy iceberg order, followed by full cancellation of the spoof groups.",
        "matched_negative_group_id": "cftc_gandhi_20131216_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_gandhi_20131216_es_sell_spoof_groups",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Findings II.A.ii, September 17 2014 December 2014 E-mini S&P example",
        "trade_date": "2014-09-17",
        "symbol": "December 2014 E-mini S&P 500 futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC respondent trader; firm account redacted",
        "participant_identifier": "Kamaldeep Gandhi / Firm A",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "10:09:15.339 America/Chicago",
        "latest_order_received_time": "10:09:16.932 America/Chicago",
        "order_count": "iceberg buy spoof order plus additional spoof group",
        "total_order_quantity": "250 contracts plus additional group quantity described in source",
        "activity_description": "Public CFTC findings describe buy-side spoof orders opposite a sell genuine iceberg order, followed by cancellation milliseconds after the genuine order filled.",
        "matched_negative_group_id": "cftc_gandhi_20140917_es_example",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_gandhi_20140917_es_buy_spoof_groups",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Findings II.A.i, December 16 2013 March 2014 E-mini S&P example",
        "trade_date": "2013-12-16",
        "symbol": "March 2014 E-mini S&P 500 futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC respondent trader; firm account redacted",
        "participant_identifier": "Kamaldeep Gandhi / Firm A",
        "side": "buy genuine iceberg order described in same CFTC facts paragraph",
        "earliest_order_received_time": "04:45:57.496 America/Chicago",
        "latest_order_received_time": "04:46:08.353 America/Chicago",
        "order_count": "one genuine iceberg order leg",
        "total_order_quantity": "100 contracts, displaying 12 contracts",
        "activity_description": "Matched same-report control seed from the CFTC facts: the buy genuine iceberg order leg described opposite the spoof groups. Schema/control seed only, not broad normal-market calibration.",
        "matched_negative_group_id": "cftc_gandhi_20131216_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_gandhi_20131216_es_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Findings II.A.ii, September 17 2014 December 2014 E-mini S&P example",
        "trade_date": "2014-09-17",
        "symbol": "December 2014 E-mini S&P 500 futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC respondent trader; firm account redacted",
        "participant_identifier": "Kamaldeep Gandhi / Firm A",
        "side": "sell genuine iceberg order described in same CFTC facts paragraph",
        "earliest_order_received_time": "10:09:14.592 America/Chicago",
        "latest_order_received_time": "10:09:16.930 America/Chicago",
        "order_count": "one genuine iceberg order leg",
        "total_order_quantity": "250 contracts, displaying 19 contracts",
        "activity_description": "Matched same-report control seed from the CFTC facts: the sell genuine iceberg order leg described opposite the spoof groups. Schema/control seed only, not broad normal-market calibration.",
        "matched_negative_group_id": "cftc_gandhi_20140917_es_example",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_gandhi_20140917_es_sell_genuine_iceberg_control",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_source() -> dict:
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    if not GANDHI_PDF.exists():
        req = Request(GANDHI_URL, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
        with urlopen(req, timeout=30) as response:
            GANDHI_PDF.write_bytes(response.read())
    text = GANDHI_TXT.read_text(encoding="utf-8", errors="ignore") if GANDHI_TXT.exists() else ""
    needles = [
        "December 16, 2013",
        "4:45:57.496 AM",
        "600 sell contracts",
        "September 17, 2014",
        "10:09:14.592 AM",
        "10:09:16.932 AM",
    ]
    return {
        "url": GANDHI_URL,
        "path": str(GANDHI_PDF),
        "bytes": GANDHI_PDF.stat().st_size,
        "sha256": sha256(GANDHI_PDF),
        "text_path": str(GANDHI_TXT) if GANDHI_TXT.exists() else None,
        "text_checks": {needle: needle.lower() in text.lower() for needle in needles},
    }


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[int, int]:
    rows = load_rows(path)
    seen = {row.get("source_row_id", "") for row in rows}
    added = 0
    for row in additions:
        if row["source_row_id"] not in seen:
            rows.append(row)
            seen.add(row["source_row_id"])
            added += 1
    write_rows(path, rows)
    return len(rows), added


def update_provenance(source_probe: dict, positive_count: int, negative_count: int) -> dict:
    if PROVENANCE.exists():
        try:
            provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            provenance = {}
    else:
        provenance = {}
    provenance["cftc_gandhi_order"] = source_probe
    provenance["gandhi_rows_materialized_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["gandhi_positive_rows_added"] = len(POSITIVE_ADDITIONS)
    provenance["gandhi_matched_negative_rows_added"] = len(NEGATIVE_ADDITIONS)
    provenance["positive_rows_count"] = positive_count
    provenance["matched_negative_rows_count"] = negative_count
    provenance["matched_control_limitations"] = (
        "CFTC same-report genuine-order legs are schema/control seeds only; "
        "they are not broad normal-market heldout controls."
    )
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    return provenance


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    source_probe = ensure_source()
    positive_count, positive_added = append_unique(POSITIVE_ROWS, POSITIVE_ADDITIONS)
    negative_count, negative_added = append_unique(NEGATIVE_ROWS, NEGATIVE_ADDITIONS)
    provenance = update_provenance(source_probe, positive_count, negative_count)

    verifier = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        verifier_json = json.loads(verifier.stdout)
    except json.JSONDecodeError:
        verifier_json = {"stdout": verifier.stdout, "stderr": verifier.stderr}

    decision = {
        "gate_result": "cftc_gandhi_source_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_unscored",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "r6_direct_species_closed": False,
    }

    summary_rows = [
        {
            "file": str(POSITIVE_ROWS),
            "rows": positive_count,
            "rows_added_this_run": positive_added,
            "sha256": sha256(POSITIVE_ROWS),
        },
        {
            "file": str(NEGATIVE_ROWS),
            "rows": negative_count,
            "rows_added_this_run": negative_added,
            "sha256": sha256(NEGATIVE_ROWS),
        },
        {
            "file": str(PROVENANCE),
            "rows": "",
            "rows_added_this_run": "",
            "sha256": sha256(PROVENANCE),
        },
    ]
    with (OUT_DIR / "cftc_gandhi_source_row_uplift_v1_intake_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "rows", "rows_added_this_run", "sha256"])
        writer.writeheader()
        writer.writerows(summary_rows)

    report = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "cftc_gandhi_source_row_uplift_v1",
        "previous_cursor": "20260511T205654+0800-codex-cftc-matched-control-seed-v1",
        "source_probe": source_probe,
        "positive_rows": positive_count,
        "negative_rows": negative_count,
        "positive_rows_added_this_run": positive_added,
        "negative_rows_added_this_run": negative_added,
        "matched_group_count": verifier_json.get("matched_group_count"),
        "verifier": {
            "command": " ".join(["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)]),
            "returncode": verifier.returncode,
            "stdout": verifier_json,
            "stderr": verifier.stderr,
        },
        "provenance_keys": sorted(provenance.keys()),
        "decision": decision,
        "artifacts": {
            "json": str(OUT_DIR / "cftc_gandhi_source_row_uplift_v1.json"),
            "md": str(OUT_DIR / "cftc_gandhi_source_row_uplift_v1.md"),
            "intake_summary_csv": str(OUT_DIR / "cftc_gandhi_source_row_uplift_v1_intake_summary.csv"),
            "assertions": str(CHECKS_DIR / "cftc_gandhi_source_row_uplift_v1_assertions.out"),
        },
    }

    assertions = {
        "source_pdf_present": GANDHI_PDF.exists(),
        "positive_rows_added": positive_added == len(POSITIVE_ADDITIONS),
        "matched_negative_rows_added": negative_added == len(NEGATIVE_ADDITIONS),
        "verifier_schema_ready_unscored": verifier.returncode == 0
        and verifier_json.get("status") == "schema_ready_unscored",
        "strict_full_objective_not_claimed": not decision["strict_full_objective_achieved"]
        and not decision["update_goal"],
    }
    with (CHECKS_DIR / "cftc_gandhi_source_row_uplift_v1_assertions.out").open(
        "w", encoding="utf-8"
    ) as handle:
        for name, passed in assertions.items():
            handle.write(f"{name}={'PASS' if passed else 'FAIL'}\n")

    md = f"""# CFTC Gandhi Source Row Uplift v1

- Gate result: `{decision['gate_result']}`.
- Previous cursor checked: `{report['previous_cursor']}`.
- Source: `{GANDHI_URL}`.
- Positive rows now: `{positive_count}`; added this run: `{positive_added}`.
- Matched negative/control rows now: `{negative_count}`; added this run: `{negative_added}`.
- Verifier status: `{verifier_json.get('status')}`; matched groups: `{verifier_json.get('matched_group_count')}`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This expands the R6 spoofing/layering intake with two additional CFTC public-order examples from Gandhi. It is still schema-ready/unscored only: support is small, controls are same-report genuine-order seeds, and there is no chronological Wilson95 or heldout-symbol/venue acceptance.

## Verifier

```json
{json.dumps(verifier_json, indent=2)}
```

## Next Action

Acquire additional source-owned/owner-approved positive and same-schema normal-control rows across more symbols, venues, and periods; then run the chronological plus heldout-symbol/venue Wilson95 calibration gate before another completion audit.

## Artifacts

- JSON: `{report['artifacts']['json']}`
- Intake summary CSV: `{report['artifacts']['intake_summary_csv']}`
- Assertions: `{report['artifacts']['assertions']}`
"""
    (OUT_DIR / "cftc_gandhi_source_row_uplift_v1.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "cftc_gandhi_source_row_uplift_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
