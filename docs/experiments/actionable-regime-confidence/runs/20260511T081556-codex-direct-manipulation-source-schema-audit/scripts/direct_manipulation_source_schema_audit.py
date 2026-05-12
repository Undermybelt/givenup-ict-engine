#!/usr/bin/env python3
"""Bounded schema audit for direct Manipulation source candidates.

This audit is intentionally fail-closed:
- direct order-book or event data is useful input provenance,
- but it is not accepted Manipulation label coverage unless the source supplies
  explicit positive/negative manipulation labels or event windows.
"""

from __future__ import annotations

import csv
import json
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T081556+0800-codex-direct-manipulation-source-schema-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T081556-codex-direct-manipulation-source-schema-audit"
OUT_DIR = RUN_ROOT / "direct-manipulation-schema"
CHECK_DIR = RUN_ROOT / "checks"
RAW_ROOT = Path("/private/tmp/ict-regime-direct-manipulation-schema-20260511T081556")
MAX_SCHEMA_SAMPLE_BYTES = 8_000_000

HF_API = "https://huggingface.co/api/datasets"
HF_RESOLVE = "https://huggingface.co/datasets/{dataset}/resolve/main/{filename}"

try:
    import pyarrow.parquet as pq  # type: ignore
except Exception:  # noqa: BLE001 - optional low-pollution dependency
    pq = None


CANDIDATES: list[dict[str, Any]] = [
    {
        "dataset_id": "trentmkelly/polymarket_crypto_derivatives",
        "source_type": "direct_order_lifecycle_order_book",
        "sample_files": [
            "btc15m_market1402567_2026-02-21_15-45-00_all/events.parquet",
            "btc15m_market1402567_2026-02-21_15-45-00_all/book_levels.parquet",
            "btc15m_market1402567_2026-02-21_15-45-00_all/steps.parquet",
        ],
        "expected_value": "direct Polymarket CLOB event/order-book source for BTC/ETH/SOL/XRP interval markets",
    },
    {
        "dataset_id": "phobia76/pmxt-l2-dump",
        "source_type": "direct_order_book_l2",
        "sample_files": [
            "hours/2026/02/21/polymarket_orderbook_2026-02-21T16.parquet",
        ],
        "expected_value": "direct Polymarket hourly L2 order-book source",
    },
    {
        "dataset_id": "muhammetakkurt/pump-fun-meme-token-dataset",
        "source_type": "token_event_context",
        "sample_files": [
            "pump_fun_memetoken_dataset.csv",
        ],
        "expected_value": "Pump.fun token creation and market/social context around a narrow event window",
    },
    {
        "dataset_id": "Washedashore/thepower",
        "source_type": "metadata_false_positive",
        "sample_files": [],
        "expected_value": "prior HF metadata false positive; included to close the loop",
    },
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None) -> urllib.request.Request:
    merged = {
        "User-Agent": "ict-engine-board-a-manipulation-schema-audit/1.0",
    }
    if headers:
        merged.update(headers)
    return urllib.request.Request(url, method=method, headers=merged)


