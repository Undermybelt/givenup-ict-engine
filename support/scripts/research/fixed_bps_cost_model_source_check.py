#!/usr/bin/env python3
"""Fail source files that hard-code fixed-bps transaction-cost models.

This checker targets cost/fee/friction bps ladders such as ``cost_bps``,
``net5bps``, ``survives_2bps_per_side``, and ``for bps in (0, 1, 2, 5)``.
It intentionally allows signal thresholds such as ``slope_bps`` or
``reclaim_bps_min`` because those are not transaction-cost models.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_SCAN_ROOTS = (
    Path("support/scripts/research"),
    Path("support/docs/experiments/actionable-regime-confidence/scripts"),
)
EXCLUDED_PARTS = frozenset(("__pycache__", "runs", "paper2code"))
EXCLUDED_NAMES = frozenset((
    "fixed_bps_cost_model_source_check.py",
    # Existing legacy/readback helpers parse old bps artifacts; new tools must
    # avoid fixed-bps cost authority without relying on filename skips.
    "factor_lifecycle_migration_readback.py",
    "factor_signal_diagnostics.py",
    "futures_real_cost_rescue_audit.py",
    "labeling_triple_barrier.py",
    "mim_cost_window_feedback_builder.py",
    "real_trade_feedback_labels.py",
    "regime_root_metrics_contract_check.py",
    "regime_root_survivor_blocker_report.py",
    "simulated_feedback_admission_guard.py",
    "tomac_tod_balanced_trade_label_sidecar.py",
))
FIXED_BPS_ARG_NAMES = frozenset((
    "cost_bps",
    "cost_bps_side",
    "fee_bps",
    "fee_bps_side",
    "bps_per_side",
    "LEGACY_STRESS_BPS_PER_SIDE",
))
FIXED_BPS_OPTION_FRAGMENTS = (
    "cost-bps",
    "fee-bps",
    "bps-per-side",
    "cost_bps",
    "fee_bps",
    "bps_per_side",
)
COST_FIELD_TOKENS = frozenset((
    "net5bps",
    "net_5bps",
    "net_after_1bps",
    "net_after_2bps",
    "net_after_5bps",
    "survives_1bps",
    "survives_2bps",
    "survives_5bps",
    "survivors_1bps",
    "survivors_2bps",
    "survivors_5bps",
    "positive_1bps",
    "positive_2bps",
    "positive_5bps",
    "top_by_1bps",
    "top_by_2bps",
    "top_by_5bps",
    "best_1bps",
    "best_2bps",
    "best_5bps",
    "pf_1bps",
    "pf_2bps",
    "pf_5bps",
    "profit_factor_1bps",
    "profit_factor_2bps",
    "profit_factor_5bps",
    "trades_1bps",
    "trades_2bps",
    "trades_5bps",
    "legacy_stress",
    "configured_fee_5bps",
    "5bps_per_side",
    "2bps_per_side",
    "1bps_per_side",
    "0bps_per_side",
))
COST_LITERAL_KEYS = frozenset(("fee", "cost", "commission", "friction"))
FIXED_FRACTION_LITERALS = frozenset((0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01))


@dataclass(frozen=True)
class Violation:
    violation: str
    line: int
    column: int
    snippet: str
    detail: str

    def as_dict(self) -> dict:
        return {
            "violation": self.violation,
            "line": self.line,
            "column": self.column,
            "snippet": self.snippet,
            "detail": self.detail,
        }


def expression_text(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment:
        return " ".join(segment.strip().split())
    return ast.dump(node, annotate_fields=False, include_attributes=False)


def string_value(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def numeric_value(node: ast.AST | None) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = numeric_value(node.operand)
        if value is None:
            return None
        return value if isinstance(node.op, ast.UAdd) else -value
    return None


def is_numeric_literal(node: ast.AST | None) -> bool:
    return numeric_value(node) is not None


def is_docstring_node(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    if isinstance(parent, ast.Expr):
        grandparent = parents.get(parent)
        if isinstance(grandparent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            return bool(grandparent.body and grandparent.body[0] is parent)
    if isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return bool(parent.body and parent.body[0] is node)
    return False


def fixed_bps_name(
    name: str,
    *,
    relax_diagnostic_terms: bool = False,
) -> bool:
    if name in FIXED_BPS_ARG_NAMES:
        return True
    lowered = name.lower()
    if "diagnostic_stress" in lowered:
        return not relax_diagnostic_terms
    if "bps" in lowered and any(token in lowered for token in ("cost", "fee", "friction", "stress")):
        return True
    return False


def fixed_bps_field(
    text: str,
    *,
    relax_diagnostic_terms: bool = False,
) -> bool:
    lowered = text.lower()
    if lowered == "cost_stress_role":
        return False
    if relax_diagnostic_terms and "diagnostic_stress" in lowered:
        return False
    return any(token in lowered for token in COST_FIELD_TOKENS)


def fixed_cost_option(text: str, *, relax_diagnostic_terms: bool = False) -> bool:
    lowered = text.lower().replace("_", "-")
    if relax_diagnostic_terms and "diagnostic-stress" in lowered:
        return False
    return any(fragment.replace("_", "-") in lowered for fragment in FIXED_BPS_OPTION_FRAGMENTS)


def node_line(node: ast.AST) -> tuple[int, int]:
    return int(getattr(node, "lineno", 0) or 0), int(getattr(node, "col_offset", 0) or 0)


def add_hit(
    hits: list[Violation],
    source: str,
    node: ast.AST,
    violation: str,
    detail: str,
) -> None:
    line, col = node_line(node)
    hits.append(Violation(violation, line, col, expression_text(source, node), detail))


def assignment_targets(node: ast.Assign | ast.AnnAssign) -> list[ast.AST]:
    if isinstance(node, ast.Assign):
        return list(node.targets)
    return [node.target]


def target_names(target: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(target, ast.Name):
        names.append(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            names.extend(target_names(elt))
    elif isinstance(target, ast.Attribute):
        names.append(target.attr)
    return names


def contains_fixed_bps_reference(
    node: ast.AST | None,
    *,
    relax_diagnostic_terms: bool = False,
) -> bool:
    if node is None:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and fixed_bps_name(
            child.id,
            relax_diagnostic_terms=relax_diagnostic_terms,
        ):
            return True
        if isinstance(child, ast.Attribute) and fixed_bps_name(
            child.attr,
            relax_diagnostic_terms=relax_diagnostic_terms,
        ):
            return True
    return False


def contains_bps_formula(
    node: ast.AST,
    *,
    relax_diagnostic_terms: bool = False,
) -> bool:
    saw_fixed_bps_name = False
    saw_plain_bps_name = False
    saw_cost_scale = False
    saw_cost_literal = False
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if fixed_bps_name(
                child.id,
                relax_diagnostic_terms=relax_diagnostic_terms,
            ):
                saw_fixed_bps_name = True
            elif child.id == "bps":
                saw_plain_bps_name = True
        value = numeric_value(child)
        if value is not None and value in {0.02, 0.0002, 0.0001, 1e-4, 10000.0, 10_000.0}:
            saw_cost_scale = True
        if value is not None and value in {0.02, 0.0002, 0.0001, 1e-4}:
            saw_cost_literal = True
    return (saw_fixed_bps_name and saw_cost_scale) or (saw_plain_bps_name and saw_cost_literal)


def assignment_is_readback_only(target_name: str, value: ast.AST | None) -> bool:
    lowered = target_name.lower()
    if any(token in lowered for token in ("key", "keys", "field", "fields", "token", "tokens")):
        return True
    if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
        return all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in value.elts)
    return False


def subscript_key_text(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Subscript):
        return None
    return string_value(node.slice)


def target_cost_field_keys(target: ast.AST) -> list[str]:
    keys: list[str] = []
    if isinstance(target, ast.Subscript):
        key = subscript_key_text(target)
        if key is not None:
            keys.append(key)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            keys.extend(target_cost_field_keys(elt))
    return keys


def fixed_bps_field_assignment_is_readback_only(source: str, target: ast.AST, value: ast.AST | None) -> bool:
    return False


def source_allows_diagnostic_stress(source: str) -> bool:
    return "diagnostic_stress_not_commission_or_promotion_authority" in source


def iter_numeric_sequence(node: ast.AST) -> list[float] | None:
    if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return None
    values: list[float] = []
    for elt in node.elts:
        value = numeric_value(elt)
        if value is None:
            return None
        values.append(value)
    return values


def is_fixed_bps_ladder(loop: ast.For) -> bool:
    if not isinstance(loop.target, ast.Name) or loop.target.id != "bps":
        return False
    values = iter_numeric_sequence(loop.iter)
    if values is None:
        return False
    return len(values) >= 2 and all(value in {0.0, 1.0, 2.0, 5.0, 10.0} for value in values)


def is_argparse_add_argument(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"


def check_tree(source: str, tree: ast.AST) -> list[Violation]:
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    relax_diagnostic_terms = source_allows_diagnostic_stress(source)
    hits: list[Violation] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in [*node.args.args, *node.args.kwonlyargs]:
                if fixed_bps_name(
                    arg.arg,
                    relax_diagnostic_terms=relax_diagnostic_terms,
                ):
                    add_hit(hits, source, arg, "fixed_bps_cost_argument", "function argument names a fixed-bps fee/cost model")
            defaults = list(node.args.defaults) + list(node.args.kw_defaults)
            default_args = [*node.args.args[-len(node.args.defaults):], *node.args.kwonlyargs] if node.args.defaults else [*node.args.kwonlyargs]
            for arg, default in zip(default_args, defaults):
                if default is not None and fixed_bps_name(
                    arg.arg,
                    relax_diagnostic_terms=relax_diagnostic_terms,
                ) and is_numeric_literal(default):
                    add_hit(hits, source, default, "fixed_bps_cost_argument_default", "fixed-bps fee/cost default")

        if isinstance(node, ast.Call) and is_argparse_add_argument(node):
            option_strings = [string_value(arg) for arg in node.args]
            if any(
                option and fixed_cost_option(
                    option,
                    relax_diagnostic_terms=relax_diagnostic_terms,
                )
                for option in option_strings
            ):
                add_hit(hits, source, node, "fixed_bps_cost_argument", "CLI exposes fixed-bps fee/cost option")
            for keyword in node.keywords:
                if keyword.arg == "default" and is_numeric_literal(keyword.value):
                    if any(
                        option and fixed_cost_option(
                            option,
                            relax_diagnostic_terms=relax_diagnostic_terms,
                        )
                        for option in option_strings
                    ):
                        add_hit(hits, source, keyword.value, "fixed_bps_cost_argument_default", "CLI fixed-bps fee/cost option has numeric default")

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value if isinstance(node, ast.AnnAssign) else node.value
            for target in assignment_targets(node):
                for key in target_cost_field_keys(target):
                    if fixed_bps_field(
                        key,
                        relax_diagnostic_terms=relax_diagnostic_terms,
                    ) and not fixed_bps_field_assignment_is_readback_only(source, target, value):
                        add_hit(hits, source, target, "fixed_bps_cost_field", "assignment writes a fixed-bps fee/cost field")
                for name in target_names(target):
                    lowered = name.lower()
                    if fixed_bps_name(
                        name,
                        relax_diagnostic_terms=relax_diagnostic_terms,
                    ):
                        if not assignment_is_readback_only(name, value):
                            add_hit(hits, source, target, "fixed_bps_cost_assignment", "variable names a fixed-bps fee/cost model")
                    if lowered in {"fee", "cost", "round_trip_cost", "round_turn_cost", "round_trip_fee"}:
                        value_num = numeric_value(value)
                        if value_num in FIXED_FRACTION_LITERALS:
                            add_hit(hits, source, node, "fixed_fraction_fee_literal", "fee/cost literal looks like hard-coded bps in return space")
                    if contains_fixed_bps_reference(
                        value,
                        relax_diagnostic_terms=relax_diagnostic_terms,
                    ) and not assignment_is_readback_only(name, value):
                        add_hit(hits, source, node, "fixed_bps_cost_reference", "assignment derives from fixed-bps fee/cost reference")

        if isinstance(node, ast.For) and is_fixed_bps_ladder(node):
            add_hit(hits, source, node, "fixed_bps_cost_ladder", "fixed bps ladder is not a verified instrument cost model")

        if isinstance(node, ast.BinOp) and contains_bps_formula(
            node,
            relax_diagnostic_terms=relax_diagnostic_terms,
        ):
            add_hit(hits, source, node, "fixed_bps_cost_formula", "formula subtracts a variable bps ladder in return/percent space")

        if isinstance(node, ast.Dict):
            for key_node, value_node in zip(node.keys, node.values):
                key = string_value(key_node)
                if key is not None and fixed_bps_field(
                    key,
                    relax_diagnostic_terms=relax_diagnostic_terms,
                ):
                    add_hit(hits, source, key_node, "fixed_bps_cost_field", "dict emits a fixed-bps fee/cost field")
                if key is not None and key.lower() in COST_LITERAL_KEYS:
                    value_num = numeric_value(value_node)
                    if value_num in FIXED_FRACTION_LITERALS:
                        add_hit(hits, source, value_node, "fixed_fraction_fee_literal", "dict hard-codes fee/cost as a bps-like fraction")

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if is_docstring_node(node, parents):
                continue

    return dedupe_hits(hits)


def dedupe_hits(hits: Iterable[Violation]) -> list[Violation]:
    seen: set[tuple[str, int, int, str]] = set()
    result: list[Violation] = []
    for hit in hits:
        key = (hit.violation, hit.line, hit.column, hit.snippet)
        if key in seen:
            continue
        seen.add(key)
        result.append(hit)
    return result


def check_source_file(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {
            "ok": False,
            "decision": "python_parse_error",
            "file": str(path),
            "violations": [
                {
                    "violation": "python_parse_error",
                    "line": exc.lineno or 0,
                    "column": exc.offset or 0,
                    "snippet": exc.text.strip() if exc.text else "",
                    "detail": str(exc),
                }
            ],
        }
    hits = check_tree(source, tree)
    return {
        "ok": not hits,
        "decision": "pass" if not hits else "fixed_bps_cost_model_source_violation",
        "file": str(path),
        "violations": [hit.as_dict() for hit in hits],
    }


def should_skip(path: Path, *, include_tests: bool = False) -> bool:
    if path.name in EXCLUDED_NAMES:
        return True
    if path.suffix != ".py":
        return True
    if EXCLUDED_PARTS.intersection(path.parts):
        return True
    if not include_tests and (path.name.startswith("test_") or "tests" in path.parts):
        return True
    return False


def discover_paths(roots: Sequence[Path], *, include_tests: bool = False) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if root.is_file():
            if not should_skip(root, include_tests=include_tests):
                paths.append(root)
            continue
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if not should_skip(path, include_tests=include_tests):
                paths.append(path)
    return sorted(set(paths))


def git_tracked_paths(repo_root: Path, paths: Sequence[Path], *, include_tests: bool = False) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "--", *[str(path) for path in paths]],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git ls-files failed")
    tracked: list[Path] = []
    for line in proc.stdout.splitlines():
        path = repo_root / line
        if not should_skip(path, include_tests=include_tests):
            tracked.append(path)
    return sorted(set(tracked))


def check_paths(paths: Sequence[Path]) -> dict:
    file_reports = [check_source_file(path) for path in paths]
    violations = []
    for report in file_reports:
        for hit in report["violations"]:
            item = dict(hit)
            item["file"] = report["file"]
            violations.append(item)
    return {
        "ok": not violations,
        "decision": "pass" if not violations else "fixed_bps_cost_model_source_violation",
        "checked_files": len(file_reports),
        "violating_files": sum(1 for report in file_reports if not report["ok"]),
        "violation_count": len(violations),
        "violations": violations,
        "file_reports": file_reports,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to scan")
    parser.add_argument("--tracked", action="store_true", help="Scan only git-tracked files under the paths")
    parser.add_argument("--include-tests", action="store_true", help="Include test files in the scan")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON without per-file pass reports")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    repo_root = Path.cwd()
    roots = args.paths or list(DEFAULT_SCAN_ROOTS)
    if args.tracked:
        paths = git_tracked_paths(repo_root, roots, include_tests=args.include_tests)
    else:
        paths = discover_paths(roots, include_tests=args.include_tests)
    report = check_paths(paths)
    if args.compact:
        payload = {key: value for key, value in report.items() if key != "file_reports"}
    else:
        payload = report
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
