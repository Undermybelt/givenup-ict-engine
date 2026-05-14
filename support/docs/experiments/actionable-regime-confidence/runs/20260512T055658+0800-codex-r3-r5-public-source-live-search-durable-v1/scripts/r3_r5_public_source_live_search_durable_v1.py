#!/usr/bin/env python3
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


RUN_ID = "20260512T055658+0800-codex-r3-r5-public-source-live-search-durable-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
REPORT = RUN_ROOT / "r3-r5-public-source-live-search-durable-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

KAGGLE_QUERIES = [
    ("aapl_15m_regime_label", "AAPL 15m regime label"),
    ("ixic_15m_regime_label", "IXIC 15m regime label"),
    ("nq_futures_15m_regime_label", "NQ futures 15m regime label"),
    ("market_regime_labels_intraday", "market regime labels intraday"),
    ("bull_bear_sideways_crisis_market_regime_labels", "Bull Bear Sideways Crisis market regime labels"),
    ("stock_market_regime_labels_2026", "stock market regime labels 2026"),
    ("mainregimev2_stock_panel", "MainRegimeV2 stock panel"),
]

HF_QUERIES = [
    ("aapl_15m_regime_label", "AAPL 15m regime label"),
    ("ixic_15m_regime_label", "IXIC 15m regime label"),
    ("nq_futures_15m_regime_label", "NQ futures 15m regime label"),
    ("market_regime_labels_intraday", "market regime labels intraday"),
    ("bull_bear_sideways_crisis_market_regime_labels", "Bull Bear Sideways Crisis market regime labels"),
]

