#!/usr/bin/env python3
"""Live native sub-hour source-owned label recheck for Board A."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194400-codex-native-subhour-source-recheck-v2"
)
OUT_DIR = RUN_ROOT / "native-subhour-source-recheck"
CHECK_DIR = RUN_ROOT / "checks"

KAGGLE_QUERIES = [
    "5m market regime",
    "intraday regime label",
    "crypto market regime 5m",
    "BTCUSD HMM market regimes",
]
HF_QUERIES = [
    "5m market regime",
    "intraday regime label",
    "crypto market regime 5m",
    "BTCUSD HMM market regimes",
    "multi timeframe market regimes",
]
GH_QUERIES = [
    '"intraday market regime" labels',
    '"market regime" "5m" labels',
    '"regime label" "BTCUSD"',
    '"multi timeframe market regimes"',
]


def run_cmd(
    args: list[str],
    timeout: int = 45,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def disposition(source: str, title: str, description: str) -> tuple[str, bool]:
    text = f"{source} {title} {description}".lower()
    if "synthetic" in text:
        return "blocked_synthetic_panel_not_source_owned_labels", False
    if "hmm" in text or "hidden markov" in text or "classifier" in text:
        return "blocked_generated_or_model_derived_regime_labels", False
    if "bot" in text or "trading strategy" in text or "signals" in text or "indicator" in text:
        return "blocked_code_or_signal_surface_not_source_owned_labels", False
    if "historical data" in text or "ohlcv" in text or "raw" in text:
        return "blocked_raw_provider_panel_no_source_owned_regime_labels", False
    if "paper" in text or "notebook" in text or "prediction" in text:
        return "blocked_research_code_or_prediction_target_not_owner_approved_labels", False
    return "blocked_no_evidence_of_native_subhour_source_owned_mainregime_labels", False


def collect_kaggle() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    readbacks: list[dict[str, object]] = []
    for query in KAGGLE_QUERIES:
        code, stdout, stderr = run_cmd(["kaggle", "datasets", "list", "-s", query, "--csv"])
        readbacks.append(
            {
                "surface": "kaggle",
                "query": query,
                "returncode": code,
                "stderr": stderr.strip(),
                "stdout_head": "\n".join(stdout.splitlines()[:8]),
            }
        )
        if code != 0 or not stdout.strip():
            continue
        reader = csv.DictReader(StringIO(stdout))
        for raw in reader:
            ref = raw.get("ref", "")
            title = raw.get("title", "")
            reason, ready = disposition("kaggle", title, ref)
            rows.append(
                {
                    "surface": "kaggle",
                    "query": query,
                    "id": ref,
                    "title": title,
                    "url": f"https://www.kaggle.com/datasets/{ref}",
                    "updated_at": raw.get("lastUpdated", ""),
                    "score": raw.get("downloadCount", ""),
                    "disposition": reason,
                    "ready_native_subhour_source_labels": ready,
                }
            )
    return rows, readbacks


def collect_hf() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    readbacks: list[dict[str, object]] = []
    for query in HF_QUERIES:
        url = "https://huggingface.co/api/datasets?" + urllib.parse.urlencode(
            {"search": query, "limit": 10}
        )
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                data = json.load(resp)
            error = ""
        except Exception as exc:  # pragma: no cover - live network guard
            data = []
            error = f"{type(exc).__name__}: {exc}"
        readbacks.append(
            {
                "surface": "huggingface",
                "query": query,
                "returncode": 0 if not error else 1,
                "stderr": error,
                "stdout_head": json.dumps(data[:5], ensure_ascii=False)[:2000],
            }
        )
        for item in data:
            dataset_id = item.get("id", "")
            tags = " ".join(item.get("tags", []) or [])
            reason, ready = disposition("huggingface", dataset_id, tags)
            rows.append(
                {
                    "surface": "huggingface",
                    "query": query,
                    "id": dataset_id,
                    "title": dataset_id,
                    "url": f"https://huggingface.co/datasets/{dataset_id}",
                    "updated_at": item.get("lastModified", ""),
                    "score": item.get("downloads", ""),
                    "disposition": reason,
                    "ready_native_subhour_source_labels": ready,
                }
            )
    return rows, readbacks


def collect_github() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    readbacks: list[dict[str, object]] = []
    env = os.environ.copy()
    env["GODEBUG"] = "tls13=0"
    for query in GH_QUERIES:
        code, stdout, stderr = run_cmd(
            [
                "gh",
                "search",
                "repos",
                query,
                "--limit",
                "8",
                "--json",
                "fullName,description,url,updatedAt,stargazersCount",
            ],
            env=env,
        )
        readbacks.append(
            {
                "surface": "github",
                "query": query,
                "returncode": code,
                "stderr": stderr.strip(),
                "stdout_head": stdout[:2000],
            }
        )
        if code != 0 or not stdout.strip():
            continue
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            data = []
        for item in data:
            name = item.get("fullName", "")
            desc = item.get("description", "") or ""
            reason, ready = disposition("github", name, desc)
            rows.append(
                {
                    "surface": "github",
                    "query": query,
                    "id": name,
                    "title": desc,
                    "url": item.get("url", ""),
                    "updated_at": item.get("updatedAt", ""),
                    "score": item.get("stargazersCount", ""),
                    "disposition": reason,
                    "ready_native_subhour_source_labels": ready,
                }
            )
    return rows, readbacks


def dedupe(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[object, object]] = set()
    out: list[dict[str, object]] = []
    for row in rows:
        key = (row["surface"], row["id"])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    rows: list[dict[str, object]] = []
    readbacks: list[dict[str, object]] = []
    for collector in (collect_kaggle, collect_hf, collect_github):
        new_rows, new_readbacks = collector()
        rows.extend(new_rows)
        readbacks.extend(new_readbacks)
    rows = dedupe(rows)

    ready_count = sum(1 for row in rows if row["ready_native_subhour_source_labels"])
    decision = "native_subhour_source_recheck_v2=no_ready_native_subhour_source_owned_labels"
    if ready_count:
        decision = "native_subhour_source_recheck_v2=potential_ready_native_subhour_sources_need_intake"

    candidate_csv = OUT_DIR / "native_subhour_source_recheck_v2_candidates.csv"
    fieldnames = [
        "surface",
        "query",
        "id",
        "title",
        "url",
        "updated_at",
        "score",
        "disposition",
        "ready_native_subhour_source_labels",
    ]
    with candidate_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    readback_csv = OUT_DIR / "native_subhour_source_recheck_v2_readbacks.csv"
    with readback_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["surface", "query", "returncode", "stderr", "stdout_head"]
        )
        writer.writeheader()
        writer.writerows(readbacks)

    disposition_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["disposition"])
        disposition_counts[key] = disposition_counts.get(key, 0) + 1

    summary = {
        "scan_started_at": started,
        "kaggle_queries": KAGGLE_QUERIES,
        "huggingface_queries": HF_QUERIES,
        "github_queries": GH_QUERIES,
        "candidate_records": len(rows),
        "ready_native_subhour_source_owned_label_sources": ready_count,
        "disposition_counts": disposition_counts,
        "decision": decision,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "native_subhour_source_overlap_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT_DIR / "native_subhour_source_recheck_v2.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    report = [
        "# Native Subhour Source Recheck v2",
        "",
        f"- Decision: `{decision}`",
        f"- Kaggle queries: `{len(KAGGLE_QUERIES)}`",
        f"- Hugging Face queries: `{len(HF_QUERIES)}`",
        f"- GitHub queries: `{len(GH_QUERIES)}`",
        f"- Candidate records: `{len(rows)}`",
        f"- Ready native sub-hour source-owned label sources: `{ready_count}`",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "Disposition summary:",
    ]
    for key, count in sorted(disposition_counts.items()):
        report.append(f"- `{key}`: `{count}`")
    report.extend(
        [
            "",
            "No raw rows were downloaded or committed. HMM/classifier datasets, raw",
            "provider panels, synthetic panels, bots, and research-code surfaces remain",
            "fail-closed for Board A native sub-hour source-label validation.",
        ]
    )
    (OUT_DIR / "native_subhour_source_recheck_v2.md").write_text("\n".join(report) + "\n")

    assertions = [
        f"decision={decision}",
        f"candidate_records={len(rows)}",
        f"ready_native_subhour_source_owned_label_sources={ready_count}",
        "native_subhour_source_overlap_closed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "native_subhour_source_recheck_v2_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
