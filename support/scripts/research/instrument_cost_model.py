#!/usr/bin/env python3
"""Shared instrument cost model: the single source of truth for transaction costs.

Why this module exists
----------------------
Before this file there was *no* shared cost model. Every factor-screening script
hard-coded its own fee. Two bad patterns were copied around:

  1. ``cost_bps = 5`` / ``fee = 0.0005`` / ``net = gross - 2 * fee`` in *return space*
     (e.g. the frozen ``trend_fixed_rrr_bracket_v1.py`` and the ``tomac_nq`` screens).
     This subtracts a flat 10bps round-turn **regardless of instrument, price, or
     contract multiplier**. For an index future like NQ the *real* IBKR round-turn
     cost is ~0.1bps of notional, so the flat 10bps over-charges by ~60-90x.
  2. Each ``run_ibkr_*_gate1`` script defining its *own* per-contract cost dict,
     so the verified numbers drifted between copies.

This module fixes the root cause: **one** verified, source-backed per-contract
cost table plus the correct ``per-contract-USD -> return-space`` conversion that the
verified scripts already proved (``all_in_round_turn / (price * multiplier)``).

Contract (from the ``ict-engi-fact-rese-muta`` skill, references
``instrument-cost-model-verification.md`` and ``futures-contract-cost-models-ibkr.md``):

  * Never hard-code a fee. The real commission model is product-specific per-contract
    cost (broker execution + exchange fee recovery + regulatory + clearing), converted
    to return space using the contract multiplier and the traded price.
  * ``bps/notional`` is valid ONLY as the actual commission model (some equities) or as
    an explicitly-labeled stress/slippage scenario, never as a stand-in for a futures
    commission. ``5bps/side`` here is legacy stress telemetry only, exposed as an
    explicit, named parameter (``LEGACY_STRESS_BPS_PER_SIDE``), NOT a commission or
    candidate gate.
  * Fail closed: an unknown or unverified instrument is ``cost_model_unverified`` and must
    block ``promotion_allowed`` / ``trade_usable`` until refreshed from an official source.

Seed provenance: the verified rows below were recorded from IBKR public pricing pages and
IBKR Products & Exchanges broker-side contract specs on 2026-05-29/30 (see the skill
reference). Refresh before any new live/paper decision via :func:`ibkr_refresh_instructions`.
The seed is a dated starting point, not eternal truth. That is why each row carries a
``status`` and ``source`` and why :func:`assert_verified_for_promotion` exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# --------------------------------------------------------------------------------------
# Legacy stress telemetry (NOT a commission model or candidate gate)
# --------------------------------------------------------------------------------------
# Legacy 5bps/side stress telemetry. It is not a futures commission model and must not
# decide factor-candidate admission; real verified instrument cost is the only cost gate.
LEGACY_STRESS_BPS_PER_SIDE: float = 5.0


def stress_round_turn_fraction(bps_per_side: float = LEGACY_STRESS_BPS_PER_SIDE) -> float:
    """Round-turn cost as a return-space fraction for an explicit per-side bps stress.

    ``bps_per_side`` is an explicitly chosen stress level (default = legacy 5bps/side
    telemetry). Round turn = 2 sides. 1 bps = 1e-4. This is intentionally
    instrument-agnostic because it is a *stress*, not a commission model or gate.
    """
    return 2.0 * float(bps_per_side) * 1e-4


def net_after_stress_bps(
    gross_return_fraction: float,
    trades: int,
    bps_per_side: float = LEGACY_STRESS_BPS_PER_SIDE,
) -> float:
    """Aggregate net return after applying explicit per-side bps *telemetry* to N trades."""
    return float(gross_return_fraction) - int(trades) * stress_round_turn_fraction(bps_per_side)


# --------------------------------------------------------------------------------------
# Cost-model status vocabulary (mirrors the skill contract)
# --------------------------------------------------------------------------------------
STATUS_VERIFIED = "verified_ibkr_broker_side"
STATUS_DEFAULT = "default_assumption_unverified"
STATUS_UNVERIFIED = "cost_model_unverified"


@dataclass(frozen=True)
class FuturesCostProfile:
    """Per-contract futures cost profile with the correct USD -> return-space conversion.

    Field order is kept compatible with the inline ``FuturesCostProfile`` that grew up in
    ``run_tomac_index_futures_clean_aq_v1.py`` so that script (and the gate1 runners) can
    adopt this shared module with a one-line import swap. Three fields are added:
    ``status``, ``source_url``, ``fetched_at`` for provenance and fail-closed promotion.
    """

    profile_id: str
    symbol: str
    exchange: str
    tick_size: float
    tick_value: float
    commission_per_contract_side: float = 1.00
    exchange_fees_per_contract_side: float = 1.40
    regulatory_fees_per_contract_side: float = 0.02
    assumed_spread_ticks: float = 1.0
    assumed_slippage_ticks_per_side: float = 1.0
    source: str = "ict_engine_default_assumption_v1"
    # --- added for the shared model: provenance + fail-closed promotion gate ---
    status: str = STATUS_DEFAULT
    source_url: str = ""
    fetched_at: str = ""
    effective_date: str = ""

    # -- contract geometry --
    @property
    def root_symbol(self) -> str:
        """Compatibility alias for older wrappers that named the futures root `root_symbol`."""
        return self.symbol

    @property
    def point_value(self) -> float:
        """USD per 1.0 price point = contract multiplier (tick_value / tick_size)."""
        return self.tick_value / self.tick_size

    @property
    def all_in_per_contract_per_side(self) -> float:
        """Broker + exchange + regulatory commission for one side, in USD."""
        return (
            self.commission_per_contract_side
            + self.exchange_fees_per_contract_side
            + self.regulatory_fees_per_contract_side
        )

    @property
    def all_in_round_turn_per_contract(self) -> float:
        """Commission-only round-turn cost (both sides), in USD."""
        return 2.0 * self.all_in_per_contract_per_side

    @property
    def verified_for_promotion(self) -> bool:
        """True only when the cost model is verified broker-side; gates downstream promotion."""
        return self.status.startswith("verified")

    # -- USD fees -> price points --
    def round_trip_fee_cash(self) -> float:
        """Commission-only round-turn cost (USD). Alias of all_in_round_turn_per_contract."""
        return self.all_in_round_turn_per_contract

    def round_trip_cost_cash(self) -> float:
        """Commission + assumed slippage/spread round-turn cost (USD).

        Slippage is an *assumed* model layered on top of the verified commission; the skill
        requires it be kept separate, hence the distinct fee-only vs cost methods.
        """
        slippage_ticks = self.assumed_spread_ticks + 2.0 * self.assumed_slippage_ticks_per_side
        return self.round_trip_fee_cash() + slippage_ticks * self.tick_value

    def round_trip_fee_points(self) -> float:
        return self.round_trip_fee_cash() / self.point_value

    def round_trip_cost_points(self) -> float:
        return self.round_trip_cost_cash() / self.point_value

    # -- price points -> return-space (% of notional) --
    def round_trip_fee_pct(self, representative_price: float) -> float:
        """Commission-only round-turn cost as PERCENT of notional at the given price."""
        if representative_price <= 0:
            raise ValueError("representative_price must be positive")
        return self.round_trip_fee_points() / representative_price * 100.0

    def round_trip_cost_pct(self, representative_price: float) -> float:
        """Commission + assumed slippage round-turn cost as PERCENT of notional."""
        if representative_price <= 0:
            raise ValueError("representative_price must be positive")
        return self.round_trip_cost_points() / representative_price * 100.0

    # -- return-space fractions (what backtests subtract from a fractional return) --
    def round_trip_fee_fraction(self, price: float) -> float:
        """Commission-only round-turn cost as a return fraction (pct / 100)."""
        return self.round_trip_fee_pct(price) / 100.0

    def round_trip_cost_fraction(self, price: float) -> float:
        """Commission + assumed slippage round-turn cost as a return fraction."""
        return self.round_trip_cost_pct(price) / 100.0

    def per_side_fee_bps(self, price: float) -> float:
        """Commission-only per-side cost in basis points of notional at the given price."""
        return self.all_in_per_contract_per_side / (price * self.point_value) * 1e4


# --------------------------------------------------------------------------------------
# Verified per-contract seed table (source-backed; refresh before live/paper decisions)
# --------------------------------------------------------------------------------------
# Components are per-contract per-side USD: (commission, exchange fee recovery, regulatory).
# Verified rows reflect IBKR tiered low-volume non-member USD rates, 2026-05-29/30, ordinary
# outright execution, no give-up surcharge. tick_size/tick_value come from IBKR broker-side
# secdef. Where the prior inline table carried an unverified guess that conflicts with the
# skill's verified value (e.g. MNQ all-in 0.62, not 0.74), the verified value wins here.
_IBKR_PRICING = "https://www.interactivebrokers.com/en/pricing/commissions-futures.php"
_V = "verified_ibkr_broker_side"
_VERIFIED_SRC = "IBKR pricing + Products&Exchanges secdef, recorded 2026-05-29/30 (skill: futures-contract-cost-models-ibkr.md)"


def _verified(
    pid: str, symbol: str, exch: str, tick: float, tv: float,
    comm: float, exch_fee: float, reg: float = 0.02,
) -> FuturesCostProfile:
    return FuturesCostProfile(
        pid, symbol, exch, tick, tv, comm, exch_fee, reg,
        source=_VERIFIED_SRC, status=_V, source_url=_IBKR_PRICING,
        fetched_at="2026-05-30", effective_date="2026-05-30",
    )


def _default(
    pid: str, symbol: str, exch: str, tick: float, tv: float,
    comm: float = 0.85, exch_fee: float = 1.40, reg: float = 0.02,
) -> FuturesCostProfile:
    return FuturesCostProfile(
        pid, symbol, exch, tick, tv, comm, exch_fee, reg,
        source="ict_engine_default_assumption_unverified", status=STATUS_DEFAULT,
    )


FUTURES_COST_PROFILES: dict[str, FuturesCostProfile] = {
    # CME / CBOT equity index: full size
    "ES": _verified("CME_ES_IBKR_verified_20260530_v1", "ES", "CME", 0.25, 12.5, 0.85, 1.38),
    "NQ": _verified("CME_NQ_IBKR_verified_20260530_v1", "NQ", "CME", 0.25, 5.0, 0.85, 1.38),
    "YM": _verified("CBOT_YM_IBKR_verified_20260530_v1", "YM", "CBOT", 1.0, 5.0, 0.85, 1.38),
    # CME / CBOT equity index: micro / e-micro
    "MES": _verified("CME_MES_IBKR_verified_20260530_v1", "MES", "CME", 0.25, 1.25, 0.25, 0.35),
    "MNQ": _verified("CME_MNQ_IBKR_verified_20260530_v1", "MNQ", "CME", 0.25, 0.5, 0.25, 0.35),
    "M2K": _verified("CME_M2K_IBKR_verified_20260530_v1", "M2K", "CME", 0.1, 0.5, 0.25, 0.35),
    "MYM": _verified("CBOT_MYM_IBKR_verified_20260530_v1", "MYM", "CBOT", 1.0, 0.5, 0.25, 0.35),
    "RTY": _default("CME_RTY_default_v1", "RTY", "CME", 0.1, 5.0),
    # COMEX precious metals
    "GC": _verified("COMEX_GC_IBKR_verified_20260530_v1", "GC", "COMEX", 0.1, 10.0, 0.85, 1.65),
    "MGC": _verified("COMEX_MGC_IBKR_verified_20260530_v1", "MGC", "COMEX", 0.1, 1.0, 0.25, 0.70),
    "SI": _verified("COMEX_SI_IBKR_verified_20260530_v1", "SI", "COMEX", 0.005, 25.0, 0.85, 1.65),
    "HG": _verified("COMEX_HG_IBKR_verified_20260530_v1", "HG", "COMEX", 0.0005, 12.5, 0.85, 1.65),
    "SIL": _default("COMEX_SIL_default_v1", "SIL", "COMEX", 0.005, 5.0, 0.25, 0.35),
    # XAU is a TOMAC continuous alias and must be mapped to GC or MGC before promotion.
    "XAU": _default("COMEX_XAU_alias_unverified_v1", "XAU", "COMEX", 0.1, 10.0, 0.85, 1.65),
    # NYMEX energy
    "CL": _verified("NYMEX_CL_IBKR_verified_20260530_v1", "CL", "NYMEX", 0.01, 10.0, 0.85, 1.50),
    "MCL": _default("NYMEX_MCL_default_v1", "MCL", "NYMEX", 0.01, 1.0, 0.25, 0.35),
    "NG": _default("NYMEX_NG_default_v1", "NG", "NYMEX", 0.001, 10.0, 0.85, 1.50),
    # CBOT rates
    "ZN": _verified("CBOT_ZN_IBKR_verified_20260530_v1", "ZN", "CBOT", 0.015625, 15.625, 0.85, 0.80),
    "ZF": _verified("CBOT_ZF_IBKR_verified_20260530_v1", "ZF", "CBOT", 0.0078125, 7.8125, 0.85, 0.65),
    "ZB": _verified("CBOT_ZB_IBKR_verified_20260530_v1", "ZB", "CBOT", 0.03125, 31.25, 0.85, 0.87),
    # CME FX
    "6E": _verified("CME_6E_IBKR_verified_20260530_v1", "6E", "CME", 0.00005, 6.25, 0.85, 1.60),
    "M6E": _default("CME_M6E_default_v1", "M6E", "CME", 0.00005, 1.25, 0.25, 0.35),
    "BRE": _verified("CME_BRE_IBKR_verified_20260530_v1", "BRE", "CME", 0.00005, 5.0, 0.85, 1.60),
    # CBOT / CME ags & livestock
    "ZC": _verified("CBOT_ZC_IBKR_verified_20260530_v1", "ZC", "CBOT", 0.0025, 12.5, 0.85, 2.15),
    "ZS": _verified("CBOT_ZS_IBKR_verified_20260530_v1", "ZS", "CBOT", 0.0025, 12.5, 0.85, 2.15),
    "ZW": _default("CBOT_ZW_default_v1", "ZW", "CBOT", 0.0025, 12.5, 0.85, 2.15),
    "LE": _verified("CME_LE_IBKR_verified_20260530_v1", "LE", "CME", 0.00025, 10.0, 0.85, 2.10),
}

# Roots ordered longest-first so MES/MNQ/MGC/MCL/M6E match before ES/NQ/GC/CL/6E.
_ROOTS_BY_LEN: tuple[str, ...] = tuple(
    sorted(FUTURES_COST_PROFILES.keys(), key=len, reverse=True)
)


def normalize_futures_root(symbol: str) -> str:
    """Map a traded symbol (e.g. ``NQ/USD``, ``MNQ1!``, ``nq future``) to a known root."""
    upper = str(symbol).upper().strip()
    for root in _ROOTS_BY_LEN:
        if upper.startswith(root):
            return root
    letters = "".join(ch for ch in upper if ch.isalpha())
    return letters


def futures_cost_profile(symbol: str) -> Optional[FuturesCostProfile]:
    """Return the cost profile for a symbol, or ``None`` if the root is unknown (fail closed)."""
    return FUTURES_COST_PROFILES.get(normalize_futures_root(symbol))


def product_label_for_symbol(symbol: str) -> str:
    root = normalize_futures_root(symbol)
    if root in {"ES", "MES", "NQ", "MNQ", "YM", "MYM", "RTY", "M2K"}:
        return "equity_index"
    if root in {"6E", "M6E", "BRE"}:
        return "fx_futures"
    if root in {"GC", "MGC", "SI", "SIL", "HG", "XAU"}:
        return "precious_metals_futures"
    if root in {"CL", "MCL", "NG"}:
        return "energy_futures"
    if root in {"ZN", "ZB", "ZF"}:
        return "rates_futures"
    if root in {"ZC", "ZS", "ZW", "LE"}:
        return "agri_livestock_futures"
    return "futures_other"


# --------------------------------------------------------------------------------------
# Public cost API: the no-hard-coding entry points screens should call
# --------------------------------------------------------------------------------------
class CostModelUnverified(RuntimeError):
    """Raised when a verified cost model is required but unavailable (fail closed)."""


def real_fee_round_turn_fraction(symbol: str, price: float) -> float:
    """Real commission-only round-turn cost as a return fraction at ``price``.

    Raises CostModelUnverified for an unknown root so callers cannot silently fall back
    to a guessed fee. This is the honest replacement for hard-coded ``2 * fee``.
    """
    profile = futures_cost_profile(symbol)
    if profile is None:
        raise CostModelUnverified(f"no cost profile for symbol root {symbol!r}; refresh from official source")
    return profile.round_trip_fee_fraction(price)


def real_cost_round_turn_fraction(symbol: str, price: float) -> float:
    """Real commission + assumed slippage round-turn cost as a return fraction at ``price``."""
    profile = futures_cost_profile(symbol)
    if profile is None:
        raise CostModelUnverified(f"no cost profile for symbol root {symbol!r}; refresh from official source")
    return profile.round_trip_cost_fraction(price)


def net_after_real_fee(gross_return_fraction: float, trades: int, symbol: str, price: float) -> float:
    """Aggregate net return after the real per-contract commission for N trades at ``price``."""
    return float(gross_return_fraction) - int(trades) * real_fee_round_turn_fraction(symbol, price)


def assert_verified_for_promotion(symbol: str) -> FuturesCostProfile:
    """Return the profile only if verified broker-side; else raise (fail closed for promotion)."""
    profile = futures_cost_profile(symbol)
    if profile is None:
        raise CostModelUnverified(f"no cost profile for {symbol!r}")
    if not profile.verified_for_promotion:
        raise CostModelUnverified(
            f"cost model for {symbol!r} is {profile.status!r}; refresh from official source before promotion"
        )
    return profile


def cost_model_packet(symbol: str, representative_price: Optional[float] = None) -> dict:
    """Build the cost-model reporting packet the skill requires in workdocs / terminal metrics.

    Includes both the real verified cost and explicit legacy 5bps stress telemetry so a
    reader can never again mistake the stress for the commission or a candidate gate.
    """
    profile = futures_cost_profile(symbol)
    if profile is None:
        return {
            "cost_model_status": STATUS_UNVERIFIED,
            "symbol": symbol,
            "reason": "no cost profile for root; refresh from official source before any cost-survival claim",
            "legacy_stress_bps_per_side": LEGACY_STRESS_BPS_PER_SIDE,
            "legacy_stress_role": "telemetry_not_futures_commission_model_not_candidate_gate",
        }
    packet = {
        # Canonical status aliases. Downstream practical-closure consumers accept
        # `status`, while Gate 1 packets historically emitted `cost_model_status`.
        "status": profile.status,
        "cost_model_status": profile.status,
        "verified_for_promotion": profile.verified_for_promotion,
        "cost_profile_id": profile.profile_id,
        "cost_model_source": profile.source,
        "cost_model_source_url": profile.source_url,
        "cost_model_fetched_at": profile.fetched_at,
        "cost_model_effective_date": profile.effective_date,
        "fee_effective_date": profile.effective_date,
        "broker": "IBKR",
        "pricing_plan": "tiered_low_volume_non_member_assumed",
        "instrument_class": "future",
        "currency": "USD",
        "unit_convention": "per_contract_round_turn_usd",
        "venue_routing": f"{profile.exchange}_direct_futures_execution_via_IBKR",
        "product_label": product_label_for_symbol(symbol),
        "symbol_root": normalize_futures_root(symbol),
        "exchange": profile.exchange,
        "contract_multiplier": profile.point_value,
        "tick_size": profile.tick_size,
        "tick_value": profile.tick_value,
        "commission_per_contract_per_side": profile.commission_per_contract_side,
        "exchange_fee_per_contract_per_side": profile.exchange_fees_per_contract_side,
        "regulatory_fee_per_contract_per_side": profile.regulatory_fees_per_contract_side,
        "all_in_per_contract_per_side": profile.all_in_per_contract_per_side,
        "all_in_round_turn_per_contract": profile.all_in_round_turn_per_contract,
        # Explicitly-labeled legacy stress telemetry. NOT the commission model or a gate.
        "legacy_stress_bps_per_side": LEGACY_STRESS_BPS_PER_SIDE,
        "legacy_stress_round_turn_pct": stress_round_turn_fraction() * 100.0,
        "legacy_stress_role": "telemetry_not_futures_commission_model_not_candidate_gate",
        "slippage_note": "assumed_slippage_spread_ticks are a separate explicit model, not broker fees",
    }
    if representative_price is None or representative_price <= 0:
        packet.update(
            {
                "representative_price": None,
                "price_dependent_cost_fields": "not_computed_without_positive_representative_price",
            }
        )
        return packet
    packet.update(
        {
            "representative_price": representative_price,
            "real_fee_per_side_bps": profile.per_side_fee_bps(representative_price),
            "real_fee_round_turn_pct": profile.round_trip_fee_pct(representative_price),
            "real_cost_round_turn_pct_incl_assumed_slippage": profile.round_trip_cost_pct(representative_price),
        }
    )
    return packet


def ibkr_refresh_instructions(symbol: str) -> dict:
    """Return the official-source refresh chain for a symbol (official-source lookup path).

    This module ships a dated, source-backed seed; it does NOT silently fabricate live rates.
    To refresh before a live/paper decision, fetch these official sources in the same work
    slice, record source URL + timestamp, and update the row's components + status.
    """
    root = normalize_futures_root(symbol)
    return {
        "symbol_root": root,
        "ibkr_main_pricing": _IBKR_PRICING,
        "ibkr_exchange_fee_pages": {
            "CME": "https://www.interactivebrokers.com/en/accounts/fees/CME.php",
            "CBOT": "https://www.interactivebrokers.com/en/accounts/fees/CBOT.php",
            "COMEX": "https://www.interactivebrokers.com/en/accounts/fees/COMEX.php",
        },
        "ibkr_contract_spec_chain": [
            "GET .../iserver/secdef/search?symbol=<ROOT>",
            "POST .../search/contract-details {productType:FUT, underConid:<conid>}",
            "GET .../trsrv/secdef?conids=<fut_conids>  # multiplier + increment -> tick_value",
        ],
        "skill_reference": "ict-engi-fact-rese-muta: references/futures-contract-cost-models-ibkr.md",
        "rule": "fail closed (cost_model_unverified) if any component cannot be verified in-slice",
    }


if __name__ == "__main__":  # pragma: no cover - manual inspection helper
    import json

    for sym, px in (("NQ", 20000.0), ("MNQ", 20000.0), ("MGC", 2300.0), ("ES", 5200.0)):
        print(json.dumps(cost_model_packet(sym, px), indent=2, sort_keys=True))
