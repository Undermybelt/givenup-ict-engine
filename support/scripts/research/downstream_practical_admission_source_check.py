#!/usr/bin/env python3
"""Scan downstream wrappers for unsafe practical-admission flag assignments."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


PRACTICAL_KEYS = frozenset(("promotion_allowed", "trade_usable", "update_goal"))
LEARNING_KEYS = frozenset((
    "learning_admission",
    "learning_admission_status",
    "learning_allowed",
))
HELPER_NAME = "practical_admission_flags"
HELPER_RESULT_NAMES = frozenset(("practical", "practical_flags", "admission_flags"))
BRANCH_ADMISSION_NAMES = frozenset(("admitted", "branch_local_admitted", "pass_exec", "pass_execution"))
DOWNSTREAM_ADMISSION_NAMES = frozenset(("downstream", "downstream_allowed"))
PDA_HARD_GATE_PATTERNS = (
    " and pda",
    "pda and ",
    "pda is True",
    "pda_hybrid_alignment is True",
    "pda_hybrid_alignment_true",
)
TWO_BPS_DOWNSTREAM_PATTERNS = (
    "survivors_2",
    "survivors_2bps",
    "exact_1m_survivors_2bps",
    "exact_5m_survivors_2bps",
    "exact_15m_survivors_2bps",
    "exact_30m_survivors_2bps",
    "exact_1h_survivors_2bps",
    "exact_4h_survivors_2bps",
    "exact_1d_survivors_2bps",
)
FIVE_BPS_DENSITY_FLOOR_PATTERNS = (
    "trades >=",
    "trade_count >=",
    "trades_per_day >=",
    "daily_avg >=",
    "density_ok",
    "practical_density",
)


def string_key(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def expression_text(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment:
        return " ".join(segment.strip().split())
    return ast.dump(node, annotate_fields=False, include_attributes=False)


def is_false_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is False


def is_practical_helper_value(node: ast.AST, key: str) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if not isinstance(node.value, ast.Name) or node.value.id not in HELPER_RESULT_NAMES:
        return False
    index = node.slice
    if isinstance(index, ast.Constant) and index.value == key:
        return True
    return False


def contains_pda_hard_gate(source: str, node: ast.AST) -> bool:
    text = expression_text(source, node)
    return any(pattern in text for pattern in PDA_HARD_GATE_PATTERNS)


def contains_two_bps_downstream_gate(source: str, node: ast.AST) -> bool:
    text = expression_text(source, node)
    return any(pattern in text for pattern in TWO_BPS_DOWNSTREAM_PATTERNS)


def contains_5bps_density_floor(source: str, node: ast.AST) -> bool:
    text = expression_text(source, node)
    return any(pattern in text for pattern in FIVE_BPS_DENSITY_FLOOR_PATTERNS)


def contains_learning_source(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Subscript) and string_key(child.slice) in LEARNING_KEYS:
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if child.value in LEARNING_KEYS:
                return True
    return False


def helper_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == HELPER_NAME:
            arg_names = {arg.arg for arg in node.args.args}
            if "branch_local_admitted" in arg_names and "extension_complete" in arg_names:
                names.add(node.name)
    return names


class PracticalAssignmentVisitor(ast.NodeVisitor):
    def __init__(self, source: str, helpers: set[str]) -> None:
        self.source = source
        self.helpers = helpers
        self.function_stack: list[str] = []
        self.helper_result_names: set[str] = set()
        self.pda_tainted_admission_names: dict[str, dict[str, Any]] = {}
        self.learning_tainted_names: set[str] = set()
        self.violations: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> Any:
        learning_tainted = self.is_learning_tainted_value(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name) and learning_tainted:
                self.learning_tainted_names.add(target.id)
        if self.calls_practical_helper(node.value):
            self.record_pda_helper_argument_violation(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.helper_result_names.add(target.id)
        if contains_pda_hard_gate(self.source, node.value):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in BRANCH_ADMISSION_NAMES:
                    self.pda_tainted_admission_names[target.id] = {
                        "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                        "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                        "value": expression_text(self.source, node.value),
                    }
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in DOWNSTREAM_ADMISSION_NAMES:
                if contains_two_bps_downstream_gate(self.source, node.value):
                    self.violations.append(
                        {
                            "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                            "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                            "key": target.id,
                            "value": expression_text(self.source, node.value),
                            "violation": "downstream_admission_uses_2bps_survivor_gate",
                        }
                    )
            if isinstance(target, ast.Subscript) and string_key(target.slice) == "survives_5bps_per_side":
                if contains_5bps_density_floor(self.source, node.value):
                    self.violations.append(
                        {
                            "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                            "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                            "key": "survives_5bps_per_side",
                            "value": expression_text(self.source, node.value),
                            "violation": "five_bps_survival_uses_trade_density_floor",
                        }
                    )
            if isinstance(target, ast.Subscript) and string_key(target.slice) in PRACTICAL_KEYS:
                key = string_key(target.slice)
                if key is None:
                    continue
                if self.is_learning_tainted_value(node.value):
                    self.violations.append(
                        {
                            "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                            "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                            "key": key,
                            "value": expression_text(self.source, node.value),
                            "violation": "learning_admission_reused_as_practical_flag",
                        }
                    )
                elif not self.is_safe_practical_value(node.value, key):
                    self.violations.append(
                        {
                            "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                            "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                            "key": key,
                            "value": expression_text(self.source, node.value),
                            "violation": "practical_flag_without_extension_complete_guard",
                        }
                    )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if node.value is not None and isinstance(node.target, ast.Name):
            if self.is_learning_tainted_value(node.value):
                self.learning_tainted_names.add(node.target.id)
        if node.value is not None and self.calls_practical_helper(node.value):
            self.record_pda_helper_argument_violation(node.value)
            if isinstance(node.target, ast.Name):
                self.helper_result_names.add(node.target.id)
        if node.value is not None and contains_pda_hard_gate(self.source, node.value):
            if isinstance(node.target, ast.Name) and node.target.id in BRANCH_ADMISSION_NAMES:
                self.pda_tainted_admission_names[node.target.id] = {
                    "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                    "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                    "value": expression_text(self.source, node.value),
                }
        if (
            node.value is not None
            and isinstance(node.target, ast.Name)
            and node.target.id in DOWNSTREAM_ADMISSION_NAMES
            and contains_two_bps_downstream_gate(self.source, node.value)
        ):
            self.violations.append(
                {
                    "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                    "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                    "key": node.target.id,
                    "value": expression_text(self.source, node.value),
                    "violation": "downstream_admission_uses_2bps_survivor_gate",
                }
            )
        if (
            node.value is not None
            and isinstance(node.target, ast.Subscript)
            and string_key(node.target.slice) == "survives_5bps_per_side"
            and contains_5bps_density_floor(self.source, node.value)
        ):
            self.violations.append(
                {
                    "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                    "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                    "key": "survives_5bps_per_side",
                    "value": expression_text(self.source, node.value),
                    "violation": "five_bps_survival_uses_trade_density_floor",
                }
            )
        if (
            node.value is not None
            and isinstance(node.target, ast.Subscript)
            and string_key(node.target.slice) in PRACTICAL_KEYS
        ):
            key = string_key(node.target.slice)
            if key is not None and self.is_learning_tainted_value(node.value):
                self.violations.append(
                    {
                        "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                        "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                        "key": key,
                        "value": expression_text(self.source, node.value),
                        "violation": "learning_admission_reused_as_practical_flag",
                    }
                )
            elif key is not None and not self.is_safe_practical_value(node.value, key):
                self.violations.append(
                    {
                        "line": getattr(node.value, "lineno", getattr(node, "lineno", 0)),
                        "column": getattr(node.value, "col_offset", getattr(node, "col_offset", 0)),
                        "key": key,
                        "value": expression_text(self.source, node.value),
                        "violation": "practical_flag_without_extension_complete_guard",
                    }
                )
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> Any:
        in_helper = bool(self.function_stack and self.function_stack[-1] in self.helpers)
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                continue
            key = string_key(key_node)
            if key not in PRACTICAL_KEYS:
                if key == "survives_5bps_per_side" and contains_5bps_density_floor(self.source, value_node):
                    self.violations.append(
                        {
                            "line": getattr(value_node, "lineno", getattr(node, "lineno", 0)),
                            "column": getattr(value_node, "col_offset", getattr(node, "col_offset", 0)),
                            "key": key,
                            "value": expression_text(self.source, value_node),
                            "violation": "five_bps_survival_uses_trade_density_floor",
                        }
                    )
                continue
            if self.is_learning_tainted_value(value_node):
                self.violations.append(
                    {
                        "line": getattr(value_node, "lineno", getattr(node, "lineno", 0)),
                        "column": getattr(value_node, "col_offset", getattr(node, "col_offset", 0)),
                        "key": key,
                        "value": expression_text(self.source, value_node),
                        "violation": "learning_admission_reused_as_practical_flag",
                    }
                )
                continue
            if in_helper or self.is_safe_practical_value(value_node, key):
                continue
            self.violations.append(
                {
                    "line": getattr(value_node, "lineno", getattr(node, "lineno", 0)),
                    "column": getattr(value_node, "col_offset", getattr(node, "col_offset", 0)),
                    "key": key,
                    "value": expression_text(self.source, value_node),
                    "violation": "practical_flag_without_extension_complete_guard",
                }
            )
        self.generic_visit(node)

    def calls_practical_helper(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in self.helpers
        )

    def is_learning_tainted_value(self, node: ast.AST) -> bool:
        if contains_learning_source(node):
            return True
        return any(
            isinstance(child, ast.Name) and child.id in self.learning_tainted_names
            for child in ast.walk(node)
        )

    def record_pda_helper_argument_violation(self, node: ast.AST) -> None:
        if not self.calls_practical_helper(node) or not node.args:
            return
        branch_arg = node.args[0]
        taint: dict[str, Any] | None = None
        if contains_pda_hard_gate(self.source, branch_arg):
            taint = {
                "line": getattr(branch_arg, "lineno", getattr(node, "lineno", 0)),
                "column": getattr(branch_arg, "col_offset", getattr(node, "col_offset", 0)),
                "value": expression_text(self.source, branch_arg),
            }
        elif isinstance(branch_arg, ast.Name):
            taint = self.pda_tainted_admission_names.get(branch_arg.id)
        if taint is None:
            return
        self.violations.append(
            {
                "line": taint["line"],
                "column": taint["column"],
                "key": "branch_local_admitted",
                "value": taint["value"],
                "violation": "branch_local_admission_uses_pda_hard_gate",
            }
        )

    def is_safe_practical_value(self, node: ast.AST, key: str) -> bool:
        if is_false_literal(node):
            return True
        if isinstance(node, ast.Subscript):
            if not isinstance(node.value, ast.Name) or node.value.id not in self.helper_result_names:
                return False
            index = node.slice
            return isinstance(index, ast.Constant) and index.value == key
        return False


def check_source(source: str, *, path: Path | None = None) -> dict[str, Any]:
    tree = ast.parse(source, filename=str(path) if path else "<source>")
    helpers = helper_names(tree)
    visitor = PracticalAssignmentVisitor(source, helpers)
    visitor.visit(tree)
    violations = sorted(
        visitor.violations,
        key=lambda hit: (hit["line"], hit["column"], hit["key"]),
    )
    return {
        "file": str(path) if path else None,
        "ok": not violations,
        "decision": (
            "practical_admission_source_ok"
            if not violations
            else "practical_admission_source_violation"
        ),
        "violations": violations,
    }


def check_source_file(path: Path) -> dict[str, Any]:
    return check_source(path.read_text(encoding="utf-8"), path=path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Python downstream wrapper files to scan")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    reports = [check_source_file(path) for path in args.files]
    print(json.dumps(reports, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if all(report["ok"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
