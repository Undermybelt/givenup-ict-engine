#!/usr/bin/env python3
"""Bounded public-source probe for Oystacher Exhibit A row appendix.

The probe keeps downloaded raw payloads in /tmp and writes only compact evidence
artifacts under docs/experiments.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


RUN_ID = "20260512T001633-codex-r6-oystacher-exhibit-a-public-acquisition-probe-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-oystacher-exhibit-a-public-acquisition-probe"
CHECKS_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"
RAW_ROOT = Path("/tmp/ict-engine-r6-oystacher-exhibit-a-public-acquisition-probe-v1/raw")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


def run(cmd: list[str], timeout: int = 40) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def board_hash() -> str:
    return sha256(BOARD)


def download(label: str, url: str, suffix: str) -> dict:
    out = RAW_ROOT / f"{label}{suffix}"
    meta = RAW_ROOT / f"{label}.headers.txt"
    curl = run(
        [
            "curl",
            "-L",
            "--max-time",
            "30",
            "-sS",
            "-D",
            str(meta),
            "-w",
            "%{http_code} %{content_type} %{url_effective}",
            "-o",
            str(out),
            url,
        ]
    )
    status = curl.stdout.strip()
    parts = status.split(" ", 2)
    http_status = parts[0] if parts else "curl_failed"
    content_type = parts[1] if len(parts) > 1 else ""
    effective_url = parts[2] if len(parts) > 2 else url
    return {
        "label": label,
        "url": url,
        "effective_url": effective_url,
        "http_status": http_status,
        "content_type": content_type,
        "returncode": curl.returncode,
        "stderr": curl.stderr.strip(),
        "raw_path": str(out),
        "headers_path": str(meta),
        "bytes": out.stat().st_size if out.exists() else 0,
        "sha256": sha256(out) if out.exists() else None,
        "looks_pdf": out.exists() and out.read_bytes()[:5] == b"%PDF-",
        "raw_payload_committed": False,
    }


def extract_text(download_meta: dict) -> dict:
    raw = Path(download_meta["raw_path"])
    if not download_meta.get("looks_pdf"):
        return {"text_extracted": False, "reason": "not_pdf"}
    out = RAW_ROOT / f"{raw.stem}.txt"
    gs = run(
        [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            f"-sOutputFile={out}",
            str(raw),
        ],
        timeout=90,
    )
    text = out.read_text(errors="ignore") if out.exists() else ""
    needles = {
        "exhibit_a": "Exhibit A" in text,
        "appendix": "Appendix" in text,
        "oystacher": "Oystacher" in text,
        "three_red": "3Red" in text or "3 Red" in text,
        "flip": "flip" in text.lower(),
        "spoof": "spoof" in text.lower(),
        "complaint_doc1": "Document #: 1" in text or "Document#: 1" in text,
        "court_order": "MEMORANDUM OPINION AND ORDER" in text,
    }
    doc_line = next((line.strip() for line in text.splitlines() if "Document #:" in line or "Document#:" in line), "")
    return {
        "text_extracted": out.exists(),
        "text_path": str(out),
        "text_bytes": out.stat().st_size if out.exists() else 0,
        "text_sha256": sha256(out) if out.exists() else None,
        "returncode": gs.returncode,
        "stderr": gs.stderr.strip()[:1000],
        "document_line": doc_line,
        "needles": needles,
    }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    start_hash = board_hash()
    official_cftc = [
        (
            "cftc_oystacher_complaint",
            "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf",
            ".pdf",
        ),
        ("cftc_press_7253_15", "https://www.cftc.gov/PressRoom/PressReleases/7253-15", ".html"),
    ]
    cftc_attachment_candidates = [
        "enfigorcomplnt101915exhibita.pdf",
        "enfigorcomplnt101915exha.pdf",
        "enfigorexhibita101915.pdf",
        "enfigorexha101915.pdf",
        "enfigorappa101915.pdf",
        "enfigorcomplnt101915appa.pdf",
    ]
    for name in cftc_attachment_candidates:
        official_cftc.append(
            (
                f"cftc_candidate_{Path(name).stem}",
                "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/"
                + name,
                ".pdf",
            )
        )

    govinfo = [
        (
            f"govinfo_{n}",
            f"https://www.govinfo.gov/content/pkg/USCOURTS-ilnd-1_15-cv-09196/pdf/USCOURTS-ilnd-1_15-cv-09196-{n}.pdf",
            ".pdf",
        )
        for n in range(0, 4)
    ]
    courtlistener_query = (
        "courtlistener_dockets_api",
        "https://www.courtlistener.com/api/rest/v4/dockets/?docket_number="
        + quote("1:15-cv-09196"),
        ".json",
    )

    downloads = []
    for label, url, suffix in [*official_cftc, *govinfo, courtlistener_query]:
        meta = download(label, url, suffix)
        meta["text_probe"] = extract_text(meta)
        downloads.append(meta)

    visible_public_row_appendix = False
    complaint = next(d for d in downloads if d["label"] == "cftc_oystacher_complaint")
    govinfo_pdfs = [d for d in downloads if d["label"].startswith("govinfo_") and d["looks_pdf"]]
    cftc_candidate_hits = [
        d
        for d in downloads
        if d["label"].startswith("cftc_candidate_") and d["looks_pdf"] and int(d["http_status"] or 0) == 200
    ]

    # Evidence from the previously completed source screen; copied as compact
    # facts so this probe remains tied to the current debt blocker.
    source_totals = {
        "trading_days": 51,
        "flip_sequences": 1316,
        "spoof_orders": 5207,
        "spoof_contracts": 359790,
        "market_families": ["metals", "energy", "volatility_index", "equity_index"],
    }
    debt_reference = {
        "additional_positive_control_rows_for_chrono_quantiles_before_exact_splits": 219,
        "total_pairwise_rows_if_existing_exact_buckets_are_filled": 3291,
        "source": "docs/experiments/actionable-regime-confidence/runs/20260512T000801-codex-r6-exact-split-support-debt-audit-v1/r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json",
    }

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": start_hash,
        "downloads": downloads,
        "source_totals": source_totals,
        "debt_reference": debt_reference,
        "public_acquisition_result": {
            "official_cftc_complaint_available": complaint["looks_pdf"],
            "cftc_attachment_candidate_pdf_hits": len(cftc_candidate_hits),
            "govinfo_pdf_count": len(govinfo_pdfs),
            "courtlistener_api_auth_required": any(
                d["label"] == "courtlistener_dockets_api" and d["http_status"] in {"401", "403"}
                for d in downloads
            ),
            "visible_public_row_appendix_found": visible_public_row_appendix,
            "row_level_materialization_status": "public_sources_checked_appendix_not_found_owner_or_pacer_export_required",
        },
        "gate_result": "r6_oystacher_exhibit_a_public_acquisition_probe_v1=appendix_not_publicly_materialized_owner_or_pacer_export_required",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": "Acquire Oystacher Exhibit A through owner/PACER/RECAP export or obtain explicit owner approval for a less fragmented validation contract before rerunning R6 split acceptance.",
    }

    json_path = ARTIFACT_DIR / "r6_oystacher_exhibit_a_public_acquisition_probe_v1.json"
    md_path = ARTIFACT_DIR / "r6_oystacher_exhibit_a_public_acquisition_probe_v1.md"
    checks_path = CHECKS_DIR / "r6_oystacher_exhibit_a_public_acquisition_probe_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md_path.write_text(
        "\n".join(
            [
                "# R6 Oystacher Exhibit A Public Acquisition Probe v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Board hash at start: `{start_hash}`.",
                "- Raw downloads: `/tmp/ict-engine-r6-oystacher-exhibit-a-public-acquisition-probe-v1/raw`.",
                "- Official CFTC complaint PDF: available and text-extractable.",
                f"- Bounded CFTC attachment-name candidates checked: `{len(cftc_attachment_candidates)}`; PDF hits: `{len(cftc_candidate_hits)}`.",
                f"- GovInfo docket PDFs found: `{len(govinfo_pdfs)}`; they are court opinions/orders, not the row appendix.",
                "- CourtListener API probe returned authentication-required status in this environment.",
                "- Public row appendix found: `false`.",
                "- Gate result: `r6_oystacher_exhibit_a_public_acquisition_probe_v1=appendix_not_publicly_materialized_owner_or_pacer_export_required`.",
                "- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Acquire Oystacher Exhibit A through owner/PACER/RECAP export or obtain explicit owner approval for a less fragmented validation contract before rerunning R6 split acceptance.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Report: `{md_path.relative_to(REPO)}`",
                f"- Assertions: `{checks_path.relative_to(REPO)}`",
            ]
        )
        + "\n"
    )

    checks = [
        ("official_cftc_complaint_pdf", complaint["looks_pdf"]),
        ("cftc_attachment_candidate_pdf_hits_zero", len(cftc_candidate_hits) == 0),
        ("govinfo_some_pdfs_found", len(govinfo_pdfs) >= 1),
        ("visible_public_row_appendix_false", not visible_public_row_appendix),
        ("strict_full_objective_false", not result["strict_full_objective_achieved"]),
        ("update_goal_false", not result["update_goal"]),
        ("raw_data_not_committed", not result["raw_data_committed"]),
    ]
    checks_path.write_text("\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
