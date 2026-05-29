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
PASSIVE_READBACK_NAMES = frozenset((
    "claim",
    "decision",
    "fields",
    "latest",
    "latest_decision",
    "live_trade",
    "payload",
    "report",
    "summary_flags",
))
PDA_HARD_GATE_PATTERNS = (
    " and pda",
    "pda and ",
    "pda is True",
    "pda_hybrid_alignment is True",
    "pda_hybrid_alignment_true",
)
TRANSITION_HARD_GATE_PATTERNS = (
    "hazard < 0.60",
    "transition_hazard < 0.60",
    "hybrid_transition_hazard < 0.60",
    "transition_hazard_gte_0.60",
)
RETIRED_PRACTICAL_GATE_KEYS = frozenset((
    "pda_hybrid_alignment",
    "pda_hybrid_alignment_true",
    "pda_required",
    "transition_hazard_lt",
    "transition_hazard_required",
))
CANONICAL_CLOSURE_BUILDER_NAMES = frozenset((
    "build_same_tree_practical_closure_packet",
    "write_same_tree_practical_closure_packet",
))
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


def references_name(node: ast.AST, name: str) -> bool:
    return any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node))


def references_any_name(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(child, ast.Name) and child.id in names for child in ast.walk(node))


def is_branch_extension_and_guard(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool" and node.args:
        return is_branch_extension_and_guard(node.args[0])
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        return references_name(node, "branch_local_admitted") and references_name(node, "extension_complete")
    return False


def is_practical_helper_value(node: ast.AST, key: str) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if not isinstance(node.value, ast.Name) or node.value.id not in HELPER_RESULT_NAMES:
        return False
    index = node.slice
    if isinstance(index, ast.Constant) and index.value == key:
        return True
    return False


def is_passive_practical_readback(node: ast.AST, key: str) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool" and node.args:
        return is_passive_practical_readback(node.args[0], key)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
        value = node.func.value
        if isinstance(value, ast.Name) and value.id in PASSIVE_READBACK_NAMES:
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == key:
                return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_extract_bool":
        if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == key:
            return True
    if isinstance(node, ast.Subscript):
        value = node.value
        if isinstance(value, ast.Name) and value.id in PASSIVE_READBACK_NAMES:
            return isinstance(node.slice, ast.Constant) and node.slice.value == key
    return False


def contains_pda_hard_gate(source: str, node: ast.AST) -> bool:
    text = expression_text(source, node)
    return any(pattern in text for pattern in PDA_HARD_GATE_PATTERNS)


def contains_transition_hard_gate(source: str, node: ast.AST) -> bool:
    text = expression_text(source, node)
    return any(pattern in text for pattern in TRANSITION_HARD_GATE_PATTERNS)


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


def is_retired_practical_gate_key(key: str | None) -> bool:
    if key is None:
        return False
    return key in RETIRED_PRACTICAL_GATE_KEYS or key.endswith("_transition_hazard_lt")


def is_allowed_retired_gate_telemetry(key: str, value_node: ast.AST) -> bool:
    return key in {"pda_required", "transition_hazard_required"} and is_false_literal(value_node)


def calls_canonical_same_tree_closure_builder(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id in CANONICAL_CLOSURE_BUILDER_NAMES
    if isinstance(node.func, ast.Attribute):
        return node.func.attr in CANONICAL_CLOSURE_BUILDER_NAMES
    return False


def dict_has_same_tree_practical_closure_schema(node: ast.Dict) -> bool:
    for key_node, value_node in zip(node.keys, node.values):
        if key_node is None:
            continue
        if string_key(key_node) == "schema_version":
            return isinstance(value_node, ast.Constant) and value_node.value == "same-tree-practical-closure/v1"
    return False


def is_canonical_same_tree_closure_source(path: Path | None) -> bool:
    return path is not None and path.name == "same_tree_practical_closure.py"


def helper_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == HELPER_NAME:
            arg_names = {arg.arg for arg in node.args.args}
            if (
                "branch_local_admitted" in arg_names
                and "extension_complete" in arg_names
                and practical_helper_values_are_extension_guarded(node)
            ):
                names.add(node.name)
    return names


def practical_helper_values_are_extension_guarded(node: ast.FunctionDef) -> bool:
    extension_guarded_names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assign) and is_branch_extension_and_guard(child.value):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    extension_guarded_names.add(target.id)
        if isinstance(child, ast.AnnAssign) and child.value is not None:
            if is_branch_extension_and_guard(child.value) and isinstance(child.target, ast.Name):
                extension_guarded_names.add(child.target.id)

    found_practical_keys: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Dict):
            for key_node, value_node in zip(child.keys, child.values):
                if key_node is None:
                    continue
                key = string_key(key_node)
                if key not in PRACTICAL_KEYS:
                    continue
                found_practical_keys.add(key)
                if not is_false_literal(value_node) and not (
                    is_branch_extension_and_guard(value_node) or references_any_name(value_node, extension_guarded_names)
                ):
                    return False
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "dict":
            for keyword in child.keywords:
                key = keyword.arg
                if key not in PRACTICAL_KEYS:
                    continue
                found_practical_keys.add(key)
                value_node = keyword.value
                if not is_false_literal(value_node) and not (
                    is_branch_extension_and_guard(value_node) or references_any_name(value_node, extension_guarded_names)
                ):
                    return False
    return PRACTICAL_KEYS.issubset(found_practical_keys)


