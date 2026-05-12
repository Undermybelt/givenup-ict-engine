#!/usr/bin/env python3
"""Open a blocked public-crypto provider lane without installing dependencies."""

from __future__ import annotations

import csv
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T072500+0800-codex-kraken-public-lowpollution-lane"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072500-codex-kraken-public-lowpollution-lane"
OUT_DIR = RUN_ROOT / "kraken-lane"
CHECK_DIR = RUN_ROOT / "checks"
RAW_DIR = Path("/private/tmp/ict-regime-kraken-public-lowpollution-20260511T072500")

PAIRS = ["XBTUSD", "ETHUSD", "SOLUSD"]
TIMEFRAMES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}
UNSUPPORTED_TIMEFRAMES = {"1mo": "kraken_public_ohlc_has_no_monthly_interval"}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fetch_ohlc(pair: str, interval: int) -> dict[str, Any]:
    params = urllib.parse.urlencode({"pair": pair, "interval": interval})
    url = f"https://api.kraken.com/0/public/OHLC?{params}"
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def write_raw_csv(pair: str, timeframe: str, rows: list[list[Any]]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"kraken_{pair}_{timeframe}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time", "open", "high", "low", "close", "vwap", "volume", "count"])
        writer.writerows(rows)
    return path


def score_rows(rows: list[list[Any]]) -> dict[str, Any]:
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    for row in rows:
        try:
            highs.append(float(row[2]))
            lows.append(float(row[3]))
            closes.append(float(row[4]))
        except (TypeError, ValueError, IndexError):
            continue
    if len(closes) < 160:
        return {"status": "insufficient_rows_for_rule_score", "bars": len(closes), "root_hits": {}}
    root_hits = {"Bull": 0, "Bear": 0, "Sideways": 0, "Crisis": 0}
    evaluated = 0
    for idx in range(128, len(closes)):
        window60 = closes[idx - 59 : idx + 1]
        window120 = closes[idx - 119 : idx + 1]
        window32_high = highs[idx - 31 : idx + 1]
        window32_low = lows[idx - 31 : idx + 1]
        window128_high = highs[idx - 127 : idx + 1]
        window128_low = lows[idx - 127 : idx + 1]
        close = closes[idx]
        ret60 = close / closes[idx - 60] - 1.0
        drawdown120 = close / max(window120) - 1.0
        range60 = (max(window60) - min(window60)) / (sum(window60) / len(window60))
        range32 = (max(window32_high) - min(window32_low)) / close
        range128 = (max(window128_high) - min(window128_low)) / close
        ret1 = [closes[j] / closes[j - 1] - 1.0 for j in range(idx - 19, idx + 1) if closes[j - 1] != 0]
        vol20 = math.sqrt(sum(value * value for value in ret1) / len(ret1)) if ret1 else math.nan
        close_drawdown60 = close / max(window60) - 1.0
        evaluated += 1
        if close_drawdown60 >= -0.0032047199531 and math.isfinite(vol20) and vol20 <= 0.152179344579:
            root_hits["Bull"] += 1
        if (-drawdown120 / 0.35) >= 1.0 and (-ret60 / 0.10) >= 1.0:
            root_hits["Bear"] += 1
        if (abs(ret60) / 0.12) <= 0.505204858191 and (range60 / 0.55) <= 0.357222193236:
            root_hits["Sideways"] += 1
        if range128 != 0 and (range32 / range128) >= 1.43116959912:
            root_hits["Crisis"] += 1
    return {
        "status": "scored_close_ohlc_proxy",
        "bars": len(closes),
        "evaluated_rows": evaluated,
        "root_hits": root_hits,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    cells: list[dict[str, Any]] = []
    for pair in PAIRS:
        for timeframe, interval in TIMEFRAMES.items():
            cell: dict[str, Any] = {
                "provider": "kraken_public_lowpollution_http",
                "pair": pair,
                "timeframe": timeframe,
                "interval": interval,
                "data_status": "not_attempted",
                "label_status": "unsupported_missing_independent_root_labels",
                "accepted_confidence_status": "blocked_no_source_root_labels",
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "trade_usable": False,
            }
            try:
                payload = fetch_ohlc(pair, interval)
                errors = payload.get("error") or []
                if errors:
                    cell.update({"data_status": "provider_error", "errors": errors})
                else:
                    result = payload.get("result", {})
                    key = next(key for key in result if key != "last")
                    rows = result[key]
                    raw_path = write_raw_csv(pair, timeframe, rows)
                    cell.update(
                        {
                            "data_status": "usable",
                            "kraken_result_key": key,
                            "bars": len(rows),
                            "raw_tmp_csv": str(raw_path),
                            "score": score_rows(rows),
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                cell.update({"data_status": "fetch_exception", "error": f"{type(exc).__name__}: {exc}"})
            cells.append(cell)
        for timeframe, reason in UNSUPPORTED_TIMEFRAMES.items():
            cells.append(
                {
                    "provider": "kraken_public_lowpollution_http",
                    "pair": pair,
                    "timeframe": timeframe,
                    "data_status": "unsupported_provider_interval",
                    "reason": reason,
                    "label_status": "not_labeled_interval_unsupported",
                    "accepted_confidence_status": "blocked_interval_unsupported",
                    "runtime_code_changed": False,
                    "thresholds_relaxed": False,
                    "trade_usable": False,
                }
            )

    usable = [cell for cell in cells if cell["data_status"] == "usable"]
    scored = [cell for cell in usable if cell.get("score", {}).get("status") == "scored_close_ohlc_proxy"]
    report = {
        "run_id": RUN_ID,
        "objective": "Open the blocked kraken_public lane with a no-new-dependency HTTP sidecar and record all cycle dispositions.",
        "goal_achieved": False,
        "provider_lane_opened": bool(usable),
        "provider": "kraken_public_lowpollution_http",
        "pairs": PAIRS,
        "timeframes_attempted": list(TIMEFRAMES) + list(UNSUPPORTED_TIMEFRAMES),
        "cell_count": len(cells),
        "usable_cells": len(usable),
        "scored_close_ohlc_proxy_cells": len(scored),
        "cells": cells,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "The lane opens public Kraken OHLC data without new dependencies, but it still has no independent source-backed MainRegimeV2 root labels.",
                "Close/OHLC root-hit scoring is applicability evidence only and cannot compute accepted Wilson95 confidence.",
                "The monthly cycle is unsupported by Kraken public OHLC and remains an explicit blocked cell.",
            ],
        },
        "gate_result": "kraken_public_lane_opened_confidence_blocked_missing_independent_labels" if usable else "blocked_kraken_public_lane_not_opened",
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "artifacts": {
            "json": rel(OUT_DIR / "kraken_public_lowpollution_lane.json"),
            "md": rel(OUT_DIR / "kraken_public_lowpollution_lane.md"),
            "csv": rel(OUT_DIR / "kraken_public_lowpollution_lane.csv"),
            "assertions": rel(CHECK_DIR / "kraken_public_lowpollution_lane_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "kraken_public_lowpollution_lane.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with (OUT_DIR / "kraken_public_lowpollution_lane.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["provider", "pair", "timeframe", "data_status", "label_status", "accepted_confidence_status", "bars"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for cell in cells:
            writer.writerow({field: cell.get(field, "") for field in fields})
    md = [
        "# Kraken Public Low-Pollution Lane",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Provider lane opened: `{str(bool(usable)).lower()}`",
        "",
        f"Usable cells: `{len(usable)}` / `{len(cells)}`",
        f"Scored close/OHLC proxy cells: `{len(scored)}`",
        "",
        "Gate result: `" + report["gate_result"] + "`",
        "",
        "This opens data availability only. It is not accepted confidence because independent source-backed root labels are still missing.",
        "",
    ]
    (OUT_DIR / "kraken_public_lowpollution_lane.md").write_text("\n".join(md))
    assertions = [
        f"provider_lane_opened={str(bool(usable)).lower()}",
        f"usable_cells={len(usable)}",
        f"scored_close_ohlc_proxy_cells={len(scored)}",
        "accepted_full_cycle_full_universe=false",
        f"gate_result={report['gate_result']}",
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "trade_usable=false",
    ]
    (CHECK_DIR / "kraken_public_lowpollution_lane_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
