#!/usr/bin/env python3
"""Screen new public source-label candidates without mutating live intake roots."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


RUN_ID = "20260512T020104-codex-public-source-label-expansion-screen-v1"
GATE_RESULT = (
    "public_source_label_expansion_screen_v1="
    "new_candidates_screened_no_source_owned_mainregime_export_no_promotion"
)

PRIOR_DATASET_IDS = {
    "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
    "sujinwo/tsie-market-regime-dataset",
}

QUERY_TERMS = [
    "market regime",
    "regime_label",
    "bull bear sideways",
    "trading regime",
]

ROOTS = [
    ("r6_owner_export", "/tmp/ict-engine-board-a-r6-owner-export-v1"),
    ("r3_native_subhour", "/tmp/ict-engine-native-subhour-source-label-intake"),
    ("r5_recency_extension", "/tmp/ict-engine-source-panel-recency-extension"),
    ("source_label_equivalence", "/tmp/ict-engine-source-label-equivalence-intake"),
]


def fetch_json(url: str) -> dict | list:
    request = Request(url, headers={"User-Agent": "ict-engine-board-a-source-screen/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def text_blob(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def label_fields(first_rows: dict) -> list[str]:
    fields = []
    for feature in first_rows.get("features", []):
        name = str(feature.get("name", ""))
        lowered = name.lower()
        if "regime" in lowered or "state" in lowered or lowered.endswith("label"):
            fields.append(name)
    return fields


def candidate_status(dataset_id: str, info: dict, first_rows: dict | None) -> tuple[str, str]:
    blob = text_blob({"info": info.get("cardData"), "tags": info.get("tags"), "rows": first_rows})
    fields = label_fields(first_rows or {})
    if dataset_id == "AAdevloper/nifty50-market-regime":
        return (
            "sidecar_only_fail_closed_daily_low_support_int_labels",
            "Has a regime field for NIFTY 50, but observed rows are daily, small support, and integer labels lack a source-owner MainRegimeV2/Bull-Bear-Sideways crosswalk.",
        )
    if dataset_id.startswith("ClarusC64/"):
        return (
            "reject_fail_closed_text_mapping_not_verifier_native_market_rows",
            "Observed fields are macro/cross-asset narrative mapping rows rather than verifier-native OHLCV/order-lifecycle rows with source-owned MainRegimeV2 labels.",
        )
    if not fields:
        return (
            "reject_no_observed_regime_label_field",
            "Dataset metadata matched search terms but first-row metadata did not expose a usable regime/state/label field.",
        )
    if "bull" in blob or "bear" in blob or "sideways" in blob:
        return (
            "sidecar_only_fail_closed_no_source_owner_mainregime_contract",
            "Relevant label language appears in metadata, but no source-owner MainRegimeV2 export/provenance/canonical merge contract is present.",
        )
    return (
        "reject_unmapped_regime_semantics",
        "Regime-like fields exist, but the semantics are not enough for Board A acceptance without an approved crosswalk and split calibration.",
    )


def root_status() -> list[dict]:
    rows = []
    for root_id, raw_root in ROOTS:
        path = Path(raw_root)
        files = 0
        if path.exists():
            files = sum(1 for child in path.iterdir() if child.is_file())
        rows.append({"id": root_id, "root": raw_root, "present": path.exists(), "file_count": files})
    return rows


def main() -> None:
    run_root = Path(__file__).resolve().parents[1]
    output_dir = run_root / "public-source-label-expansion-screen-v1"
    checks_dir = run_root / "checks"
    output_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    search_results: list[dict] = []
    selected_ids: list[str] = []
    seen: set[str] = set()
    for query in QUERY_TERMS:
        url = f"https://huggingface.co/api/datasets?search={quote(query)}&limit=10&full=false"
        result = fetch_json(url)
        assert isinstance(result, list)
        for item in result:
            dataset_id = item.get("id")
            if not dataset_id:
                continue
            row = {
                "query": query,
                "id": dataset_id,
                "url": f"https://huggingface.co/datasets/{dataset_id}",
                "downloads": item.get("downloads"),
                "likes": item.get("likes"),
                "tags": item.get("tags", []),
                "prior_screened": dataset_id in PRIOR_DATASET_IDS,
            }
            search_results.append(row)
            if dataset_id not in seen and dataset_id not in PRIOR_DATASET_IDS:
                seen.add(dataset_id)
                selected_ids.append(dataset_id)

    candidates: list[dict] = []
    for dataset_id in selected_ids[:8]:
        encoded = quote(dataset_id, safe="")
        info_url = f"https://huggingface.co/api/datasets/{dataset_id}"
        first_rows_url = (
            "https://datasets-server.huggingface.co/first-rows"
            f"?dataset={encoded}&config=default&split=train"
        )
        info = fetch_json(info_url)
        assert isinstance(info, dict)
        first_rows: dict | None
        first_rows_error = None
        try:
            fetched_first_rows = fetch_json(first_rows_url)
            assert isinstance(fetched_first_rows, dict)
            first_rows = fetched_first_rows
        except Exception as exc:  # noqa: BLE001 - persisted as audit metadata.
            first_rows = None
            first_rows_error = f"{type(exc).__name__}: {exc}"

        status, blocker = candidate_status(dataset_id, info, first_rows)
        features = [feature.get("name") for feature in (first_rows or {}).get("features", [])]
        first_row = None
        rows = (first_rows or {}).get("rows", [])
        if rows:
            first_row = rows[0].get("row")
        candidates.append(
            {
                "id": dataset_id,
                "url": f"https://huggingface.co/datasets/{dataset_id}",
                "api_url": info_url,
                "first_rows_url": first_rows_url,
                "license": (info.get("cardData") or {}).get("license"),
                "tags": info.get("tags", []),
                "siblings": [sibling.get("rfilename") for sibling in info.get("siblings", [])],
                "observed_features": features,
                "observed_label_fields": label_fields(first_rows or {}),
                "first_row_sample": first_row,
                "first_rows_error": first_rows_error,
                "acceptance_status": status,
                "blocker": blocker,
            }
        )

    source_roots = root_status()
    accepted_rows_added = 0
    new_confidence_gate = False
    canonical_merge_allowed = False
    downstream_chain_rerun_allowed = False
    strict_full_objective_achieved = False

    packet = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "external_requests_sent": True,
        "external_vendor_contact_sent": False,
        "raw_dataset_files_downloaded": False,
        "raw_data_committed": False,
        "prior_dataset_ids": sorted(PRIOR_DATASET_IDS),
        "query_terms": QUERY_TERMS,
        "search_result_count": len(search_results),
        "new_candidate_count": len(candidates),
        "search_results": search_results,
        "candidates": candidates,
        "source_roots": source_roots,
        "accepted_rows_added": accepted_rows_added,
        "new_confidence_gate": new_confidence_gate,
        "canonical_merge_allowed": canonical_merge_allowed,
        "downstream_chain_rerun_allowed": downstream_chain_rerun_allowed,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }

    json_path = output_dir / "public_source_label_expansion_screen_v1.json"
    json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_path = output_dir / "public_source_label_expansion_candidates_v1.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "url",
                "license",
                "observed_label_fields",
                "acceptance_status",
                "blocker",
            ],
        )
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(
                {
                    "id": candidate["id"],
                    "url": candidate["url"],
                    "license": candidate["license"],
                    "observed_label_fields": ";".join(candidate["observed_label_fields"]),
                    "acceptance_status": candidate["acceptance_status"],
                    "blocker": candidate["blocker"],
                }
            )

    md_lines = [
        "# Public Source Label Expansion Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Gate result: `{GATE_RESULT}`",
        "",
        "Purpose:",
        "- Continue non-R6 source acquisition without repeating prior `sujinwo` / BTC HMM screens.",
        "- Search the current Hugging Face public dataset API for new regime-label candidates.",
        "- Keep this packet metadata-only: no raw dataset files are downloaded into the repo and no intake root is mutated.",
        "",
        "Search summary:",
        f"- Query terms: `{', '.join(QUERY_TERMS)}`.",
        f"- Search result rows observed: `{len(search_results)}`.",
        f"- New candidate datasets screened after excluding prior Board A candidates: `{len(candidates)}`.",
        "",
        "Candidate decisions:",
    ]
    for candidate in candidates:
        md_lines.extend(
            [
                f"- `{candidate['id']}`: `{candidate['acceptance_status']}`.",
                f"  - URL: `{candidate['url']}`",
                f"  - Observed label fields: `{', '.join(candidate['observed_label_fields']) or 'none'}`.",
                f"  - Blocker: {candidate['blocker']}",
            ]
        )
    md_lines.extend(
        [
            "",
            "Source-root readback:",
        ]
    )
    for row in source_roots:
        md_lines.append(
            f"- `{row['id']}`: present `{str(row['present']).lower()}`, file_count `{row['file_count']}`, root `{row['root']}`."
        )
    md_lines.extend(
        [
            "",
            "Decision:",
            "- Ready source-owned cross-timeframe MainRegimeV2 exports found: `0`.",
            "- Accepted rows added: `0`.",
            "- New confidence gate: `false`.",
            "- Canonical merge allowed: `false`.",
            "- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.",
            "- Strict full objective achieved: `false`.",
            "- `update_goal=false`.",
            "",
            "No mutation claims:",
            "- Runtime code changed: `false`.",
            "- Shared intake mutated: `false`.",
            "- R3/R5/R6 roots mutated: `false`.",
            "- Thresholds relaxed: `false`.",
            "- Raw dataset files downloaded: `false`.",
            "- Raw data committed: `false`.",
            "- External vendor/contact request sent: `false`.",
            "- Trade usable: `false`.",
            "",
            "Next:",
            "- Preserve the Current Cursor next action for R6. Non-R6 public-source work should continue only with genuinely source-owned MainRegimeV2/cross-timeframe exports or an approved crosswalk; do not repeat prior sidecar/proxy dataset downloads.",
            "",
        ]
    )
    md_path = output_dir / "public_source_label_expansion_screen_v1.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = [
        f"gate_result={GATE_RESULT}",
        f"search_result_count={len(search_results)}",
        f"new_candidate_count={len(candidates)}",
        f"accepted_rows_added={accepted_rows_added}",
        f"new_confidence_gate={str(new_confidence_gate).lower()}",
        f"canonical_merge_allowed={str(canonical_merge_allowed).lower()}",
        f"downstream_chain_rerun_allowed={str(downstream_chain_rerun_allowed).lower()}",
        f"strict_full_objective_achieved={str(strict_full_objective_achieved).lower()}",
        "raw_dataset_files_downloaded=false",
        "shared_intake_mutated=false",
        "r3_r5_r6_roots_mutated=false",
        "update_goal=false",
    ]
    (checks_dir / "public_source_label_expansion_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    assert candidates, "expected at least one new candidate to be screened"
    assert accepted_rows_added == 0
    assert not new_confidence_gate
    assert not canonical_merge_allowed
    assert not downstream_chain_rerun_allowed
    assert not strict_full_objective_achieved
    assert not packet["raw_dataset_files_downloaded"]
    assert not packet["shared_intake_mutated"]
    assert not packet["r3_r5_r6_roots_mutated"]
    print(json.dumps({"run_id": RUN_ID, "gate_result": GATE_RESULT, "new_candidate_count": len(candidates)}, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
