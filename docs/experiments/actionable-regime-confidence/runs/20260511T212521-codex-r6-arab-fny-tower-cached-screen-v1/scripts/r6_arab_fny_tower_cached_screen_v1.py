#!/usr/bin/env python3
"""Fail-closed screen for cached Arab/FNY/Tower CFTC candidates.

This script is intentionally read-only with respect to the live intake root. It
uses already-cached /tmp sources, records compact provenance, and confirms the
current direct-Manipulation verifier state without materializing rows.
"""

from __future__ import annotations

import csv
import hashlib
import html.parser
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T212521-codex-r6-arab-fny-tower-cached-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-arab-fny-tower-cached-screen"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
TMP_ROOT = Path("/tmp/ict-engine-r6-cftc-public-order-candidate-uplift-v1")
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    source_url: str
    binary_path: Path
    text_path: Path | None
    source_kind: str
    cached_summary: str
    fail_closed_reason: str


class TextExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)

    def text(self) -> str:
        return "\n".join(self.parts)


CANDIDATES = [
    Candidate(
        candidate_id="cftc_arab_trading_group_order_2020",
        source_url="https://www.cftc.gov/media/4861/enfarbtradinggrouporder093020/download",
        binary_path=TMP_ROOT / "cftc_arab_trading_group_order_2020.bin",
        text_path=TMP_ROOT / "cftc_arab_trading_group_order_2020.gs.txt",
        source_kind="official_cftc_order_cached_pdf_text",
        cached_summary=(
            "The cached order gives respondent/trader groups, product families, "
            "date ranges, and generic genuine/spoof order patterns."
        ),
        fail_closed_reason=(
            "No row-level trade date, side, exact contract, order timestamp, or "
            "single matched genuine order is exposed for any one event."
        ),
    ),
    Candidate(
        candidate_id="cftc_fny_order_2020",
        source_url="https://www.cftc.gov/media/4811/enffnyorder092820/download",
        binary_path=TMP_ROOT / "cftc_fny_order_2020.bin",
        text_path=TMP_ROOT / "cftc_fny_order_2020.gs.txt",
        source_kind="official_cftc_order_cached_pdf_text",
        cached_summary=(
            "The cached order gives a former trader, broad product families, "
            "the relevant period, and a generic genuine/spoof pattern."
        ),
        fail_closed_reason=(
            "No event-level date, side, exact order quantity, timestamp, or "
            "matched source-described genuine control row is present."
        ),
    ),
    Candidate(
        candidate_id="cftc_tower_press_release_2019",
        source_url="https://www.cftc.gov/PressRoom/PressReleases/8074-19",
        binary_path=TMP_ROOT / "cftc_tower_press_release_2019.bin",
        text_path=None,
        source_kind="official_cftc_press_release_cached_html",
        cached_summary=(
            "The cached press release gives an official order link, the broad "
            "2012-2013 period, equity-index futures venue context, and the "
            "generic genuine/spoof order pattern."
        ),
        fail_closed_reason=(
            "The cached HTML is a press release, not the linked order; it lacks "
            "row-level dates, symbols, sides, quantities, and matched controls. "
            "The linked order was not fetched in this no-network slice."
        ),
    ),
]


DATE_PATTERN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_candidate_text(candidate: Candidate) -> str:
    if candidate.text_path and candidate.text_path.exists():
        return candidate.text_path.read_text(encoding="utf-8", errors="replace")
    raw = candidate.binary_path.read_bytes()
    if candidate.source_kind.endswith("cached_html"):
        parser = TextExtractor()
        parser.feed(raw.decode("utf-8", errors="replace"))
        return parser.text()
    return raw.decode("utf-8", errors="replace")


def current_intake_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for name in [
        "positive_spoofing_layering_rows.csv",
        "matched_negative_normal_activity_rows.csv",
        "provenance_manifest.json",
    ]:
        path = INTAKE / name
        result[name] = sha256_file(path) if path.exists() else "missing"
    return result


