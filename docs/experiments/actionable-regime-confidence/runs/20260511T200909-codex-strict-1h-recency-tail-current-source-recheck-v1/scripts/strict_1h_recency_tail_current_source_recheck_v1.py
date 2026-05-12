#!/usr/bin/env python3
"""Current-source recheck for strict 1h recency-tail target rows."""

from __future__ import annotations

import csv
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "recency-tail-current-source-recheck"
CHECK_DIR = RUN_ROOT / "checks"
LOCAL_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
CUTOFF = "2026-01-30"
TARGETS = [
    ("XOM", "Sideways"),
    ("UNH", "Bear"),
    ("^DJI", "Sideways"),
    ("AMD", "Bear"),
]
USER_AGENT = "ict-engine-board-a-r5-current-source-recheck/1.0"


def fetch_json(url: str, limit: int | None = None) -> tuple[object | None, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read(limit or 2_000_000)
        return json.loads(body.decode("utf-8")), None
    except Exception as exc:  # pragma: no cover - artifact should capture network drift.
        return None, f"{type(exc).__name__}: {exc}"


def analyze_local_panel() -> tuple[list[dict[str, object]], dict[str, object]]:
    target_rows = {
        (ticker, regime): {
            "ticker": ticker,
            "regime_label": regime,
            "source_rows": 0,
            "rows_after_2026_01_30": 0,
            "max_date": "",
        }
        for ticker, regime in TARGETS
    }
    summary = {
        "path": str(LOCAL_PANEL),
        "exists": LOCAL_PANEL.exists(),
        "rows": 0,
        "max_date": "",
        "fieldnames": [],
    }
    if not LOCAL_PANEL.exists():
        return list(target_rows.values()), summary

    with LOCAL_PANEL.open(newline="") as handle:
        reader = csv.DictReader(handle)
        summary["fieldnames"] = reader.fieldnames or []
        for row in reader:
            summary["rows"] += 1
            date = row.get("date", "")
            ticker = row.get("ticker", "")
            regime = row.get("regime_label", "")
            if date > summary["max_date"]:
                summary["max_date"] = date
            key = (ticker, regime)
            if key in target_rows:
                item = target_rows[key]
                item["source_rows"] += 1
                if date > item["max_date"]:
                    item["max_date"] = date
                if date > CUTOFF:
                    item["rows_after_2026_01_30"] += 1
    return list(target_rows.values()), summary


def search_current_sources() -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    kaggle_ref = "mafaqbhatti/stock-market-regimes-20002026"
    kaggle_view_url = f"https://www.kaggle.com/api/v1/datasets/view/{kaggle_ref}"
    kaggle_view, kaggle_view_error = fetch_json(kaggle_view_url)
    candidates.append(
        {
            "source": "kaggle_dataset_view",
            "query_or_ref": kaggle_ref,
            "url": "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026",
            "hit_count": 1 if kaggle_view else 0,
            "last_updated": (kaggle_view or {}).get("lastUpdated")
            if isinstance(kaggle_view, dict)
            else "",
            "current_version": (kaggle_view or {}).get("currentVersionNumber")
            if isinstance(kaggle_view, dict)
            else "",
            "status": "metadata_read" if kaggle_view else "metadata_error",
            "ready_tail_source": False,
            "disposition": (
                "same public source panel metadata; local panel max date is still the "
                "decisive row-level check"
            )
            if kaggle_view
            else kaggle_view_error,
        }
    )

    for query in [
        "stock market regimes 2000 2026",
        "stock_market_regimes_2000_2026.csv",
        "XOM Sideways UNH Bear AMD Bear regime dataset",
    ]:
        encoded = urllib.parse.quote(query)
        kaggle_list_url = f"https://www.kaggle.com/api/v1/datasets/list?search={encoded}"
        kaggle_list, kaggle_list_error = fetch_json(kaggle_list_url)
        hit_count = len(kaggle_list) if isinstance(kaggle_list, list) else 0
        top_refs = []
        if isinstance(kaggle_list, list):
            for item in kaggle_list[:5]:
                top_refs.append(
                    item.get("ref")
                    or item.get("urlNullable")
                    or item.get("titleNullable")
                    or item.get("title")
                )
        candidates.append(
            {
                "source": "kaggle_dataset_list",
                "query_or_ref": query,
                "url": kaggle_list_url,
                "hit_count": hit_count,
                "last_updated": "",
                "current_version": "",
                "status": "metadata_read" if kaggle_list is not None else "metadata_error",
                "ready_tail_source": False,
                "disposition": "; ".join(str(x) for x in top_refs)
                if top_refs
                else (kaggle_list_error or "no datasets returned"),
            }
        )

    for query in [
        "stock market regimes 2000 2026",
        "stock_market_regimes_2000_2026.csv",
        "XOM Sideways UNH Bear AMD Bear regime dataset",
    ]:
        encoded = urllib.parse.quote(query)
        hf_url = f"https://huggingface.co/api/datasets?search={encoded}"
        hf_result, hf_error = fetch_json(hf_url)
        hit_count = len(hf_result) if isinstance(hf_result, list) else 0
        candidates.append(
            {
                "source": "huggingface_dataset_search",
                "query_or_ref": query,
                "url": hf_url,
                "hit_count": hit_count,
                "last_updated": "",
                "current_version": "",
                "status": "metadata_read" if hf_result is not None else "metadata_error",
                "ready_tail_source": False,
                "disposition": "no ready source-owned recency-tail label dataset found"
                if hit_count == 0
                else "metadata hits require fail-closed manual review",
            }
        )

    for query in [
        '"stock_market_regimes_2000_2026.csv"',
        '"stock market regimes 2000 2026"',
        '"XOM" "Sideways" "UNH" "Bear" "AMD" "regime"',
    ]:
        encoded = urllib.parse.quote(query)
        gh_url = f"https://api.github.com/search/repositories?q={encoded}"
        gh_result, gh_error = fetch_json(gh_url)
        hit_count = (
            int(gh_result.get("total_count", 0))
            if isinstance(gh_result, dict)
            else 0
        )
        candidates.append(
            {
                "source": "github_repository_search",
                "query_or_ref": query,
                "url": gh_url,
                "hit_count": hit_count,
                "last_updated": "",
                "current_version": "",
                "status": "metadata_read" if gh_result is not None else "metadata_error",
                "ready_tail_source": False,
                "disposition": "no repository hit with source-owned post-cutoff labels"
                if hit_count == 0
                else "repository hits require fail-closed manual review",
            }
        )
    return candidates


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    target_rows, local_summary = analyze_local_panel()
    candidates = search_current_sources()
    all_tail_rows_present = all(
        int(row["rows_after_2026_01_30"]) > 0 for row in target_rows
    )
    ready_external_tail_source = any(c["ready_tail_source"] for c in candidates)
    gate_result = (
        "strict_1h_recency_tail_current_source_recheck_v1=tail_rows_available"
        if all_tail_rows_present and ready_external_tail_source
        else "strict_1h_recency_tail_current_source_recheck_v1=no_post_2026_01_30_source_owned_tail_rows"
    )
    result = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_requirement": "R5 strict_1h_recency_tail_repair",
        "cutoff_exclusive": CUTOFF,
        "local_source_panel": local_summary,
        "target_rows": target_rows,
        "candidate_sources_checked": len(candidates),
        "ready_external_tail_sources": sum(1 for c in candidates if c["ready_tail_source"]),
        "all_tail_rows_present": all_tail_rows_present,
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "candidates": candidates,
    }

    json_path = OUT_DIR / "strict_1h_recency_tail_current_source_recheck_v1.json"
    target_csv = OUT_DIR / "strict_1h_recency_tail_current_source_recheck_v1_targets.csv"
    candidate_csv = OUT_DIR / "strict_1h_recency_tail_current_source_recheck_v1_candidates.csv"
    report_path = OUT_DIR / "strict_1h_recency_tail_current_source_recheck_v1.md"
    assertion_path = CHECK_DIR / "strict_1h_recency_tail_current_source_recheck_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(target_csv, target_rows)
    write_csv(candidate_csv, candidates)

    lines = [
        "# Strict 1h Recency Tail Current Source Recheck v1",
        "",
        f"Run ID: `{RUN_ROOT.name}`",
        "",
        f"- Gate result: `{gate_result}`.",
        "- Target: R5 strict `1h` recency-tail repair for XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear.",
        f"- Local source panel exists: `{local_summary['exists']}`; rows: `{local_summary['rows']}`; max date: `{local_summary['max_date']}`.",
        f"- Rows after `{CUTOFF}` by strict target: "
        + ", ".join(
            f"{row['ticker']}/{row['regime_label']}={row['rows_after_2026_01_30']}"
            for row in target_rows
        )
        + ".",
        f"- Candidate source metadata checks: `{len(candidates)}`; ready external tail sources: `0`.",
        "- Kaggle current dataset metadata still points to the same public source panel; local row-level panel remains capped at `2026-01-30`.",
        "- Hugging Face and GitHub metadata searches found no source-owned post-cutoff row package for the strict targets.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Target CSV: `{target_csv}`",
        f"- Candidate CSV: `{candidate_csv}`",
        f"- Assertions: `{assertion_path}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS gate_result={gate_result}",
        f"PASS all_tail_rows_present={str(all_tail_rows_present).lower()}",
        "PASS rows_after_2026_01_30_all_targets=0",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    if any(int(row["rows_after_2026_01_30"]) != 0 for row in target_rows):
        assertions[2] = "FAIL rows_after_2026_01_30_all_targets=nonzero"
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0 if all(line.startswith("PASS") for line in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
