"""Small verdict helpers for IBKR provider-ladder admission.

These helpers intentionally do not call IBKR. They classify already-recorded
provider exits and row counts so Gate 1 wrappers do not mistake provider-status
readiness for direct historical-data proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class IbkrLadderVerdict:
    decision: str
    reason: str
    provider_rows_ready: bool
    allow_material_build: bool
    allow_auto_quant: bool
    factor_verdict: bool
    cooldown_recommended: bool = False


def classify_ibkr_ladder_state(
    *,
    provider_status_exit: int | None,
    fetch_exits: Mapping[str, int],
    row_counts: Mapping[str, int],
    material_count: int,
    ranked_row_count: int,
    recent_blocked_ladders: int = 0,
) -> IbkrLadderVerdict:
    """Classify whether an IBKR ladder has enough evidence for AQ.

    `provider-status --provider ibkr` only proves the configured provider path
    can be inspected. It does not prove `reqHistoricalData` returned rows for
    the target contract. Any AQ/material/rank stage needs real rows first.
    """

    total_rows = sum(max(int(value), 0) for value in row_counts.values())
    all_fetches_empty = bool(fetch_exits) and all(int(code) != 0 for code in fetch_exits.values())
    repeated_provider_block = recent_blocked_ladders >= 2

    if total_rows <= 0 and material_count <= 0:
        status_text = (
            "provider-status succeeded"
            if provider_status_exit == 0
            else f"provider-status exit={provider_status_exit}"
        )
        fetch_text = "all fetch exits were non-zero" if all_fetches_empty else "no fetch produced rows"
        if repeated_provider_block:
            return IbkrLadderVerdict(
                decision="provider_cooldown_after_repeated_no_rows",
                reason=(
                    f"{status_text}, but {fetch_text}; no normalized IBKR rows exist; "
                    f"recent blocked IBKR ladders={recent_blocked_ladders}."
                ),
                provider_rows_ready=False,
                allow_material_build=False,
                allow_auto_quant=False,
                factor_verdict=False,
                cooldown_recommended=True,
            )
        return IbkrLadderVerdict(
            decision="provider_blocked_no_rows_no_materials",
            reason=f"{status_text}, but {fetch_text}; no normalized IBKR rows exist.",
            provider_rows_ready=False,
            allow_material_build=False,
            allow_auto_quant=False,
            factor_verdict=False,
        )

    if total_rows > 0 and material_count <= 0:
        return IbkrLadderVerdict(
            decision="provider_rows_ready",
            reason="normalized IBKR provider rows exist; material build may proceed.",
            provider_rows_ready=True,
            allow_material_build=True,
            allow_auto_quant=False,
            factor_verdict=False,
        )

    if material_count > 0 and ranked_row_count <= 0:
        return IbkrLadderVerdict(
            decision="materials_ready_no_rank",
            reason="AQ materials exist but no rank rows have been written.",
            provider_rows_ready=True,
            allow_material_build=False,
            allow_auto_quant=True,
            factor_verdict=False,
        )

    return IbkrLadderVerdict(
        decision="rank_rows_ready",
        reason="AQ rank rows exist; classify factor economics from cost stress.",
        provider_rows_ready=True,
        allow_material_build=False,
        allow_auto_quant=False,
        factor_verdict=True,
    )
