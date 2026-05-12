#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T130457+0800-codex-spoofing-appendix-direct-case-inventory"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130457-codex-spoofing-appendix-direct-case-inventory"
OUT_DIR = RUN_ROOT / "direct-case-inventory"
CHECK_DIR = RUN_ROOT / "checks"
RAW_XLSX = Path("/private/tmp/ict-regime-spoofing-appendix-c/online_appendix_c.xlsx")

SOURCE_RECORD_URL = "https://zenodo.org/records/16629490"
SOURCE_FILE_URL = "https://zenodo.org/records/16629490/files/Online%20Appendix%20C.xlsx?download=1"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def col_idx(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        raise ValueError(cell_ref)
    value = 0
    for char in match.group(1):
        value = value * 26 + ord(char) - 64
    return value - 1


def xlsx_rows(path: Path) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(path) as z:
        shared_xml = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
        strings: list[str] = []
        for item in re.findall(r"<si>(.*?)</si>", shared_xml, flags=re.S):
            texts = re.findall(r"<t[^>]*>(.*?)</t>", item, flags=re.S)
            strings.append(html.unescape("".join(texts)))

        workbook_xml = z.read("xl/workbook.xml").decode("utf-8", errors="ignore")
        sheet_names = re.findall(r'<sheet name="([^"]+)"', workbook_xml)

        out: dict[str, list[list[str]]] = {}
        for sheet_number, sheet_name in enumerate(sheet_names, 1):
            sheet_xml = z.read(f"xl/worksheets/sheet{sheet_number}.xml").decode("utf-8", errors="ignore")
            rows: list[list[str]] = []
            max_col = 0
            for _, row_body in re.findall(r'<row[^>]*?r="(\d+)"[^>]*>(.*?)</row>', sheet_xml, flags=re.S):
                values: dict[int, str] = {}
                for cell_match in re.finditer(r'<c[^>]*?r="([A-Z]+\d+)"([^>]*)>(.*?)</c>', row_body, flags=re.S):
                    cell_ref, attrs, body = cell_match.groups()
                    idx = col_idx(cell_ref)
                    max_col = max(max_col, idx)
                    value_match = re.search(r"<v>(.*?)</v>", body, flags=re.S)
                    if not value_match:
                        value = ""
                    elif 't="s"' in attrs:
                        value = strings[int(value_match.group(1))]
                    else:
                        value = html.unescape(value_match.group(1))
                    values[idx] = value.strip()
                if values:
                    rows.append([values.get(i, "") for i in range(max_col + 1)])
            out[sheet_name] = rows
        return out


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return clean or "unnamed"


def variety_tags(row: dict[str, str]) -> list[str]:
    text = " ".join([
        row.get("spoofing_type", ""),
        row.get("note", ""),
        row.get("automated_features", ""),
    ]).lower()
    tags: list[str] = []
    if "layer" in text:
        tags.append("layering")
    if "single" in text:
        tags.append("single_spoof_order")
    if "flash" in text:
        tags.append("flash_spoofing")
    if "flipping" in text:
        tags.append("flipping")
    if "spread squeezing" in text:
        tags.append("spread_squeezing")
    if "iceberg" in text:
        tags.append("iceberg_context")
    if "algorithm" in row.get("algorithmic_manual", "").lower():
        tags.append("algorithmic")
    if "manual" in row.get("algorithmic_manual", "").lower():
        tags.append("manual")
    if not tags:
        tags.append("spoofing_case_unspecified_pattern")
    return sorted(set(tags))


def normalize_case_rows(workbook: dict[str, list[list[str]]]) -> list[dict[str, str]]:
    case_rows: list[dict[str, str]] = []
    for sheet_name in ["CFTC", "ICE Futures U.S.", "CME Group"]:
        rows = workbook.get(sheet_name, [])
        if len(rows) < 3:
            continue
        headers = [slug(value) for value in rows[1]]
        for row_index, values in enumerate(rows[2:], 1):
            if not any(values):
                continue
            raw = {headers[i] if i < len(headers) else f"col_{i}": values[i] if i < len(values) else "" for i in range(len(headers))}
            case_number = raw.get("case_number", "")
            if not case_number:
                continue
            normalized = {
                "case_inventory_id": f"spoofing-appendix-c-{slug(sheet_name)}-{row_index:04d}",
                "regulator": raw.get("regulator", sheet_name),
                "case_number": case_number,
                "year_order_notice": raw.get("year_order_notice", ""),
                "defendants": raw.get("defendants", ""),
                "relevant_period_days": raw.get("relevant_period_days", ""),
                "instrument": raw.get("instrument", ""),
                "market_category": raw.get("market_category", ""),
                "underlying_asset_or_commodity": raw.get("underlying_asset_commodity_delivery_month", ""),
                "spoof_count_text": raw.get("number_of_times_spoofed_in_relevant_period", ""),
                "algorithmic_manual": raw.get("algorithmic_manual", ""),
                "automated_features": raw.get("automated_features", ""),
                "spoofing_type": raw.get("spoofing_type", ""),
                "individual_coordinated": raw.get("individual_coordinated", ""),
                "same_correlated_market": raw.get("same_correlated_market", ""),
                "different_tags_accounts_mentioned": raw.get("different_tags_accounts_mentioned", ""),
                "monetary_penalty": raw.get("monetary_penalty", ""),
                "disgorgements": raw.get("disgorgements", ""),
                "note": raw.get("note", ""),
                "direct_label": "Manipulation",
                "direct_evidence_family": "regulator_spoofing_case_inventory",
                "positive_case_label": "spoofing_enforcement_case",
                "matched_negative_available": "false",
                "confidence_gate_eligible_now": "false",
            }
            normalized["variety_tags"] = ";".join(variety_tags(normalized))
            case_rows.append(normalized)
    return case_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def counter(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "") or "NA" for row in rows).items()))


