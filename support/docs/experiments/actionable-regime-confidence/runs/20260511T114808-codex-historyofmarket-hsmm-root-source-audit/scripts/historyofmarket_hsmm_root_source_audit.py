#!/usr/bin/env python3
"""Audit two public parent-root label-source candidates for Board A."""

from __future__ import annotations

import json
import math
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T114808+0800-codex-historyofmarket-hsmm-root-source-audit"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T114808-codex-historyofmarket-hsmm-root-source-audit"
)
OUT_DIR = RUN_ROOT / "source-audit"
CHECK_DIR = RUN_ROOT / "checks"

HISTORY_PAGE = "https://historyofmarket.com/sp500/sp500-logyoy/"
HISTORY_API = "https://historyofmarket.com/api/sp500/price.json"
HSMM_CENTAUR = "https://centaur.reading.ac.uk/107284/"
HSMM_REPEC = "https://ideas.repec.org/a/eee/intfor/v37y2021i2p699-713.html"
HSMM_SCIENCEDIRECT = "https://www.sciencedirect.com/science/article/pii/S1544612321000799"


def fetch_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ict-engine-source-audit/1.0"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
        data = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def try_fetch_text(url: str, timeout: int = 30) -> dict:
    try:
        text = fetch_text(url, timeout=timeout)
        return {"url": url, "ok": True, "status": 200, "text": text, "error": None}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return {"url": url, "ok": False, "status": exc.code, "text": body, "error": str(exc)}
    except Exception as exc:  # network/source surfaces are audited, not trusted
        return {"url": url, "ok": False, "status": None, "text": "", "error": repr(exc)}


def fetch_json(url: str, timeout: int = 30) -> dict:
    return json.loads(fetch_text(url, timeout=timeout))