def get_json(url: str) -> Any:
    with urllib.request.urlopen(request(url), timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text_prefix(url: str, limit: int = 12000) -> str:
    with urllib.request.urlopen(request(url), timeout=30) as response:
        return response.read(limit).decode("utf-8", "replace")


def resolve_url(dataset_id: str, filename: str) -> str:
    return HF_RESOLVE.format(
        dataset=urllib.parse.quote(dataset_id, safe="/"),
        filename=urllib.parse.quote(filename, safe="/"),
    )


def head_file(dataset_id: str, filename: str) -> dict[str, Any]:
    url = resolve_url(dataset_id, filename)
    try:
        with urllib.request.urlopen(request(url, method="HEAD"), timeout=30) as response:
            length = response.headers.get("content-length")
            return {
                "filename": filename,
                "status": "head_ok",
                "content_length": int(length) if length and length.isdigit() else None,
                "content_type": response.headers.get("content-type") or "",
                "resolved_url_prefix": response.geturl()[:160],
            }
    except Exception as exc:  # noqa: BLE001 - preserve source failure
        return {
            "filename": filename,
            "status": "head_failed",
            "error": f"{type(exc).__name__}: {exc}",
        }


def download_small_file(dataset_id: str, filename: str, content_length: int | None) -> Path | None:
    if content_length is None or content_length > MAX_SCHEMA_SAMPLE_BYTES:
        return None
    target_dir = RAW_ROOT / dataset_id.replace("/", "__")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename.replace("/", "__")
    with urllib.request.urlopen(request(resolve_url(dataset_id, filename)), timeout=60) as response:
        with target.open("wb") as out:
            shutil.copyfileobj(response, out)
    return target


def csv_header_sample(dataset_id: str, filename: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request(resolve_url(dataset_id, filename), headers={"Range": "bytes=0-65535"}), timeout=30) as response:
            text = response.read(65536).decode("utf-8", "replace")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        columns = next(csv.reader([first_line])) if first_line else []
        return {
            "schema_status": "csv_header_sampled",
            "columns": columns,
            "column_count": len(columns),
            "raw_sample_committed": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "schema_status": "csv_header_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "raw_sample_committed": False,
        }


def parquet_schema_sample(dataset_id: str, filename: str, content_length: int | None) -> dict[str, Any]:
    if pq is None:
        return {
            "schema_status": "parquet_schema_not_sampled_pyarrow_missing",
            "raw_sample_committed": False,
        }
    local = download_small_file(dataset_id, filename, content_length)
    if local is None:
        return {
            "schema_status": "parquet_schema_not_sampled_size_unbounded",
            "content_length": content_length,
            "raw_sample_committed": False,
        }
    try:
        parquet_file = pq.ParquetFile(local)
        schema = parquet_file.schema_arrow
        return {
            "schema_status": "parquet_schema_sampled",
            "columns": [field.name for field in schema],
            "column_types": {field.name: str(field.type) for field in schema},
            "column_count": len(schema),
            "metadata_rows": parquet_file.metadata.num_rows if parquet_file.metadata else None,
            "local_sample_path": str(local),
            "raw_sample_committed": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "schema_status": "parquet_schema_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "local_sample_path": str(local),
            "raw_sample_committed": False,
        }


def schema_for_file(dataset_id: str, file_info: dict[str, Any]) -> dict[str, Any]:
    filename = file_info["filename"]
    if file_info["status"] != "head_ok":
        return file_info | {"schema_status": "not_sampled_head_failed"}
    content_length = file_info.get("content_length")
    if filename.endswith(".csv"):
        return file_info | csv_header_sample(dataset_id, filename)
    if filename.endswith(".parquet"):
        return file_info | parquet_schema_sample(dataset_id, filename, content_length)
    return file_info | {"schema_status": "not_sampled_unsupported_extension"}


def source_url(dataset_id: str) -> str:
    return f"https://huggingface.co/datasets/{dataset_id}"


def classify(row: dict[str, Any]) -> dict[str, Any]:
    dataset_id = row["dataset_id"]
    readme = row.get("readme_prefix", "").lower()
    columns = " ".join(
        " ".join(sample.get("columns") or [])
        for sample in row.get("sample_files", [])
        if isinstance(sample, dict)
    ).lower()
    text = f"{readme} {columns}"

    candidate_declares_direct_order_flow = row.get("source_type") in {
        "direct_order_lifecycle_order_book",
        "direct_order_book_l2",
    }
    schema_has_order_flow = any(
        term in text
        for term in [
            "orderbook",
            "order book",
            "book_levels",
            "event_type",
            "clob",
            "bid",
            "ask",
            "imbalance",
            "is_sell_side",
            "level_index",
            "tick size",
        ]
    )
    has_direct_order_flow = candidate_declares_direct_order_flow and schema_has_order_flow
    has_event_context = any(term in text for term in ["pump.fun", "token", "creator", "social media", "market performance"])
    has_explicit_manipulation_label = any(
        term in text
        for term in [
            "manipulation_label",
            "manipulation label",
            "spoofing_label",
            "layering_label",
            "wash_trade_label",
            "pump_dump_label",
            "positive window",
            "negative window",
            "ground truth",
            "labeled manipulation",
        ]
    )

    if dataset_id == "Washedashore/thepower":
        status = "rejected_metadata_false_positive"
        reason = "dataset card is a generic template and does not provide market event/order-flow labels"
    elif has_explicit_manipulation_label:
        status = "candidate_needs_label_window_attachability"
        reason = "explicit manipulation-label terms found; needs symbol/time/window attachment before acceptance"
    elif has_direct_order_flow:
        status = "direct_input_source_unlabeled"
        reason = "direct order-book/order-lifecycle fields exist, but no explicit manipulation-positive/negative labels or event windows were found"
    elif has_event_context:
        status = "event_context_unlabeled"
        reason = "token/event context exists, but no explicit manipulation labels or order-lifecycle evidence were found"
    else:
        status = "not_a_direct_manipulation_label_source"
        reason = "metadata/schema does not evidence direct manipulation labels"

    return {
        "status": status,
        "reason": reason,
        "has_direct_order_flow": has_direct_order_flow,
        "has_event_context": has_event_context,
        "has_explicit_manipulation_label": has_explicit_manipulation_label,
        "accepted_for_direct_manipulation": False,
        "accepted_for_mainregimev2_roots": False,
    }


def audit_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    dataset_id = candidate["dataset_id"]
    meta_url = f"{HF_API}/{urllib.parse.quote(dataset_id, safe='/')}"
    readme_url = f"{source_url(dataset_id)}/resolve/main/README.md"
    row: dict[str, Any] = {
        "dataset_id": dataset_id,
        "url": source_url(dataset_id),
        "source_type": candidate["source_type"],
        "expected_value": candidate["expected_value"],
        "sample_files": [],
    }
    try:
        metadata = get_json(meta_url)
        row["metadata_status"] = "ok"
        row["last_modified"] = metadata.get("lastModified", "")
        row["downloads"] = metadata.get("downloads", 0)
        row["likes"] = metadata.get("likes", 0)
        row["tags"] = metadata.get("tags", [])[:25]
        row["siblings_seen"] = len(metadata.get("siblings") or [])
    except Exception as exc:  # noqa: BLE001
        row["metadata_status"] = "failed"
        row["metadata_error"] = f"{type(exc).__name__}: {exc}"
        row["tags"] = []
        row["siblings_seen"] = 0

    try:
        row["readme_prefix"] = fetch_text_prefix(readme_url)
        row["readme_status"] = "ok"
    except Exception as exc:  # noqa: BLE001
        row["readme_prefix"] = ""
        row["readme_status"] = "failed"
        row["readme_error"] = f"{type(exc).__name__}: {exc}"

    for filename in candidate["sample_files"]:
        row["sample_files"].append(schema_for_file(dataset_id, head_file(dataset_id, filename)))

    row.update(classify(row))
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "dataset_id",
        "url",
        "source_type",
        "metadata_status",
        "readme_status",
        "status",
        "reason",
        "has_direct_order_flow",
        "has_event_context",
        "has_explicit_manipulation_label",
        "accepted_for_direct_manipulation",
        "accepted_for_mainregimev2_roots",
        "sample_file_count",
        "sample_schema_statuses",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            samples = row.get("sample_files") or []
            writer.writerow(
                {
                    "dataset_id": row["dataset_id"],
                    "url": row["url"],
                    "source_type": row["source_type"],
                    "metadata_status": row.get("metadata_status", ""),
                    "readme_status": row.get("readme_status", ""),
                    "status": row["status"],
                    "reason": row["reason"],
                    "has_direct_order_flow": row["has_direct_order_flow"],
                    "has_event_context": row["has_event_context"],
                    "has_explicit_manipulation_label": row["has_explicit_manipulation_label"],
                    "accepted_for_direct_manipulation": row["accepted_for_direct_manipulation"],
                    "accepted_for_mainregimev2_roots": row["accepted_for_mainregimev2_roots"],
                    "sample_file_count": len(samples),
                    "sample_schema_statuses": "|".join(str(sample.get("schema_status", "")) for sample in samples),
                }
            )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    rows = [audit_candidate(candidate) for candidate in CANDIDATES]
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    accepted_direct = [row for row in rows if row["accepted_for_direct_manipulation"]]
    direct_unlabeled = [row for row in rows if row["status"] == "direct_input_source_unlabeled"]

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Schema-audit direct Manipulation event/order-book/order-lifecycle candidates without counting unlabeled sources as accepted labels.",
        "active_taxonomy": "MainRegimeV2",
        "direct_event_class": "Manipulation",
        "raw_root": str(RAW_ROOT),
        "raw_sample_committed": False,
        "pyarrow_available": pq is not None,
        "candidates_seen": len(rows),
        "status_counts": status_counts,
        "direct_input_sources_materialized": len(direct_unlabeled),
        "accepted_direct_manipulation_label_sources": len(accepted_direct),
        "mainregimev2_root_slots_added": 0,
        "manipulation_label_slots_added": 0,
        "goal_achieved": False,
        "accepted_full_cycle_full_universe": False,
        "completion_accounting": {
            "accepted_confidence": False,
            "why_not_accepted": [
                "Direct order-book/order-lifecycle schemas are input provenance, not independent Manipulation labels.",
                "No audited source supplies explicit manipulation-positive and manipulation-negative labeled windows attached to symbol/time.",
                "No audited source supplies Bull/Bear/Sideways/Crisis root labels for the 564 missing/rejected root-label slots.",
                "Raw schema samples were kept under /private/tmp and not committed.",
            ],
        },
        "rows": rows,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "blocked_direct_manipulation_sources_unlabeled_no_accepted_label_windows",
        "next_action": "Acquire explicit labeled Manipulation event windows with positive/negative examples, or continue searching for independent non-yfinance/intraday/monthly MainRegimeV2 root-label panels.",
        "artifacts": {
            "summary_json": rel(OUT_DIR / "direct_manipulation_source_schema_audit.json"),
            "summary_md": rel(OUT_DIR / "direct_manipulation_source_schema_audit.md"),
            "summary_csv": rel(OUT_DIR / "direct_manipulation_source_schema_audit.csv"),
            "assertions": rel(CHECK_DIR / "direct_manipulation_source_schema_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "direct_manipulation_source_schema_audit.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_csv(OUT_DIR / "direct_manipulation_source_schema_audit.csv", rows)

    source_lines = [
        f"| {row['dataset_id']} | {row['status']} | {row['reason']} |"
        for row in rows
    ]
    (OUT_DIR / "direct_manipulation_source_schema_audit.md").write_text(
        "\n".join(
            [
                "# Direct Manipulation Source Schema Audit",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "Goal achieved: `false`",
                "",
                "## Summary",
                "",
                f"- Candidates schema-audited: `{len(rows)}`",
                f"- Direct input sources materialized: `{len(direct_unlabeled)}`",
                f"- Accepted direct `Manipulation` label sources: `{len(accepted_direct)}`",
                "- MainRegimeV2 root-label slots added: `0`",
                "- Manipulation label slots added: `0`",
                f"- Raw schema sample root: `{RAW_ROOT}`",
                "- Raw schema samples committed: `false`",
                "",
                "## Source Dispositions",
                "",
                "| Source | Decision | Reason |",
                "|---|---|---|",
                *source_lines,
                "",
                "## Accounting",
                "",
                "- Polymarket order-book / event schemas are useful direct-input provenance for a future `Manipulation` gate, but they are unlabeled.",
                "- Pump.fun token/event context is not an accepted manipulation label panel because no explicit positive/negative manipulation windows were found.",
                "- No audited source adds accepted `Bull` / `Bear` / `Sideways` / `Crisis` root labels.",
                "- No threshold was relaxed and no runtime code was changed.",
                "",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
                "",
            ]
        )
    )

    assertion_lines = [
        "goal_achieved=false",
        f"candidates_seen={len(rows)}",
        f"direct_input_sources_materialized={len(direct_unlabeled)}",
        f"accepted_direct_manipulation_label_sources={len(accepted_direct)}",
        "mainregimev2_root_slots_added=0",
        "manipulation_label_slots_added=0",
        "accepted_full_cycle_full_universe=false",
        "raw_sample_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        f"gate_result={summary['gate_result']}",
    ]
    for status, count in sorted(status_counts.items()):
        assertion_lines.append(f"status.{status}={count}")
    (CHECK_DIR / "direct_manipulation_source_schema_audit_assertions.out").write_text("\n".join(assertion_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
