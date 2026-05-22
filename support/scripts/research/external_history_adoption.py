from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import market_data_resolver as resolver


DEFAULT_PROFILE = "thrill3r_nq_external_history_v1"
DEFAULT_STATE_DIR = "/tmp/ict-engine-external-history-adoption"
TIMEFRAME_PRIORITY = {
    "1m": 1,
    "5m": 2,
    "15m": 3,
    "30m": 4,
    "1h": 5,
    "4h": 6,
    "1d": 7,
}


def parse_timeframe_inputs(specs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in specs:
        key, sep, raw_path = spec.partition("=")
        if not sep or not key.strip() or not raw_path.strip():
            raise ValueError(
                f"bad --input value {spec!r}; expected '<timeframe>=<normalized-json>'"
            )
        mapping[key.strip()] = str(Path(raw_path.strip()).expanduser().resolve())
    return mapping


def rank_timeframes(mapping: dict[str, str]) -> list[tuple[str, str]]:
    return sorted(
        mapping.items(),
        key=lambda item: TIMEFRAME_PRIORITY.get(item[0], 999),
    )


def choose_primary_timeframe(mapping: dict[str, str]) -> tuple[str, str]:
    ranked = rank_timeframes(mapping)
    if not ranked:
        raise ValueError("at least one normalized timeframe input is required")
    preferred = next((item for item in ranked if item[0] == "1h"), None)
    return preferred or ranked[-1]


def build_analyze_command(symbol: str, state_dir: str, mapping: dict[str, str]) -> str:
    ranked = rank_timeframes(mapping)
    if not ranked:
        raise ValueError("analyze command requires at least one normalized input")
    if {"1d", "4h", "1h"}.issubset(mapping):
        htf = mapping["1d"]
        mtf = mapping["4h"]
        ltf = mapping["1h"]
        note = ""
    else:
        _, fallback = choose_primary_timeframe(mapping)
        htf = mtf = ltf = fallback
        note = " # single-timeframe smoke fallback"
    return (
        f"cargo run --quiet -- analyze --symbol {symbol} "
        f"--data-htf {shell_quote(htf)} --data-mtf {shell_quote(mtf)} "
        f"--data-ltf {shell_quote(ltf)} --state-dir {shell_quote(state_dir)} --human{note}"
    )


def build_workflow_status_command(
    symbol: str,
    state_dir: str,
    profile_selector: str | None,
) -> str:
    parts = [
        "cargo run --quiet -- workflow-status",
        f"--symbol {symbol}",
        f"--state-dir {shell_quote(state_dir)}",
    ]
    if profile_selector:
        parts.append(f"--profile {profile_selector}")
    parts.append("--agent")
    return " ".join(parts)


def build_factor_research_command(
    symbol: str,
    state_dir: str,
    profile_selector: str | None,
    mapping: dict[str, str],
    objective: str,
) -> str:
    primary_tf, primary_path = choose_primary_timeframe(mapping)
    parts = [
        "cargo run --quiet -- factor-research",
        f"--symbol {symbol}",
        f"--data {shell_quote(primary_path)}",
        f"--objective {objective}",
        "--backend auto-quant",
        "--auto-quant-profile synthetic_ohlcv",
        f"--state-dir {shell_quote(state_dir)}",
        "--human",
    ]
    if profile_selector:
        parts.insert(6, f"--profile {profile_selector}")
    for timeframe, path in rank_timeframes(mapping):
        parts.append(f"--data-{timeframe} {shell_quote(path)}")
    parts.append(f"# primary_timeframe={primary_tf}")
    return " ".join(parts)


def build_command_set(
    workflow_symbol: str,
    objective: str,
    state_dir: str,
    timeframe_inputs: dict[str, str],
    profile_selector: str | None,
) -> dict[str, str]:
    return {
        "workflow_status": build_workflow_status_command(
            workflow_symbol, state_dir, profile_selector
        ),
        "analyze": build_analyze_command(workflow_symbol, state_dir, timeframe_inputs),
        "factor_research": build_factor_research_command(
            workflow_symbol,
            state_dir,
            profile_selector,
            timeframe_inputs,
            objective,
        ),
        "auto_quant_prepare": (
            f"cargo run --quiet -- auto-quant-prepare --state-dir {shell_quote(state_dir)}"
        ),
        "auto_quant_adoption_review": (
            f"cargo run --quiet -- auto-quant-adoption-review --symbol {workflow_symbol} "
            f"--state-dir {shell_quote(state_dir)}"
        ),
    }


def render_choice_shell_lines(command_choices: list[dict[str, Any]]) -> list[str]:
    lines = ["#!/usr/bin/env bash", ""]
    command_order = [
        "workflow_status",
        "analyze",
        "factor_research",
        "auto_quant_prepare",
        "auto_quant_adoption_review",
    ]
    for choice in command_choices:
        header = f"# {choice['choice_id']}"
        if choice.get("recommended"):
            header += " (recommended)"
        lines.append(header)
        lines.append(f"# {choice['summary']}")
        for key in command_order:
            lines.append(choice["suggested_commands"][key])
        lines.append("")
    return lines


def build_adoption_bundle(
    repo_root: Path | str,
    market_selector: str,
    profile_selector: str,
    workflow_symbol: str,
    objective: str,
    state_dir: str,
    timeframe_inputs: dict[str, str],
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    resolution = resolver.build_resolution_bundle(
        repo_root=repo_root,
        market_selector=market_selector,
        profile_selector=profile_selector,
        timeframes=list(timeframe_inputs),
    )
    selected_profile = resolution["symbol_resolution"]["selected_profile"] or {}
    command_profile_selector = selected_profile.get("selector") or profile_selector
    primary_tf, primary_path = choose_primary_timeframe(timeframe_inputs)
    keep_zero_config_commands = build_command_set(
        workflow_symbol,
        objective,
        state_dir,
        timeframe_inputs,
        None,
    )
    opt_in_commands = build_command_set(
        workflow_symbol,
        objective,
        state_dir,
        timeframe_inputs,
        command_profile_selector,
    )
    selected_profile_name = selected_profile.get("display_name") or profile_selector
    command_choices = [
        {
            "choice_id": "keep_zero_config",
            "label": "Keep zero-config defaults",
            "recommended": True,
            "profile_selector": None,
            "summary": "Stay on the generic public-default lane and use the normalized files only for this run.",
            "suggested_commands": keep_zero_config_commands,
        },
        {
            "choice_id": "reuse_saved_profile",
            "label": "Reuse opt-in profile",
            "recommended": False,
            "profile_selector": command_profile_selector,
            "summary": f"Reuse the optional profile {selected_profile_name} on commands that support --profile.",
            "suggested_commands": opt_in_commands,
        },
    ]
    return {
        "schema_version": "external-history-adoption/v2",
        "default_choice_id": "keep_zero_config",
        "market_key": resolution["symbol_resolution"]["market_key"],
        "workflow_symbol": workflow_symbol,
        "objective": objective,
        "state_dir": state_dir,
        "selection_mode": resolution["normalized_dataset_summary"]["selection_mode"],
        "selected_profile": selected_profile,
        "primary_input": {
            "timeframe": primary_tf,
            "path": primary_path,
        },
        "normalized_inputs": [
            {"timeframe": timeframe, "path": path}
            for timeframe, path in rank_timeframes(timeframe_inputs)
        ],
        "data_catalog_summary": resolution["data_catalog"]["summary"],
        "dataset_contracts": resolution["data_catalog"]["datasets"],
        "command_choices": command_choices,
        "suggested_commands": keep_zero_config_commands,
        "opt_in_suggested_commands": opt_in_commands,
    }


def shell_quote(value: str) -> str:
    escaped = value.replace("'", "'\"'\"'")
    return f"'{escaped}'"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a token-friendly adoption bundle for an opt-in external history lane."
    )
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--market", required=True, help="Market key or alias, for example NQ.")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help="Opt-in provider profile selector to advertise in the bundle.",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Workflow symbol to use for analyze/factor-research commands.",
    )
    parser.add_argument(
        "--objective",
        default="regime_conditioned_profitability",
        help="Factor-research objective to stamp into suggested commands.",
    )
    parser.add_argument(
        "--state-dir",
        default=DEFAULT_STATE_DIR,
        help="Target state dir for the suggested commands.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Repeat '<timeframe>=<normalized-json>' for each normalized input.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the adoption bundle and command file will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timeframe_inputs = parse_timeframe_inputs(args.input)
    bundle = build_adoption_bundle(
        repo_root=args.repo_root,
        market_selector=args.market,
        profile_selector=args.profile,
        workflow_symbol=args.symbol,
        objective=args.objective,
        state_dir=args.state_dir,
        timeframe_inputs=timeframe_inputs,
    )
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "external_history_adoption_bundle.json"
    _write_json(bundle_path, bundle)
    commands_path = output_dir / "suggested_commands.sh"
    commands_path.write_text(
        "\n".join(render_choice_shell_lines(bundle["command_choices"])),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output_dir": str(output_dir),
                "market_key": bundle["market_key"],
                "profile_id": bundle["selected_profile"].get("profile_id"),
                "primary_input": bundle["primary_input"],
                "artifacts": [
                    "external_history_adoption_bundle.json",
                    "suggested_commands.sh",
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
