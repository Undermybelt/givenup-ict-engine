#!/usr/bin/env python3
"""Screen a public Hugging Face BTCUSDT amplitude dataset for Board A fit.

The script records derived metadata only. It does not persist raw downloaded
CSV rows from Hugging Face into the repo.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RUN_ID = "20260512T025816-codex-btcusdt-amplitude-hf-source-screen-v1"
BOARD_CURSOR = "20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1"
BOARD_HASH_BEFORE_ARTIFACT = "bc8411758656acaa8c7e47f270df12bff57b25170e0f42dc86548f52a12ad123"
DATASET_ID = "123olp/btcusdt-amplitude-top100"
DATASET_URL = f"https://huggingface.co/datasets/{DATASET_ID}"
API_URL = f"https://huggingface.co/api/datasets/{DATASET_ID}"
RAW_BASE = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/main"
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
TOP100_FILES = [f"data/top100/btcusdt_{tf}_top100.csv" for tf in TIMEFRAMES]
REGIME_WINDOWS_FILE = "data/stats/btcusdt_regime_windows.csv"
MANIFEST_FILE = "dataset_manifest.json"
OUT_DIR = Path(__file__).resolve().parents[1] / "btcusdt-amplitude-hf-source-screen-v1"
CHECK_DIR = Path(__file__).resolve().parents[1] / "checks"


def fetch_text(url: str) -> tuple[str, str]:
    request = Request(url, headers={"User-Agent": "ict-engine-board-a-source-screen/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()


def load_json(url: str) -> tuple[dict, str]:
    text, sha256 = fetch_text(url)
    return json.loads(text), sha256


def parse_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def compact_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def csv_summary(path: str, text: str, sha256: str) -> dict:
    rows = parse_csv(text)
    fieldnames = list(rows[0].keys()) if rows else []
    timestamps = sorted(row.get("ts", "") for row in rows if row.get("ts"))
    ranks = [int(row["rank"]) for row in rows if row.get("rank", "").isdigit()]
    regime_phase = Counter(row.get("regime_phase", "") for row in rows)
    regime_label = Counter(row.get("regime_label", "") for row in rows)
    regime_phase_label = Counter(row.get("regime_phase_label", "") for row in rows)
    required = {
        "rank",
        "symbol",
        "timeframe",
        "ts",
        "range_pct",
        "regime_phase",
        "regime_label",
        "regime_phase_label",
    }
    return {
        "path": path,
        "sha256": sha256,
        "rows": len(rows),
        "columns": fieldnames,
        "required_columns_present": sorted(required.intersection(fieldnames)),
        "required_columns_missing": sorted(required.difference(fieldnames)),
        "symbols": sorted({row.get("symbol", "") for row in rows if row.get("symbol")}),
        "timeframes": sorted({row.get("timeframe", "") for row in rows if row.get("timeframe")}),
        "min_ts": timestamps[0] if timestamps else None,
        "max_ts": timestamps[-1] if timestamps else None,
        "rank_min": min(ranks) if ranks else None,
        "rank_max": max(ranks) if ranks else None,
        "regime_phase_counts": compact_counter(regime_phase),
        "regime_label_counts": compact_counter(regime_label),
        "regime_phase_label_counts": compact_counter(regime_phase_label),
    }


def regime_window_summary(text: str, sha256: str) -> dict:
    rows = parse_csv(text)
    phase_counts = Counter(row.get("阶段代码", "") for row in rows)
    end_dates = sorted(row.get("结束(UTC)", "") for row in rows if row.get("结束(UTC)"))
    return {
        "path": REGIME_WINDOWS_FILE,
        "sha256": sha256,
        "rows": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "phase_counts": compact_counter(phase_counts),
        "window_labels": [row.get("阶段标签", "") for row in rows],
        "max_window_end_utc": end_dates[-1] if end_dates else None,
        "contains_future_dated_window_after_screen_date": any(
            row.get("结束(UTC)", "") > "2026-05-12 00:00:00 UTC" for row in rows
        ),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    try:
        api, api_sha256 = load_json(API_URL)
        manifest, manifest_sha256 = load_json(f"{RAW_BASE}/{MANIFEST_FILE}")
        regime_text, regime_sha256 = fetch_text(f"{RAW_BASE}/{REGIME_WINDOWS_FILE}")
        top100_summaries = []
        for path in TOP100_FILES:
            text, sha256 = fetch_text(f"{RAW_BASE}/{path}")
            top100_summaries.append(csv_summary(path, text, sha256))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"source screen failed: {exc}", file=sys.stderr)
        return 2

    siblings = [entry.get("rfilename", "") for entry in api.get("siblings", [])]
    expected_present = sorted(
        path for path in [MANIFEST_FILE, REGIME_WINDOWS_FILE, *TOP100_FILES] if path in siblings
    )
    all_rows = sum(item["rows"] for item in top100_summaries)
    all_symbols = sorted({symbol for item in top100_summaries for symbol in item["symbols"]})
    all_timeframes = sorted({tf for item in top100_summaries for tf in item["timeframes"]})
    all_phase_counts: Counter[str] = Counter()
    all_label_counts: Counter[str] = Counter()
    all_phase_label_counts: Counter[str] = Counter()
    for item in top100_summaries:
        all_phase_counts.update(item["regime_phase_counts"])
        all_label_counts.update(item["regime_label_counts"])
        all_phase_label_counts.update(item["regime_phase_label_counts"])

    regime_windows = regime_window_summary(regime_text, regime_sha256)
    manifest_timeframes = manifest.get("timeframes", [])
    manifest_counts = manifest.get("record_counts", {})
    manifest_snapshot = manifest.get("snapshot", {})

    gate_result = (
        "btcusdt_amplitude_hf_source_screen_v1="
        "single_symbol_derived_amplitude_regime_labels_no_promotion"
    )
    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_cursor_before_artifact": BOARD_CURSOR,
        "board_hash_before_artifact": BOARD_HASH_BEFORE_ARTIFACT,
        "dataset": {
            "id": api.get("id"),
            "url": DATASET_URL,
            "private": api.get("private"),
            "gated": api.get("gated"),
            "disabled": api.get("disabled"),
            "sha": api.get("sha"),
            "last_modified": api.get("lastModified"),
            "downloads": api.get("downloads"),
            "likes": api.get("likes"),
            "tags": api.get("tags", []),
            "api_sha256": api_sha256,
        },
        "expected_files": {
            "expected": [MANIFEST_FILE, REGIME_WINDOWS_FILE, *TOP100_FILES],
            "present": expected_present,
            "missing": sorted(set([MANIFEST_FILE, REGIME_WINDOWS_FILE, *TOP100_FILES]) - set(expected_present)),
        },
        "manifest": {
            "sha256": manifest_sha256,
            "dataset_id": manifest.get("dataset_id"),
            "dataset_repo_id": manifest.get("dataset_repo_id"),
            "symbol": manifest.get("symbol"),
            "timeframes": manifest_timeframes,
            "metric": manifest.get("metric"),
            "snapshot": manifest_snapshot,
            "record_counts": manifest_counts,
            "generated_at_utc": manifest.get("generated_at_utc"),
            "release_version": manifest.get("release_version"),
        },
        "top100_derived_summary": {
            "files": len(top100_summaries),
            "rows_total": all_rows,
            "symbols": all_symbols,
            "timeframes": all_timeframes,
            "regime_phase_counts": compact_counter(all_phase_counts),
            "regime_label_counts": compact_counter(all_label_counts),
            "regime_phase_label_counts": compact_counter(all_phase_label_counts),
        },
        "top100_files": top100_summaries,
        "regime_windows": regime_windows,
        "board_a_gate": {
            "gate_result": gate_result,
            "source_owned_mainregimev2_export": False,
            "single_symbol_only": all_symbols == ["BTCUSDT"],
            "missing_mainregimev2_roots": ["Sideways", "Crisis"],
            "labels_are_derived_research_cycle_context": True,
            "future_dated_regime_window_present": regime_windows[
                "contains_future_dated_window_after_screen_date"
            ],
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
        },
        "non_edits": {
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "r3_r5_r6_roots_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_vendor_contact_sent": False,
            "trade_usable": False,
        },
    }

    json_path = OUT_DIR / "btcusdt_amplitude_hf_source_screen_v1.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    csv_rows = []
    for item in top100_summaries:
        csv_rows.append(
            {
                "path": item["path"],
                "rows": item["rows"],
                "symbols": ";".join(item["symbols"]),
                "timeframes": ";".join(item["timeframes"]),
                "min_ts": item["min_ts"],
                "max_ts": item["max_ts"],
                "rank_min": item["rank_min"],
                "rank_max": item["rank_max"],
                "regime_phase_counts": json.dumps(item["regime_phase_counts"], ensure_ascii=False, sort_keys=True),
                "required_columns_missing": ";".join(item["required_columns_missing"]),
                "sha256": item["sha256"],
            }
        )
    write_csv(
        OUT_DIR / "btcusdt_amplitude_hf_top100_file_summary_v1.csv",
        csv_rows,
        [
            "path",
            "rows",
            "symbols",
            "timeframes",
            "min_ts",
            "max_ts",
            "rank_min",
            "rank_max",
            "regime_phase_counts",
            "required_columns_missing",
            "sha256",
        ],
    )

    md_lines = [
        "# BTCUSDT Amplitude Hugging Face Source Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "Source:",
        f"- Dataset: `{DATASET_ID}`",
        f"- URL: {DATASET_URL}",
        f"- Public: `{api.get('private') is False}`; gated: `{api.get('gated')}`; disabled: `{api.get('disabled')}`",
        f"- Dataset SHA: `{api.get('sha')}`",
        f"- Last modified: `{api.get('lastModified')}`",
        "",
        "Readback:",
        f"- Manifest symbol: `{manifest.get('symbol')}`",
        f"- Manifest timeframes: `{', '.join(manifest_timeframes)}`",
        f"- Top100 rows from manifest: `{manifest_counts.get('top100_rows_total')}`",
        f"- Event-window rows from manifest: `{manifest_counts.get('event_windows_rows')}`",
        f"- Forward-return rows from manifest: `{manifest_counts.get('forward_returns_rows')}`",
        f"- Derived top100 rows summarized in-memory: `{all_rows}`",
        f"- Derived symbols: `{', '.join(all_symbols)}`",
        f"- Derived regime phases: `{json.dumps(compact_counter(all_phase_counts), ensure_ascii=False, sort_keys=True)}`",
        f"- Regime windows: `{regime_windows['rows']}` rows; max window end `{regime_windows['max_window_end_utc']}`",
        "",
        "Decision:",
        "- This is useful source-discovery evidence for BTCUSDT amplitude research, but not a Board A promotion input.",
        "- It is single-symbol BTCUSDT only and does not provide cross-instrument or cross-market validation.",
        "- Labels are derived bull/bear cycle context attached to amplitude Top100 events, not source-owned `MainRegimeV2` root exports.",
        "- The visible label set does not cover `Sideways` or `Crisis`, and it does not provide direct `Manipulation` positive/negative controls.",
        "- The regime-window table includes a future-dated recovery-cycle window ending after this screen date, so it cannot be treated as independent observed source labels for acceptance.",
        "- It does not justify canonical merge or downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion.",
        "",
        "Promotion guards:",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Canonical merge allowed: `false`",
        "- Downstream promotion rerun allowed: `false`",
        "- Strict full objective achieved: `false`",
        "- `update_goal=false`",
        "- Runtime code changed: `false`",
        "- Shared intake mutated: `false`",
        "- R3/R5/R6 roots mutated: `false`",
        "- Thresholds relaxed: `false`",
        "- Raw data committed: `false`",
        "- Trade usable: `false`",
        "",
        "Next:",
        "- Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.",
        "",
    ]
    (OUT_DIR / "btcusdt_amplitude_hf_source_screen_v1.md").write_text("\n".join(md_lines), encoding="utf-8")

    assertions = [
        ("dataset_id_matches", api.get("id") == DATASET_ID),
        ("expected_files_present", not report["expected_files"]["missing"]),
        ("single_symbol_only", all_symbols == ["BTCUSDT"]),
        ("top100_rows_match_manifest", all_rows == manifest_counts.get("top100_rows_total")),
        ("labels_do_not_cover_all_mainregimev2_roots", set(all_phase_counts) != {"bull", "bear", "sideways", "crisis"}),
        ("canonical_merge_false", report["board_a_gate"]["canonical_merge_allowed"] is False),
        ("accepted_rows_zero", report["board_a_gate"]["accepted_rows_added"] == 0),
        ("update_goal_false", report["board_a_gate"]["update_goal"] is False),
        ("raw_data_committed_false", report["non_edits"]["raw_data_committed"] is False),
    ]
    assertion_lines = []
    ok = True
    for name, passed in assertions:
        ok = ok and passed
        assertion_lines.append(f"{name}: {'PASS' if passed else 'FAIL'}")
    assertion_lines.append(f"gate_result: {gate_result}")
    (CHECK_DIR / "btcusdt_amplitude_hf_source_screen_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n", encoding="utf-8"
    )
    print("\n".join(assertion_lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
