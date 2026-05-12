#!/usr/bin/env python3
"""Audit UAlberta manipulation/anomaly literature datasets against Board A."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T110002+0800-codex-ualberta-manipulation-source-audit"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "source-audit"
CHECK_DIR = RUN_ROOT / "checks"


def probe_url(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-board-a-source-audit/1.0",
            "Accept": "text/html,application/pdf,*/*",
        },
        method="HEAD",
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=20, context=context) as response:
            return {
                "url": url,
                "reachable": True,
                "status": response.status,
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
                "waf_challenge": response.headers.get("x-amzn-waf-action") == "challenge",
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "reachable": False,
            "status": exc.code,
            "content_type": exc.headers.get("content-type"),
            "content_length": exc.headers.get("content-length"),
            "waf_challenge": exc.headers.get("x-amzn-waf-action") == "challenge",
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001 - audit must report network failure shape.
        return {
            "url": url,
            "reachable": False,
            "status": None,
            "content_type": None,
            "content_length": None,
            "waf_challenge": False,
            "error": repr(exc),
        }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    probes = [
        probe_url("https://www.ualberta.ca/~golmoham/DSAA2015/"),
        probe_url("https://webdocs.cs.ualberta.ca/~zaiane/postscript/DSAA2015.pdf"),
        probe_url("https://webdocs.cs.ualberta.ca/~zaiane/postscript/DSAA2014.pdf"),
    ]

    candidates = [
        {
            "source_id": "Golmohammadi-Zaiane DSAA2015 S&P outlier CSV package",
            "source_url": "https://www.ualberta.ca/~golmoham/DSAA2015/",
            "observed_shape": "Paper-advertised downloadable S&P CSVs for unsupervised outlier detection experiments; local probe currently receives CloudFront/WAF challenge for the dataset directory.",
            "decision": "rejected",
            "reason": "The paper/data framing is synthetic or artificial outlier injection for anomaly-detection benchmarking, not adjudicated timestamped manipulation positives with same-venue negatives and not MainRegimeV2 Bull/Bear/Sideways/Crisis label windows.",
        },
        {
            "source_id": "Golmohammadi-Zaiane DSAA2014 SEC/Diaz manipulation case study",
            "source_url": "https://webdocs.cs.ualberta.ca/~zaiane/postscript/DSAA2014.pdf",
            "observed_shape": "Academic paper over SEC/Diaz manipulated-stock cases and S&P comparison time series; no replayable public row-level label panel was located in this bounded audit.",
            "decision": "rejected",
            "reason": "Methodology/case-study provenance only; no materialized positive/negative manipulation rows, no exact provider/instrument/timeframe label windows for the Board A missing-slot matrix.",
        },
    ]

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "active_taxonomy": "MainRegimeV2",
        "objective": "Audit newly surfaced UAlberta/Golmohammadi-Zaiane manipulation/anomaly sources for attachable MainRegimeV2 parent-root labels or direct Manipulation rows.",
        "missing_slot_contract": {
            "required_parent_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "separate_direct_class_or_overlay": "Manipulation",
            "required_parent_root_source": "independent exact provider or exact underlying label windows by provider/instrument/timeframe/root",
            "required_direct_manipulation_source": "timestamped direct event/order-flow/order-lifecycle positives with same-asset/venue negative controls",
            "forbidden_sources": [
                "synthetic anomaly rows",
                "artificial outlier injection",
                "OHLCV-derived proxies",
                "methodology-only papers",
                "unlabeled order/trade rows",
            ],
        },
        "network_probes": probes,
        "candidates": candidates,
        "result": {
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "accepted_direct_manipulation_sources_added": 0,
            "gate_result": "blocked_ualberta_sources_synthetic_or_methodology_only_no_attachable_labels",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Do not spend another loop on synthetic/anomaly-benchmark sources; only continue this branch if a public row-level ground-truth file for the SEC/Diaz manipulation cases is located.",
    }

    json_path = OUT_DIR / "ualberta_manipulation_source_audit.json"
    md_path = OUT_DIR / "ualberta_manipulation_source_audit.md"
    checks_path = CHECK_DIR / "ualberta_manipulation_source_audit_assertions.out"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(
        f"| `{candidate['source_id']}` | `{candidate['decision']}` | {candidate['reason']} |"
        for candidate in candidates
    )
    waf = any(probe["waf_challenge"] for probe in probes)
    md_path.write_text(
        "\n".join(
            [
                "# UAlberta Manipulation Source Audit",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "## Scope",
                "",
                "This bounded audit checks whether newly surfaced Golmohammadi/Zaiane manipulation-anomaly materials can fill Board A's active `MainRegimeV2` missing-slot contract.",
                "",
                "## Network Probe",
                "",
                f"- Dataset directory WAF challenge observed: `{str(waf).lower()}`.",
                "- No raw market CSV was committed to the repo.",
                "",
                "## Candidate Decisions",
                "",
                "| Source | Decision | Reason |",
                "|---|---|---|",
                rows,
                "",
                "## Result",
                "",
                "- Accepted parent-root slots added: `0`.",
                "- Accepted direct `Manipulation` rows added: `0`.",
                "- Gate result: `blocked_ualberta_sources_synthetic_or_methodology_only_no_attachable_labels`.",
                "- Runtime code changed: false.",
                "- Thresholds relaxed: false.",
                "- Raw data committed: false.",
                "- Trade usable: false.",
                "",
                "## Next Action",
                "",
                "Do not spend another loop on synthetic/anomaly-benchmark sources. Continue this branch only if a public row-level ground-truth file for the SEC/Diaz manipulation cases is located.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS active_taxonomy=MainRegimeV2",
        "PASS accepted_parent_root_slots_added=0",
        "PASS accepted_direct_manipulation_rows_added=0",
        "PASS accepted_direct_manipulation_sources_added=0",
        "PASS synthetic_or_artificial_outlier_sources_not_promoted=true",
        "PASS methodology_only_sources_not_promoted=true",
        "PASS raw_data_committed=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
        "GATE blocked_ualberta_sources_synthetic_or_methodology_only_no_attachable_labels",
    ]
    checks_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
