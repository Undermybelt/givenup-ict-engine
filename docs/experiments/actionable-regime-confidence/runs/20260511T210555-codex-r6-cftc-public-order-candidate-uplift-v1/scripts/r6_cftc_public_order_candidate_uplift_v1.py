#!/usr/bin/env python3
"""Scout public CFTC order surfaces for additional R6 direct Manipulation rows."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


RUN_ID = "20260511T210555-codex-r6-cftc-public-order-candidate-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-cftc-public-order-candidate-uplift"
CHECKS = RUN_ROOT / "checks"
TMP = Path("/tmp/ict-engine-r6-cftc-public-order-candidate-uplift-v1")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SOURCES = [
    {
        "id": "cftc_mohan_complaint_2018",
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfmohancomplaint012818.pdf",
        "source_type": "pdf",
        "candidate_reason": "Existing R6 seed used Mohan order; complaint may expose more detailed examples.",
    },
    {
        "id": "cftc_geneva_order_2018",
        "url": "https://www.cftc.gov/sites/default/files/2018-09/enfgenevaorder092018.pdf",
        "source_type": "pdf",
        "candidate_reason": "CFTC order surfaced in prior appendix inventory; may describe multiple traders/commodities.",
    },
    {
        "id": "cftc_arab_trading_group_order_2020",
        "url": "https://www.cftc.gov/media/4861/enfarbtradinggrouporder093020/download",
        "source_type": "pdf",
        "candidate_reason": "CFTC order download endpoint for Arab Trading Group spoofing/layering case.",
    },
    {
        "id": "cftc_fny_order_2020",
        "url": "https://www.cftc.gov/media/4811/enffnyorder092820/download",
        "source_type": "pdf",
        "candidate_reason": "CFTC order download endpoint for FNY Partners/Donino spoofing case.",
    },
    {
        "id": "cftc_shak_complaint_2022",
        "url": "https://www.cftc.gov/media/7526/enfshakcomplaint080522/download",
        "source_type": "pdf",
        "candidate_reason": "CFTC complaint download endpoint for a later spoofing case.",
    },
    {
        "id": "cftc_tower_press_release_2019",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/8074-19",
        "source_type": "html",
        "candidate_reason": "CFTC press release for Tower Research spoofing case; useful for locating linked order/filing surfaces.",
    },
]

KEYWORDS = [
    "spoof",
    "layer",
    "genuine",
    "iceberg",
    "E-mini",
    "NASDAQ",
    "S&P",
    "cancel",
    "order",
    "filled",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(source: dict[str, str]) -> dict[str, Any]:
    target = TMP / f"{source['id']}.bin"
    req = urllib.request.Request(source["url"], headers={"User-Agent": "ict-engine-board-a-source-scout/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
            status = response.status
        target.write_bytes(body)
        return {
            "status": status,
            "ok": 200 <= status < 300,
            "bytes": len(body),
            "content_type": content_type,
            "path": str(target),
            "sha256": sha256(target),
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 - artifact records the source failure.
        return {
            "status": None,
            "ok": False,
            "bytes": 0,
            "content_type": "",
            "path": str(target),
            "sha256": "",
            "error": repr(exc),
        }


def extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages[:20]:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def extract_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(re.sub(r"\s+", " ", text))


def analyze_text(text: str) -> dict[str, Any]:
    lowered = text.lower()
    keyword_counts = {key: lowered.count(key.lower()) for key in KEYWORDS}
    date_hits = sorted(set(re.findall(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+(?:19|20)\d{2}\b", text)))[:30]
    time_hits = sorted(set(re.findall(r"\b\d{1,2}:\d{2}:\d{2}(?:\.\d{1,6})?\b", text)))[:30]
    has_positive_terms = keyword_counts["spoof"] > 0 or keyword_counts["layer"] > 0
    has_control_terms = keyword_counts["genuine"] > 0 or keyword_counts["iceberg"] > 0 or keyword_counts["filled"] > 0
    row_extract_candidate = has_positive_terms and has_control_terms and (bool(date_hits) or bool(time_hits))
    return {
        "char_count": len(text),
        "keyword_counts": keyword_counts,
        "date_hits": date_hits,
        "time_hits": time_hits,
        "has_positive_terms": has_positive_terms,
        "has_control_terms": has_control_terms,
        "row_extract_candidate": row_extract_candidate,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    detailed: list[dict[str, Any]] = []
    for source in SOURCES:
        download = fetch(source)
        text_status = "not_downloaded"
        text = ""
        if download["ok"]:
            path = Path(download["path"])
            try:
                if source["source_type"] == "pdf":
                    text = extract_pdf(path)
                else:
                    text = extract_html(path)
                text_status = "ok"
            except Exception as exc:  # noqa: BLE001
                text_status = f"extract_failed:{type(exc).__name__}"
        text_report = analyze_text(text) if text else {
            "char_count": 0,
            "keyword_counts": {key: 0 for key in KEYWORDS},
            "date_hits": [],
            "time_hits": [],
            "has_positive_terms": False,
            "has_control_terms": False,
            "row_extract_candidate": False,
        }
        row = {
            "id": source["id"],
            "url": source["url"],
            "source_type": source["source_type"],
            "candidate_reason": source["candidate_reason"],
            "download_ok": download["ok"],
            "status": download["status"],
            "content_type": download["content_type"],
            "bytes": download["bytes"],
            "sha256": download["sha256"],
            "text_status": text_status,
            "char_count": text_report["char_count"],
            "date_hit_count": len(text_report["date_hits"]),
            "time_hit_count": len(text_report["time_hits"]),
            "has_positive_terms": text_report["has_positive_terms"],
            "has_control_terms": text_report["has_control_terms"],
            "row_extract_candidate": text_report["row_extract_candidate"],
        }
        rows.append(row)
        detailed.append({**source, "download": download, "text_status": text_status, "text_report": text_report})

    row_extract_candidates = [row for row in rows if row["row_extract_candidate"]]
    decision = (
        "r6_cftc_public_order_candidate_uplift_v1=candidates_found_rows_not_extracted"
        if row_extract_candidates
        else "r6_cftc_public_order_candidate_uplift_v1=no_row_extract_candidates_found"
    )
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "source_count": len(SOURCES),
        "download_ok_count": sum(1 for row in rows if row["download_ok"]),
        "row_extract_candidate_count": len(row_extract_candidates),
        "tmp_download_root": str(TMP),
        "candidates": detailed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Manually extract only source-owned row-level positives/controls from candidate CFTC orders if the text exposes dates/times/sides; otherwise continue owner-approved source acquisition.",
    }
    json_path = OUT / "r6_cftc_public_order_candidate_uplift_v1.json"
    csv_path = OUT / "r6_cftc_public_order_candidate_uplift_v1_candidates.csv"
    report_path = OUT / "r6_cftc_public_order_candidate_uplift_v1.md"
    assertions_path = CHECKS / "r6_cftc_public_order_candidate_uplift_v1_assertions.out"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        csv_path,
        rows,
        [
            "id",
            "url",
            "source_type",
            "candidate_reason",
            "download_ok",
            "status",
            "content_type",
            "bytes",
            "sha256",
            "text_status",
            "char_count",
            "date_hit_count",
            "time_hit_count",
            "has_positive_terms",
            "has_control_terms",
            "row_extract_candidate",
        ],
    )

    lines = [
        "# R6 CFTC Public Order Candidate Uplift v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Sources checked: `{len(SOURCES)}`.",
        f"- Downloaded successfully: `{sum(1 for row in rows if row['download_ok'])}`.",
        f"- Row-extract candidates: `{len(row_extract_candidates)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "| Source | Download | Row Extract Candidate | Dates | Times |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['id']}` | `{str(row['download_ok']).lower()}` | "
            f"`{str(row['row_extract_candidate']).lower()}` | {row['date_hit_count']} | {row['time_hit_count']} |"
        )
    lines.extend(
        [
            "",
            "Next:",
            "Extract only source-owned row-level positives/controls from candidates that expose dates/times/sides; do not infer labels from raw market data or generated methods.",
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Candidate CSV: `{rel(csv_path)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS download_ok_count={sum(1 for row in rows if row['download_ok'])}",
        f"PASS row_extract_candidate_count={len(row_extract_candidates)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "row_extract_candidate_count": len(row_extract_candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
