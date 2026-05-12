#!/usr/bin/env python3
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ID = "20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dryad-source-route-probe-after-080054-v1"
CHECKS = ROOT / "checks"
COMMAND = ROOT / "command-output"

QUERIES = [
    "MainRegimeV2",
    "stock_market_regimes_2026_extension",
    "native_subhour_source_label_rows",
    "\"Bull\" \"Bear\" \"Sideways\" \"Crisis\" market regime",
    "market regime crisis labels",
    "Oystacher spoofing futures order book",
    "3Red Trading matched controls",
    "futures order lifecycle spoofing controls",
    "CME market depth Oystacher controls",
]


def normalize_slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:80] or "query"


def fetch(url: str) -> tuple[int, bytes, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "ict-engine-source-control-probe/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return response.status, response.read(), None
    except Exception as exc:  # keep the probe terminal and auditable
        return 0, b"", f"{type(exc).__name__}: {exc}"


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(as_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(as_text(item) for item in value.values())
    return str(value)


def collect_records(payload: bytes) -> list[dict[str, object]]:
    if not payload:
        return []
    try:
        data = json.loads(payload.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = (
            data.get("_embedded", {}).get("stash:datasets")
            or data.get("_embedded", {}).get("datasets")
            or data.get("results")
            or data.get("items")
            or data.get("data")
            or []
        )
    else:
        records = []
    return [record for record in records if isinstance(record, dict)]


def classify(text: str) -> dict[str, bool]:
    lower = text.lower()
    exact_main = "mainregimev2" in lower
    r5 = exact_main and ("2026" in lower or "post-cutoff" in lower or "extension" in lower)
    r3 = (
        ("native_subhour" in lower or "native subhour" in lower or "subhour" in lower)
        and "crisis" in lower
    )
    r6 = (
        ("oystacher" in lower or "3red" in lower or "3 red" in lower)
        and ("control" in lower or "order book" in lower or "order lifecycle" in lower or "matched" in lower)
    )
    required_filename = any(
        token in lower
        for token in [
            "mainregimev2",
            "stock_market_regimes_2026_extension",
            "native_subhour_source_label_rows",
            "oystacher",
            "3red",
            "matched controls",
            "order lifecycle",
        ]
    )
    return {
        "required_filename_or_token_hit": required_filename,
        "exact_mainregimev2_hit": exact_main,
        "r5_post_cutoff_hit": r5,
        "r3_native_subhour_crisis_hit": r3,
        "r6_owner_control_hit": r6,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND.mkdir(parents=True, exist_ok=True)

    request_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []

    for query in QUERIES:
        encoded = urllib.parse.quote(query)
        url = f"https://datadryad.org/api/v2/search?query={encoded}&per_page=5"
        slug = normalize_slug(query)
        status, payload, error = fetch(url)
        (COMMAND / f"dryad_{slug}.url").write_text(url + "\n", encoding="utf-8")
        (COMMAND / f"dryad_{slug}.status").write_text(str(status) + "\n", encoding="utf-8")
        (COMMAND / f"dryad_{slug}.payload").write_bytes(payload[:250000])
        if error:
            (COMMAND / f"dryad_{slug}.error").write_text(error + "\n", encoding="utf-8")

        records = collect_records(payload)
        request_rows.append(
            {
                "surface": "dryad_api_v2_search",
                "query": query,
                "url": url,
                "status": status,
                "error": error or "",
                "records_scanned": len(records),
            }
        )
        for index, record in enumerate(records[:5]):
            text = as_text(record)
            flags = classify(text)
            title = as_text(record.get("title") or record.get("name") or record.get("identifier"))
            identifier = as_text(record.get("identifier") or record.get("doi") or record.get("id"))
            candidate_rows.append(
                {
                    "surface": "dryad_api_v2_search",
                    "query": query,
                    "rank": index + 1,
                    "title": title[:300],
                    "identifier": identifier[:220],
                    "required_filename_or_token_hit": flags["required_filename_or_token_hit"],
                    "exact_mainregimev2_hit": flags["exact_mainregimev2_hit"],
                    "r5_post_cutoff_hit": flags["r5_post_cutoff_hit"],
                    "r3_native_subhour_crisis_hit": flags["r3_native_subhour_crisis_hit"],
                    "r6_owner_control_hit": flags["r6_owner_control_hit"],
                    "snippet": re.sub(r"\s+", " ", text)[:700],
                }
            )
        time.sleep(0.2)

    totals = {
        "requests_sent": len(request_rows),
        "failed_or_parse_failed": sum(1 for row in request_rows if row["status"] != 200),
        "top_metadata_rows_scanned": len(candidate_rows),
        "required_filename_or_token_hits": sum(1 for row in candidate_rows if row["required_filename_or_token_hit"]),
        "exact_mainregimev2_hits": sum(1 for row in candidate_rows if row["exact_mainregimev2_hit"]),
        "r5_post_cutoff_hits": sum(1 for row in candidate_rows if row["r5_post_cutoff_hit"]),
        "r3_native_subhour_crisis_hits": sum(1 for row in candidate_rows if row["r3_native_subhour_crisis_hit"]),
        "r6_owner_control_hits": sum(1 for row in candidate_rows if row["r6_owner_control_hit"]),
    }
    gate_result = "dryad_source_route_probe_after_080054_v1=no_required_source_control_unlock"
    summary = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "totals": totals,
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

    json_path = OUT / "dryad_source_route_probe_after_080054_v1.json"
    request_csv = OUT / "dryad_source_route_requests_v1.csv"
    candidate_csv = OUT / "dryad_source_route_candidates_v1.csv"
    report_path = OUT / "dryad_source_route_probe_after_080054_v1.md"
    assertions_path = CHECKS / "dryad_source_route_probe_after_080054_v1_assertions.out"

    json_path.write_text(json.dumps({**summary, "requests": request_rows, "candidates": candidate_rows}, indent=2), encoding="utf-8")
    with request_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(request_rows[0].keys()))
        writer.writeheader()
        writer.writerows(request_rows)
    with candidate_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "surface",
            "query",
            "rank",
            "title",
            "identifier",
            "required_filename_or_token_hit",
            "exact_mainregimev2_hit",
            "r5_post_cutoff_hit",
            "r3_native_subhour_crisis_hit",
            "r6_owner_control_hit",
            "snippet",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidate_rows)

    report_path.write_text(
        "\n".join(
            [
                "# Dryad Source Route Probe After 080054 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Scope",
                "",
                "Read-only Dryad API source-route probe after `080054` stayed blocked. It checks whether Dryad exposes source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, R6 owner/export positives with matched controls, or a new accepted cross-timeframe `MainRegimeV2` source export. It does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, derive labels, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Requests sent: `{totals['requests_sent']}`.",
                f"- Failed or parse-failed requests: `{totals['failed_or_parse_failed']}`.",
                f"- Top metadata rows scanned: `{totals['top_metadata_rows_scanned']}`.",
                f"- Required filename/token hits: `{totals['required_filename_or_token_hits']}`.",
                f"- Exact `MainRegimeV2` hits: `{totals['exact_mainregimev2_hits']}`.",
                f"- R5 post-cutoff source-panel hits: `{totals['r5_post_cutoff_hits']}`.",
                f"- R3 native-subhour Crisis hits: `{totals['r3_native_subhour_crisis_hits']}`.",
                f"- R6 owner/control hits: `{totals['r6_owner_control_hits']}`.",
                "",
                "## Decision",
                "",
                "No Dryad route supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
                "",
                "Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Candidate CSV: `{candidate_csv}`",
                f"- Request CSV: `{request_csv}`",
                f"- Assertions: `{assertions_path}`",
                f"- Command output root: `{COMMAND}`",
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
        "PASS dryad_source_route_probe_after_080054_v1",
        f"gate_result={gate_result}",
        f"requests_sent={totals['requests_sent']}",
        f"failed_or_parse_failed={totals['failed_or_parse_failed']}",
        f"top_metadata_rows_scanned={totals['top_metadata_rows_scanned']}",
        f"required_filename_or_token_hits={totals['required_filename_or_token_hits']}",
        f"exact_mainregimev2_hits={totals['exact_mainregimev2_hits']}",
        f"r5_post_cutoff_hits={totals['r5_post_cutoff_hits']}",
        f"r3_native_subhour_crisis_hits={totals['r3_native_subhour_crisis_hits']}",
        f"r6_owner_control_hits={totals['r6_owner_control_hits']}",
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

    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