def run_verifier() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    before_hashes = current_intake_hashes()
    rows: list[dict[str, object]] = []
    for candidate in CANDIDATES:
        binary_exists = candidate.binary_path.exists()
        text_exists = bool(candidate.text_path and candidate.text_path.exists())
        text = read_candidate_text(candidate) if binary_exists else ""
        date_hits = sorted(set(DATE_PATTERN.findall(text)))
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "source_url": candidate.source_url,
                "source_kind": candidate.source_kind,
                "binary_exists": binary_exists,
                "text_exists": text_exists,
                "binary_sha256": sha256_file(candidate.binary_path) if binary_exists else "missing",
                "text_sha256": (
                    sha256_file(candidate.text_path)
                    if candidate.text_path and candidate.text_path.exists()
                    else "n/a"
                ),
                "char_count": len(text),
                "date_hit_count": len(date_hits),
                "date_hits": "; ".join(date_hits[:12]),
                "mentions_genuine_order": "Genuine Order" in text or "genuine orders" in text.lower(),
                "mentions_spoof_order": "Spoof Order" in text or "spoof orders" in text.lower(),
                "row_materializable": False,
                "positive_rows_added": 0,
                "matched_controls_added": 0,
                "cached_summary": candidate.cached_summary,
                "fail_closed_reason": candidate.fail_closed_reason,
            }
        )

    verifier = run_verifier()
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(
        verifier.stdout, encoding="utf-8"
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(
        verifier.stderr, encoding="utf-8"
    )
    after_hashes = current_intake_hashes()

    candidate_csv = OUT / "r6_arab_fny_tower_cached_screen_v1_candidates.csv"
    fields = [
        "candidate_id",
        "source_url",
        "source_kind",
        "binary_exists",
        "text_exists",
        "binary_sha256",
        "text_sha256",
        "char_count",
        "date_hit_count",
        "date_hits",
        "mentions_genuine_order",
        "mentions_spoof_order",
        "row_materializable",
        "positive_rows_added",
        "matched_controls_added",
        "cached_summary",
        "fail_closed_reason",
    ]
    write_csv(candidate_csv, rows, fields)

    all_cached = all(row["binary_exists"] for row in rows)
    no_rows_materialized = all(row["positive_rows_added"] == 0 for row in rows)
    intake_unchanged = before_hashes == after_hashes
    gate_rows = [
        {
            "gate": "cached_sources_present",
            "value": str(all_cached).lower(),
            "required": "true",
            "status": "pass" if all_cached else "fail",
        },
        {
            "gate": "row_materialization",
            "value": "0",
            "required": "only if row-level source fields exist",
            "status": "fail_closed",
        },
        {
            "gate": "intake_unchanged",
            "value": str(intake_unchanged).lower(),
            "required": "true",
            "status": "pass" if intake_unchanged else "fail",
        },
        {
            "gate": "external_requests_sent",
            "value": "false",
            "required": "false",
            "status": "pass",
        },
        {
            "gate": "accepted_confidence",
            "value": "false",
            "required": "true",
            "status": "blocked",
        },
    ]
    gates_csv = OUT / "r6_arab_fny_tower_cached_screen_v1_gates.csv"
    write_csv(gates_csv, gate_rows, ["gate", "value", "required", "status"])

    result = {
        "run_id": RUN_ID,
        "created_at_utc": utc_now(),
        "input_root": str(TMP_ROOT),
        "intake_root": str(INTAKE),
        "candidate_count": len(rows),
        "row_materializable_candidates": 0,
        "positive_rows_added": 0,
        "matched_controls_added": 0,
        "intake_hashes_before": before_hashes,
        "intake_hashes_after": after_hashes,
        "intake_unchanged": intake_unchanged,
        "verifier_returncode": verifier.returncode,
        "external_requests_sent": False,
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "gate_result": "r6_arab_fny_tower_cached_screen_v1=cached_candidates_fail_closed_no_row_level_events",
        "candidates": rows,
        "artifacts": {
            "json": str(OUT / "r6_arab_fny_tower_cached_screen_v1.json"),
            "report": str(OUT / "r6_arab_fny_tower_cached_screen_v1.md"),
            "candidate_csv": str(candidate_csv),
            "gates_csv": str(gates_csv),
            "verifier_stdout": str(CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"),
            "verifier_stderr": str(CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"),
            "assertions": str(CHECKS / "r6_arab_fny_tower_cached_screen_v1_assertions.out"),
        },
    }
    json_path = OUT / "r6_arab_fny_tower_cached_screen_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 Arab/FNY/Tower Cached Screen v1",
        "",
        "## Scope",
        "",
        "Read-only screen of the cached Arab Trading Group, FNY, and Tower CFTC candidate sources from the earlier public-order candidate run. No network requests were sent and the direct-Manipulation intake files were not changed.",
        "",
        "## Result",
        "",
        "- Candidate sources checked: `3`.",
        "- Row-materializable candidates: `0`.",
        "- Positive rows added: `0`.",
        "- Matched controls added: `0`.",
        "- Intake unchanged: `" + str(intake_unchanged).lower() + "`.",
        "- Direct verifier return code: `" + str(verifier.returncode) + "`.",
        "- Gate result: `r6_arab_fny_tower_cached_screen_v1=cached_candidates_fail_closed_no_row_level_events`.",
        "",
        "## Candidate Decisions",
        "",
    ]
    for row in rows:
        report.extend(
            [
                f"### {row['candidate_id']}",
                "",
                f"- Source kind: `{row['source_kind']}`.",
                f"- Cached text chars: `{row['char_count']}`; date hits: `{row['date_hit_count']}`.",
                f"- Summary: {row['cached_summary']}",
                f"- Fail-closed reason: {row['fail_closed_reason']}",
                "- Rows materialized: `0`.",
                "",
            ]
        )
    report.extend(
        [
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Candidate CSV: `{candidate_csv}`",
            f"- Gates CSV: `{gates_csv}`",
            f"- Verifier stdout: `{CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt'}`",
            f"- Assertions: `{CHECKS / 'r6_arab_fny_tower_cached_screen_v1_assertions.out'}`",
            "",
            "## Non-Completion",
            "",
            "This run does not close R6 or the full Board A objective. It only prevents broad-order summaries from being promoted as row-level confidence evidence.",
            "",
        ]
    )
    report_path = OUT / "r6_arab_fny_tower_cached_screen_v1.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    assertions = [
        "cached_sources_present=" + str(all_cached).lower(),
        "row_materializable_candidates=0",
        "positive_rows_added=0",
        "matched_controls_added=0",
        "intake_unchanged=" + str(intake_unchanged).lower(),
        "external_requests_sent=false",
        "raw_data_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "gate_result=r6_arab_fny_tower_cached_screen_v1=cached_candidates_fail_closed_no_row_level_events",
    ]
    (CHECKS / "r6_arab_fny_tower_cached_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )

    if not all_cached or not no_rows_materialized or not intake_unchanged:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
