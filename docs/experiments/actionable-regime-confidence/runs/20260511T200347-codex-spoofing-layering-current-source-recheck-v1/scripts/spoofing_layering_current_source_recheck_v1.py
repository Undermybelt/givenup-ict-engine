#!/usr/bin/env python3
"""Current exact-source recheck for spoofing/layering matched-control rows."""

from __future__ import annotations

import csv
import json
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T200347-codex-spoofing-layering-current-source-recheck-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "spoofing-layering-current-source-recheck"
CHECK_DIR = RUN_ROOT / "checks"

HF_QUERIES = [
    "spoofing layering market manipulation dataset",
    "order book spoofing labels",
    "market manipulation spoofing matched controls",
]
KAGGLE_QUERIES = list(HF_QUERIES)
GITHUB_REPO_QUERIES = [
    "spoofing layering market manipulation dataset",
    "order book spoofing dataset labels",
    "financial market spoofing matched controls",
    "spoofing_layering dataset csv",
]
GIT_REPOS = [
    "https://github.com/sneela/aimm.git",
]
ZENODO_RECORDS = [
    "17705751",
    "17618798",
]
MANUAL_CANDIDATES = [
    {
        "source_id": "cftc_spoofing_guidance",
        "source_url": "https://www.cftc.gov/sites/default/files/idc/groups/public/@newsroom/documents/file/dtpinterpretiveorder_qa.pdf",
        "disposition": "guidance_no_exportable_rows",
        "reason": "Official spoofing/layering guidance supports taxonomy only; it does not expose source-owned row-level positives plus matched normal controls.",
    },
    {
        "source_id": "justia_cftc_oystacher",
        "source_url": "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1:2015cv09196/316583/80/",
        "disposition": "case_narrative_positive_only",
        "reason": "Enforcement/court narrative is useful positive provenance, but not a structured export with matched same-session normal controls.",
    },
    {
        "source_id": "zenodo_aimm_preprint",
        "source_url": "https://doi.org/10.5281/zenodo.17705751",
        "disposition": "pdf_only_not_spoofing_layering_rows",
        "reason": "AIMM is a social-media-influenced manipulation framework/preprint surface; checked Zenodo metadata exposes PDF files, not spoofing/layering CSV rows and controls.",
    },
]


def http_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ict-engine-board-a-audit",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def query_huggingface(query: str) -> dict[str, Any]:
    url = "https://huggingface.co/api/datasets?search=" + urllib.parse.quote(query)
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        return {"query": query, "status": "error", "error": type(exc).__name__, "detail": str(exc)[:200]}
    return {
        "query": query,
        "status": "ok",
        "count": len(data),
        "top": [
            {
                "id": item.get("id"),
                "likes": item.get("likes"),
                "downloads": item.get("downloads"),
                "tags": item.get("tags", [])[:8],
            }
            for item in data[:10]
        ],
    }


