#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RELEASE_MIRROR_URL = "https://github.com/Undermybelt/ict-engine-release.git"


def repo_root(anchor: Path) -> Path:
    for candidate in [anchor, *anchor.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "src").exists():
            return candidate
    raise RuntimeError(f"could not discover repo root from {anchor}")


def run_command(
    argv: list[str],
    cwd: Path,
    timeout: int = 20,
    env_overrides: dict[str, str] | None = None,
) -> tuple[str, dict[str, Any]]:
    env = None
    if env_overrides:
        env = os.environ.copy()
        env.update(env_overrides)
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            "fail",
            {
                "argv": argv,
                "error": "timeout",
                "stdout": _text(exc.stdout),
                "stderr": _text(exc.stderr),
            },
        )
    return (
        "pass" if result.returncode == 0 else "fail",
        {
            "argv": argv,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def parse_cargo_metadata(text: str) -> dict[str, Any]:
    data = tomllib.loads(text)
    package = data.get("package")
    if not isinstance(package, dict):
        raise ValueError("Cargo.toml missing [package]")
    return {
        "version": package.get("version"),
        "license": package.get("license"),
        "repository": package.get("repository"),
        "publish": package.get("publish"),
    }


def parse_ls_remote(text: str) -> dict[str, dict[str, str]]:
    heads: dict[str, str] = {}
    tags: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "\t" not in line:
            continue
        commit, ref = line.split("\t", 1)
        if ref.startswith("refs/heads/"):
            heads[ref.removeprefix("refs/heads/")] = commit
        elif ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            tags[ref.removeprefix("refs/tags/")] = commit
    return {"heads": heads, "tags": tags}


def build_public_remote_probe_plan(remote_name: str, declared_url: str) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "remote_name": remote_name,
        "declared_url": declared_url,
        "default_target": remote_name,
    }
    no_rewrite_env = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    match = re.fullmatch(r"git@github\.com:(.+?)(?:\.git)?", declared_url.strip())
    if match:
        repo_path = match.group(1)
        plan["fallback_public_url"] = f"https://github.com/{repo_path}.git"
        plan["fallback_transport"] = "https_public_no_rewrite"
        plan["fallback_env_overrides"] = no_rewrite_env
        return plan
    https_match = re.fullmatch(r"https://github\.com/(.+?)(?:\.git)?", declared_url.strip())
    if https_match:
        repo_path = https_match.group(1)
        plan["fallback_public_url"] = f"https://github.com/{repo_path}.git"
        plan["fallback_transport"] = "https_public_no_rewrite"
        plan["fallback_env_overrides"] = no_rewrite_env
    return plan


def evaluate_worktree_clean(status_text: str) -> dict[str, Any]:
    entries = [line for line in status_text.splitlines() if line.strip()]
    details = summarize_worktree_status(entries)
    details.update(
        {
            "sample": entries[:20],
            "rule": "release export must start from an explicitly selected committed tree, not a broad dirty worktree",
            "next_action": "commit or exclude a narrow source slice, then build release evidence from a clean sanitized export",
        }
    )
    return {
        "id": "worktree_clean_for_release",
        "status": "pass" if not entries else "fail",
        "details": details,
    }


def summarize_worktree_status(entries: list[str]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    tracked_entries = 0
    untracked_entries = 0
    staged_entries = 0
    unstaged_entries = 0
    modified_entries = 0
    deleted_entries = 0
    renamed_entries = 0
    for entry in entries:
        code = entry[:2]
        status_counts[code] = status_counts.get(code, 0) + 1
        if code == "??":
            untracked_entries += 1
            continue
        tracked_entries += 1
        index_status = code[0]
        worktree_status = code[1]
        if index_status != " ":
            staged_entries += 1
        if worktree_status != " ":
            unstaged_entries += 1
        if "M" in code:
            modified_entries += 1
        if "D" in code:
            deleted_entries += 1
        if "R" in code:
            renamed_entries += 1
    return {
        "status_entries": len(entries),
        "tracked_entries": tracked_entries,
        "untracked_entries": untracked_entries,
        "staged_entries": staged_entries,
        "unstaged_entries": unstaged_entries,
        "modified_entries": modified_entries,
        "deleted_entries": deleted_entries,
        "renamed_entries": renamed_entries,
        "status_counts": status_counts,
    }


def evaluate_version_tag(
    version: str | None,
    release_tags: set[str],
    version_source_path: str = "Cargo.toml",
) -> dict[str, Any]:
    tag = f"v{version}" if version else None
    blocking = sorted([tag] if tag and tag in release_tags else [])
    suggested = suggest_next_patch_version(version, release_tags)
    details: dict[str, Any] = {
        "version": version,
        "version_source_path": version_source_path,
        "candidate_tag": tag,
        "blocking_tags": blocking,
        "suggested_next_patch_version": suggested,
        "suggested_next_patch_tag": f"v{suggested}" if suggested else None,
        "known_release_tags": sorted(release_tags),
        "rule": "never reuse an existing release mirror tag",
    }
    if blocking:
        next_action = f"update {version_source_path} to an unused version"
        if suggested:
            next_action += f" such as {suggested}"
        details["next_action"] = next_action + ", then rerun release readiness audit"
    return {
        "id": "release_version_tag_available",
        "status": "pass" if tag and not blocking else "fail",
        "details": details,
    }


def suggest_next_patch_version(version: str | None, release_tags: set[str]) -> str | None:
    if not version:
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    while True:
        patch += 1
        candidate = f"{major}.{minor}.{patch}"
        if f"v{candidate}" not in release_tags:
            return candidate


def evaluate_version_tag_unknown(reason: str) -> dict[str, Any]:
    details: dict[str, Any] = {
        "reason": reason,
        "enable_with": "--check-remotes",
        "rule": "release tag availability must be checked against release mirror tags, not local tags",
    }
    if reason == "release_mirror_tags_unavailable":
        details.update(
            {
                "blocked_by_gate": "remote_readback",
                "next_action": "resolve remote_readback, then rerun release readiness audit with --check-remotes",
            }
        )
    return {
        "id": "release_version_tag_available",
        "status": "skip",
        "details": details,
    }


def evaluate_remote_readback(
    origin_state: str,
    origin_details: dict[str, Any],
    mirror_state: str,
    mirror_details: dict[str, Any],
) -> dict[str, Any]:
    effective_origin_state, effective_origin_details = effective_remote_readback(origin_state, origin_details)
    effective_mirror_state, effective_mirror_details = effective_remote_readback(mirror_state, mirror_details)
    status = "pass" if effective_origin_state == "pass" and effective_mirror_state == "pass" else "fail"
    details: dict[str, Any] = {
        "enabled": True,
        "origin_status": "pass_via_fallback" if origin_state != "pass" and effective_origin_state == "pass" else origin_state,
        "release_mirror_status": "pass_via_fallback" if mirror_state != "pass" and effective_mirror_state == "pass" else mirror_state,
        "origin_raw_status": origin_state,
        "release_mirror_raw_status": mirror_state,
        "origin": effective_origin_details,
        "release_mirror": effective_mirror_details,
    }
    if status != "pass":
        diagnostic_class = classify_remote_probe_drift(effective_origin_details, effective_mirror_details)
        details.update(
            {
                "blocked_gate": "release_version_tag_available",
                "next_action": remote_readback_next_action(diagnostic_class),
                "rule": "release mirror heads and tags must be readable before tag availability can be trusted",
            }
        )
        if diagnostic_class:
            details["diagnostic_class"] = diagnostic_class
    return {
        "id": "remote_readback",
        "status": status,
        "details": details,
    }


def effective_remote_readback(state: str, details: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if state == "pass":
        return state, details
    fallback = details.get("fallback_public_probe")
    if not isinstance(fallback, dict):
        return state, details
    result = fallback.get("result")
    if not isinstance(result, dict) or result.get("returncode") != 0:
        return state, details
    merged = dict(details)
    merged["effective_readback"] = "fallback_public_probe"
    merged["raw_probe"] = {key: value for key, value in details.items() if key != "fallback_public_probe"}
    for key in ("argv", "returncode", "stdout", "stderr"):
        if key in result:
            merged[key] = result[key]
    return "pass", merged


def remote_readback_next_action(diagnostic_class: str | None) -> str:
    if diagnostic_class == "https_probe_ssh_transport_drift":
        return (
            "restore release mirror readback after checking local git transport rewrite drift "
            "for `url.*.insteadof`, `core.sshCommand`, and `http.*.proxy` "
            "(for example `git config --show-origin --get-regexp '^(url\\..*\\.insteadof|core\\.sshCommand|http\\..*\\.proxy)$'`), "
            "or rerun from a network that can reach the release mirror, then rerun release readiness audit with --check-remotes"
        )
    return (
        "restore release mirror git/network/auth readback, or rerun from a network "
        "that can reach the release mirror, then rerun release readiness audit with "
        "--check-remotes"
    )


def classify_remote_probe_drift(*remote_details: dict[str, Any]) -> str | None:
    for details in remote_details:
        fallback = details.get("fallback_public_probe")
        if not isinstance(fallback, dict):
            continue
        target = fallback.get("target")
        transport = fallback.get("transport")
        result = fallback.get("result")
        if not isinstance(target, str) or not isinstance(result, dict):
            continue
        stderr_text = _text(result.get("stderr"))
        if (
            transport == "https_public_no_rewrite"
            and target.startswith("https://github.com/")
            and "port 22" in stderr_text
        ):
            return "https_probe_ssh_transport_drift"
    return None


def read_remote_probe(
    root: Path,
    remote_name: str,
    timeout: int = 30,
) -> tuple[str, dict[str, Any]]:
    state, details = run_command(
        ["git", "ls-remote", "--heads", "--tags", remote_name],
        root,
        timeout=timeout,
    )
    declared_state, declared_details = run_command(
        ["git", "remote", "get-url", remote_name],
        root,
        timeout=10,
    )
    if declared_state != "pass":
        return state, details

    declared_url = declared_details["stdout"].strip()
    if not declared_url:
        return state, details

    plan = build_public_remote_probe_plan(remote_name, declared_url)
    details["remote_name"] = remote_name
    details["declared_url"] = declared_url
    if state == "pass" or not plan.get("fallback_public_url"):
        return state, details

    fallback_target = str(plan["fallback_public_url"])
    fallback_state, fallback_details = run_command(
        ["git", "ls-remote", "--heads", "--tags", fallback_target],
        root,
        timeout=timeout,
        env_overrides=plan.get("fallback_env_overrides"),
    )
    details["fallback_public_probe"] = {
        "target": fallback_target,
        "transport": plan["fallback_transport"],
        "result": fallback_details,
    }
    return state, details


def read_url_remote_probe(
    root: Path,
    remote_name: str,
    remote_url: str,
    timeout: int = 30,
) -> tuple[str, dict[str, Any]]:
    state, details = run_command(
        ["git", "ls-remote", "--heads", "--tags", remote_url],
        root,
        timeout=timeout,
    )
    plan = build_public_remote_probe_plan(remote_name, remote_url)
    details["remote_name"] = remote_name
    details["declared_url"] = remote_url
    if state == "pass" or not plan.get("fallback_public_url"):
        return state, details
    fallback_target = str(plan["fallback_public_url"])
    fallback_state, fallback_details = run_command(
        ["git", "ls-remote", "--heads", "--tags", fallback_target],
        root,
        timeout=timeout,
        env_overrides=plan.get("fallback_env_overrides"),
    )
    details["fallback_public_probe"] = {
        "target": fallback_target,
        "transport": plan["fallback_transport"],
        "result": fallback_details,
    }
    return state, details


def evaluate_cargo_release_policy(metadata: dict[str, Any]) -> dict[str, Any]:
    publish = metadata.get("publish")
    license_name = metadata.get("license")
    repository = metadata.get("repository")
    ok = (
        publish is False
        and license_name == "PolyForm-Noncommercial-1.0.0"
        and repository == "https://github.com/Undermybelt/ict-engine-release"
    )
    return {
        "id": "cargo_release_policy",
        "status": "pass" if ok else "fail",
        "details": {
            "publish": publish,
            "license": license_name,
            "repository": repository,
            "rule": "private mirror only; public package-manager publication stays disabled",
        },
    }


def evaluate_docs_freshness(
    signoff_text: str,
    notes_text: str,
    signoff_path: str = "support/docs/audits/release-signoff.md",
    notes_path: str = "support/docs/release-notes-draft.md",
) -> dict[str, Any]:
    markers: list[str] = []
    signoff_lower = signoff_text.lower()
    notes_lower = notes_text.lower()
    if "historical" in signoff_lower or "not current release permission" in signoff_lower:
        markers.append("release_signoff_historical")
    if "historical" in notes_lower or "not valid release notes" in notes_lower:
        markers.append("release_notes_historical")
    if "no release permission" in signoff_lower or "do not publish" in signoff_lower:
        markers.append("release_signoff_blocks_publish")
    details: dict[str, Any] = {
        "markers": markers,
        "doc_paths": [signoff_path, notes_path],
        "rule": "signoff and release notes must describe the selected fresh tag/export, not historical evidence",
    }
    if markers:
        details["next_action"] = "refresh release signoff and release notes for the selected tag/export, then rerun release readiness audit"
    return {
        "id": "release_docs_fresh_for_selected_tag",
        "status": "pass" if not markers else "fail",
        "details": details,
    }


def parse_origin_divergence(text: str, ref: str = "origin/main") -> dict[str, Any]:
    parts = text.split()
    if len(parts) < 2:
        raise ValueError("origin divergence output must contain ahead and behind counts")
    behind, ahead = (int(parts[0]), int(parts[1]))
    return {
        "ahead": ahead,
        "behind": behind,
        "ref": ref,
    }


def evaluate_source_origin_alignment(
    head: str,
    origin_main: str | None,
    mirror_main: str | None,
    origin_divergence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    aligned = bool(head and origin_main == head)
    details: dict[str, Any] = {
        "head": head,
        "origin_main": origin_main,
        "release_mirror_main": mirror_main,
        "rule": "source origin/main must match the selected source commit before a clean export is published",
    }
    if origin_divergence:
        details.update(
            {
                "source_ahead_of_origin": origin_divergence.get("ahead"),
                "source_behind_origin": origin_divergence.get("behind"),
                "origin_ref": origin_divergence.get("ref"),
            }
        )
    if not aligned:
        ahead = origin_divergence.get("ahead") if origin_divergence else None
        behind = origin_divergence.get("behind") if origin_divergence else None
        if ahead and not behind:
            next_action = "push selected source commit or publish from a clean export at the selected commit"
        elif behind:
            next_action = "sync local source with origin/main before selecting a release export commit"
        else:
            next_action = "inspect source/origin drift before release export"
        details["next_action"] = next_action
    return {
        "id": "source_origin_matches_selected_source",
        "status": "pass" if aligned else "fail",
        "details": details,
    }


def summarize(gates: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = [gate["id"] for gate in gates if gate.get("status") == "fail"]
    return {
        "status": "needs_fix" if unresolved else "pass",
        "pass_count": sum(1 for gate in gates if gate.get("status") == "pass"),
        "fail_count": len(unresolved),
        "skip_count": sum(1 for gate in gates if gate.get("status") == "skip"),
        "total_gates": len(gates),
        "unresolved": unresolved,
    }


def build_report(root: Path, check_remotes: bool) -> dict[str, Any]:
    status_state, status_details = run_command(["git", "status", "--short"], root)
    if status_state != "pass":
        raise RuntimeError(status_details["stderr"] or "git status failed")
    head_state, head_details = run_command(["git", "rev-parse", "HEAD"], root)
    if head_state != "pass":
        raise RuntimeError(head_details["stderr"] or "git rev-parse HEAD failed")

    metadata = parse_cargo_metadata((root / "Cargo.toml").read_text(encoding="utf-8"))
    release_tags: set[str] | None = None

    gates = [
        evaluate_worktree_clean(status_details["stdout"]),
        evaluate_cargo_release_policy(metadata),
        evaluate_docs_freshness(
            (root / "support/docs/audits/release-signoff.md").read_text(encoding="utf-8"),
            (root / "support/docs/release-notes-draft.md").read_text(encoding="utf-8"),
        ),
    ]

    remote_details: dict[str, Any] = {"enabled": check_remotes}
    if check_remotes:
        origin_state, origin_details = read_remote_probe(root, "origin", timeout=30)
        mirror_state, mirror_details = read_url_remote_probe(
            root,
            "release_mirror",
            RELEASE_MIRROR_URL,
            timeout=30,
        )
        effective_origin_state, effective_origin_details = effective_remote_readback(origin_state, origin_details)
        effective_mirror_state, effective_mirror_details = effective_remote_readback(mirror_state, mirror_details)
        if effective_origin_state == "pass" and effective_mirror_state == "pass":
            origin = parse_ls_remote(effective_origin_details["stdout"])
            mirror = parse_ls_remote(effective_mirror_details["stdout"])
            divergence: dict[str, Any] | None = None
            divergence_state, divergence_details = run_command(
                ["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"],
                root,
                timeout=20,
            )
            if divergence_state == "pass":
                divergence = parse_origin_divergence(divergence_details["stdout"], ref="origin/main")
            release_tags = set(mirror["tags"])
            remote_details.update(
                {
                    "origin_main": origin["heads"].get("main"),
                    "release_mirror_main": mirror["heads"].get("main"),
                    "release_mirror_tags": sorted(mirror["tags"]),
                    "origin_raw_status": origin_state,
                    "release_mirror_raw_status": mirror_state,
                    "origin_status": "pass_via_fallback" if origin_state != "pass" else "pass",
                    "release_mirror_status": "pass_via_fallback" if mirror_state != "pass" else "pass",
                    "origin": effective_origin_details,
                    "release_mirror": effective_mirror_details,
                    "origin_divergence": divergence if divergence else divergence_details,
                }
            )
            gates.append(
                evaluate_source_origin_alignment(
                    head_details["stdout"].strip(),
                    origin["heads"].get("main"),
                    mirror["heads"].get("main"),
                    origin_divergence=divergence,
                )
            )
        else:
            remote_readback = evaluate_remote_readback(origin_state, origin_details, mirror_state, mirror_details)
            remote_details.update(remote_readback["details"])
            gates.append(remote_readback)
    else:
        gates.append(
            {
                "id": "remote_readback",
                "status": "skip",
                "details": {
                    "reason": "network_check_not_enabled",
                    "enable_with": "--check-remotes",
                },
            }
        )

    if release_tags is None:
        reason = "network_check_not_enabled" if not check_remotes else "release_mirror_tags_unavailable"
        gates.append(evaluate_version_tag_unknown(reason))
    else:
        gates.append(evaluate_version_tag(str(metadata.get("version") or ""), release_tags))

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "head": head_details["stdout"].strip(),
        "cargo": metadata,
        "remote_details": remote_details,
        "summary": summarize(gates),
        "gates": gates,
    }


def _repo_relative_text(value: str, root: str) -> str:
    if not root:
        return value
    result = value.replace(root + "/", "")
    return result.replace(root, ".")


def _line_count(value: str) -> int:
    if not value:
        return 0
    return len(value.splitlines())


def _compact_command_details(value: dict[str, Any], root: str) -> dict[str, Any]:
    compacted = {
        key: _compact_value(nested, root)
        for key, nested in value.items()
        if key not in {"stdout", "stderr"}
    }
    for stream_name in ["stdout", "stderr"]:
        stream_text = _repo_relative_text(str(value.get(stream_name) or ""), root)
        compacted[f"{stream_name}_line_count"] = _line_count(stream_text)
        if stream_text.strip():
            compacted[f"{stream_name}_excerpt"] = stream_text.splitlines()[0][:200]
    return compacted


def _compact_value(value: Any, root: str) -> Any:
    if isinstance(value, str):
        return _repo_relative_text(value, root)
    if isinstance(value, list):
        return [_compact_value(item, root) for item in value]
    if isinstance(value, dict):
        if "argv" in value and ("stdout" in value or "stderr" in value):
            return _compact_command_details(value, root)
        return {key: _compact_value(nested, root) for key, nested in value.items()}
    return value


def _compact_report(report: dict[str, Any]) -> dict[str, Any]:
    root = str(report.get("repo_root") or "")
    return {
        "timestamp_utc": report.get("timestamp_utc"),
        "head": report.get("head"),
        "cargo": report.get("cargo"),
        "remote_details": _compact_value(report.get("remote_details", {}), root),
        "summary": report.get("summary"),
        "gates": _compact_value(report.get("gates", []), root),
    }


def format_report(report: dict[str, Any], compact: bool) -> str:
    payload = _compact_report(report) if compact else report
    indent = None if compact else 2
    separators = (",", ":") if compact else None
    return json.dumps(payload, indent=indent, separators=separators, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ict-engine release readiness audit")
    parser.add_argument("--check-remotes", action="store_true", help="Run git ls-remote against source origin and release mirror")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument("--compact", action="store_true", help="Emit single-line JSON for token-friendly agent use")
    args = parser.parse_args()

    root = repo_root(Path(__file__).resolve())
    report = build_report(root, check_remotes=args.check_remotes)
    text = format_report(report, compact=args.compact)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if report["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