class PracticalAssignmentVisitor(ast.NodeVisitor):
    def __init__(self, source: str, helpers: set[str], *, canonical_closure_source: bool = False) -> None:
        self.source = source
        self.helpers = helpers
        self.canonical_closure_source = canonical_closure_source
        self.function_stack: list[str] = []
        self.helper_result_names: set[str] = set()
        self.pda_tainted_admission_names: dict[str, dict[str, Any]] = {}
        self.transition_tainted_admission_names: dict[str, dict[str, Any]] = {}
        self.learning_tainted_names: set[str] = set()
        self.false_practical_names: dict[str, str] = {}
        self.passive_practical_readback_names: dict[str, str] = {}
        self.dict_context_stack: list[str] = []
        self.violations: list[dict[str, Any]] = []

    def in_canonical_same_tree_closure_builder(self) -> bool:
        return bool(
            self.canonical_closure_source
            and self.function_stack
            and self.function_stack[-1] in CANONICAL_CLOSURE_BUILDER_NAMES
        )

    def record_manual_same_tree_practical_closure_writer(self, node: ast.AST, value: str) -> None:
        if self.in_canonical_same_tree_closure_builder():
            return
        self.violations.append(
            {
                "line": getattr(node, "lineno", 0),
                "column": getattr(node, "col_offset", 0),
                "key": "same_tree_practical_closure",
                "value": value,
                "violation": "manual_same_tree_practical_closure_packet_writer",
            }
        )

    def transition_taint_for_value(self, node: ast.AST) -> dict[str, Any] | None:
        if contains_transition_hard_gate(self.source, node):
            return {
                "line": getattr(node, "lineno", 0),
                "column": getattr(node, "col_offset", 0),
                "value": expression_text(self.source, node),
            }
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in self.transition_tainted_admission_names:
                return self.transition_tainted_admission_names[child.id]
        return None

    def record_transition_hard_gate_violation(self, *, key: str, taint: dict[str, Any]) -> None:
        self.violations.append(
            {
                "line": taint["line"],
                "column": taint["column"],
                "key": key,
                "value": taint["value"],
                "violation": "branch_local_admission_uses_transition_hard_gate",
            }
        )

    def record_extension_complete_argument_violation(self, node: ast.Call) -> None:
        for keyword in node.keywords:
            if keyword.arg != "extension_complete":
                continue
            if is_false_literal(keyword.value):
                return
            self.violations.append(
                {
                    "line": getattr(keyword.value, "lineno", getattr(node, "lineno", 0)),
                    "column": getattr(keyword.value, "col_offset", getattr(node, "col_offset", 0)),
                    "key": "extension_complete",
                    "value": expression_text(self.source, keyword.value),
                    "violation": "extension_complete_without_validated_practical_closure_source",
                }
            )
            return

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.function_stack.append(node.name)
        prior_helper_result_names = self.helper_result_names
        prior_pda_tainted_names = self.pda_tainted_admission_names
        prior_transition_tainted_names = self.transition_tainted_admission_names
        prior_learning_tainted_names = self.learning_tainted_names
        prior_false_practical_names = self.false_practical_names
        prior_passive_practical_readback_names = self.passive_practical_readback_names
        self.helper_result_names = set()
        self.pda_tainted_admission_names = {}
        self.transition_tainted_admission_names = {}
        self.learning_tainted_names = set()
        self.false_practical_names = dict(prior_false_practical_names)
        self.passive_practical_readback_names = {}
        try:
            self.generic_visit(node)
        finally:
            self.helper_result_names = prior_helper_result_names
            self.pda_tainted_admission_names = prior_pda_tainted_names
            self.transition_tainted_admission_names = prior_transition_tainted_names
            self.learning_tainted_names = prior_learning_tainted_names
            self.false_practical_names = prior_false_practical_names
            self.passive_practical_readback_names = prior_passive_practical_readback_names
            self.function_stack.pop()

    def track_safe_name_assignment(self, target: ast.expr, value: ast.AST) -> None:
        if not isinstance(target, ast.Name):
            return
        self.false_practical_names.pop(target.id, None)
        self.passive_practical_readback_names.pop(target.id, None)
        if is_false_literal(value):
            self.false_practical_names[target.id] = target.id if target.id in PRACTICAL_KEYS else "*"
            return
        for key in PRACTICAL_KEYS:
            if is_passive_practical_readback(value, key):
                self.passive_practical_readback_names[target.id] = key
                return

    def visit_Assign(self, node: ast.Assign) -> Any:
        learning_tainted = self.is_learning_tainted_value(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name) and learning_tainted:
                self.learning_tainted_names.add(target.id)
            self.track_safe_name_assignment(target, node.value)
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
        transition_taint = self.transition_taint_for_value(node.value)
        if transition_taint is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.transition_tainted_admission_names[target.id] = transition_taint
                    if target.id in BRANCH_ADMISSION_NAMES:
                        self.record_transition_hard_gate_violation(
                            key=target.id,
                            taint=transition_taint,
                        )
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
            self.track_safe_name_assignment(node.target, node.value)
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
        transition_taint = self.transition_taint_for_value(node.value) if node.value is not None else None
        if transition_taint is not None and isinstance(node.target, ast.Name):
            self.transition_tainted_admission_names[node.target.id] = transition_taint
            if isinstance(node.target, ast.Name) and node.target.id in BRANCH_ADMISSION_NAMES:
                self.record_transition_hard_gate_violation(
                    key=node.target.id,
                    taint=transition_taint,
                )
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
        if dict_has_same_tree_practical_closure_schema(node):
            self.record_manual_same_tree_practical_closure_writer(
                node,
                "schema_version=same-tree-practical-closure/v1",
            )
            return
        in_helper = bool(self.function_stack and self.function_stack[-1] in self.helpers)
        in_allowed_targets = "allowed_targets" in self.dict_context_stack
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                continue
            key = string_key(key_node)
            if is_retired_practical_gate_key(key) and not is_allowed_retired_gate_telemetry(key, value_node):
                self.violations.append(
                    {
                        "line": getattr(value_node, "lineno", getattr(node, "lineno", 0)),
                        "column": getattr(value_node, "col_offset", getattr(node, "col_offset", 0)),
                        "key": key,
                        "value": expression_text(self.source, value_node),
                        "violation": "retired_field_used_as_practical_gate_template",
                    }
                )
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
            if in_allowed_targets:
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
        for key_node, value_node in zip(node.keys, node.values):
            key = string_key(key_node) if key_node is not None else None
            if key == "allowed_targets":
                self.dict_context_stack.append("allowed_targets")
                try:
                    self.visit(value_node)
                finally:
                    self.dict_context_stack.pop()
            else:
                self.visit(value_node)

    def visit_Call(self, node: ast.Call) -> Any:
        if self.calls_practical_helper(node):
            self.record_extension_complete_argument_violation(node)
        if self.canonical_closure_source and calls_canonical_same_tree_closure_builder(node):
            self.generic_visit(node)
            return
        if isinstance(node.func, ast.Name) and node.func.id == "dict":
            in_helper = bool(self.function_stack and self.function_stack[-1] in self.helpers)
            for keyword in node.keywords:
                if (
                    keyword.arg == "schema_version"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == "same-tree-practical-closure/v1"
                ):
                    self.record_manual_same_tree_practical_closure_writer(
                        node,
                        "schema_version=same-tree-practical-closure/v1",
                    )
                    return
            for keyword in node.keywords:
                key = keyword.arg
                if (
                    key is not None
                    and is_retired_practical_gate_key(key)
                    and not is_allowed_retired_gate_telemetry(key, keyword.value)
                ):
                    self.violations.append(
                        {
                            "line": getattr(keyword.value, "lineno", getattr(node, "lineno", 0)),
                            "column": getattr(keyword.value, "col_offset", getattr(node, "col_offset", 0)),
                            "key": key,
                            "value": expression_text(self.source, keyword.value),
                            "violation": "retired_field_used_as_practical_gate_template",
                        }
                    )
                if key is None or key not in PRACTICAL_KEYS:
                    continue
                value_node = keyword.value
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

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if node.attr == "write_text":
            value_text = expression_text(self.source, node.value)
            if "same_tree_practical_closure" in value_text:
                self.violations.append(
                    {
                        "line": getattr(node, "lineno", 0),
                        "column": getattr(node, "col_offset", 0),
                        "key": "same_tree_practical_closure",
                        "value": value_text,
                        "violation": "manual_same_tree_practical_closure_packet_writer",
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
        if not self.calls_practical_helper(node):
            return
        if not node.args:
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
        if taint is not None:
            self.violations.append(
                {
                    "line": taint["line"],
                    "column": taint["column"],
                    "key": "branch_local_admitted",
                    "value": taint["value"],
                    "violation": "branch_local_admission_uses_pda_hard_gate",
                }
            )
        transition_taint = self.transition_taint_for_value(branch_arg)
        if transition_taint is not None:
            self.record_transition_hard_gate_violation(
                key="branch_local_admitted",
                taint=transition_taint,
            )

    def is_safe_practical_value(self, node: ast.AST, key: str) -> bool:
        if is_false_literal(node):
            return True
        if is_passive_practical_readback(node, key):
            return True
        if isinstance(node, ast.Name) and self.false_practical_names.get(node.id) == key:
            return True
        if isinstance(node, ast.Name) and self.false_practical_names.get(node.id) == "*":
            return True
        if isinstance(node, ast.Name) and self.passive_practical_readback_names.get(node.id) == key:
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
    visitor = PracticalAssignmentVisitor(
        source,
        helpers,
        canonical_closure_source=is_canonical_same_tree_closure_source(path),
    )
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
