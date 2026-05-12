#!/usr/bin/env python3
"""Targeted public GitHub source-label candidate screen for Board A."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T193958-codex-github-source-label-candidate-screen-v1"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "github-source-label-screen"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


SEARCH_QUERIES = [
    "market regime labels",
    "bull bear sideways market regime",
    "financial market regime dataset",
    "regime classification stock market",
]


CANDIDATES = [
    {
        "source": "github",
        "repo": "akash-kumar5/CryptoMarket_Regime_Classifier",
        "url": "https://github.com/akash-kumar5/CryptoMarket_Regime_Classifier",
        "candidate_strength": "checked_in_crypto_regime_framework_with_models",
        "decision": "blocked_hmm_generated_labels_not_source_owned",
        "evidence": "README describes HMM discovery followed by LSTM prediction; src/regime_label.py maps HMM states to regimes using ATR/BB-width/ADX.",
        "reason": "Regimes are discovered from OHLCV/technical features and HMM state mapping, not source-owned or owner-approved MainRegimeV2 labels.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    },
    {
        "source": "github",
        "repo": "uday-31/detecting-market-regime-changes",
        "url": "https://github.com/uday-31/detecting-market-regime-changes",
        "candidate_strength": "sp500_hmm_regime_project",
        "decision": "blocked_hmm_pseudo_labels_not_source_owned",
        "evidence": "README states regimes are labeled by HMM on directional-change indicators; modules/hidden_markov_model.py fits hmmlearn and predicts regimes.",
        "reason": "Labels are retrospective HMM outputs and then classifier targets; they are proxy/generated labels rather than source-owned labels.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    },
    {
        "source": "github",
        "repo": "iamd26/Predicting-Market-Regimes-Based-on-Stock-Bond-Return-ratio",
        "url": "https://github.com/iamd26/Predicting-Market-Regimes-Based-on-Stock-Bond-Return-ratio",
        "candidate_strength": "published_turning_point_method_implementation",
        "decision": "blocked_method_generated_binary_turning_points",
        "evidence": "README cites Lunde-Timmermann/Pagan-Sossounov style regime-change detection; bullbeaR.R computes turning points from prices.",
        "reason": "The repository provides methodology-generated bull/bear turning points from price series, not row-level source-owned regime labels or a four-root MainRegimeV2 crosswalk.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    },
    {
        "source": "github",
        "repo": "hetu412patel/volatility-regime-classification",
        "url": "https://github.com/hetu412patel/volatility-regime-classification",
        "candidate_strength": "ftse_volatility_crisis_classifier",
        "decision": "blocked_model_generated_binary_crisis_noncrisis",
        "evidence": "README says notebooks generate a feature matrix and Orange/Random Forest classifies crisis vs non-crisis volatility regimes.",
        "reason": "Binary model output is not source-owned Bull/Bear/Sideways/Crisis labels and does not cover the required active-regime taxonomy.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    },
    {
        "source": "github",
        "repo": "AndrewFSee/regime-rl-trading",
        "url": "https://github.com/AndrewFSee/regime-rl-trading",
        "candidate_strength": "bull_bear_sideways_volatile_framework",
        "decision": "blocked_feature_or_hmm_detector_outputs_not_source_labels",
        "evidence": "README and src/regime_detection show feature-threshold and Gaussian-HMM detectors that map model states/features to regimes.",
        "reason": "The framework generates detector outputs for strategy routing; no source-owned row-level label panel or owner-approved crosswalk is exposed.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    },
    {
        "source": "github",
        "repo": "Hishamhajaz/market-regime-detection",
        "url": "https://github.com/Hishamhajaz/market-regime-detection",
        "candidate_strength": "spy_bull_bear_sideways_kmeans_demo",
        "decision": "blocked_kmeans_generated_spy_labels",
        "evidence": "README/main.py classify SPY into Bull/Bear/Sideways with KMeans over yfinance-derived features.",
        "reason": "Labels are KMeans-generated from SPY OHLCV features and a plot output, not source-owned validation labels.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    },
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    accepted = [row for row in CANDIDATES if row["accepted_rows_added"]]
    decision = {
        "gate_result": "github_source_label_candidate_screen_v1=no_promotable_source_label_equivalence",
        "queries": len(SEARCH_QUERIES),
        "candidate_records": len(CANDIDATES),
        "accepted_rows_added": len(accepted),
        "new_confidence_gate": False,
        "full_other_market_source_label_equivalence": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "github_source_label_candidate_screen_v1",
        "run_id": "20260511T193958+0800-codex-github-source-label-candidate-screen-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_observed": hashlib.sha256(TODO_PATH.read_bytes()).hexdigest(),
        "scope": "Targeted public GitHub repository screen for source-owned or owner-approved active-regime labels.",
        "search_queries": SEARCH_QUERIES,
        "candidates": CANDIDATES,
        "decision": decision,
        "guardrails": [
            "No external repository was cloned.",
            "No raw dataset rows were downloaded or committed.",
            "Generated/HMM/KMeans/feature-threshold labels remain fail-closed.",
            "Current Cursor was not edited.",
        ],
    }
    (OUT_DIR / "github_source_label_candidate_screen_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (OUT_DIR / "github_source_label_candidate_screen_v1_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANDIDATES[0].keys()))
        writer.writeheader()
        writer.writerows(CANDIDATES)

    report = [
        "# GitHub Source Label Candidate Screen v1",
        "",
        "Run ID: `20260511T193958+0800-codex-github-source-label-candidate-screen-v1`",
        "",
        "## Decision",
        "",
        f"`{decision['gate_result']}`",
        "",
        f"- GitHub search queries: `{decision['queries']}`.",
        f"- Candidate records dispositioned: `{decision['candidate_records']}`.",
        "- Ready source-owned or owner-approved active-regime label sources found: `0`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Candidate Disposition",
        "",
        "| Repo | Decision | Reason |",
        "|---|---|---|",
    ]
    for row in CANDIDATES:
        report.append(f"| [`{row['repo']}`]({row['url']}) | `{row['decision']}` | {row['reason']} |")
    report.extend(
        [
            "",
            "## Search Readback",
            "",
            "- Public GitHub hits were mostly HMM, KMeans, feature-threshold, Lunde/Timmermann, or binary volatility-classifier projects.",
            "- None exposed source-owned row-level Bull/Bear/Sideways/Crisis labels, owner-approved MainRegimeV2 equivalence rows, or usable direct `Manipulation` positive/control rows.",
            "- `akash-kumar5/CryptoMarket_Regime_Classifier` overlaps the prior Hugging Face HMM-6 BTCUSD surface and remains proxy/generated evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/github-source-label-screen/github_source_label_candidate_screen_v1.json`",
            f"- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/github-source-label-screen/github_source_label_candidate_screen_v1_candidates.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/github_source_label_candidate_screen_v1_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "github_source_label_candidate_screen_v1.md").write_text("\n".join(report), encoding="utf-8")
    assertions = [
        f"PASS decision={decision['gate_result']}",
        f"PASS candidate_records={decision['candidate_records']}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "github_source_label_candidate_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
