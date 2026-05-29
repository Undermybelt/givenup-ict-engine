from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SYMBOL_RE = re.compile(r"\b(?:NQ|YM|XAU|ES|MES|MNQ|GC|CL|SI|RTY|BTC|ETH)\b")
TIMEFRAME_RE = re.compile(r"\b(?:1m|5m|15m|30m|1h|4h|1d)\b", re.IGNORECASE)
BRANCH_CALL_RE = re.compile(
    r"branch\(\s*['\"](?P<main>[A-Za-z][A-Za-z0-9_ ]+)['\"]\s*,\s*['\"](?P<sub>[A-Za-z][A-Za-z0-9_ ]+)['\"]\s*,",
    re.MULTILINE,
)
REGIME_CALL_RE = re.compile(
    r"(?:add_trade|add_trade_risk|_add_trade|add_risk_trade)\(",
    re.MULTILINE,
)

INDICATOR_PATTERNS: dict[str, re.Pattern[str]] = {
    "adx": re.compile(r"\badx\b", re.IGNORECASE),
    "breakout": re.compile(r"\bbreakout\b", re.IGNORECASE),
    "contrarian": re.compile(r"\bcontrarian\b", re.IGNORECASE),
    "donchian": re.compile(r"\bdonch(?:ian)?\b", re.IGNORECASE),
    "fvg": re.compile(r"\bfvg\b|fair value gap", re.IGNORECASE),
    "high_excursion": re.compile(r"high[_ -]?excursion", re.IGNORECASE),
    "ict": re.compile(r"\bict\b", re.IGNORECASE),
    "killzone": re.compile(r"kill[_ -]?zone", re.IGNORECASE),
    "liquidity_sweep": re.compile(r"liquidity[_ -]?sweep", re.IGNORECASE),
    "opening_drive": re.compile(r"opening[_ -]?drive", re.IGNORECASE),
    "order_block": re.compile(r"order[_ -]?block|\bob\b", re.IGNORECASE),
    "ote": re.compile(r"\bote\b|optimal trade entry", re.IGNORECASE),
    "pair": re.compile(r"\bpair\b", re.IGNORECASE),
    "relative_value": re.compile(r"relative[_ -]?value", re.IGNORECASE),
    "reversion": re.compile(r"\breversion\b", re.IGNORECASE),
    "rvol": re.compile(r"\brv(?:ol)?\b", re.IGNORECASE),
    "seasonality": re.compile(r"seasonality", re.IGNORECASE),
    "session": re.compile(r"\bsession\b", re.IGNORECASE),
    "supertrend": re.compile(r"supertrend", re.IGNORECASE),
    "swing": re.compile(r"\bswing\b", re.IGNORECASE),
    "tod": re.compile(r"\btod\b|time[_ -]?of[_ -]?day", re.IGNORECASE),
    "trend": re.compile(r"\btrend\b", re.IGNORECASE),
    "volatility": re.compile(r"volatility", re.IGNORECASE),
    "vwap": re.compile(r"\bvwap\b", re.IGNORECASE),
    "zscore": re.compile(r"z[_ -]?score|\bzscore\b", re.IGNORECASE),
}

REGIME_TO_BRANCH: dict[str, str] = {
    "OpeningDrive": "TrendExpansion -> OpeningDriveBreakout",
    "FailedBreakoutFade": "RangeReversion -> OpeningDriveFailedBreakoutFade",
    "LiquiditySweepReversal": "RangeReversion -> PriorDayLiquiditySweepReversal",
    "CompressionExpansion": "VolatilityCompressionExpansion -> CrabelNR7",
    "VolatilityCompressionExpansion": "VolatilityCompressionExpansion -> CrabelNR7",
    "VwapReclaimPersistence": "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
    "OpeningDriveTwoLegContinuation": "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation",
}


@dataclass(frozen=True)
class TomacStrategyRow:
    relative_path: str
    file_kind: str
    family: str
    symbols: list[str]
    timeframes: list[str]
    indicators: list[str]
    strategy_classes: list[str]
    branch_hints: list[str]


@dataclass(frozen=True)
class TomacBranchRow:
    relative_path: str
    file_kind: str
    family: str
    branch_path: str
    symbols: list[str]
    timeframes: list[str]
    indicators: list[str]
    strategy_classes: list[str]