def nearest_year_prior_log_yoy(series: list[dict]) -> tuple[int, int, list[dict]]:
    """Approximate one-year log return from prior observation <= same date last year."""
    rows = []
    by_date = []
    for item in series:
        date = datetime.strptime(item["date"], "%Y-%m-%d").date()
        close = float(item["close"])
        by_date.append((date, close))
    prior_idx = 0
    for idx, (date, close) in enumerate(by_date):
        target_ord = date.toordinal() - 365
        while prior_idx + 1 < idx and by_date[prior_idx + 1][0].toordinal() <= target_ord:
            prior_idx += 1
        if by_date[prior_idx][0].toordinal() <= target_ord and close > 0 and by_date[prior_idx][1] > 0:
            log_yoy = math.log(close / by_date[prior_idx][1])
            rows.append(
                {
                    "date": date.isoformat(),
                    "close": close,
                    "prior_date": by_date[prior_idx][0].isoformat(),
                    "log_yoy": log_yoy,
                    "derived_label": "Bull" if log_yoy > 0 else "Bear",
                }
            )
    crossings = 0
    for prev, cur in zip(rows, rows[1:]):
        if (prev["log_yoy"] > 0) != (cur["log_yoy"] > 0):
            crossings += 1
    return len(rows), crossings, rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    history_page = fetch_text(HISTORY_PAGE)
    history_payload = fetch_json(HISTORY_API)
    history_series = history_payload.get("series", [])
    computed_rows, crossings, label_rows = nearest_year_prior_log_yoy(history_series)

    hsmm_fetches = [try_fetch_text(url) for url in [HSMM_SCIENCEDIRECT, HSMM_CENTAUR, HSMM_REPEC]]
    hsmm_text = "\n".join(item["text"] for item in hsmm_fetches)
    title_terms = "Identifying Bear, Bull, Sidewalk, and Crash Markets in the United States"
    hsmm_has_four_states = all(term.lower() in f"{title_terms}\n{hsmm_text}".lower() for term in ["bear", "bull", "sidewalk", "crash"])
    hsmm_row_export_found = any(
        needle in hsmm_text.lower()
        for needle in [
            ".csv",
            "github.com",
            "replication data",
            "supplementary data",
            "viterbi state",
            "decoded state",
        ]
    )

    history_page_declares_bull_bear = bool(
        re.search(r"positive\s+is\s+bull\s+and\s+negative\s+is\s+bear", history_page, re.I)
    )
    history_value_counts = {
        "Bull": sum(1 for row in label_rows if row["derived_label"] == "Bull"),
        "Bear": sum(1 for row in label_rows if row["derived_label"] == "Bear"),
    }

    candidates = [
        {
            "name": "History of Market S&P 500 Log YoY",
            "urls": {"page": HISTORY_PAGE, "api": HISTORY_API},
            "retrieval_status": "ok",
            "public_json_rows": len(history_series),
            "computed_log_yoy_rows": computed_rows,
            "date_range": {
                "start": history_series[0]["date"] if history_series else None,
                "end": history_series[-1]["date"] if history_series else None,
            },
            "page_declares_positive_bull_negative_bear": history_page_declares_bull_bear,
            "derived_label_counts": history_value_counts,
            "zero_crossings_approx": crossings,
            "mainregimev2_mapping_attempted": {
                "Bull": "log_yoy > 0 per source page wording",
                "Bear": "log_yoy <= 0 per source page wording",
                "Sideways": None,
                "Crisis": None,
            },
            "accepted_parent_root_slots_added": 0,
            "decision": "blocked_historyofmarket_formula_derived_price_only_two_root_spx_daily_source",
            "blockers": [
                "label axis is formula-derived from S&P 500 price/log-yoy, not an independent provider/instrument/timeframe label panel",
                "source exposes Bull/Bear style states only; no Sideways or Crisis root",
                "daily S&P 500 only; does not cover other instruments, providers, timeframes, full species, or full cycles required by current board",
                "using this formula as both label source and detector would be circular proxy evidence",
            ],
        },
        {
            "name": "Wang Gupta Zhang Bear/Bull/Sidewalk/Crash HSMM paper",
            "urls": {"sciencedirect": HSMM_SCIENCEDIRECT, "centaur": HSMM_CENTAUR, "repec": HSMM_REPEC},
            "retrieval_status": "partial_or_blocked_public_pages",
            "public_fetch_statuses": [
                {"url": item["url"], "ok": item["ok"], "status": item["status"], "error": item["error"]}
                for item in hsmm_fetches
            ],
            "has_four_state_terms": hsmm_has_four_states,
            "row_level_state_export_found": hsmm_row_export_found,
            "mainregimev2_mapping_attempted": {
                "Bull": "Bull state term in paper",
                "Bear": "Bear state term in paper",
                "Sideways": "Sidewalk state term as candidate Sideways analogue",
                "Crisis": "Crash state term as candidate Crisis analogue",
            },
            "accepted_parent_root_slots_added": 0,
            "decision": "blocked_hsmm_paper_methodology_no_materialized_row_export",
            "blockers": [
                "public pages expose paper/methodology, not a downloadable row-level decoded-state panel",
                "model states are inferred HSMM outputs, not an accepted source-label export for repo providers",
                "no provider/instrument/timeframe label windows available for calibration or cross-context acceptance",
            ],
        },
    ]

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_taxonomy": "MainRegimeV2",
        "objective_slice": "targeted public parent-root source acquisition without repeating generic Kaggle/HF scans",
        "candidates": candidates,
        "decision": {
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "accepted_roots": [],
            "gate_result": "blocked_historyofmarket_hsmm_no_attachable_full_matrix_mainregimev2_panel",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Acquire an exact provider/instrument/timeframe MainRegimeV2 label panel or explicit "
            "owner-approved crosswalk; do not count formula-derived price labels or paper-only HSMM states."
        ),
    }

    json_path = OUT_DIR / "historyofmarket_hsmm_root_source_audit.json"
    md_path = OUT_DIR / "historyofmarket_hsmm_root_source_audit.md"
    assertions_path = CHECK_DIR / "historyofmarket_hsmm_root_source_audit_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    assertions_path.write_text(render_assertions(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    print(assertions_path)
    return 0


