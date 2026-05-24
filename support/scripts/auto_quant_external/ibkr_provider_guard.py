"""Small verdict helpers for IBKR provider-ladder admission.

These helpers intentionally do not call IBKR. They classify already-recorded
provider exits and row counts so Gate 1 wrappers do not mistake provider-status
readiness for direct historical-data proof.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
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
    known_good_preflight_ready: bool = True


_TIME_COLUMNS = ("timestamp", "time", "datetime", "date", "ts")


def read_exit_file(path: Path) -> int | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return None
    try:
        return int(text.splitlines()[-1].strip())
    except ValueError:
        return None


def count_provider_rows(path: Path) -> int:
    """Count normalized provider rows, accepting common IBKR time columns."""

    if not path.exists() or path.stat().st_size <= 0:
        return 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return 0
        time_column = next((column for column in _TIME_COLUMNS if column in reader.fieldnames), None)
        if time_column is None:
            return 0
        return sum(1 for row in reader if (row.get(time_column) or "").strip())


def _parse_label_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"expected LABEL=PATH, got {value!r}")
    label, path = value.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError(f"empty label in {value!r}")
    return label, Path(path).expanduser()


def classify_ibkr_ladder_artifacts(
    *,
    provider_status_exit_file: Path | None,
    fetch_exit_files: Mapping[str, Path],
    row_csvs: Mapping[str, Path],
    material_count: int,
    ranked_row_count: int,
    recent_blocked_ladders: int = 0,
    known_good_row_csvs: Mapping[str, Path] | None = None,
    require_known_good_preflight: bool = False,
) -> IbkrLadderVerdict:
    fetch_exits = {}
    for label, path in fetch_exit_files.items():
        exit_code = read_exit_file(path)
        fetch_exits[label] = exit_code if exit_code is not None else 999
    return classify_ibkr_ladder_state(
        provider_status_exit=(
            read_exit_file(provider_status_exit_file)
            if provider_status_exit_file is not None
            else None
        ),
        fetch_exits=fetch_exits,
        row_counts={label: count_provider_rows(path) for label, path in row_csvs.items()},
        material_count=material_count,
        ranked_row_count=ranked_row_count,
        recent_blocked_ladders=recent_blocked_ladders,
        known_good_row_counts={
            label: count_provider_rows(path)
            for label, path in (known_good_row_csvs or {}).items()
        },
        require_known_good_preflight=require_known_good_preflight,
    )


def classify_ibkr_ladder_state(
    *,
    provider_status_exit: int | None,
    fetch_exits: Mapping[str, int],
    row_counts: Mapping[str, int],
    material_count: int,
    ranked_row_count: int,
    recent_blocked_ladders: int = 0,
    known_good_row_counts: Mapping[str, int] | None = None,
    require_known_good_preflight: bool = False,
) -> IbkrLadderVerdict:
    """Classify whether an IBKR ladder has enough evidence for AQ.

    `provider-status --provider ibkr` only proves the configured provider path
    can be inspected. It does not prove `reqHistoricalData` returned rows for
    the target contract. Any AQ/material/rank stage needs real rows first.
    """

    known_good_rows = sum(max(int(value), 0) for value in (known_good_row_counts or {}).values())
    if require_known_good_preflight and known_good_rows <= 0:
        return IbkrLadderVerdict(
            decision="known_good_preflight_missing_no_rows",
            reason="fresh IBKR stock ladder requires a known-good stock/ETF historical preflight with nonzero rows.",
            provider_rows_ready=False,
            allow_material_build=False,
            allow_auto_quant=False,
            factor_verdict=False,
            cooldown_recommended=True,
            known_good_preflight_ready=False,
        )

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify recorded IBKR historical ladder artifacts before AQ admission."
    )
    parser.add_argument("--provider-status-exit-file", type=Path, default=None)
    parser.add_argument("--fetch-exit", action="append", default=[], type=_parse_label_path,
                        metavar="LABEL=PATH")
    parser.add_argument("--row-csv", action="append", default=[], type=_parse_label_path,
                        metavar="LABEL=PATH")
    parser.add_argument("--material-count", type=int, default=0)
    parser.add_argument("--ranked-row-count", type=int, default=0)
    parser.add_argument("--recent-blocked-ladders", type=int, default=0)
    parser.add_argument("--known-good-row-csv", action="append", default=[], type=_parse_label_path,
                        metavar="LABEL=PATH")
    parser.add_argument(
        "--require-known-good-preflight",
        action="store_true",
        help="require a nonzero-row known-good stock/ETF historical preflight before fresh stock ladders",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="exit 2 when recorded artifacts do not prove provider rows are ready",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    verdict = classify_ibkr_ladder_artifacts(
        provider_status_exit_file=args.provider_status_exit_file,
        fetch_exit_files=dict(args.fetch_exit),
        row_csvs=dict(args.row_csv),
        material_count=args.material_count,
        ranked_row_count=args.ranked_row_count,
        recent_blocked_ladders=args.recent_blocked_ladders,
        known_good_row_csvs=dict(args.known_good_row_csv),
        require_known_good_preflight=args.require_known_good_preflight,
    )
    print(json.dumps(asdict(verdict), indent=2, sort_keys=True))
    if args.fail_on_blocked and not verdict.provider_rows_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
