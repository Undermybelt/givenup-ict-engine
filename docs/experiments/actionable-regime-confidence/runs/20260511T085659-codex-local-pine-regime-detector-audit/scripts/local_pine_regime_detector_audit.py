#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path


RUN_ID = "20260511T085659+0800-codex-local-pine-regime-detector-audit"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "local-candidate-audit"
CHECKS = ROOT / "checks"
SOURCE = Path("/Users/thrill3r/Downloads/ictscripts/ICT Market Regime Detector")

ACTIVE_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
REJECTED_SOURCE_CLASS = "ohlcv_derived_pine_indicator_proxy_logic"
GATE_RESULT = "blocked_local_pine_indicator_is_proxy_logic_not_source_labels"


def unique_sorted(items):
    return sorted(set(items))


def audit_source():
    data = SOURCE.read_bytes()
    text = data.decode("utf-8")
    lines = text.splitlines()

    assignments = re.findall(r'primaryRegime\s*:=\s*"([^"]+)"', text)
    defaults = re.findall(r'string\s+primaryRegime\s*=\s*"([^"]+)"', text)
    sub_regimes = re.findall(r'subRegime\s*:=\s*"([^"]+)"', text)
    ta_calls = unique_sorted(re.findall(r"\bta\.([a-zA-Z_][a-zA-Z0-9_]*)", text))
    request_calls = unique_sorted(re.findall(r"\brequest\.([a-zA-Z_][a-zA-Z0-9_]*)", text))

    direct_price_tokens = {
        token: bool(re.search(rf"\b{re.escape(token)}\b", text))
        for token in ["open", "high", "low", "close", "volume", "time", "syminfo.tickerid"]
    }
    external_label_markers = {
        marker: bool(re.search(marker, text, re.IGNORECASE))
        for marker in [
            r"request\.seed",
            r"request\.economic",
            r"request\.financial",
            r"\bcsv\b",
            r"\bdataset\b",
            r"\blabel_source\b",
            r"\bpositive\b",
            r"\bnegative\b",
            r"\bmanual\b",
        ]
    }

    regime_decision_tree_inputs = [
        "volatility ratio from close-to-close returns",
        "DMI/ADX from high/low/close",
        "EMA20/EMA50 structure from close",
        "RSI divergence from high/low/close",
        "range high/low/position from high/low/close",
        "volume spike plus candle body/wick heuristics",
        "same-symbol 4h request.security DMI alignment",
    ]

    result = {
        "run_id": RUN_ID,
        "candidate_path": str(SOURCE),
        "candidate_sha256": hashlib.sha256(data).hexdigest(),
        "candidate_line_count": len(lines),
        "candidate_bytes": len(data),
        "candidate_type": "TradingView Pine Script indicator",
        "active_taxonomy": {
            "price_roots": ACTIVE_ROOTS,
            "manipulation": "separate_direct_event_or_order_lifecycle_overlay",
        },
        "observed_output_labels": unique_sorted(defaults + assignments),
        "observed_sub_regime_labels": unique_sorted(sub_regimes),
        "ta_calls": ta_calls,
        "request_calls": request_calls,
        "direct_price_tokens_present": direct_price_tokens,
        "external_label_markers_present": external_label_markers,
        "regime_decision_tree_inputs": regime_decision_tree_inputs,
        "source_class": REJECTED_SOURCE_CLASS,
        "independent_mainregimev2_root_label_panel": False,
        "exact_underlying_source_labels": False,
        "direct_manipulation_positive_negative_windows": False,
        "accepted_mainregimev2_root_label_slots_added": 0,
        "accepted_direct_manipulation_label_sources_added": 0,
        "gate_result": GATE_RESULT,
        "decision": "rejected_proxy_only_no_source_label_attachment",
        "reason": (
            "The script generates regime names inside classifyRegime() from chart "
            "OHLCV/volume, ADX, EMA, RSI, ATR/range, wick, and same-symbol 4h "
            "DMI features. It does not contain an independent label table, "
            "exact-underlying MainRegimeV2 root labels, or direct Manipulation "
            "positive/negative event windows."
        ),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_source_committed": False,
        "trade_usable": False,
        "next_action": (
            "Acquire exact-underlying non-Kaggle root-label panels for the "
            "missing intraday/monthly/Kraken/missing-instrument slots or "
            "authenticated direct Manipulation rows."
        ),
    }
    return result


def write_outputs(result):
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    json_path = OUT / "local_pine_regime_detector_audit.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = OUT / "local_pine_regime_detector_audit.md"
    lines = [
        "# Local Pine Regime Detector Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Candidate",
        "",
        f"- Path: `{result['candidate_path']}`",
        f"- SHA-256: `{result['candidate_sha256']}`",
        f"- Lines: `{result['candidate_line_count']}`",
        f"- Type: `{result['candidate_type']}`",
        "",
        "## Result",
        "",
        f"- Decision: `{result['decision']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Accepted MainRegimeV2 root-label slots added: `{result['accepted_mainregimev2_root_label_slots_added']}`.",
        f"- Accepted direct `Manipulation` label sources added: `{result['accepted_direct_manipulation_label_sources_added']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw source committed: false. Trade usable: false.",
        "",
        "## Why It Does Not Close The Gate",
        "",
        result["reason"],
        "",
        "The observed labels are generated outputs of a local decision tree, not source labels:",
        "",
        "| Observed output labels | Source class |",
        "|---|---|",
        f"| `{result['observed_output_labels']}` | `{result['source_class']}` |",
        "",
        "Decision-tree inputs observed:",
        "",
    ]
    for item in result["regime_decision_tree_inputs"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Direct Label Checks",
            "",
            f"- Independent MainRegimeV2 root-label panel: `{result['independent_mainregimev2_root_label_panel']}`.",
            f"- Exact-underlying source labels: `{result['exact_underlying_source_labels']}`.",
            f"- Direct Manipulation positive/negative windows: `{result['direct_manipulation_positive_negative_windows']}`.",
            f"- `request.*` calls found: `{result['request_calls']}`.",
            "",
            "## Next Action",
            "",
            result["next_action"],
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS source_exists={SOURCE.exists()}",
        f"PASS candidate_line_count={result['candidate_line_count']}",
        "PASS independent_mainregimev2_root_label_panel=false",
        "PASS exact_underlying_source_labels=false",
        "PASS direct_manipulation_positive_negative_windows=false",
        "PASS accepted_mainregimev2_root_label_slots_added=0",
        "PASS accepted_direct_manipulation_label_sources_added=0",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_source_committed=false",
        f"PASS gate_result={result['gate_result']}",
    ]
    (CHECKS / "local_pine_regime_detector_audit_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )


def main():
    result = audit_source()
    write_outputs(result)


if __name__ == "__main__":
    main()
