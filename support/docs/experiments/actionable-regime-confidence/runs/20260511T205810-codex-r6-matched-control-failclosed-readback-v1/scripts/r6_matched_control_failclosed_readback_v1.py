#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


RUN_ID = "20260511T205810+0800-codex-r6-matched-control-failclosed-readback-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205810-codex-r6-matched-control-failclosed-readback-v1"
)
OUT_DIR = RUN_ROOT / "r6-matched-control-failclosed-readback"
CHECKS_DIR = RUN_ROOT / "checks"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
POSITIVE_ROWS = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
NEGATIVE_ROWS = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE_ROOT / "provenance_manifest.json"


def read_csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return max(0, len(rows) - 1)


def fetch_probe(url: str, needles: list[str]) -> dict:
    req = Request(url, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    try:
        with urlopen(req, timeout=20) as response:
            body = response.read()
            text = body.decode("utf-8", errors="ignore")
            return {
                "url": url,
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "bytes": len(body),
                "needle_checks": {needle: needle.lower() in text.lower() for needle in needles},
            }
    except Exception as exc:
        return {
            "url": url,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "needle_checks": {needle: False for needle in needles},
        }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    verifier = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    positive_count = read_csv_count(POSITIVE_ROWS)
    negative_count = read_csv_count(NEGATIVE_ROWS)
    provenance_present = PROVENANCE.exists()
    verifier_json = {}
    try:
        verifier_json = json.loads(verifier.stdout)
    except json.JSONDecodeError:
        verifier_json = {"stdout": verifier.stdout, "stderr": verifier.stderr}

    finra_probe = fetch_probe(
        "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
        [
            "Potential Manipulation Report",
            "layering",
            "cross-market quote spoofing",
            "Report Center",
        ],
    )
    cftc_probe = fetch_probe(
        "https://www.cftc.gov/PressRoom/PressReleases/7881-19",
        [
            "Krishna Mohan",
            "spoofing",
            "E-mini NASDAQ",
        ],
    )

    verifier_status = verifier_json.get("status")
    schema_ready_unscored = verifier.returncode == 0 and verifier_status == "schema_ready_unscored"

    decision = {
        "gate_result": "r6_matched_control_readback_v1=direct_intake_schema_ready_unscored_confidence_gate_false"
        if schema_ready_unscored
        else "r6_matched_control_readback_v1=direct_intake_not_ready_blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "matched_controls_constructed": negative_count > 0,
        "matched_controls_construction_reason": (
            "schema-ready seed only: matched controls are same-report CFTC genuine-order legs, "
            "not a broad normal-market calibration sample"
            if negative_count > 0
            else "blocked: no source-owned or owner-approved same-schema normal-control rows were found"
        ),
    }

    intake_rows = [
        {
            "file": str(POSITIVE_ROWS),
            "present": POSITIVE_ROWS.exists(),
            "rows": positive_count,
            "role": "source_owned_positive_rows",
        },
        {
            "file": str(NEGATIVE_ROWS),
            "present": NEGATIVE_ROWS.exists(),
            "rows": negative_count,
            "role": "required_same_schema_matched_normal_controls",
        },
        {
            "file": str(PROVENANCE),
            "present": provenance_present,
            "rows": "",
            "role": "provenance_manifest",
        },
    ]

    with (OUT_DIR / "r6_matched_control_failclosed_readback_v1_intake_files.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "present", "rows", "role"])
        writer.writeheader()
        writer.writerows(intake_rows)

    report = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "r6_matched_control_failclosed_readback_v1",
        "previous_cursor": "20260511T205654+0800-codex-cftc-matched-control-seed-v1",
        "intake_root": str(INTAKE_ROOT),
        "verifier": {
            "command": " ".join(["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)]),
            "returncode": verifier.returncode,
            "stdout": verifier_json,
            "stderr": verifier.stderr,
        },
        "public_source_probes": {
            "finra_potential_manipulation_report": finra_probe,
            "cftc_mohan_press_release": cftc_probe,
        },
        "intake_files": intake_rows,
        "decision": decision,
        "artifacts": {
            "json": str(OUT_DIR / "r6_matched_control_failclosed_readback_v1.json"),
            "md": str(OUT_DIR / "r6_matched_control_failclosed_readback_v1.md"),
            "intake_csv": str(OUT_DIR / "r6_matched_control_failclosed_readback_v1_intake_files.csv"),
            "assertions": str(CHECKS_DIR / "r6_matched_control_failclosed_readback_v1_assertions.out"),
        },
    }

    assertions = {
        "positive_rows_present": positive_count > 0,
        "provenance_present": provenance_present,
        "matched_negative_controls_present": negative_count > 0 and NEGATIVE_ROWS.exists(),
        "verifier_schema_ready_unscored": schema_ready_unscored,
        "strict_full_objective_not_claimed": not decision["strict_full_objective_achieved"]
        and not decision["update_goal"],
    }
    with (CHECKS_DIR / "r6_matched_control_failclosed_readback_v1_assertions.out").open(
        "w", encoding="utf-8"
    ) as handle:
        for name, passed in assertions.items():
            handle.write(f"{name}={'PASS' if passed else 'FAIL'}\n")

    md = f"""# R6 Matched Control Readback v1

- Gate result: `{decision['gate_result']}`.
- Previous cursor checked: `{report['previous_cursor']}`.
- Positive source-owned CFTC spoofing/layering rows present: `{positive_count}`.
- Provenance manifest present: `{provenance_present}`.
- Required same-schema matched normal-control rows present: `{negative_count}`.
- Verifier return code: `{verifier.returncode}`.
- Verifier status: `{verifier_status}`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Source Boundary

- CFTC public material supports positive spoofing/layering examples and provenance.
- Same-report CFTC genuine-order legs now provide a same-schema control seed.
- FINRA public material supports schema/report-center routing for potential-manipulation exceptions, not broad public normal-market exports.
- This is schema readiness only: the two-positive/two-control same-report seed is too small for chronological Wilson95 calibration or heldout-symbol/venue validation.
- I did not derive controls from OHLCV or claim full direct `Manipulation` species coverage.

## Verifier

```json
{json.dumps(verifier_json, indent=2)}
```

## Next Action

Acquire additional source-owned/owner-approved positive and same-schema normal-control rows across more symbols, venues, and periods; then run the chronological plus heldout-symbol/venue Wilson95 calibration gate before any completion audit.

## Artifacts

- JSON: `{report['artifacts']['json']}`
- Intake CSV: `{report['artifacts']['intake_csv']}`
- Assertions: `{report['artifacts']['assertions']}`
"""
    (OUT_DIR / "r6_matched_control_failclosed_readback_v1.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "r6_matched_control_failclosed_readback_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
