from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomac_strategy_inventory as inventory


@dataclass(frozen=True)
class CoverageRow:
    family: str
    subfamily: str
    representative_branch: str
    source_files: int
    source_paths: list[str]
    match_tokens: list[str]
    active_claim_count: int
    active_claim_agents: list[str]
    active_claim_files: list[str]
    status: str
    note: str


SUBFAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("initial_balance_mtf_reentry", ("mtftrendcontinuationreentry", "ibreentry", "tomacibreentrydensityrepairscan")),
    ("initial_balance_mtf_continuation", ("mtftrendcontinuation", "initialbalanceextension", "ibextensiontrend", "tomacinitialbalanceextensionmtfcontinuation")),
    ("cross_index_relative_value", ("crossindexrelativemomentum", "crossindexrelativevalue", "zscoretrendcontinuation", "zscoremeanreversion", "pairrelativevalue")),
    ("balanced_tod_portfolio", ("balancedadaptiveslotportfolio", "todportfolio", "balancedtodportfolio")),
    ("session_seasonality_slots", ("adaptiveslotmomentum", "adaptiveslotcontrarian", "portfolioadaptiveslotcontrarian")),
    ("daily_atr_squeeze_breakout", ("dailyatrsqueezebreakout", "swingvolatilityscan", "squeezebreakout")),
    ("daily_donchian_trend_continuation", ("dailydonchiantrendcontinuation", "dailydonchian")),
    ("vwap_mean_reclaim", ("vwapmeanreclaim", "vwapreclaim", "rangetransition")),
    ("vwap_reclaim_persistence", ("vwapreclaimpersistence",)),
    ("nr7_crabel_range_expansion", ("crabelnr7", "nr7", "nr7rangeexpansion", "narrowrangecompression", "volatilitycompressionexpansion")),
    ("trend_pullback_reclaim", ("pullbackreclaim", "trendpullback")),
    ("donchian_trend_breakout", ("donchianchannel", "donchiantrendbreak", "trendbreak")),
    ("opening_drive_breakout", ("openingdrivebreakout", "orbreakout", "openingrangecontinuation")),
    ("opening_drive_failed_breakout_fade", ("failedbreakoutfade", "orfailedbreakoutfade")),
    ("opening_drive_two_leg_continuation", ("openingdrivetwolegcontinuation", "ortwolegcontinuation")),
    ("prior_day_liquidity_sweep_reversal", ("liquiditysweepreversal", "pdhsweepreversal", "pdlsweepreversal")),
    ("high_excursion_priorday_overnight", ("highexcursion", "priordayextremecontinuation", "overnight", "overnightinventoryfade", "impulse", "impulsefollowthrough")),
    ("supertrend_adx_displacement", ("supertrendadxdisplacement", "trendpullbackorliquiditysweepreclaim", "trendpullbackreclaim", "liquiditysweepreclaim")),
    ("killzone_sweep_fvg_ob", ("killzonesweepfvgobreclaim", "killzoneliquiditysweepreclaim")),
)

SUBFAMILY_FAMILY: dict[str, str] = {
    "balanced_tod_portfolio": "session_seasonality",
    "cross_index_relative_value": "pair_relative_value",
    "daily_atr_squeeze_breakout": "volatility_expansion",
    "daily_donchian_trend_continuation": "trend_continuation",
    "donchian_trend_breakout": "trend_continuation",
    "high_excursion_priorday_overnight": "high_excursion",
    "initial_balance_mtf_continuation": "trend_continuation",
    "initial_balance_mtf_reentry": "trend_continuation",
    "killzone_sweep_fvg_ob": "trend_continuation",
    "nr7_crabel_range_expansion": "volatility_expansion",
    "opening_drive_breakout": "opening_drive",
    "opening_drive_failed_breakout_fade": "opening_drive",
    "opening_drive_two_leg_continuation": "opening_drive",
    "prior_day_liquidity_sweep_reversal": "liquidity_sweep_reversal",
    "session_seasonality_slots": "session_seasonality",
    "supertrend_adx_displacement": "trend_continuation",
    "swing_volatility": "swing_volatility",
    "trend_pullback_reclaim": "trend_continuation",
    "vwap_mean_reclaim": "range_transition",
    "vwap_reclaim_persistence": "range_transition",
}