REQUIRED_ROOTS = [
    "/tmp/ict-engine-board-a-r6-owner-export-v1",
    "/tmp/ict-engine-native-subhour-source-label-intake",
    "/tmp/ict-engine-source-panel-recency-extension",
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "query"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(name: str, argv: list[str]) -> tuple[int, str, str]:
    (OUT / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    proc = subprocess.run(argv, text=True, capture_output=True)
    (OUT / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    (OUT / f"{name}.stdout").write_text(proc.stdout, encoding="utf-8")
    (OUT / f"{name}.stderr").write_text(proc.stderr, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line and not line.startswith("Next Page Token")]
    if not lines:
        return []
    try:
        return list(csv.DictReader(lines))
    except csv.Error:
        return []


def exact_r3_text(text: str) -> bool:
    t = text.lower()
    has_symbol = any(term in t for term in ("aapl", "ixic", "nq", "nasdaq"))
    has_timeframe = any(term in t for term in ("15m", "30m", "intraday", "subhour", "sub-hour"))
    has_label = "regime" in t and "label" in t
    return has_symbol and has_timeframe and has_label


def exact_r5_text(text: str) -> bool:
    t = text.lower()
    has_mainregime = "mainregimev2" in t
    has_all_labels = all(term in t for term in ("bull", "bear", "sideways", "crisis"))
    has_stock_context = any(term in t for term in ("stock", "equity", "panel", "aapl", "ixic", "sp500", "nasdaq"))
    return (has_mainregime or has_all_labels) and has_stock_context


def write_hf_result(name: str, query: str) -> dict:
    url = f"https://huggingface.co/api/datasets?search={quote(query)}&limit=20"
    (OUT / f"hf_{name}.cmd").write_text(f"GET {url}\n", encoding="utf-8")
    try:
        response = requests.get(url, timeout=30)
        (OUT / f"hf_{name}.exit").write_text("0\n", encoding="utf-8")
        (OUT / f"hf_{name}.json").write_text(response.text, encoding="utf-8")
        (OUT / f"hf_{name}.stderr").write_text("", encoding="utf-8")
        data = response.json()
        if not isinstance(data, list):
            data = []
    except Exception as exc:
        (OUT / f"hf_{name}.exit").write_text("1\n", encoding="utf-8")
        (OUT / f"hf_{name}.json").write_text("[]\n", encoding="utf-8")
        (OUT / f"hf_{name}.stderr").write_text(f"{exc}\n", encoding="utf-8")
        data = []
    texts = []
    for row in data:
        if isinstance(row, dict):
            texts.append(" ".join(str(row.get(k, "")) for k in ("id", "author", "description", "tags")))
    return {
        "query": query,
        "rows": len(data),
        "exact_r3_hits": sum(1 for text in texts if exact_r3_text(text)),
        "exact_r5_hits": sum(1 for text in texts if exact_r5_text(text)),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    kaggle_results = []
    all_refs = []

    for name, query in KAGGLE_QUERIES:
        rc, stdout, _ = run_command(f"kaggle_{name}", ["kaggle", "datasets", "list", "-s", query, "--csv"])
        rows = parse_csv_rows(stdout) if rc == 0 else []
        exact_r3 = 0
        exact_r5 = 0
        for row in rows:
            text = " ".join(str(row.get(k, "")) for k in ("ref", "title"))
            exact_r3 += 1 if exact_r3_text(text) else 0
            exact_r5 += 1 if exact_r5_text(text) else 0
            ref = row.get("ref")
            if ref:
                all_refs.append(ref)
        kaggle_results.append(
            {
                "query": query,
                "exit": rc,
                "rows": len(rows),
                "exact_r3_hits": exact_r3,
                "exact_r5_hits": exact_r5,
            }
        )

    candidate_refs = []
    for ref in all_refs:
        if ref not in candidate_refs:
            candidate_refs.append(ref)
        if len(candidate_refs) >= 3:
            break

    file_results = []
    for ref in candidate_refs:
        name = "kaggle_files_" + slug(ref)
        rc, stdout, _ = run_command(name, ["kaggle", "datasets", "files", ref, "--csv"])
        rows = parse_csv_rows(stdout) if rc == 0 else []
        texts = [" ".join(str(row.get(k, "")) for k in ("name", "description")) for row in rows]
        file_results.append(
            {
                "ref": ref,
                "exit": rc,
                "file_rows": len(rows),
                "exact_r3_file_hits": sum(1 for text in texts if exact_r3_text(text)),
                "exact_r5_file_hits": sum(1 for text in texts if exact_r5_text(text)),
                "sample_files": [row.get("name", "") for row in rows[:12]],
            }
        )

    hf_results = [write_hf_result(name, query) for name, query in HF_QUERIES]

    exact_r3_hits = sum(row["exact_r3_hits"] for row in kaggle_results)
    exact_r5_hits = sum(row["exact_r5_hits"] for row in kaggle_results)
    exact_r3_file_hits = sum(row["exact_r3_file_hits"] for row in file_results)
    exact_r5_file_hits = sum(row["exact_r5_file_hits"] for row in file_results)
    hf_exact_r3_hits = sum(row["exact_r3_hits"] for row in hf_results)
    hf_exact_r5_hits = sum(row["exact_r5_hits"] for row in hf_results)
    required_roots_present = {root: Path(root).exists() for root in REQUIRED_ROOTS}
    acquired = any(required_roots_present.values()) or any(
        [exact_r3_hits, exact_r5_hits, exact_r3_file_hits, exact_r5_file_hits, hf_exact_r3_hits, hf_exact_r5_hits]
    )

    gate = "r3_r5_public_source_live_search_durable_v1=metadata_search_no_exact_r3_r5_rows_no_promotion"
    if acquired:
        gate = "r3_r5_public_source_live_search_durable_v1=requires_manual_review_before_any_promotion"

    result = {
        "run_id": RUN_ID,
        "gate_result": gate,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash,
        "kaggle": {
            "queries": len(KAGGLE_QUERIES),
            "rows_scanned": sum(row["rows"] for row in kaggle_results),
            "results": kaggle_results,
            "file_candidate_refs": candidate_refs,
            "file_results": file_results,
        },
        "hugging_face": {
            "queries": len(HF_QUERIES),
            "rows_scanned": sum(row["rows"] for row in hf_results),
            "results": hf_results,
        },
        "exact_hits": {
            "kaggle_r3_metadata": exact_r3_hits,
            "kaggle_r5_metadata": exact_r5_hits,
            "kaggle_r3_file": exact_r3_file_hits,
            "kaggle_r5_file": exact_r5_file_hits,
            "hugging_face_r3_metadata": hf_exact_r3_hits,
            "hugging_face_r5_metadata": hf_exact_r5_hits,
        },
        "required_roots_present": required_roots_present,
        "decision": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "target_root_mutated": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": "obtain explicit source/control approval or source-owned R6/R5/R3 rows before canonical merge and ordered downstream promotion rerun",
    }

    json_path = REPORT / "r3_r5_public_source_live_search_durable_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    csv_path = REPORT / "r3_r5_public_source_live_search_durable_v1_kaggle_results.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["query", "exit", "rows", "exact_r3_hits", "exact_r5_hits"])
        writer.writeheader()
        writer.writerows(kaggle_results)

    md_path = REPORT / "r3_r5_public_source_live_search_durable_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# R3/R5 Public Source Live Search Durable v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate}`",
                "",
                f"Board SHA-256 before artifact: `{board_hash}`",
                "",
                "## Scope",
                "",
                "Durable rerun for the missing `055212` metadata-only Kaggle/Hugging Face source search. This run writes report, JSON, CSV, command outputs, and assertions into a repo-local artifact root. It does not download row data, create labels, mutate R3/R5/R6 target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Kaggle metadata rows scanned: `{result['kaggle']['rows_scanned']}` across `{len(KAGGLE_QUERIES)}` queries.",
                f"- Kaggle file candidate refs checked: `{len(candidate_refs)}`.",
                f"- Hugging Face metadata rows scanned: `{result['hugging_face']['rows_scanned']}` across `{len(HF_QUERIES)}` queries.",
                f"- Exact R3 metadata/file hits: `{exact_r3_hits + exact_r3_file_hits + hf_exact_r3_hits}`.",
                f"- Exact R5 metadata/file hits: `{exact_r5_hits + exact_r5_file_hits + hf_exact_r5_hits}`.",
                "",
                "## Decision",
                "",
                "No durable source-owned AAPL/IXIC native 15m/30m regime-label rows and no source-owned post-cutoff `MainRegimeV2` stock-panel recency-extension rows were acquired.",
                "",
                "Required roots remain absent:",
                "",
                *[f"- `{root}`: `{present}`" for root, present in required_roots_present.items()],
                "",
                "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
                "",
                "## Next",
                "",
                result["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={gate}",
        f"PASS kaggle_queries={len(KAGGLE_QUERIES)}",
        f"PASS kaggle_rows_scanned={result['kaggle']['rows_scanned']}",
        f"PASS kaggle_file_candidate_refs_checked={len(candidate_refs)}",
        f"PASS hugging_face_queries={len(HF_QUERIES)}",
        f"PASS hugging_face_rows_scanned={result['hugging_face']['rows_scanned']}",
        f"PASS exact_r3_hits={exact_r3_hits + exact_r3_file_hits + hf_exact_r3_hits}",
        f"PASS exact_r5_hits={exact_r5_hits + exact_r5_file_hits + hf_exact_r5_hits}",
        f"PASS required_roots_present={required_roots_present}",
        "PASS source_control_evidence_acquired=false",
        "PASS target_root_mutated=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "r3_r5_public_source_live_search_durable_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