def tag_counter(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for tag in row["variety_tags"].split(";"):
            counts[tag] += 1
    return dict(sorted(counts.items()))


def main() -> None:
    if not RAW_XLSX.exists():
        raise FileNotFoundError(f"missing raw xlsx: {RAW_XLSX}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    workbook = xlsx_rows(RAW_XLSX)
    case_rows = normalize_case_rows(workbook)
    csv_path = OUT_DIR / "spoofing_appendix_direct_case_inventory.csv"
    write_csv(csv_path, case_rows)

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "direct_manipulation_spoofing_case_inventory",
        "source": {
            "record_url": SOURCE_RECORD_URL,
            "file_url": SOURCE_FILE_URL,
            "raw_xlsx_path": str(RAW_XLSX),
            "raw_xlsx_sha256": sha256(RAW_XLSX),
            "raw_data_committed": False,
        },
        "inventory": {
            "csv": repo_rel(csv_path),
            "positive_case_rows": len(case_rows),
            "by_regulator": counter(case_rows, "regulator"),
            "by_market_category": counter(case_rows, "market_category"),
            "by_instrument": counter(case_rows, "instrument"),
            "variety_tags": tag_counter(case_rows),
        },
        "decision": {
            "direct_manipulation_positive_case_inventory_added": len(case_rows),
            "accepted_95_direct_gate_added": 0,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "direct_spoofing_case_inventory_attached_no_matched_negative_95_gate",
            "blockers": [
                "case inventory is positive direct enforcement evidence but has no matched negative rows",
                "rows are case-level, not replayable order-book event rows",
                "cannot compute chronological calibration/test Wilson95 without controls",
                "does not close quote-stuffing/order-book full variety coverage",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Use this as direct Manipulation provenance; acquire matched negative order-lifecycle/order-book rows before any 95 gate claim.",
    }
    json_path = OUT_DIR / "spoofing_appendix_direct_case_inventory.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    md = [
        "# Spoofing Appendix Direct Case Inventory",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Parsed positive direct spoofing case rows: `{len(case_rows)}`.",
        f"- By regulator: `{summary['inventory']['by_regulator']}`.",
        f"- Variety tags: `{summary['inventory']['variety_tags']}`.",
        "- Accepted 95 direct gate added: `0`.",
        "- Full objective achieved: `false`.",
        "",
        "## Boundary",
        "",
        "- This is direct regulator/enforcement case evidence for `Manipulation`, not an OHLCV proxy.",
        "- It is positive-only and case-level. There are no matched negative order-lifecycle rows, so no Wilson95 calibration gate is claimed.",
        "- Raw `.xlsx` remains under `/private/tmp`; only compact CSV/JSON/MD artifacts are committed under the run directory.",
        "",
        "## Sources",
        "",
        f"- Zenodo record: `{SOURCE_RECORD_URL}`",
        f"- Downloaded file: `{SOURCE_FILE_URL}`",
        "",
        "## Next",
        "",
        "Acquire matched negative order-lifecycle/order-book rows for spoofing/layering/quote-stuffing before any direct `Manipulation` 95 gate claim.",
    ]
    md_path = OUT_DIR / "spoofing_appendix_direct_case_inventory.md"
    md_path.write_text("\n".join(md) + "\n")

    assertions = {
        "run_id": RUN_ID,
        "positive_case_rows": len(case_rows),
        "accepted_95_direct_gate_added": 0,
        "full_objective_achieved": False,
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "assertion_status": "PASS" if case_rows else "FAIL",
    }
    assertions_path = CHECK_DIR / "spoofing_appendix_direct_case_inventory_assertions.out"
    assertions_path.write_text(json.dumps(assertions, indent=2, sort_keys=True) + "\n")
    if not case_rows:
        raise AssertionError("no direct spoofing cases parsed")


if __name__ == "__main__":
    main()
