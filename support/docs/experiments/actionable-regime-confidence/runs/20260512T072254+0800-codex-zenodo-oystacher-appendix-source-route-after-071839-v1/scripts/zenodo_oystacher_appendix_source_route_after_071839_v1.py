#!/usr/bin/env python3
"""Profile public Zenodo Oystacher/spoofing appendix candidates fail-closed."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1")
OUT = RUN_ROOT / "zenodo-oystacher-appendix-source-route-after-071839-v1"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"

QUERY = "Oystacher spoofing futures order book dataset"
ZENODO_API = "https://zenodo.org/api/records"
REQUIRED_FILENAMES = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}
REQUIRED_LABELS = {"Oystacher", "3Red", "CFTC", "COMEX", "NYMEX", "CFE", "CME"}


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def xml_text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def read_xlsx_cells(path: Path) -> dict:
    # The local Homebrew Python has a broken pyexpat linkage, so avoid XML
    # parser dependencies and extract a bounded workbook profile with regex.
    with zipfile.ZipFile(path) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            shared_xml = xml_text(zf.read("xl/sharedStrings.xml"))
            for si in re.findall(r"<si\b.*?</si>", shared_xml, flags=re.S):
                parts = re.findall(r"<t[^>]*>(.*?)</t>", si, flags=re.S)
                shared.append("".join(re.sub(r"<[^>]+>", "", p) for p in parts))

        workbook_xml = xml_text(zf.read("xl/workbook.xml"))
        rels_xml = xml_text(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rid: "xl/" + target.lstrip("/")
            for rid, target in re.findall(r'<Relationship[^>]+Id="([^"]+)"[^>]+Target="([^"]+)"', rels_xml)
        }
        sheets = []
        for attrs in re.findall(r"<sheet\b([^>]*)/>", workbook_xml):
            name_match = re.search(r'name="([^"]+)"', attrs)
            rel_match = re.search(r'r:id="([^"]+)"', attrs)
            if rel_match:
                sheets.append((name_match.group(1) if name_match else "sheet", rel_map.get(rel_match.group(1), "")))

        workbook_profile = {}
        for sheet_name, sheet_path in sheets:
            if not sheet_path or sheet_path not in zf.namelist():
                continue
            sheet_xml = xml_text(zf.read(sheet_path))
            rows = []
            nonempty = 0
            token_hits = {token: 0 for token in REQUIRED_LABELS}
            headers = []
            for row_xml in re.findall(r"<row\b.*?</row>", sheet_xml, flags=re.S):
                values = []
                for cell_xml in re.findall(r"<c\b.*?</c>", row_xml, flags=re.S):
                    value = ""
                    value_match = re.search(r"<v>(.*?)</v>", cell_xml, flags=re.S)
                    if value_match:
                        value = value_match.group(1)
                        if ' t="s"' in cell_xml:
                            try:
                                value = shared[int(value)]
                            except (ValueError, IndexError):
                                pass
                    inline_match = re.search(r"<is\b.*?</is>", cell_xml, flags=re.S)
                    if inline_match:
                        value = " ".join(re.findall(r"<t[^>]*>(.*?)</t>", inline_match.group(0), flags=re.S))
                    if value:
                        nonempty += 1
                    for token in token_hits:
                        if token.lower() in value.lower():
                            token_hits[token] += 1
                    values.append(value)
                if values and not headers:
                    headers = values
                if len(rows) < 20:
                    rows.append(values)
            workbook_profile[sheet_name] = {
                "sheet_path": sheet_path,
                "first_rows": rows,
                "headers": headers,
                "nonempty_cell_count": nonempty,
                "token_hits": token_hits,
            }
        return workbook_profile


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    url = f"{ZENODO_API}?{urllib.parse.urlencode({'q': QUERY, 'size': 10})}"
    search = fetch_json(url)
    (CMD / "zenodo_search_url.txt").write_text(url + "\n")
    (CMD / "zenodo_search_raw.json").write_text(json.dumps(search, indent=2, sort_keys=True) + "\n")

    candidates = []
    for hit in search.get("hits", {}).get("hits", []):
        title = hit.get("metadata", {}).get("title", "")
        description = re.sub(r"\s+", " ", hit.get("metadata", {}).get("description", "") or "")
        files = []
        required_name_hits = []
        downloaded_profiles = []
        for item in hit.get("files", []):
            key = item.get("key", "")
            links = item.get("links", {}) or {}
            files.append({"key": key, "size": item.get("size"), "links": links})
            if key in REQUIRED_FILENAMES:
                required_name_hits.append(key)
            if key.lower().endswith((".xlsx", ".xlsm")) and len(downloaded_profiles) < 3:
                file_url = links.get("self") or links.get("download")
                if file_url:
                    blob = fetch_bytes(file_url)
                    file_path = CMD / key.replace("/", "_")
                    file_path.write_bytes(blob)
                    downloaded_profiles.append({
                        "key": key,
                        "sha256": hashlib.sha256(blob).hexdigest(),
                        "bytes": len(blob),
                        "workbook_profile": read_xlsx_cells(file_path),
                    })
        text = " ".join([title, description, json.dumps(files, sort_keys=True)])
        candidates.append({
            "id": hit.get("id"),
            "doi": hit.get("doi"),
            "conceptdoi": hit.get("conceptdoi"),
            "url": hit.get("links", {}).get("html"),
            "title": title,
            "publication_date": hit.get("metadata", {}).get("publication_date"),
            "description_snippet": description[:500],
            "file_count": len(files),
            "files": files,
            "required_filename_hits": required_name_hits,
            "required_token_hits": {token: text.lower().count(token.lower()) for token in REQUIRED_LABELS},
            "downloaded_profiles": downloaded_profiles,
        })

    required_file_count = sum(len(c["required_filename_hits"]) for c in candidates)
    owner_export_unlock = False
    r6_control_unlock = False
    decision = {
        "run_id": "20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1",
        "query": QUERY,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "required_filename_hit_count": required_file_count,
        "r6_owner_export_unlock": owner_export_unlock,
        "r6_control_unlock": r6_control_unlock,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    (OUT / "zenodo_oystacher_appendix_source_route_after_071839_v1.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    with (OUT / "zenodo_oystacher_appendix_source_route_after_071839_v1.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "id",
                "doi",
                "url",
                "title",
                "publication_date",
                "file_count",
                "required_filename_hits",
                "downloaded_profile_count",
                "gate",
            ],
        )
        writer.writeheader()
        for c in candidates:
            writer.writerow({
                "id": c["id"],
                "doi": c["doi"],
                "url": c["url"],
                "title": c["title"],
                "publication_date": c["publication_date"],
                "file_count": c["file_count"],
                "required_filename_hits": ";".join(c["required_filename_hits"]),
                "downloaded_profile_count": len(c["downloaded_profiles"]),
                "gate": "no_required_owner_export_or_controls",
            })

    lines = [
        "gate_result=zenodo_oystacher_appendix_source_route_after_071839_v1=no_required_owner_export_controls_no_unlock",
        f"candidate_count={len(candidates)}",
        f"required_filename_hit_count={required_file_count}",
        "r6_owner_export_unlock=false",
        "r6_control_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECKS / "zenodo_oystacher_appendix_source_route_after_071839_v1_assertions.out").write_text("\n".join(lines) + "\n")

    report_lines = [
        "# Zenodo Oystacher Appendix Source Route After 071839 v1",
        "",
        "Run id: `20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1`",
        "",
        "Gate result: `zenodo_oystacher_appendix_source_route_after_071839_v1=no_required_owner_export_controls_no_unlock`",
        "",
        "## Scope",
        "",
        "Read-only public-source route probe for Oystacher/spoofing appendix candidates. This packet does not mutate R3/R5/R6 roots, approve academic/legal proxy rows, run direct verifier, run split calibration, run canonical merge, run provider/AutoQuant promotion, run downstream filter/Pre-Bayes/BBN/CatBoost/execution-tree, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Zenodo query: `{QUERY}`",
        f"- Candidates returned: `{len(candidates)}`.",
        f"- Required file-name hits: `{required_file_count}`.",
    ]
    for c in candidates[:5]:
        report_lines.append(f"- Candidate `{c['id']}`: `{c['title']}` ({c['url']}); files `{c['file_count']}`, downloaded workbook profiles `{len(c['downloaded_profiles'])}`.")
    report_lines.extend([
        "",
        "## Decision",
        "",
        "The probe may strengthen public-source route awareness, but it does not supply verifier-native R6 owner/export positive rows, matched normal controls, or provenance. It also does not supply source-owned post-2026-01-30 R5 `MainRegimeV2` rows or Crisis-capable native-subhour R3 labels.",
        "",
        "Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        "- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1/zenodo-oystacher-appendix-source-route-after-071839-v1/zenodo_oystacher_appendix_source_route_after_071839_v1.json`",
        "- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1/zenodo-oystacher-appendix-source-route-after-071839-v1/zenodo_oystacher_appendix_source_route_after_071839_v1.csv`",
        "- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1/checks/zenodo_oystacher_appendix_source_route_after_071839_v1_assertions.out`",
        "- Raw Zenodo search: `docs/experiments/actionable-regime-confidence/runs/20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1/command-output/zenodo_search_raw.json`",
        "",
        "## Next",
        "",
        "Continue only from explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export before downstream promotion.",
    ])
    (OUT / "zenodo_oystacher_appendix_source_route_after_071839_v1.md").write_text("\n".join(report_lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