SUBFAMILY_BRANCH_FALLBACKS: dict[str, str] = {
    "balanced_tod_portfolio": "SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio",
    "cross_index_relative_value": "RangeReversion -> CrossIndexRelativeValue -> ZScoreMeanReversion",
    "daily_atr_squeeze_breakout": "VolatilityCompressionExpansion -> DailyAtrSqueezeBreakout -> SwingBreakoutContinuation",
    "daily_donchian_trend_continuation": "TrendExpansion -> DailyDonchianTrendContinuation -> SwingBreakoutContinuation",
    "donchian_trend_breakout": "TrendExpansion -> DonchianChannel",
    "high_excursion_priorday_overnight": "TrendExpansion -> PriorDayExtremeContinuation",
    "initial_balance_mtf_continuation": "TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuation",
    "initial_balance_mtf_reentry": "TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuationReentry",
    "nr7_crabel_range_expansion": "VolatilityCompressionExpansion -> CrabelNR7",
    "opening_drive_breakout": "TrendExpansion -> OpeningDriveBreakout",
    "opening_drive_failed_breakout_fade": "RangeReversion -> OpeningDriveFailedBreakoutFade",
    "opening_drive_two_leg_continuation": "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation",
    "prior_day_liquidity_sweep_reversal": "RangeReversion -> PriorDayLiquiditySweepReversal",
    "session_seasonality_slots": "SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian",
    "trend_pullback_reclaim": "TrendExpansion -> PullbackReclaim",
    "vwap_mean_reclaim": "RangeTransition -> VWAPMeanReclaim",
    "vwap_reclaim_persistence": "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
}

GENERIC_BRANCH_TOKENS = {
    "mixedrootobservation",
    "mtftrendalignment",
    "rangereversion",
    "rangetransition",
    "sessionrhythm",
    "timeofdayseasonality",
    "trendexpansion",
    "volatilitycompressionexpansion",
}


def _branch_component_alias_tokens(value: str) -> list[str]:
    normalized = _normalize_text(value)
    tokens: set[str] = {normalized} if normalized else set()
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", value)
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", spaced)
    words = [piece.lower() for piece in re.split(r"[^A-Za-z0-9]+", spaced) if piece]
    for size in range(3, len(words) + 1):
        tokens.add("".join(words[:size]))
    return sorted(tokens)


def _normalize_claim_text(payload: dict[str, Any], claim_path: Path) -> str:
    fields = [
        claim_path.name,
        str(payload.get("branch_path") or ""),
        str(payload.get("factor_id") or ""),
        str(payload.get("scope") or ""),
        str(payload.get("active_task") or ""),
        str(payload.get("progress_report") or ""),
        str(payload.get("latest_report") or ""),
        str(payload.get("write_surface") or ""),
        str(payload.get("run_root") or ""),
        str(payload.get("tmp_root") or ""),
        str(payload.get("repo_packet") or ""),
    ]
    return _normalize_text(" ".join(fields))


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _claim_status(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "").lower()
    if (
        payload.get("terminalized_at")
        or payload.get("terminal_at")
        or payload.get("terminal_status")
        or status.startswith("terminal")
        or "terminalized" in status
    ):
        return "terminalized"
    if payload.get("decision") or payload.get("terminal_decision"):
        return "terminalized"
    return "active"


def _branch_component_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for component in value.split("->"):
        for token in _branch_component_alias_tokens(component):
            if token and token not in GENERIC_BRANCH_TOKENS:
                tokens.append(token)
    return tokens


