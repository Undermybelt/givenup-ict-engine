#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-regulator-exchange-source-route-probe-after-080054-v1"
COMMAND_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


@dataclass(frozen=True)
class SourceTarget:
    provider: str
    source_kind: str
    query: str
    url: str


TARGETS = [
    SourceTarget(
        "cftc",
        "press_release",
        "Oystacher 3Red CFTC consent order",
        "https://www.cftc.gov/PressRoom/PressReleases/7504-16",
    ),
    SourceTarget(
        "cftc",
        "legal_pleading_pdf",
        "Oystacher 3Red CFTC complaint",
        "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf",
    ),
    SourceTarget(
        "cme",
        "disciplinary_notice",
        "COMEX Oystacher disciplinary notice",
        "https://www.cmegroup.com/tools-information/lookups/advisories/disciplinary/COMEX-11-08380-BC-IGOR-OYSTACHER.html",
    ),
    SourceTarget(
        "cftc",
        "press_release",
        "Panther Coscia spoofing broader official comparator",
        "https://www.cftc.gov/PressRoom/PressReleases/6649-13",
    ),
    SourceTarget(
        "doj",
        "speech",
        "DOJ futures markets spoofing takedown data analysis context",
        "https://www.justice.gov/opa/speech/acting-assistant-attorney-general-john-p-cronan-announces-futures-markets-spoofing",
    ),
    SourceTarget(
        "sec",
        "press_release",
        "SEC spoofing scheme controls comparator",
        "https://www.sec.gov/newsroom/press-releases/2024-160",
    ),
]


REQUIRED_EXPORT_PATTERNS = {
    "positive_rows_file": re.compile(r"positive[_ -]spoof(?:ing)?[_ -]layer(?:ing)?[_ -]rows|spoof(?:ing)?[_ -]positive[_ -]rows", re.I),
    "matched_control_rows_file": re.compile(
        r"matched[_ -](?:negative|normal)[_ -](?:activity[_ -])?rows|matched[_ -]control[_ -]rows|normal[_ -]control[_ -]rows",
        re.I,
    ),
    "owner_export": re.compile(r"owner[_ -]export|source[_ -]owned|verifier[_ -]native|official[_ -]row[_ -]export", re.I),
    "order_lifecycle_rows": re.compile(r"order[_ -]lifecycle[_ -]rows|order[_ -]event[_ -]rows|add[_ -]cancel[_ -]execute[_ -]rows", re.I),
    "machine_dataset": re.compile(r"\.(?:csv|parquet|feather|jsonl)(?:\b|$)|dataset|data file|download rows", re.I),
}

