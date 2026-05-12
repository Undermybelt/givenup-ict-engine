#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T085230+0800-codex-nonkaggle-github-source-label-search"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T085230-codex-nonkaggle-github-source-label-search"
)
ACQUISITION_V2_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/source_label_acquisition_package_v2.json"
)
CURRENT_AUDIT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T084755-codex-current-goal-completion-audit/"
    "completion-audit/current_goal_completion_audit.json"
)

GITHUB_SEARCH_QUERIES = [
    '"market regime" "bull" "bear" "sideways" labels',
    '"market regimes" dataset "bull" "bear"',
    '"stock market regime" labels csv',
    '"regime classification" "bull" "bear" "crisis"',
    '"market regime" "crisis" "sideways" "csv"',
    '"Bull" "Bear" "Sideways" "Crisis" "market regime"',
]

ROOT_TERMS = ["bull", "bear", "sideways", "crisis"]
PROXY_TERMS = ["hmm", "gmm", "kmeans", "unsupervised", "clustering", "strategy", "prediction"]
DATA_TERMS = ["csv", "dataset", "labels", "label", "regime"]
TARGET_TERMS = ["qqq", "spy", "nq", "es", "btc", "kraken", "yfinance", "intraday", "1h", "15m"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def github_get(url: str) -> tuple[int | None, dict[str, Any] | None, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ict-engine-board-a-source-label-search/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8")), None
    except Exception as exc:  # noqa: BLE001 - retry with curl below.
        curl = subprocess.run(
            [
                "curl",
                "-L",
                "--silent",
                "--show-error",
                "--max-time",
                "30",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "User-Agent: ict-engine-board-a-source-label-search/1.0",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if curl.returncode != 0:
            return None, None, f"{repr(exc)}; curl={curl.stderr.strip()}"
        try:
            return 200, json.loads(curl.stdout), None
        except Exception as parse_exc:  # noqa: BLE001
            return None, None, f"{repr(exc)}; curl_parse={repr(parse_exc)}"


def search_repos(query: str) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(
        {"q": query, "per_page": "8", "sort": "updated", "order": "desc"}
    )
    url = f"https://api.github.com/search/repositories?{encoded}"
    status, payload, error = github_get(url)
    return {
        "query": query,
        "url": url,
        "status": status,
        "error": error,
        "items": (payload or {}).get("items", []) if payload else [],
        "total_count": (payload or {}).get("total_count") if payload else None,
    }


def fetch_readme(full_name: str) -> dict[str, Any]:
    status, payload, error = github_get(f"https://api.github.com/repos/{full_name}/readme")
    if not payload or "content" not in payload:
        return {"status": status, "error": error, "text": ""}
    try:
        raw = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return {"status": status, "error": repr(exc), "text": ""}
    return {"status": status, "error": error, "text": raw[:30_000]}


def term_hits(text: str, terms: list[str]) -> dict[str, int]:
    return {term: len(re.findall(re.escape(term), text, re.I)) for term in terms}


def classify_repo(repo: dict[str, Any], readme: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        [
            str(repo.get("name", "")),
            str(repo.get("description", "")),
            readme.get("text", ""),
        ]
    )
    roots = term_hits(text, ROOT_TERMS)
    proxy = term_hits(text, PROXY_TERMS)
    data = term_hits(text, DATA_TERMS)
    targets = term_hits(text, TARGET_TERMS)

    has_all_roots = all(roots[root] > 0 for root in ROOT_TERMS)
    has_data_hint = any(count > 0 for count in data.values())
    has_target_hint = any(count > 0 for count in targets.values())
    proxy_heavy = sum(proxy.values()) > 0

    if has_all_roots and has_data_hint and has_target_hint and not proxy_heavy:
        decision = "manual_raw_panel_inspection_required"
        reason = (
            "Metadata/README mention all roots plus data and target terms, but this "
            "run did not find a replayable source-label panel or raw label file."
        )
    elif proxy_heavy:
        decision = "rejected_proxy_or_methodology_only"
        reason = "README/metadata emphasize model, HMM/GMM, clustering, strategy, or prediction terms rather than independent labels."
    elif has_data_hint:
        decision = "source_discovery_only_no_attachable_panel"
        reason = "Dataset/label terms appear, but exact Bull/Bear/Sideways/Crisis root coverage and provider/timeframe attachability were not present."
    else:
        decision = "not_a_label_panel"
        reason = "No evidence of an independent source-label panel for Board A roots."

    return {
        "full_name": repo.get("full_name"),
        "html_url": repo.get("html_url"),
        "description": repo.get("description"),
        "updated_at": repo.get("updated_at"),
        "readme_status": readme.get("status"),
        "root_term_hits": roots,
        "proxy_term_hits": proxy,
        "data_term_hits": data,
        "target_term_hits": targets,
        "decision": decision,
        "reason": reason,
    }


def main() -> None:
    out_dir = RUN_ROOT / "source-search"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    acquisition = load_json(ACQUISITION_V2_JSON)
    audit = load_json(CURRENT_AUDIT_JSON)

    search_results = []
    repos: dict[str, dict[str, Any]] = {}
    for query in GITHUB_SEARCH_QUERIES:
        result = search_repos(query)
        search_results.append(
            {
                "query": result["query"],
                "status": result["status"],
                "error": result["error"],
                "total_count": result["total_count"],
                "item_count": len(result["items"]),
            }
        )
        for item in result["items"]:
            full_name = item.get("full_name")
            if full_name and full_name not in repos:
                repos[full_name] = item
        time.sleep(1.0)

    classified = []
    for repo in list(repos.values())[:24]:
        readme = fetch_readme(repo["full_name"])
        classified.append(classify_repo(repo, readme))
        time.sleep(0.5)

    manual_followups = [
        row for row in classified if row["decision"] == "manual_raw_panel_inspection_required"
    ]

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": (
            "Search non-Kaggle GitHub/public repository metadata for independent "
            "Bull/Bear/Sideways/Crisis label panels attachable to the missing Board A slots."
        ),
        "active_taxonomy": "MainRegimeV2",
        "input_evidence": {
            "source_label_acquisition_package_v2": str(ACQUISITION_V2_JSON),
            "current_goal_completion_audit": str(CURRENT_AUDIT_JSON),
        },
        "missing_slot_accounting": {
            "accepted_gate": audit["accepted_gate"],
            "missing_or_rejected_slots": acquisition["acquisition_request"][
                "missing_or_rejected_slots"
            ],
            "missing_or_rejected_slots_by_root": acquisition["acquisition_request"][
                "missing_or_rejected_slots_by_root"
            ],
            "missing_or_rejected_slots_by_reason": acquisition["acquisition_request"][
                "missing_or_rejected_slots_by_reason"
            ],
        },
        "github_search_results": search_results,
        "repos_classified": classified,
        "manual_followup_candidates": manual_followups,
        "accepted_new_independent_label_sources": 0,
        "new_attached_root_label_slots": 0,
        "gate_result": "blocked_nonkaggle_github_search_no_attachable_root_label_panel",
        "completion_accounting": {
            "accepted_confidence": False,
            "accepted_full_cycle_full_universe": False,
            "goal_achieved": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Authenticated/user-provided exact-underlying source-label panels are still required; "
            "GitHub metadata search did not produce attachable non-Kaggle root labels."
        ),
        "artifacts": {
            "summary_json": str(out_dir / "nonkaggle_github_source_label_search.json"),
            "summary_md": str(out_dir / "nonkaggle_github_source_label_search.md"),
            "assertions": str(checks_dir / "nonkaggle_github_source_label_search_assertions.out"),
            "script": str(RUN_ROOT / "scripts/nonkaggle_github_source_label_search.py"),
        },
    }

    (out_dir / "nonkaggle_github_source_label_search.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    rows = "".join(
        f"| `{row['full_name']}` | `{row['decision']}` | {row['reason']} |\n"
        for row in classified[:12]
    )
    md = f"""# Non-Kaggle GitHub Source Label Search

Run id: `{RUN_ID}`

## Result

- Active taxonomy: `MainRegimeV2`.
- GitHub queries run: `{len(GITHUB_SEARCH_QUERIES)}`.
- Unique repos classified: `{len(classified)}`.
- Accepted new independent source-label sources: `0`.
- New attached root-label slots: `0`.
- Manual follow-up candidates: `{len(manual_followups)}`.
- Gate result: `blocked_nonkaggle_github_search_no_attachable_root_label_panel`.

## Top Classified Repos

| Repo | Decision | Reason |
|---|---|---|
{rows}
## Accounting

- Current accepted gate remains `{audit["accepted_gate"]}`.
- Missing/rejected slots remain `{acquisition["acquisition_request"]["missing_or_rejected_slots"]}`.
- Raw data committed: false. Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

## Next Action

Authenticated/user-provided exact-underlying source-label panels are still required; GitHub metadata search did not produce attachable non-Kaggle root labels.
"""
    (out_dir / "nonkaggle_github_source_label_search.md").write_text(md)

    assertions = [
        f"PASS github_queries={len(GITHUB_SEARCH_QUERIES)}",
        f"PASS repos_classified={len(classified)}",
        "PASS accepted_new_independent_label_sources=0",
        "PASS new_attached_root_label_slots=0",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS gate_result=blocked_nonkaggle_github_search_no_attachable_root_label_panel",
    ]
    (checks_dir / "nonkaggle_github_source_label_search_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
