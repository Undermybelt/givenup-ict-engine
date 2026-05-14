#!/usr/bin/env python3
"""Scout official CFTC public surfaces for R6 direct-manipulation expansion.

This is deliberately acquisition-only: it does not promote public enforcement
writeups to accepted rows and it does not synthesize broad normal controls.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-official-cftc-expansion-scout"
CHECKS = RUN_ROOT / "checks"
TMP_RAW = Path("/tmp/ict-engine-r6-official-cftc-expansion-scout-v1/raw")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SOURCES = [
    {
        "source_id": "cftc_pr_8267_20_sunoco",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/8267-20",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Sunoco spoofing order press release",
    },
    {
        "source_id": "cftc_pr_8104_19_mirae",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/8104-19",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Mirae spoofing order press release",
    },
    {
        "source_id": "cftc_pr_7946_19_merrill",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7946-19",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Merrill Lynch spoofing order press release",
    },
    {
        "source_id": "cftc_pr_8259_20_donino",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/8259-20",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Michael Donino spoofing order press release",
    },
    {
        "source_id": "cftc_pr_7796_18_franko",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7796-18",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Michael Franko spoofing order press release",
    },
    {
        "source_id": "cftc_pr_8075_19_mitsubishi",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/8075-19",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Mitsubishi International spoofing order press release",
    },
    {
        "source_id": "cftc_pr_7818_18_bns",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7818-18",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Bank of Nova Scotia spoofing order press release",
    },
    {
        "source_id": "cftc_pr_7686_18_vorley_chanu",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7686-18",
        "owner": "CFTC",
        "source_kind": "press_release_html",
        "expected_surface": "Vorley and Chanu spoofing press release",
    },
    {
        "source_id": "cftc_pdf_tower_research_order_2019",
        "url": "https://www.cftc.gov/media/2986/enftowerresearchorder110619/download",
        "owner": "CFTC",
        "source_kind": "order_pdf",
        "expected_surface": "Tower Research spoofing order PDF",
    },
]

TERMS = [
    "spoof",
    "spoofing",
    "genuine order",
    "genuine orders",
    "layering",
    "E-mini",
    "NASDAQ",
    "CME",
    "COMEX",
    "NYMEX",
    "Treasury",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def board_hash() -> str:
    return sha256(BOARD.read_bytes())


def fetch(url: str) -> tuple[int | None, str, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ict-engine-board-a-public-source-scout/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type", "")
            body = response.read()
            return status, content_type, body, ""
    except urllib.error.HTTPError as exc:
        body = exc.read() if exc.fp else b""
        return exc.code, exc.headers.get("Content-Type", ""), body, str(exc)
    except Exception as exc:  # noqa: BLE001 - artifact should capture exact source failure.
        return None, "", b"", str(exc)


def html_to_text(body: bytes) -> str:
    text = body.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def text_signals(text: str) -> dict[str, str | int | bool]:
    lower = text.lower()
    counts = {term: lower.count(term.lower()) for term in TERMS}
    date_like = sorted(set(re.findall(r"\b(?:20\d{2}|19\d{2})\b", text)))[:12]
    return {
        "term_hits": ";".join(f"{term}={count}" for term, count in counts.items() if count),
        "spoof_hits": counts["spoof"] + counts["spoofing"],
        "genuine_order_hits": counts["genuine order"] + counts["genuine orders"],
        "official_positive_pattern": (counts["spoof"] + counts["spoofing"]) > 0,
        "public_genuine_order_pattern": (counts["genuine order"] + counts["genuine orders"]) > 0,
        "years_seen": ";".join(date_like),
    }


def classify(row: dict) -> tuple[str, str]:
    if not row["fetched"]:
        return "blocked_fetch_failed", "Official URL did not fetch in this environment."
    if row["source_kind"] == "order_pdf" and not row["text_extract_supported"]:
        return "candidate_pdf_needs_parser_or_manual_extract", "Official PDF fetched, but this environment lacks a PDF text extractor; no row-level fields were extracted."
    if row["official_positive_pattern"] and row["public_genuine_order_pattern"]:
        return "candidate_positive_and_genuine_pattern_not_row_ready", "Official text mentions spoofing and genuine-order language, but no same-schema row export was acquired."
    if row["official_positive_pattern"]:
        return "candidate_positive_only_not_row_ready", "Official text supports spoofing-positive provenance only; no matched normal-control rows were acquired."
    return "not_ready_no_relevant_row_surface", "No row-level positive/control intake surface was found."


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    TMP_RAW.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for source in SOURCES:
        status, content_type, body, error = fetch(source["url"])
        raw_path = TMP_RAW / f"{source['source_id']}.bin"
        if body:
            raw_path.write_bytes(body)
        is_html = "html" in content_type.lower()
        is_pdf = "pdf" in content_type.lower() or source["source_kind"].endswith("pdf")
        text = html_to_text(body) if is_html else ""
        signals = text_signals(text)
        row = {
            **source,
            "status": status or "",
            "content_type": content_type,
            "bytes": len(body),
            "sha256": sha256(body) if body else "",
            "raw_tmp_path": str(raw_path) if body else "",
            "error": error,
            "fetched": bool(body) and not error,
            "text_extract_supported": is_html and not is_pdf,
            "text_excerpt": text[:240],
            "row_level_timestamped_export_acquired": False,
            "same_schema_positive_rows_added": 0,
            "same_schema_normal_controls_added": 0,
            "provenance_manifest_updated": False,
            "accepted_now": False,
            **signals,
        }
        decision, reason = classify(row)
        row["decision"] = decision
        row["reason"] = reason
        rows.append(row)

    candidate_count = sum(1 for row in rows if row["decision"].startswith("candidate_"))
    ready_row_sources = sum(1 for row in rows if row["row_level_timestamped_export_acquired"])
    fetched_count = sum(1 for row in rows if row["fetched"])
    positive_pattern_count = sum(1 for row in rows if row["official_positive_pattern"])
    genuine_pattern_count = sum(1 for row in rows if row["public_genuine_order_pattern"])
    board_hash_before = board_hash()

    fields = [
        "source_id",
        "owner",
        "source_kind",
        "url",
        "status",
        "content_type",
        "bytes",
        "sha256",
        "fetched",
        "text_extract_supported",
        "official_positive_pattern",
        "public_genuine_order_pattern",
        "term_hits",
        "years_seen",
        "row_level_timestamped_export_acquired",
        "same_schema_positive_rows_added",
        "same_schema_normal_controls_added",
        "decision",
        "reason",
    ]
    write_csv(OUT / "r6_official_cftc_expansion_scout_v1_sources.csv", rows, fields)

    artifact = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": board_hash_before,
        "decision": "r6_official_cftc_expansion_scout_v1=official_candidates_found_rows_not_acquired",
        "official_sources_checked": len(rows),
        "fetched_sources": fetched_count,
        "candidate_sources": candidate_count,
        "positive_pattern_sources": positive_pattern_count,
        "genuine_order_pattern_sources": genuine_pattern_count,
        "ready_row_sources": ready_row_sources,
        "same_schema_positive_rows_added": 0,
        "same_schema_normal_controls_added": 0,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "raw_download_root_tmp": str(TMP_RAW),
        "operator_boundary": "Official CFTC public surfaces are candidate provenance/request targets only unless row-level same-schema positives, normal controls, and provenance are acquired.",
        "next_action": "Use candidate official CFTC surfaces only as request/extraction targets; do not promote them until same-schema rows plus chronological and heldout Wilson95 calibration pass.",
        "sources": rows,
    }
    (OUT / "r6_official_cftc_expansion_scout_v1.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = [
        "# R6 Official CFTC Expansion Scout v1",
        "",
        f"Decision: `{artifact['decision']}`.",
        "",
        "Result:",
        f"- Official CFTC surfaces checked: `{len(rows)}`; fetched: `{fetched_count}`.",
        f"- Candidate official surfaces: `{candidate_count}`.",
        f"- Positive-pattern surfaces: `{positive_pattern_count}`; genuine-order-pattern surfaces: `{genuine_pattern_count}`.",
        "- Same-schema rows added: `0`; accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Boundary:",
        "- Raw fetched public pages/PDFs are stored under `/tmp/ict-engine-r6-official-cftc-expansion-scout-v1/raw`.",
        "- This scout does not convert press-release prose or PDFs into accepted rows.",
        "- Candidate sources still need same-schema positive/control rows and chronological plus heldout Wilson95 calibration.",
        "",
        "Artifacts:",
        f"- JSON: `{OUT / 'r6_official_cftc_expansion_scout_v1.json'}`",
        f"- Source CSV: `{OUT / 'r6_official_cftc_expansion_scout_v1_sources.csv'}`",
        f"- Assertions: `{CHECKS / 'r6_official_cftc_expansion_scout_v1_assertions.out'}`",
        "",
    ]
    (OUT / "r6_official_cftc_expansion_scout_v1.md").write_text("\n".join(report), encoding="utf-8")

    assertions = [
        f"PASS decision={artifact['decision']}",
        f"PASS official_sources_checked={len(rows)}",
        f"PASS candidate_sources={candidate_count}",
        "PASS same_schema_positive_rows_added=0",
        "PASS same_schema_normal_controls_added=0",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "r6_official_cftc_expansion_scout_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