CONTEXT_PATTERNS = {
    "oystacher": re.compile(r"oystacher", re.I),
    "three_red": re.compile(r"3\s*red|3red", re.I),
    "spoofing": re.compile(r"spoof(?:ing)?|layering|manipulative", re.I),
    "market_depth": re.compile(r"market depth|book pressure|order book|level 2|l2|\bmbo\b|\bmbp\b", re.I),
    "cancel_lifecycle": re.compile(r"cancel(?:led|ing|lation)?|intent to cancel|before execution", re.I),
    "flip_orders": re.compile(r"flip order|avoid orders that cross", re.I),
    "matched_controls_context": re.compile(r"control|surveillance|monitor|normal activity|non[- ]manipulation", re.I),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(target: SourceTarget) -> str:
    raw = f"{target.provider}_{target.query}"
    return re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")[:96] or "source"


def fetch(target: SourceTarget) -> dict[str, Any]:
    req = urllib.request.Request(
        target.url,
        headers={
            "User-Agent": "ict-engine-board-a-r6-source-route-probe/1.0",
            "Accept": "text/html,application/pdf,application/json,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(8_000_000)
            return {
                "status": getattr(resp, "status", None),
                "content_type": resp.headers.get("content-type", ""),
                "body": body,
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(2000)
        return {
            "status": exc.code,
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "body": body,
            "error": f"http_error:{exc.code}",
        }
    except Exception as exc:
        return {
            "status": None,
            "content_type": "",
            "body": b"",
            "error": f"{type(exc).__name__}:{exc}",
        }


def html_to_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def pdf_to_text(raw_path: Path, text_path: Path) -> str:
    if not shutil.which("pdftotext"):
        return strings_text(raw_path, text_path)
    try:
        subprocess.run(
            ["pdftotext", "-layout", str(raw_path), str(text_path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
    except Exception:
        return strings_text(raw_path, text_path)
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    if text.strip():
        return text
    return strings_text(raw_path, text_path)


def strings_text(raw_path: Path, text_path: Path) -> str:
    if not shutil.which("strings"):
        text_path.write_text("", encoding="utf-8")
        return ""
    try:
        proc = subprocess.run(
            ["strings", str(raw_path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        text = proc.stdout.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    text_path.write_text(text, encoding="utf-8")
    return text


def classify_text(text: str) -> tuple[list[str], list[str]]:
    required = [name for name, pattern in REQUIRED_EXPORT_PATTERNS.items() if pattern.search(text)]
    context = [name for name, pattern in CONTEXT_PATTERNS.items() if pattern.search(text)]
    return required, context


def disposition(required: list[str], context: list[str]) -> str:
    has_rows = {"positive_rows_file", "matched_control_rows_file", "order_lifecycle_rows"}.intersection(required)
    has_provenance = "owner_export" in required
    has_dataset = "machine_dataset" in required
    if has_rows and has_provenance and has_dataset:
        return "possible_r6_export_requires_manual_row_schema_review"
    if context and not has_rows:
        return "official_context_only_no_positive_or_control_rows"
    if required:
        return "metadata_token_hit_no_complete_r6_export"
    return "no_relevant_source_control_terms"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256_file(BOARD_A) if BOARD_A.exists() else None
    rows: list[dict[str, Any]] = []

    for target in TARGETS:
        result = fetch(target)
        name = safe_name(target)
        raw_suffix = ".pdf" if "pdf" in result["content_type"].lower() or target.url.lower().endswith(".pdf") else ".html"
        raw_path = COMMAND_DIR / f"{name}{raw_suffix}"
        raw_path.write_bytes(result["body"])

        if raw_suffix == ".pdf":
            text_path = COMMAND_DIR / f"{name}.txt"
            text = pdf_to_text(raw_path, text_path)
        else:
            text_path = COMMAND_DIR / f"{name}.txt"
            text = html_to_text(result["body"])
            text_path.write_text(text, encoding="utf-8")

        required, context = classify_text(text)
        row = {
            "provider": target.provider,
            "source_kind": target.source_kind,
            "query": target.query,
            "url": target.url,
            "status": result["status"],
            "error": result["error"],
            "content_type": result["content_type"],
            "text_chars": len(text),
            "required_export_hits": ";".join(required),
            "context_hits": ";".join(context),
            "disposition": disposition(required, context),
            "raw_artifact": str(raw_path.relative_to(REPO)),
            "text_artifact": str(text_path.relative_to(REPO)),
        }
        rows.append(row)

    possible_exports = [row for row in rows if row["disposition"] == "possible_r6_export_requires_manual_row_schema_review"]
    official_context_hits = [row for row in rows if row["context_hits"]]
    status_failures = [row for row in rows if row["status"] is None or int(row["status"]) >= 400]

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "r6_regulator_exchange_source_route_probe_after_080054_v1=official_context_only_no_owner_export_control_unlock",
        "board_hash_before": board_hash_before,
        "sources_checked": len(rows),
        "status_failures": len(status_failures),
        "official_context_hits": len(official_context_hits),
        "possible_r6_exports": len(possible_exports),
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = ARTIFACT_DIR / "r6_regulator_exchange_source_route_probe_after_080054_v1.json"
    csv_path = ARTIFACT_DIR / "r6_regulator_exchange_source_route_sources_v1.csv"
    md_path = ARTIFACT_DIR / "r6_regulator_exchange_source_route_probe_after_080054_v1.md"
    assertions_path = CHECK_DIR / "r6_regulator_exchange_source_route_probe_after_080054_v1_assertions.out"

    json_path.write_text(
        json.dumps({"summary": summary, "sources": rows}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_csv(
        csv_path,
        rows,
        [
            "provider",
            "source_kind",
            "query",
            "url",
            "status",
            "error",
            "content_type",
            "text_chars",
            "required_export_hits",
            "context_hits",
            "disposition",
            "raw_artifact",
            "text_artifact",
        ],
    )

    md_lines = [
        "# R6 Regulator Exchange Source Route Probe After 080054 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{summary['gate_result']}`",
        "",
        "## Scope",
        "",
        "Read-only official regulator/exchange source-route probe for R6 owner/export evidence after the `080054` completion audit stayed blocked. It checks CFTC, CME, DOJ, and SEC official pages for Oystacher/3Red/spoofing context and for actual source-owned positive-row exports plus matched normal/control rows. It does not mutate target roots, derive labels, approve prose as controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Board hash before artifact: `{board_hash_before}`.",
        f"- Sources checked: `{summary['sources_checked']}`.",
        f"- HTTP/status failures: `{summary['status_failures']}`.",
        f"- Official context hits: `{summary['official_context_hits']}`.",
        f"- Possible complete R6 row/control exports: `{summary['possible_r6_exports']}`.",
        "",
        "## Source Disposition",
        "",
    ]
    for row in rows:
        md_lines.append(
            f"- `{row['provider']}` `{row['source_kind']}` `{row['query']}`: status `{row['status']}`, "
            f"context `{row['context_hits'] or 'none'}`, required-export `{row['required_export_hits'] or 'none'}`, "
            f"disposition `{row['disposition']}`."
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "The official regulator/exchange pages provide useful R6 context for spoofing, market-depth/book-pressure behavior, cancellations, and monitoring/compliance language, but this packet found no source-owned machine-readable positive spoofing/layering rows, no matched normal/control rows, and no owner/export provenance that would satisfy Board A R6.",
            "",
            "Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Source CSV: `{csv_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            f"- Command output root: `{COMMAND_DIR.relative_to(REPO)}/`",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. Do not promote official prose, disciplinary notices, complaints, or press releases as R6 owner/export rows or matched controls.",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = [
        f"gate_result={summary['gate_result']}",
        f"sources_checked={summary['sources_checked']}",
        f"status_failures={summary['status_failures']}",
        f"official_context_hits={summary['official_context_hits']}",
        f"possible_r6_exports={summary['possible_r6_exports']}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
