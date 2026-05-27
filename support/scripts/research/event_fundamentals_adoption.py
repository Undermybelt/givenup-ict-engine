from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import market_data_resolver as resolver


DEFAULT_PROFILE = "thrill3r_nq_event_fundamentals_v1"
DEFAULT_STATE_DIR = "/tmp/ict-engine-event-fundamentals-adoption"
BUNDLE_FILENAME = "event_fundamentals_adoption_bundle.json"
SHELL_FILENAME = "suggested_commands.sh"
ALLOWED_ARTIFACT_KINDS = ("earnings", "dividends", "macro", "fundamentals")
ARTIFACT_KIND_TO_CONTRACT_ID = {
    "earnings": "earnings_event_series",
    "dividends": "dividend_event_series",
    "macro": "macro_event_series",
    "fundamentals": "lagged_fundamentals_sidecar",
}


def shell_quote(value: str) -> str:
    escaped = value.replace("'", "'\"'\"'")
    return f"'{escaped}'"


def parse_artifact_inputs(specs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in specs:
        key, sep, raw_path = spec.partition("=")
        if not sep or not key.strip() or not raw_path.strip():
            raise ValueError(
                f"bad --artifact value {spec!r}; expected '<kind>=<path>'"
            )
        kind = key.strip().lower()
        if kind not in ALLOWED_ARTIFACT_KINDS:
            raise ValueError(
                f"unsupported artifact kind {kind!r}; supported: {sorted(ALLOWED_ARTIFACT_KINDS)}"
            )
        mapping[kind] = str(Path(raw_path.strip()).expanduser().resolve())
    return mapping


def _artifact_entries(mapping: dict[str, str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for kind, path in sorted(mapping.items()):
        resolved = Path(path)
        entries.append(
            {
                "artifact_kind": kind,
                "path": str(resolved),
                "path_exists": resolved.exists(),
            }
        )
    return entries


def build_artifact_readiness(
    artifact_entries: list[dict[str, Any]],
    dataset_contracts: list[dict[str, Any]],
) -> dict[str, Any]:
    relevant_contract_ids = [
        contract["dataset_id"]
        for contract in dataset_contracts
        if contract["dataset_id"] in ARTIFACT_KIND_TO_CONTRACT_ID.values()
    ]
    covered_contract_ids = sorted(
        {
            ARTIFACT_KIND_TO_CONTRACT_ID[entry["artifact_kind"]]
            for entry in artifact_entries
            if entry["artifact_kind"] in ARTIFACT_KIND_TO_CONTRACT_ID
        }
    )
    missing_contract_ids = [
        contract_id
        for contract_id in relevant_contract_ids
        if contract_id not in covered_contract_ids
    ]
    return {
        "profile_contract_ready": not missing_contract_ids,
        "covered_contract_count": len(covered_contract_ids),
        "covered_contract_ids": covered_contract_ids,
        "missing_contract_ids": missing_contract_ids,
    }


def build_usage_warnings(artifact_kinds: list[str]) -> list[str]:
    warnings: list[str] = []
    if "fundamentals" in artifact_kinds:
        warnings.append("Lag fundamentals by effective date before backtest or live reuse.")
    if "earnings" in artifact_kinds:
        warnings.append("Treat earnings timestamps as scheduled-event context until confirmed effective in your replay or live clock.")
    if "dividends" in artifact_kinds:
        warnings.append("Use ex-dividend timestamps rather than announcement time when deriving trading context.")
    if "macro" in artifact_kinds:
        warnings.append("Keep macro events aligned to scheduled release timestamps and explicit importance tiers.")
    return warnings


def build_downstream_handoff(
    artifact_kinds: list[str],
    artifact_readiness: dict[str, Any],
) -> dict[str, Any]:
    missing_artifact_kinds = [
        kind
        for kind in ALLOWED_ARTIFACT_KINDS
        if ARTIFACT_KIND_TO_CONTRACT_ID[kind] in artifact_readiness["missing_contract_ids"]
    ]
    readiness = (
        "profile_contract_ready"
        if artifact_readiness["profile_contract_ready"]
        else "partial_sidecar_pack"
    )
    return {
        "readiness": readiness,
        "missing_artifact_kinds": missing_artifact_kinds,
        "allowed_use_modes": [
            "research_context",
            "factor_research_opt_in",
            "auto_quant_handoff_context",
        ],
    }


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


def build_analyze_command(
    symbol: str,
    state_dir: str,
) -> str:
    return (
        f"cargo run --quiet -- analyze --symbol {symbol} --demo "
        f"--state-dir {shell_quote(state_dir)} --human"
    )


def build_factor_research_command(
    symbol: str,
    objective: str,
    state_dir: str,
    profile_selector: str | None,
) -> str:
    parts = [
        "cargo run --quiet -- factor-research",
        f"--symbol {symbol}",
        f"--objective {objective}",
        "--backend auto-quant",
        "--auto-quant-profile synthetic_ohlcv",
        f"--state-dir {shell_quote(state_dir)}",
        "--human",
    ]
    if profile_selector:
        parts.insert(4, f"--profile {profile_selector}")
    return " ".join(parts)


def build_review_command(bundle_artifact_name: str) -> str:
    return f"python3 -m json.tool {shell_quote(bundle_artifact_name)}"


def build_command_set(
    workflow_symbol: str,
    objective: str,
    state_dir: str,
    profile_selector: str | None,
    bundle_artifact_name: str,
) -> dict[str, str]:
    return {
        "review_sidecars": build_review_command(bundle_artifact_name),
        "workflow_status": build_workflow_status_command(
            workflow_symbol, state_dir, profile_selector
        ),
        "analyze": build_analyze_command(workflow_symbol, state_dir),
        "factor_research": build_factor_research_command(
            workflow_symbol,
            objective,
            state_dir,
            profile_selector,
        ),
        "auto_quant_adoption_review": (
            f"cargo run --quiet -- auto-quant-adoption-review --symbol {workflow_symbol} "
            f"--state-dir {shell_quote(state_dir)}"
        ),
    }


def render_choice_shell_lines(command_choices: list[dict[str, Any]]) -> list[str]:
    lines = ["#!/usr/bin/env bash", ""]
    command_order = [
        "review_sidecars",
        "workflow_status",
        "analyze",
        "factor_research",
        "auto_quant_adoption_review",
    ]
    for choice in command_choices:
        header = f"# {choice['choice_id']}"
        if choice.get("recommended"):
            header += " (recommended)"
        lines.append(header)
        lines.append(f"# {choice['summary']}")
        for key in command_order:
            lines.append(f"# {key}")
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
    artifact_inputs: dict[str, str],
    bundle_artifact_name: str = BUNDLE_FILENAME,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    resolution = resolver.build_resolution_bundle(
        repo_root=repo_root,
        market_selector=market_selector,
        profile_selector=profile_selector,
    )
    selected_profile = resolution["symbol_resolution"]["selected_profile"] or {}
    command_profile_selector = selected_profile.get("selector") or profile_selector
    artifact_entries = _artifact_entries(artifact_inputs)
    artifact_kinds = [entry["artifact_kind"] for entry in artifact_entries]
    dataset_contracts = resolution["data_catalog"]["datasets"]
    artifact_readiness = build_artifact_readiness(artifact_entries, dataset_contracts)
    usage_warnings = build_usage_warnings(artifact_kinds)
    downstream_handoff = build_downstream_handoff(artifact_kinds, artifact_readiness)
    keep_zero_config_commands = build_command_set(
        workflow_symbol,
        objective,
        state_dir,
        None,
        bundle_artifact_name,
    )
    opt_in_commands = build_command_set(
        workflow_symbol,
        objective,
        state_dir,
        command_profile_selector,
        bundle_artifact_name,
    )
    selected_profile_name = selected_profile.get("display_name") or profile_selector
    command_choices = [
        {
            "choice_id": "keep_zero_config",
            "label": "Keep zero-config defaults",
            "recommended": True,
            "profile_selector": None,
            "summary": "Stay on the generic public-default lane and treat the sidecar pack as optional context only.",
            "suggested_commands": keep_zero_config_commands,
        },
        {
            "choice_id": "reuse_saved_profile",
            "label": "Reuse opt-in sidecar profile",
            "recommended": False,
            "profile_selector": command_profile_selector,
            "summary": f"Reuse the optional profile {selected_profile_name} on commands that support --profile while keeping the sidecar pack explicit.",
            "suggested_commands": opt_in_commands,
        },
    ]
    return {
        "schema_version": "event-fundamentals-adoption/v1",
        "default_choice_id": "keep_zero_config",
        "market_key": resolution["symbol_resolution"]["market_key"],
        "workflow_symbol": workflow_symbol,
        "objective": objective,
        "state_dir": state_dir,
        "selected_profile": selected_profile,
        "artifact_summary": {
            "provided_artifact_count": len(artifact_entries),
            "provided_artifact_kinds": [entry["artifact_kind"] for entry in artifact_entries],
        },
        "artifact_readiness": artifact_readiness,
        "usage_warnings": usage_warnings,
        "downstream_handoff": downstream_handoff,
        "artifacts": artifact_entries,
        "data_catalog_summary": resolution["data_catalog"]["summary"],
        "dataset_contracts": dataset_contracts,
        "command_choices": command_choices,
        "suggested_commands": keep_zero_config_commands,
        "opt_in_suggested_commands": opt_in_commands,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a token-friendly adoption bundle for optional event and lagged-fundamentals sidecars."
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
        help="Workflow symbol label carried into the suggested commands.",
    )
    parser.add_argument(
        "--objective",
        default="regime_conditioned_profitability",
        help="Objective label carried into factor-research suggestions.",
    )
    parser.add_argument(
        "--state-dir",
        default=DEFAULT_STATE_DIR,
        help="Explicit state dir used in suggested commands.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Explicit sidecar input in the form kind=path; supported kinds: earnings, dividends, macro, fundamentals.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the bundle and suggested command shell file will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_inputs = parse_artifact_inputs(args.artifact)
    bundle = build_adoption_bundle(
        repo_root=args.repo_root,
        market_selector=args.market,
        profile_selector=args.profile,
        workflow_symbol=args.symbol,
        objective=args.objective,
        state_dir=args.state_dir,
        artifact_inputs=artifact_inputs,
        bundle_artifact_name=BUNDLE_FILENAME,
    )
    bundle_path = output_dir / BUNDLE_FILENAME
    _write_json(bundle_path, bundle)
    shell_path = output_dir / SHELL_FILENAME
    shell_path.write_text(
        "\n".join(render_choice_shell_lines(bundle["command_choices"])) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output_dir": str(output_dir),
                "market_key": bundle["market_key"],
                "artifact_count": bundle["artifact_summary"]["provided_artifact_count"],
                "artifacts": [BUNDLE_FILENAME, SHELL_FILENAME],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
