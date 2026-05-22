#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "name",
    "stability",
    "entrypoint",
    "safe_default",
    "requires_data",
    "test_command",
}

ALLOWED_STABILITY = {
    "active_bridge",
    "audit_helper",
    "ci_guard",
    "docs_guard",
    "operator_bridge",
    "optional_bridge",
    "provider_bridge",
    "public_wrapper",
    "read_only_utility",
    "stable_helper",
}

REQUIRED_PUBLIC_WRAPPERS = {
    "support/scripts/search_local.py",
    "support/scripts/search_cluster.py",
    "support/scripts/evaluate_bottleneck.py",
    "support/scripts/research_verdict.py",
}

REQUIRED_PUBLIC_HELPERS = {
    "support/scripts/smoke_acceptance.sh",
    "support/scripts/help_audit.py",
    "support/scripts/check_factor_truth_map.py",
    "support/scripts/check_script_manifest.py",
    "support/scripts/ci/check_docs_runtime_isolation.py",
    "support/scripts/release_readiness_audit.py",
}


def repo_root(anchor: Path) -> Path:
    for candidate in [anchor, *anchor.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "src").exists():
            return candidate
    raise RuntimeError(f"could not discover repo root from {anchor}")


def has_private_path(value: str) -> bool:
    return "/Users/" in value or value.startswith("~")


def validate_entry(index: int, item: object, root: Path, seen_names: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(item, dict):
        return [f"entry[{index}] is not an object"]

    keys = set(item)
    missing = REQUIRED_FIELDS - keys
    extra = keys - REQUIRED_FIELDS
    if missing:
        errors.append(f"entry[{index}] missing fields: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"entry[{index}] has unknown fields: {', '.join(sorted(extra))}")
    if missing:
        return errors

    name = item["name"]
    stability = item["stability"]
    entrypoint = item["entrypoint"]
    safe_default = item["safe_default"]
    requires_data = item["requires_data"]
    test_command = item["test_command"]

    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+", name):
        errors.append(f"entry[{index}] name must be snake_case: {name!r}")
    elif name in seen_names:
        errors.append(f"entry[{index}] duplicate name: {name}")
    else:
        seen_names.add(name)

    if stability not in ALLOWED_STABILITY:
        errors.append(f"entry[{index}] invalid stability: {stability!r}")

    if not isinstance(entrypoint, str) or not entrypoint:
        errors.append(f"entry[{index}] entrypoint must be a non-empty string")
    else:
        entry_path = Path(entrypoint)
        if entry_path.is_absolute() or has_private_path(entrypoint):
            errors.append(f"entry[{index}] entrypoint must be repo-relative: {entrypoint!r}")
        else:
            resolved = (root / entry_path).resolve()
            if root not in [resolved, *resolved.parents]:
                errors.append(f"entry[{index}] entrypoint escapes repo: {entrypoint!r}")
            if not resolved.exists():
                errors.append(f"entry[{index}] entrypoint does not exist: {entrypoint!r}")

    if not isinstance(safe_default, bool):
        errors.append(f"entry[{index}] safe_default must be boolean")
    if not isinstance(requires_data, bool):
        errors.append(f"entry[{index}] requires_data must be boolean")

    if not isinstance(test_command, str) or not test_command.strip():
        errors.append(f"entry[{index}] test_command must be a non-empty string")
    elif has_private_path(test_command):
        errors.append(f"entry[{index}] test_command must not contain private paths")

    return errors


def main() -> int:
    root = repo_root(Path(__file__).resolve())
    manifest = root / "support" / "scripts" / "script_manifest.json"
    try:
        data = json.loads(manifest.read_text())
    except FileNotFoundError:
        print(f"script_manifest status=fail missing={manifest.relative_to(root)}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"script_manifest status=fail invalid_json={exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if not isinstance(data, list):
        errors.append("manifest root must be a list")
        data = []

    seen_names: set[str] = set()
    entrypoints: set[str] = set()
    safe_required_public_entries = 0
    for index, item in enumerate(data):
        errors.extend(validate_entry(index, item, root, seen_names))
        if isinstance(item, dict) and isinstance(item.get("entrypoint"), str):
            entrypoints.add(item["entrypoint"])
            if item["entrypoint"] in REQUIRED_PUBLIC_WRAPPERS and item.get("safe_default") is True:
                safe_required_public_entries += 1

    missing_wrappers = REQUIRED_PUBLIC_WRAPPERS - entrypoints
    missing_helpers = REQUIRED_PUBLIC_HELPERS - entrypoints
    if missing_wrappers:
        errors.append(
            "missing required public wrappers: " + ", ".join(sorted(missing_wrappers))
        )
    if missing_helpers:
        errors.append(
            "missing required public helpers: " + ", ".join(sorted(missing_helpers))
        )

    if errors:
        print("script_manifest status=fail", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "script_manifest status=pass "
        f"entries={len(data)} "
        f"required_public_entries={len(REQUIRED_PUBLIC_WRAPPERS)} "
        f"safe_required_public_entries={safe_required_public_entries}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
