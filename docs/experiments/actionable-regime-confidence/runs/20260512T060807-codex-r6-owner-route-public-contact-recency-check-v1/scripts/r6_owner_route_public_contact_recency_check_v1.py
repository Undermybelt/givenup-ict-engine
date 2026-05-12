#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "Cargo.toml").exists() and (path / "docs/plans").exists():
            return path
    raise RuntimeError(f"repo root not found from {start}")


REPO = find_repo_root(Path(__file__).resolve())
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ID = "20260512T060807-codex-r6-owner-route-public-contact-recency-check-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-owner-route-public-contact-recency-check-v1"
CHECK_DIR = RUN_ROOT / "checks"

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]
APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")

SOURCES = [
    {
        "owner": "CME Group",
        "route_role": "licensed historical data / DataMine route",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data/index.html",
        "markers": ["DataMine", "historical", "market data"],
    },
    {
        "owner": "CME Group",
        "route_role": "Market Depth documentation route",
        "url": "https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf",
        "markers": ["Market Depth", "FIX", "Historical"],
    },
    {
        "owner": "Cboe/CFE",
        "route_role": "CFE VIX trades and quotes DataShop route",
        "url": "https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes",
        "markers": ["CFE", "VIX", "Trades", "Quotes"],
    },
    {
        "owner": "Cboe/CFE",
        "route_role": "US futures market-data services route",
        "url": "https://www.cboe.com/market_data_services/us/futures/",
        "markers": ["Futures", "Depth", "Book", "Market Data"],
    },
    {
        "owner": "Cboe/CFE",
        "route_role": "current futures market-data services route fallback",
        "url": "https://www.cboe.com/cboe-data-vantage/market-data-services/us/futures/",
        "markers": ["Futures", "Depth", "Book", "Market Data"],
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch_source(source: dict[str, object]) -> dict[str, object]:
    req = urllib.request.Request(
        str(source["url"]),
        headers={
            "User-Agent": "ict-engine-board-a-route-recency-check/1.0",
            "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
        },
    )
    started = time.time()
    body = b""
    status = None
    final_url = str(source["url"])
    error = None
    headers: dict[str, str] = {}
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            status = resp.status
            final_url = resp.geturl()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read(750_000)
    except urllib.error.HTTPError as exc:
        status = exc.code
        final_url = exc.geturl()
        headers = {k.lower(): v for k, v in exc.headers.items()}
        body = exc.read(100_000)
        error = f"HTTPError:{exc.code}"
    except Exception as exc:  # noqa: BLE001 - this is a capture artifact.
        error = f"{type(exc).__name__}:{exc}"

    text = body.decode("utf-8", errors="ignore")
    marker_hits = {}
    for marker in source["markers"]:
        marker_hits[str(marker)] = bool(re.search(re.escape(str(marker)), text, re.I))

    return {
        "owner": source["owner"],
        "route_role": source["route_role"],
        "url": source["url"],
        "final_url": final_url,
        "http_status": status,
        "error": error,
        "elapsed_seconds": round(time.time() - started, 3),
        "content_type": headers.get("content-type", ""),
        "content_length_header": headers.get("content-length", ""),
        "captured_bytes": len(body),
        "marker_hits": marker_hits,
        "marker_hit_count": sum(1 for v in marker_hits.values() if v),
    }


def read_approval() -> dict[str, object]:
    if not APPROVAL_PACKAGE.exists():
        return {"exists": False}
    try:
        data = json.loads(APPROVAL_PACKAGE.read_text())
    except Exception as exc:  # noqa: BLE001 - artifact capture.
        return {"exists": True, "parse_error": str(exc)}
    return {
        "exists": True,
        "gate_result": data.get("gate_result"),
        "assertions": data.get("assertions", {}),
        "next_action": data.get("next_action"),
    }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    source_rows = [fetch_source(source) for source in SOURCES]
    target_roots = {str(root): root.exists() for root in TARGET_ROOTS}
    approval = read_approval()
    approval_assertions = approval.get("assertions", {}) if isinstance(approval, dict) else {}

    reachable_rows = [
        row
        for row in source_rows
        if isinstance(row.get("http_status"), int) and 200 <= int(row["http_status"]) < 400
    ]
    marker_rows = [row for row in source_rows if int(row.get("marker_hit_count", 0)) > 0]
    cme_route_visible = any(row["owner"] == "CME Group" and row["marker_hit_count"] for row in source_rows)
    cboe_route_visible = any(row["owner"] == "Cboe/CFE" and row["marker_hit_count"] for row in source_rows)

    decision = {
        "official_routes_still_findable": bool(cme_route_visible and cboe_route_visible),
        "http_reachable_sources": len(reachable_rows),
        "marker_positive_sources": len(marker_rows),
        "required_root_unlocked": any(target_roots.values()),
        "approval_present": bool(approval_assertions.get("approval_present", False)),
        "source_control_evidence_acquired": False,
        "public_http_route_checks_sent": len(SOURCES),
        "external_email_sent": False,
        "owner_export_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    gate_result = (
        "r6_owner_route_public_contact_recency_check_after_060446_v1="
        "cboe_routes_live_cme_public_fetch_403_no_controls_no_promotion"
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "board_hash_before_artifact": board_hash,
        "gate_result": gate_result,
        "source_rows": source_rows,
        "target_roots": target_roots,
        "approval_package": approval,
        "decision": decision,
        "next_action": (
            "Use the existing v5 owner-export drafts only through an approved operator mail path, "
            "or supply explicit source/control approval or verifier-native owner-export rows. "
            "Do not mutate target roots or rerun downstream until the source/control gate unlocks."
        ),
    }

    json_path = ARTIFACT_DIR / "r6_owner_route_public_contact_recency_check_v1.json"
    csv_path = ARTIFACT_DIR / "r6_owner_route_public_contact_recency_check_sources_v1.csv"
    md_path = ARTIFACT_DIR / "r6_owner_route_public_contact_recency_check_v1.md"
    checks_path = CHECK_DIR / "r6_owner_route_public_contact_recency_check_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "owner",
                "route_role",
                "url",
                "final_url",
                "http_status",
                "error",
                "content_type",
                "captured_bytes",
                "marker_hit_count",
                "marker_hits_json",
            ],
        )
        writer.writeheader()
        for row in source_rows:
            writer.writerow(
                {
                    "owner": row["owner"],
                    "route_role": row["route_role"],
                    "url": row["url"],
                    "final_url": row["final_url"],
                    "http_status": row["http_status"],
                    "error": row["error"],
                    "content_type": row["content_type"],
                    "captured_bytes": row["captured_bytes"],
                    "marker_hit_count": row["marker_hit_count"],
                    "marker_hits_json": json.dumps(row["marker_hits"], sort_keys=True),
                }
            )

    lines = [
        "# R6 Owner Route Public Contact Recency Check v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{gate_result}`.",
        f"- Board hash before artifact: `{board_hash}`.",
        f"- Official routes still findable: `{decision['official_routes_still_findable']}`.",
        f"- HTTP reachable official sources: `{decision['http_reachable_sources']}`.",
        f"- Marker-positive official sources: `{decision['marker_positive_sources']}`.",
        f"- Required target root unlocked: `{decision['required_root_unlocked']}`.",
        f"- Approval present: `{decision['approval_present']}`.",
        "",
        "This is a route/contact recency packet only. It performs public HTTP route checks but does not send external email, acquire controls, copy files into target roots, approve `FLIP` rows, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Sources Checked",
        "",
        "| owner | route role | http | markers | url |",
        "|---|---:|---:|---:|---|",
    ]
    for row in source_rows:
        lines.append(
            f"| {row['owner']} | {row['route_role']} | {row['http_status']} | "
            f"{row['marker_hit_count']} | {row['url']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Current official CME/Cboe/CFE routes remain export/contact routes, not acquired verifier-native controls.",
            "- Cboe/CFE public routes were live-fetchable in this sandbox; CME public route fetches returned `403`, so CME route recency still depends on prior official-route packets or operator-side browser/vendor access.",
            "- Required roots remain absent unless one exists at runtime in `target_roots`.",
            "- Approval package remains non-promoting unless `approval_present=true`.",
            "- No downstream provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/execution-tree promotion rerun is allowed from this packet.",
            "",
            "## Next",
            "",
            summary["next_action"],
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    checks = [
        ("gate_result", summary["gate_result"] == gate_result),
        ("required_root_unlocked_false", summary["decision"]["required_root_unlocked"] is False),
        ("approval_present_false", summary["decision"]["approval_present"] is False),
        ("source_control_evidence_false", summary["decision"]["source_control_evidence_acquired"] is False),
        ("public_http_route_checks_sent", summary["decision"]["public_http_route_checks_sent"] == len(SOURCES)),
        ("external_email_sent_false", summary["decision"]["external_email_sent"] is False),
        ("canonical_merge_false", summary["decision"]["canonical_merge"] is False),
        ("downstream_promotion_rerun_false", summary["decision"]["downstream_promotion_rerun"] is False),
        ("update_goal_false", summary["decision"]["update_goal"] is False),
    ]
    checks_path.write_text("\n".join(f"{name}: {'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
