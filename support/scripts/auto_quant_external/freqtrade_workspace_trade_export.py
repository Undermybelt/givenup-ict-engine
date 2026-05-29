from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import freqtrade_backtest_trade_export as payload_export


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _discover_strategy_name(workspace_dir: Path) -> str:
    strategies_dir = workspace_dir / "user_data" / "strategies_external"
    names = sorted(path.stem for path in strategies_dir.glob("*.py") if not path.stem.startswith("_"))
    if len(names) != 1:
        raise ValueError(
            f"workspace strategy discovery requires exactly one strategy file, found {len(names)} in {strategies_dir}"
        )
    return names[0]


def export_workspace_trades(
    *,
    workspace_dir: Path,
    output_jsonl: Path,
    strategy_mutation_id: str,
    auto_quant_run_id: str,
    symbol: str,
    provider: str,
    instrument: str,
    timeframe: str,
    branch_path: str,
    strategy_name: str | None = None,
) -> dict[str, Any]:
    workspace = workspace_dir.resolve()
    run_tomac = _load_module(workspace / "run_tomac.py")
    resolved_strategy = strategy_name or _discover_strategy_name(workspace)
    payload = run_tomac.run_backtest(resolved_strategy)
    summary = payload_export.export_payload_trades(
        payload=payload,
        strategy_name=resolved_strategy,
        output_jsonl=output_jsonl,
        strategy_mutation_id=strategy_mutation_id,
        auto_quant_run_id=auto_quant_run_id,
        symbol=symbol,
        provider=provider,
        instrument=instrument,
        timeframe=timeframe,
        branch_path=branch_path,
    )
    summary["workspace_dir"] = str(workspace)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a TOMAC/Freqtrade workspace and export normalized trades.")
    parser.add_argument("--workspace-dir", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--strategy-mutation-id", required=True)
    parser.add_argument("--auto-quant-run-id", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--branch-path", required=True)
    parser.add_argument("--strategy-name")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = export_workspace_trades(
        workspace_dir=Path(args.workspace_dir),
        output_jsonl=Path(args.output_jsonl),
        strategy_mutation_id=args.strategy_mutation_id,
        auto_quant_run_id=args.auto_quant_run_id,
        symbol=args.symbol,
        provider=args.provider,
        instrument=args.instrument,
        timeframe=args.timeframe,
        branch_path=args.branch_path,
        strategy_name=args.strategy_name,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
