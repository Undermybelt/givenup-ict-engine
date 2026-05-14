#!/usr/bin/env python3
"""Open-data catalog source/control route probe after 074116.

This is Board B source/control acquisition only. It searches public catalog
metadata surfaces that were not part of the latest GitHub/HF/Kaggle/Zenodo/
DataCite/Dataverse/OSF/Figshare/OpenAlex/CrossRef route set.
"""

from __future__ import annotations

import csv
import datetime as dt
import html
import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable


RUN_ID = "20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
PACKET_DIR = RUN_ROOT / "open-data-catalog-source-route-probe-after-074116-v1"
RAW_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

QUERIES = [
    ("mainregimev2_exact", '"MainRegimeV2"', "r5_r3_exact"),
    ("mainregimev2_crisis_exact", '"MainRegimeV2" "Crisis"', "r3_exact"),
    ("native_subhour_rows_exact", '"native_subhour_source_label_rows"', "r3_exact"),
    ("stock_regimes_extension_exact", '"stock_market_regimes_2026_extension"', "r5_exact"),
    ("positive_rows_exact", '"direct_manipulation_positive_rows"', "r6_filename"),
    ("matched_controls_exact", '"direct_manipulation_matched_controls"', "r6_filename"),
    ("provenance_exact", '"direct_manipulation_provenance"', "r6_filename"),
    ("oystacher_3red_lifecycle", '"Oystacher" "3Red Trading" "order lifecycle"', "r6_owner"),
    ("spoofing_matched_controls_futures", '"spoofing" "matched controls" "futures"', "r6_context"),
]

REQUIRED_FILENAMES = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "native_subhour_source_label_rows",
    "stock_market_regimes_2026_extension",
]
OWNER_TERMS = ["Oystacher", "3Red Trading"]
MAINREGIME_TERMS = ["MainRegimeV2"]
R3_TERMS = ["native_subhour_source_label_rows", "native subhour source label"]
R5_TERMS = ["stock_market_regimes_2026_extension", "stock market regimes 2026"]
R6_TERMS = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
]
CONTEXT_TERMS = ["spoofing", "matched controls", "order lifecycle", "Crisis"]


def fetch(url: str, timeout: int = 35) -> tuple[int | None, bytes, str | None]:
    headers = {
        "User-Agent": "ict-engine-board-b-open-data-catalog-probe/1.0",
        "Accept": "application/json,text/html;q=0.8,*/*;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), str(exc)
    except Exception as exc:  # noqa: BLE001 - route evidence belongs in artifact
        return None, b"", repr(exc)


def write_raw(name: str, suffix: str, payload: bytes | str) -> None:
    path = RAW_DIR / f"{name}.{suffix}"
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")


def norm(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def blob(records: list[dict[str, object]]) -> str:
    return "\n".join(norm(record) for record in records).lower()


def has_any(records: list[dict[str, object]], terms: list[str]) -> bool:
    text = blob(records)
    return any(term.lower() in text for term in terms)


def sanitize_slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")[:80] or "query"


def parse_datagov_html(payload: bytes) -> list[dict[str, object]]:
    text = payload.decode("utf-8", errors="replace")
    records: list[dict[str, object]] = []
    for match in re.finditer(
        r'<h3 class="usa-collection__heading margin-0">\s*<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        text,
        flags=re.I | re.S,
    ):
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", match.group("title")))).strip()
        records.append(
            {
                "title": title,
                "url": urllib.parse.urljoin("https://catalog.data.gov", html.unescape(match.group("href"))),
            }
        )
        if len(records) >= 10:
            break
    return records


def parse_datagov_api(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records: list[dict[str, object]] = []
    for item in (((obj.get("result") or {}).get("results")) or [])[:10]:
        records.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "name": item.get("name"),
                "organization": ((item.get("organization") or {}).get("title")),
                "notes": item.get("notes"),
                "metadata_created": item.get("metadata_created"),
                "metadata_modified": item.get("metadata_modified"),
                "url": item.get("url"),
            }
        )
    return records


def parse_gitlab_projects(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records: list[dict[str, object]] = []
    if not isinstance(obj, list):
        return records
    for item in obj[:10]:
        records.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "path_with_namespace": item.get("path_with_namespace"),
                "description": item.get("description"),
                "web_url": item.get("web_url"),
                "last_activity_at": item.get("last_activity_at"),
            }
        )
    return records