def _normalize_timeframes(matches: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for match in matches:
        value = match.lower()
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _ordered_unique(values: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _normalize_branch_hint(value: str) -> str:
    normalized = value.strip().rstrip(",").strip().strip("\"'`()[]{}").rstrip(",").strip()
    normalized = re.sub(r"\s*->\s*", " -> ", normalized)
    return normalized.strip()


def _extract_inline_branch_hints(text: str) -> list[str]:
    hints: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "->" not in line or len(line) > 240:
            continue
        if "branch(" in line:
            continue
        candidates = re.findall(r"['\"]([^'\"]{3,240})['\"]", line)
        if not candidates and "=" in line:
            _, rhs = line.split("=", 1)
            candidates = [rhs.strip()]
        for raw_candidate in candidates:
            if "->" not in raw_candidate:
                continue
            candidate = _normalize_branch_hint(raw_candidate)
            segments = [segment.strip(" ,.:;") for segment in candidate.split("->")]
            if len(segments) < 2 or len(segments) > 5:
                continue
            if any(not segment or not re.match(r"^[A-Za-z][A-Za-z0-9_ ]{0,80}$", segment) for segment in segments):
                continue
            hints.append(" -> ".join(segments))
    return hints


def _extract_regime_branch_hints(text: str) -> list[str]:
    hints: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr
            else:
                continue
            if func_name not in {"add_trade", "add_trade_risk", "_add_trade", "add_risk_trade"}:
                continue
            if len(node.args) < 4:
                continue
            regime_arg = node.args[3]
            if not isinstance(regime_arg, ast.Constant) or not isinstance(regime_arg.value, str):
                continue
            hint = REGIME_TO_BRANCH.get(regime_arg.value, "")
            if hint:
                hints.append(hint)

    if hints:
        return hints

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not REGIME_CALL_RE.search(line):
            continue
        quoted = re.findall(r"['\"]([A-Za-z][A-Za-z0-9_]{2,80})['\"]", line)
        if not quoted:
            continue
        regime = quoted[-1]
        hint = REGIME_TO_BRANCH.get(regime, "")
        if hint:
            hints.append(hint)
    return hints


def _parse_strategy_classes(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def _extract_branch_hints(text: str) -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()

    for hint in _extract_inline_branch_hints(text):
        if hint not in seen:
            seen.add(hint)
            hints.append(hint)

    for match in BRANCH_CALL_RE.finditer(text):
        hint = _normalize_branch_hint(f"{match.group('main')} -> {match.group('sub')}")
        if hint and " -> " in hint and hint not in seen:
            seen.add(hint)
            hints.append(hint)

    for hint in _extract_regime_branch_hints(text):
        if hint and hint not in seen:
            seen.add(hint)
            hints.append(hint)

    return hints


def _extract_indicators(text: str) -> list[str]:
    found = [name for name, pattern in INDICATOR_PATTERNS.items() if pattern.search(text)]
    if "killzone" in found and "session" not in found:
        found.append("session")
    return sorted(found)


def _detect_family(
    path_text: str,
    full_text: str,
    indicators: list[str],
    branch_hints: list[str],
    strategy_classes: list[str],
) -> str:
    primary_lower = "\n".join([path_text, *branch_hints, *strategy_classes]).lower()
    lower = f"{primary_lower}\n{full_text}".lower()
    if "pair_relative_value" in lower or "crossindexrelative" in primary_lower or ("pair" in indicators and "relative_value" in indicators):
        return "pair_relative_value"
    if "seasonality" in indicators or "timeofdayseasonality" in primary_lower or "adaptiveslot" in primary_lower:
        return "session_seasonality"
    if any(token in primary_lower for token in ("vwapmeanreclaim", "vwapreclaimpersistence", "rangetransition")):
        return "range_transition"
    if any(token in primary_lower for token in ("liquiditysweepreversal", "priordayliquiditysweepreversal")):
        return "liquidity_sweep_reversal"
    if "dailyatrsqueezebreakout" in primary_lower or "crabelnr7" in primary_lower:
        return "volatility_expansion"
    if "opening_drive" in indicators or "openingdrive" in primary_lower or "openingrang" in primary_lower:
        return "opening_drive"
    if "swingvolatility" in primary_lower or ("swing" in indicators and "volatility" in indicators):
        return "swing_volatility"
    if any(
        token in primary_lower
        for token in (
            "initialbalanceextension",
            "mtftrendalignment",
            "donchiancontinuation",
            "trendpullbackreclaim",
            "dailydonchiantrendcontinuation",
            "pullbackreclaim",
        )
    ):
        return "trend_continuation"
    if any(token in primary_lower for token in ("highexcursion", "priorday", "overnightinventoryfade", "impulsefollowthrough")):
        return "high_excursion"
    if "ib_reentry" in lower or "reentry" in primary_lower:
        return "ib_reentry_density_repair"
    if "high_excursion" in indicators:
        return "high_excursion"
    if any(indicator in indicators for indicator in ("ict", "fvg", "killzone", "order_block", "ote")):
        return "trend_continuation"
    if "trend" in indicators or "supertrend" in indicators or "adx" in indicators:
        return "trend_continuation"
    if "volatility" in indicators:
        return "volatility_expansion"
    return "uncategorized"


def _file_kind(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("test_"):
        return "test"
    if "scan" in name:
        return "scan"
    if "strategy" in name:
        return "strategy"
    return "utility"


def scan_tomac_tree(root: Path) -> list[TomacStrategyRow]:
    rows: list[TomacStrategyRow] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = str(path.relative_to(root))
        symbols = sorted(set(SYMBOL_RE.findall(text.upper())) | set(SYMBOL_RE.findall(relative_path.upper())))
        timeframes = _normalize_timeframes(TIMEFRAME_RE.findall(f"{relative_path}\n{text}"))
        indicators = _extract_indicators(f"{relative_path}\n{text}")
        strategy_classes = _parse_strategy_classes(text)
        branch_hints = _extract_branch_hints(text)
        family = _detect_family(relative_path, text, indicators, branch_hints, strategy_classes)
        rows.append(
            TomacStrategyRow(
                relative_path=relative_path,
                file_kind=_file_kind(path),
                family=family,
                symbols=symbols,
                timeframes=timeframes,
                indicators=indicators,
                strategy_classes=strategy_classes,
                branch_hints=branch_hints,
            )
        )
    return rows


def build_summary(rows: list[TomacStrategyRow]) -> dict[str, object]:
    family_counts = Counter(row.family for row in rows)
    symbol_counts = Counter(symbol for row in rows for symbol in row.symbols)
    timeframe_counts = Counter(timeframe for row in rows for timeframe in row.timeframes)
    indicator_counts = Counter(indicator for row in rows for indicator in row.indicators)
    file_kind_counts = Counter(row.file_kind for row in rows)
    return {
        "total_files": len(rows),
        "family_counts": dict(family_counts.most_common()),
        "symbol_counts": dict(symbol_counts.most_common()),
        "timeframe_counts": dict(timeframe_counts.most_common()),
        "indicator_counts": dict(indicator_counts.most_common()),
        "file_kind_counts": dict(file_kind_counts.most_common()),
    }


def build_branch_rows(rows: list[TomacStrategyRow]) -> list[TomacBranchRow]:
    branch_rows: list[TomacBranchRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if row.file_kind == "test":
            continue
        for branch_hint in row.branch_hints:
            key = (row.relative_path, branch_hint)
            if key in seen:
                continue
            seen.add(key)
            family = _detect_family(row.relative_path, "", row.indicators, [branch_hint], row.strategy_classes)
            branch_rows.append(
                TomacBranchRow(
                    relative_path=row.relative_path,
                    file_kind=row.file_kind,
                    family=family,
                    branch_path=branch_hint,
                    symbols=row.symbols,
                    timeframes=row.timeframes,
                    indicators=row.indicators,
                    strategy_classes=row.strategy_classes,
                )
            )
    return branch_rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory local TOMAC Python strategies and scans.")
    parser.add_argument("--tomac-root", required=True, help="Path to the TOMAC root directory.")
    parser.add_argument("--output-json", required=True, help="Where to write the inventory JSON payload.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.tomac_root)
    rows = scan_tomac_tree(root)
    branch_rows = build_branch_rows(rows)
    payload = {
        "tomac_root": str(root),
        "summary": {
            **build_summary(rows),
            "branch_count": len(branch_rows),
        },
        "rows": [asdict(row) for row in rows],
        "branch_rows": [asdict(row) for row in branch_rows],
    }
    output = Path(args.output_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