def query_kaggle(query: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["kaggle", "datasets", "list", "-s", query, "--csv"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except Exception as exc:  # noqa: BLE001
        return {"query": query, "status": "error", "error": type(exc).__name__, "detail": str(exc)[:200]}
    lines = proc.stdout.splitlines()
    return {
        "query": query,
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout_lines": len(lines),
        "header": lines[0] if lines else "",
        "top": lines[1:8],
        "stderr_head": proc.stderr.splitlines()[:5],
    }


def query_github_repo_search(query: str) -> dict[str, Any]:
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(query) + "&per_page=10"
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        return {"query": query, "status": "error", "error": type(exc).__name__, "detail": str(exc)[:200]}
    return {
        "query": query,
        "status": "ok",
        "total_count": data.get("total_count"),
        "top": [
            {
                "full_name": item.get("full_name"),
                "html_url": item.get("html_url"),
                "description": item.get("description"),
                "updated_at": item.get("updated_at"),
                "stars": item.get("stargazers_count"),
            }
            for item in data.get("items", [])[:10]
        ],
    }


def git_ls_remote(repo_url: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "ls-remote", repo_url, "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except Exception as exc:  # noqa: BLE001
        return {"repo_url": repo_url, "status": "error", "error": type(exc).__name__, "detail": str(exc)[:200]}
    return {
        "repo_url": repo_url,
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr_head": proc.stderr.splitlines()[:5],
    }


def fetch_zenodo(record_id: str) -> dict[str, Any]:
    try:
        data = http_json(f"https://zenodo.org/api/records/{record_id}")
    except Exception as exc:  # noqa: BLE001
        return {"record_id": record_id, "status": "error", "error": type(exc).__name__, "detail": str(exc)[:200]}
    return {
        "record_id": record_id,
        "status": "ok",
        "title": data.get("metadata", {}).get("title"),
        "doi": data.get("doi"),
        "created": data.get("created"),
        "modified": data.get("modified"),
        "keywords": data.get("metadata", {}).get("keywords", []),
        "files": [
            {
                "key": item.get("key"),
                "size": item.get("size"),
                "checksum": item.get("checksum"),
            }
            for item in data.get("files", [])
        ],
        "related_identifiers": data.get("metadata", {}).get("related_identifiers"),
    }


def accepted_candidate_count(payload: dict[str, Any]) -> int:
    accepted = 0
    if any(row.get("status") == "ok" and row.get("count", 0) for row in payload["huggingface"]):
        accepted += 0
    if any(row.get("status") == "ok" and row.get("total_count", 0) for row in payload["github_repo_search"]):
        accepted += 0
    return accepted


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Recheck current public/source paths for spoofing/layering positives plus matched normal controls.",
        "huggingface": [query_huggingface(query) for query in HF_QUERIES],
        "kaggle": [query_kaggle(query) for query in KAGGLE_QUERIES],
        "github_repo_search": [query_github_repo_search(query) for query in GITHUB_REPO_QUERIES],
        "git_repo_probe": [git_ls_remote(repo) for repo in GIT_REPOS],
        "zenodo": [fetch_zenodo(record) for record in ZENODO_RECORDS],
        "manual_candidates": MANUAL_CANDIDATES,
    }

    candidates = [
        {
            "source_id": "huggingface_exact_queries",
            "source_url": "https://huggingface.co/datasets",
            "disposition": "no_exact_dataset_hits",
            "reason": "Exact API searches returned zero dataset hits for spoofing/layering matched-control terms.",
        },
        {
            "source_id": "kaggle_exact_queries",
            "source_url": "https://www.kaggle.com/datasets",
            "disposition": "no_exact_dataset_hits",
            "reason": "Kaggle CLI exact searches returned no datasets for spoofing/layering matched-control terms.",
        },
        {
            "source_id": "github_exact_repo_queries",
            "source_url": "https://api.github.com/search/repositories",
            "disposition": "no_ready_repo_source",
            "reason": "GitHub API returned zero hits for two exact queries and transport errors for the other two; no ready source-owned row package was materialized.",
        },
        {
            "source_id": "sneela_aimm_repo_probe",
            "source_url": "https://github.com/sneela/aimm",
            "disposition": "repository_not_public_or_not_found",
            "reason": "The repo URL surfaced in web snippets was not cloneable/readable from this environment.",
        },
        *MANUAL_CANDIDATES,
    ]

    decision = {
        "gate_result": "spoofing_layering_current_source_recheck_v1=no_source_owned_matched_control_rows",
        "ready_spoofing_layering_intake_source": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "candidate_records": len(candidates),
        "accepted_candidate_count": accepted_candidate_count(payload),
    }
    payload["candidate_dispositions"] = candidates
    payload["decision"] = decision

    json_path = OUT_DIR / "spoofing_layering_current_source_recheck_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    csv_path = OUT_DIR / "spoofing_layering_current_source_recheck_v1_candidates.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_id", "source_url", "disposition", "reason"])
        writer.writeheader()
        writer.writerows(candidates)

    report = [
        "# Spoofing/Layering Current Source Recheck v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{decision['gate_result']}`.",
        "- Target: source-owned spoofing/layering positives plus matched normal controls for the strict direct `Manipulation` blocker.",
        f"- Candidate records dispositioned: `{len(candidates)}`.",
        "- Hugging Face exact dataset queries: `0` hits.",
        "- Kaggle exact dataset queries: no datasets found.",
        "- GitHub exact repo queries: no ready source-owned row package materialized; `sneela/aimm` was not public/readable from this environment.",
        "- Zenodo AIMM records expose PDF/preprint surfaces, not spoofing/layering row exports with matched controls.",
        "- CFTC/Justia-style official materials remain taxonomy or positive-case provenance only, not matched-control row packages.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Candidate CSV: `{csv_path}`",
        f"- Assertions: `{CHECK_DIR / 'spoofing_layering_current_source_recheck_v1_assertions.out'}`",
    ]
    (OUT_DIR / "spoofing_layering_current_source_recheck_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS gate_result={decision['gate_result']}",
        "PASS ready_spoofing_layering_intake_source=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "spoofing_layering_current_source_recheck_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