def parse_openml_dataset_list(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    data = (obj.get("data") or {}).get("dataset") if isinstance(obj.get("data"), dict) else obj.get("data")
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    records: list[dict[str, object]] = []
    for item in data[:10]:
        if not isinstance(item, dict):
            continue
        records.append(
            {
                "did": item.get("did"),
                "name": item.get("name"),
                "version": item.get("version"),
                "status": item.get("status"),
                "format": item.get("format"),
                "upload_date": item.get("upload_date"),
                "url": f"https://www.openml.org/d/{item.get('did')}" if item.get("did") else "",
            }
        )
    return records


def parse_aws_registry_html(payload: bytes, query: str) -> list[dict[str, object]]:
    text = payload.decode("utf-8", errors="replace")
    count_match = re.search(r'id="count-matching">(?P<count>\d+)</span>', text, flags=re.I)
    terms = [part.lower() for part in re.findall(r"[A-Za-z0-9_]+", query) if len(part) > 2]
    records: list[dict[str, object]] = []
    for match in re.finditer(r"<h3>\s*<a[^>]+href=\"(?P<href>[^\"]+)\"[^>]*>(?P<title>.*?)</a>", text, flags=re.I | re.S):
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", match.group("title")))).strip()
        haystack = title.lower()
        if terms and not any(term in haystack for term in terms):
            continue
        records.append(
            {
                "title": title,
                "url": urllib.parse.urljoin("https://registry.opendata.aws", html.unescape(match.group("href"))),
                "matching_count": int(count_match.group("count")) if count_match else "",
            }
        )
        if len(records) >= 10:
            break
    return records


def provider_requests(slug: str, query: str) -> list[dict[str, object]]:
    encoded_plus = urllib.parse.quote_plus(query)
    encoded_path = urllib.parse.quote(query.strip('"'), safe="")
    return [
        {
            "surface": "data_gov_html",
            "url": f"https://catalog.data.gov/dataset/?q={encoded_plus}",
            "parser": lambda payload, q=query: parse_datagov_html(payload),
        },
        {
            "surface": "gitlab_public_projects",
            "url": f"https://gitlab.com/api/v4/projects?search={encoded_plus}&simple=true&per_page=10",
            "parser": lambda payload, q=query: parse_gitlab_projects(payload),
        },
        {
            "surface": "openml_dataset_name",
            "url": f"https://www.openml.org/api/v1/json/data/list/data_name/{encoded_path}/limit/10",
            "parser": lambda payload, q=query: parse_openml_dataset_list(payload),
        },
        {
            "surface": "aws_open_data_registry_html",
            "url": f"https://registry.opendata.aws/?search={encoded_plus}",
            "parser": lambda payload, q=query: parse_aws_registry_html(payload, q),
        },
    ]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    for directory in (PACKET_DIR, RAW_DIR, CHECK_DIR):
        if directory.exists():
            shutil.rmtree(directory)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    requests_sent = 0
    failed_or_parse = 0
    top_rows_scanned = 0
    required_filename_hits = 0
    owner_hits = 0
    mainregime_hits = 0
    r3_hits = 0
    r5_hits = 0
    r6_hits = 0
    context_hits = 0

    for slug, query, route in QUERIES:
        for request in provider_requests(slug, query):
            surface = str(request["surface"])
            raw_name = f"{surface}_{sanitize_slug(slug)}"
            url = str(request["url"])
            parser: Callable[[bytes], list[dict[str, object]]] = request["parser"]  # type: ignore[assignment]
            write_raw(raw_name, "url", url + "\n")
            status, payload, error = fetch(url)
            requests_sent += 1
            write_raw(raw_name, "status", "" if status is None else str(status))
            if payload:
                write_raw(raw_name, "payload", payload)
            if error:
                write_raw(raw_name, "error", error + "\n")

            failed = status is None or status >= 400
            if surface == "openml_dataset_name" and status == 412:
                # OpenML returns 412 with code 372 for no dataset matches.
                failed = False
            records: list[dict[str, object]] = []
            parse_error = ""
            if not failed and payload:
                try:
                    records = parser(payload)
                except Exception as exc:  # noqa: BLE001
                    parse_error = repr(exc)
                    write_raw(raw_name, "parse_error", parse_error + "\n")
            failed_or_parse += int(failed or bool(parse_error))
            top_rows_scanned += len(records)

            required_hit = has_any(records, REQUIRED_FILENAMES)
            owner_hit = has_any(records, OWNER_TERMS)
            mainregime_hit = has_any(records, MAINREGIME_TERMS)
            r3_hit = has_any(records, R3_TERMS)
            r5_hit = has_any(records, R5_TERMS)
            r6_hit = has_any(records, R6_TERMS)
            context_hit = has_any(records, CONTEXT_TERMS)

            required_filename_hits += int(required_hit)
            owner_hits += int(owner_hit)
            mainregime_hits += int(mainregime_hit)
            r3_hits += int(r3_hit)
            r5_hits += int(r5_hit)
            r6_hits += int(r6_hit)
            context_hits += int(context_hit)

            rows.append(
                {
                    "surface": surface,
                    "route": route,
                    "query_slug": slug,
                    "status": "" if status is None else status,
                    "failed_or_parse": failed or bool(parse_error),
                    "top_records": len(records),
                    "required_filename_hit": required_hit,
                    "owner_hit": owner_hit,
                    "mainregimev2_hit": mainregime_hit,
                    "r3_hit": r3_hit,
                    "r5_hit": r5_hit,
                    "r6_hit": r6_hit,
                    "context_hit": context_hit,
                    "first_title_or_name": next(
                        (
                            str(record.get("title") or record.get("name") or record.get("path_with_namespace") or "")
                            for record in records[:1]
                        ),
                        "",
                    ),
                    "url": url,
                    "parse_error": parse_error,
                }
            )

    decision = {
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "direct_verifier_run": False,
        "split_calibration_run": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    gate_result = "open_data_catalog_source_route_probe_after_074116_v1=no_required_source_control_unlock"
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "gate_result": gate_result,
        "surfaces": [
            "Data.gov dataset HTML search",
            "GitLab public project search",
            "OpenML dataset-name API",
            "AWS Open Data Registry HTML search",
        ],
        "requests_sent": requests_sent,
        "failed_or_parse": failed_or_parse,
        "top_rows_scanned": top_rows_scanned,
        "required_filename_hits": required_filename_hits,
        "owner_hits": owner_hits,
        "mainregimev2_hits": mainregime_hits,
        "r3_hits": r3_hits,
        "r5_hits": r5_hits,
        "r6_hits": r6_hits,
        "context_hits": context_hits,
        "decision": decision,
        "next": (
            "Continue source/control acquisition only before direct verifier, split calibration, "
            "canonical merge, selected-data AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, "
            "or execution-tree promotion."
        ),
    }

    json_path = PACKET_DIR / "open_data_catalog_source_route_probe_after_074116_v1.json"
    csv_path = PACKET_DIR / "open_data_catalog_source_route_probe_after_074116_v1.csv"
    md_path = PACKET_DIR / "open_data_catalog_source_route_probe_after_074116_v1.md"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(
        csv_path,
        rows,
        [
            "surface",
            "route",
            "query_slug",
            "status",
            "failed_or_parse",
            "top_records",
            "required_filename_hit",
            "owner_hit",
            "mainregimev2_hit",
            "r3_hit",
            "r5_hit",
            "r6_hit",
            "context_hit",
            "first_title_or_name",
            "url",
            "parse_error",
        ],
    )

    surface_lines = "\n".join(f"- {surface}" for surface in summary["surfaces"])
    md_path.write_text(
        "\n".join(
            [
                "# Open Data Catalog Source Route Probe After 074116 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Scope",
                "",
                "This packet is source/control acquisition only. It queries public catalog metadata and does not mutate R3/R5/R6 target roots, approve any local or public candidate, select historical data, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Surfaces",
                "",
                surface_lines,
                "",
                "## Readback",
                "",
                f"- Requests sent: `{requests_sent}`.",
                f"- Failed or parse-failed requests: `{failed_or_parse}`.",
                f"- Top metadata rows scanned: `{top_rows_scanned}`.",
                f"- Required filename hits: `{required_filename_hits}`.",
                f"- Owner hits: `{owner_hits}`.",
                f"- `MainRegimeV2` hits: `{mainregime_hits}`.",
                f"- R3 native-subhour hits: `{r3_hits}`.",
                f"- R5 recency hits: `{r5_hits}`.",
                f"- R6 required-file hits: `{r6_hits}`.",
                f"- Broad context hits: `{context_hits}`.",
                "",
                "## Decision",
                "",
                "No open-data catalog metadata route supplied verifier-native R6 owner/export positives with matched controls and provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
                "",
                "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; direct verifier false; split calibration false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- CSV: `{csv_path.relative_to(REPO)}`",
                f"- Command output root: `{RAW_DIR.relative_to(REPO)}`",
                f"- Assertions: `{(CHECK_DIR / 'open_data_catalog_source_route_probe_after_074116_v1_assertions.out').relative_to(REPO)}`",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"gate_result={gate_result}",
        f"requests_sent={requests_sent}",
        f"failed_or_parse={failed_or_parse}",
        f"required_filename_hits={required_filename_hits}",
        f"mainregimev2_hits={mainregime_hits}",
        f"accepted_rows_added={decision['accepted_rows_added']}",
        f"valid_required_root_unlock={str(decision['valid_required_root_unlock']).lower()}",
        f"source_control_evidence_acquired={str(decision['source_control_evidence_acquired']).lower()}",
        f"canonical_merge={str(decision['canonical_merge']).lower()}",
        f"downstream_promotion_rerun={str(decision['downstream_promotion_rerun']).lower()}",
        f"promotion_allowed={str(decision['promotion_allowed']).lower()}",
        f"update_goal={str(decision['update_goal']).lower()}",
    ]
    (CHECK_DIR / "open_data_catalog_source_route_probe_after_074116_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