def _load_active_claims(claims_dir: Path) -> list[tuple[Path, dict[str, Any], str]]:
    rows: list[tuple[Path, dict[str, Any], str]] = []
    for claim_path in sorted(claims_dir.glob("*.claim")):
        try:
            payload = json.loads(claim_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if _claim_status(payload) != "active":
            continue
        rows.append((claim_path, payload, _normalize_claim_text(payload, claim_path)))
    return rows


def _match_subfamilies(haystack: str) -> list[str]:
    matches: list[str] = []
    for subfamily, tokens in SUBFAMILY_RULES:
        if any(token in haystack for token in tokens):
            matches.append(subfamily)
    return matches


def _derive_subfamilies(row: inventory.TomacStrategyRow) -> list[str]:
    matches: list[str] = []
    for branch_hint in row.branch_hints:
        matches.extend(_match_subfamilies(_normalize_text(branch_hint)))
    haystack_parts = [row.relative_path, *row.branch_hints, *row.strategy_classes]
    matches.extend(_match_subfamilies(_normalize_text(" ".join(haystack_parts))))
    if matches:
        return sorted(set(matches))
    return [row.family]


def _representative_branch_for_subfamily(row: inventory.TomacStrategyRow, subfamily: str) -> str:
    for branch_hint in row.branch_hints:
        normalized = _normalize_text(branch_hint)
        for name, tokens in SUBFAMILY_RULES:
            if name == subfamily and any(token in normalized for token in tokens):
                return branch_hint
    if len(row.branch_hints) == 1:
        return row.branch_hints[0]
    return SUBFAMILY_BRANCH_FALLBACKS.get(subfamily, "")


def _match_tokens_for_subfamily(subfamily: str, rows: list[inventory.TomacStrategyRow]) -> list[str]:
    tokens: list[str] = []
    subfamily_rule_tokens: tuple[str, ...] = ()
    for name, subfamily_tokens in SUBFAMILY_RULES:
        if name == subfamily:
            tokens.extend(subfamily_tokens)
            subfamily_rule_tokens = subfamily_tokens
            break
    fallback_branch = SUBFAMILY_BRANCH_FALLBACKS.get(subfamily)
    if fallback_branch:
        tokens.extend(_branch_component_tokens(fallback_branch))
    for row in rows:
        stem = _normalize_text(Path(row.relative_path).stem)
        if stem:
            tokens.append(stem)
        for hint in row.branch_hints:
            if not hint:
                continue
            normalized_hint = _normalize_text(hint)
            if subfamily_rule_tokens and not any(token in normalized_hint for token in subfamily_rule_tokens):
                continue
            tokens.extend(_branch_component_tokens(hint))
    return sorted({token for token in tokens if token})


def _claim_matches_tokens(tokens: list[str], normalized_text: str) -> bool:
    matched = [token for token in tokens if token and token in normalized_text]
    if not matched:
        return False
    if any(len(token) >= 10 for token in matched):
        return True
    return len(matched) >= 2


def build_coverage_rows(tomac_rows: list[inventory.TomacStrategyRow], active_claims: list[tuple[Path, dict[str, Any], str]]) -> list[CoverageRow]:
    by_group: dict[tuple[str, str], list[inventory.TomacStrategyRow]] = {}
    for row in tomac_rows:
        if row.file_kind == "test":
            continue
        for subfamily in _derive_subfamilies(row):
            canonical_family = SUBFAMILY_FAMILY.get(subfamily, row.family)
            by_group.setdefault((canonical_family, subfamily), []).append(row)

    coverage_rows: list[CoverageRow] = []
    for (family, subfamily), rows in sorted(by_group.items()):
        representative_branch = next(
            (_representative_branch_for_subfamily(row, subfamily) for row in rows if _representative_branch_for_subfamily(row, subfamily)),
            "",
        )
        match_tokens = _match_tokens_for_subfamily(subfamily, rows)
        matched_claims = [
            (claim_path, payload)
            for claim_path, payload, normalized in active_claims
            if _claim_matches_tokens(match_tokens, normalized)
        ]
        active_claim_agents = [str(payload.get("agent_name") or "") for _, payload in matched_claims if payload.get("agent_name")]
        active_claim_files = [claim_path.name for claim_path, _ in matched_claims]
        status = "active_claimed" if matched_claims else "available_for_rotation"
        note = "active Board B work exists" if matched_claims else "no active Board B claim matched this family"
        coverage_rows.append(
            CoverageRow(
                family=family,
                subfamily=subfamily,
                representative_branch=representative_branch,
                source_files=len(rows),
                source_paths=[row.relative_path for row in rows[:8]],
                match_tokens=match_tokens,
                active_claim_count=len(matched_claims),
                active_claim_agents=active_claim_agents,
                active_claim_files=active_claim_files,
                status=status,
                note=note,
            )
        )
    return coverage_rows


def write_csv(rows: list[CoverageRow], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family",
                "subfamily",
                "representative_branch",
                "source_files",
                "source_paths",
                "match_tokens",
                "active_claim_count",
                "active_claim_agents",
                "active_claim_files",
                "status",
                "note",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "family": row.family,
                    "subfamily": row.subfamily,
                    "representative_branch": row.representative_branch,
                    "source_files": row.source_files,
                    "source_paths": "|".join(row.source_paths),
                    "match_tokens": "|".join(row.match_tokens),
                    "active_claim_count": row.active_claim_count,
                    "active_claim_agents": "|".join(row.active_claim_agents),
                    "active_claim_files": "|".join(row.active_claim_files),
                    "status": row.status,
                    "note": row.note,
                }
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a TOMAC family coverage matrix from inventory and current Board B claims.")
    parser.add_argument("--tomac-root", required=True)
    parser.add_argument("--claims-dir", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tomac_root = Path(args.tomac_root)
    claims_dir = Path(args.claims_dir)
    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)

    tomac_rows = inventory.scan_tomac_tree(tomac_root)
    active_claims = _load_active_claims(claims_dir)
    coverage_rows = build_coverage_rows(tomac_rows, active_claims)

    payload = {
        "tomac_root": str(tomac_root),
        "claims_dir": str(claims_dir),
        "family_count": len(coverage_rows),
        "coverage_rows": [row.__dict__ for row in coverage_rows],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv(coverage_rows, output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