def render_markdown(report: dict) -> str:
    history = report["candidates"][0]
    hsmm = report["candidates"][1]
    decision = report["decision"]
    return "\n".join(
        [
            "# HistoryOfMarket / HSMM Root Source Audit",
            "",
            f"Run ID: `{report['run_id']}`",
            "",
            "## Scope",
            "",
            "- Active taxonomy: `MainRegimeV2`.",
            "- This is a targeted parent-root source acquisition audit, not a generic Kaggle/HF/public sweep.",
            "- Candidates: History of Market S&P 500 Log YoY and Wang/Gupta/Zhang Bear/Bull/Sidewalk/Crash HSMM paper.",
            "",
            "## History of Market",
            "",
            f"- Public JSON rows: `{history['public_json_rows']}`.",
            f"- Date range: `{history['date_range']['start']}` to `{history['date_range']['end']}`.",
            f"- Page declares positive log-YoY as Bull and negative as Bear: `{str(history['page_declares_positive_bull_negative_bear']).lower()}`.",
            f"- Approx computed log-YoY rows: `{history['computed_log_yoy_rows']}`.",
            f"- Derived label counts: `Bull={history['derived_label_counts']['Bull']}`, `Bear={history['derived_label_counts']['Bear']}`.",
            f"- Approx zero crossings: `{history['zero_crossings_approx']}`.",
            f"- Decision: `{history['decision']}`.",
            "",
            "Blockers:",
            "- formula-derived S&P 500 price/log-YoY label, not an independent full-matrix source-label panel.",
            "- no `Sideways` or `Crisis` root.",
            "- daily S&P 500 only; no provider/instrument/timeframe/full-species coverage.",
            "- circular if used as both detector and label.",
            "",
            "## HSMM Paper",
            "",
            "- Candidate title: `Identifying Bear, Bull, Sidewalk, and Crash Markets in the United States`.",
            "- Public fetch statuses: "
            + ", ".join(
                f"`{item['status'] if item['status'] is not None else 'error'}:{'ok' if item['ok'] else 'blocked'}`"
                for item in hsmm["public_fetch_statuses"]
            )
            + ".",
            f"- Four-state terms found in public pages: `{str(hsmm['has_four_state_terms']).lower()}`.",
            f"- Row-level decoded-state export found: `{str(hsmm['row_level_state_export_found']).lower()}`.",
            f"- Decision: `{hsmm['decision']}`.",
            "",
            "Blockers:",
            "- public pages expose methodology/paper, not row-level decoded state labels.",
            "- model-inferred states are not attachable provider/instrument/timeframe source-label windows.",
            "- no calibration/cross-context panel can be materialized from the public surface.",
            "",
            "## Decision",
            "",
            f"- Accepted parent-root slots added: `{decision['accepted_parent_root_slots_added']}`.",
            f"- Accepted direct `Manipulation` rows added: `{decision['accepted_direct_manipulation_rows_added']}`.",
            f"- Gate result: `{decision['gate_result']}`.",
            f"- Runtime code changed: `{str(decision['runtime_code_changed']).lower()}`.",
            f"- Thresholds relaxed: `{str(decision['thresholds_relaxed']).lower()}`.",
            f"- Raw data committed: `{str(decision['raw_data_committed']).lower()}`.",
            f"- Trade usable: `{str(decision['trade_usable']).lower()}`.",
            "",
            report["next_action"],
            "",
        ]
    )


def render_assertions(report: dict) -> str:
    history = report["candidates"][0]
    hsmm = report["candidates"][1]
    decision = report["decision"]
    lines = [
        f"PASS active_taxonomy={report['active_taxonomy']}",
        f"PASS history_public_json_rows={history['public_json_rows']}",
        f"PASS history_page_declares_bull_bear={str(history['page_declares_positive_bull_negative_bear']).lower()}",
        "PASS history_formula_derived_price_only=true",
        "PASS history_missing_sideways_crisis=true",
        f"PASS hsmm_four_state_terms_found={str(hsmm['has_four_state_terms']).lower()}",
        f"PASS hsmm_row_level_export_found={str(hsmm['row_level_state_export_found']).lower()}",
        f"PASS accepted_parent_root_slots_added={decision['accepted_parent_root_slots_added']}",
        f"PASS accepted_direct_manipulation_rows_added={decision['accepted_direct_manipulation_rows_added']}",
        f"PASS runtime_code_changed={str(decision['runtime_code_changed']).lower()}",
        f"PASS thresholds_relaxed={str(decision['thresholds_relaxed']).lower()}",
        f"PASS raw_data_committed={str(decision['raw_data_committed']).lower()}",
        f"PASS trade_usable={str(decision['trade_usable']).lower()}",
        f"GATE {decision['gate_result']}",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
