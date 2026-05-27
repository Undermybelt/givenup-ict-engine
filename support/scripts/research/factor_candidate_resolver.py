from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
from typing import Any
import zipfile

import factor_candidate_pack as pack
import regime_artifact_bundle as regime_bundle

PRESET_PATH = Path("config/factor_candidate_harness_presets.json")
PROFILE_DIR = Path("support/examples/factor_candidate_profiles")
EXAMPLE_PACKS_DIR = Path("support/examples/factor_candidate_packs")
NAMING_CONTRACT_VERSION = "factor-artifact-naming/v1"
REQUIRED_CANDIDATE_PACK_FILES = (
    "factor_expression.json",
    "factor_eval_grid_summary.json",
    "transfer_score.json",
)
PACK_MANIFEST_FILE = "pack_manifest.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _load_presets(repo_root: Path) -> list[dict[str, Any]]:
    return _load_json(repo_root / PRESET_PATH).get("candidates", [])


def _artifact_path(path: str | Path, repo_root: Path) -> Path:
    artifact_path = Path(path).expanduser()
    if artifact_path.is_absolute():
        return artifact_path
    return (repo_root / artifact_path).resolve()


def _artifact_ref(path: str | Path, repo_root: Path | None = None) -> str:
    artifact_path = Path(path).expanduser()
    if artifact_path.is_absolute():
        if repo_root is not None:
            repo_root = repo_root.resolve()
            try:
                return artifact_path.resolve().relative_to(repo_root).as_posix()
            except ValueError:
                pass
        return artifact_path.name
    return artifact_path.as_posix()


def _load_profiles(repo_root: Path) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for path in sorted((repo_root / PROFILE_DIR).glob("*.json")):
        payload = _load_json(path)
        payload["_source_path"] = str(path)
        payload["_source_stem"] = path.stem
        profiles.append(payload)
    return profiles


def _resolve_profile(repo_root: Path, selector: str | None) -> dict[str, Any] | None:
    if not selector:
        return None
    wanted = _normalized(selector)
    for profile in _load_profiles(repo_root):
        if wanted in {
            _normalized(profile["profile_id"]),
            _normalized(profile.get("display_name", "")),
            _normalized(profile.get("_source_stem", "")),
        }:
            return profile
    raise ValueError(f"unknown factor candidate profile '{selector}'")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            isinstance(value, dict)
            and isinstance(merged.get(key), dict)
            and key not in {"cross_market_metrics"}
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _selected_profile_surface(profile: dict[str, Any] | None) -> dict[str, Any] | None:
    if not profile:
        return None
    return {
        "profile_id": profile["profile_id"],
        "selector": profile.get("_source_stem", profile["profile_id"]),
        "display_name": profile["display_name"],
        "opt_in_only": profile.get("opt_in_only", False),
        "summary": profile.get("summary", ""),
    }


def _freqtrade_zip_validation_reason(path: Path) -> str | None:
    if not path.exists():
        return f"missing_artifact:{path}"
    try:
        with zipfile.ZipFile(path) as archive:
            corrupt_member = archive.testzip()
    except zipfile.BadZipFile as exc:
        return f"invalid_artifact:{path}:{exc}"
    if corrupt_member:
        return f"invalid_artifact:{path}:crc_failed:{corrupt_member}"
    return None


def _candidate_pack_validation_reason(path: Path) -> str | None:
    if not path.exists():
        return f"missing_artifact:{path}"
    if not path.is_dir():
        return f"invalid_artifact:{path}:not_directory"
    missing = [
        name
        for name in (*REQUIRED_CANDIDATE_PACK_FILES, PACK_MANIFEST_FILE)
        if not (path / name).exists()
    ]
    if missing:
        return f"invalid_artifact:{path}:missing_files:{','.join(missing)}"
    try:
        for name in REQUIRED_CANDIDATE_PACK_FILES:
            _load_json(path / name)
        manifest = _load_json(path / PACK_MANIFEST_FILE)
        if manifest.get("schema_version") != "factor-candidate-pack-manifest/v1":
            raise ValueError("pack manifest schema_version mismatch")
        if manifest.get("artifact_family") != "factor_candidate_pack":
            raise ValueError("pack manifest artifact_family mismatch")
        if manifest.get("artifact_files") != list(REQUIRED_CANDIDATE_PACK_FILES):
            raise ValueError("pack manifest artifact_files mismatch")
    except Exception as exc:
        return f"invalid_artifact:{path}:{exc}"
    return None


def _artifact_kind(candidate: dict[str, Any]) -> str:
    artifact_source = candidate.get("artifact_source", {})
    if artifact_source.get("candidate_pack_dir"):
        return "candidate_pack_dir"
    if artifact_source.get("freqtrade_backtest_zip"):
        return "freqtrade_backtest_zip"
    if artifact_source.get("strategy_library_json"):
        return "strategy_library_json"
    if artifact_source.get("regime_benchmark_jsons") or candidate.get(
        "reusable_input_kind"
    ) == "regime_benchmark_json":
        return "regime_benchmark_json"
    if candidate.get("promotion_state") == "regime_only":
        return "regime_gate_placeholder"
    return "candidate_placeholder"


def _artifact_plan(candidate: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    artifact_source = candidate.get("artifact_source", {})
    artifact_kind = _artifact_kind(candidate)
    explicit_reason = candidate.get("pack_readiness_reason")
    if explicit_reason:
        return {
            "artifact_kind": artifact_kind,
            "artifact_ready": False,
            "build_mode": None,
            "pack_build_reason": explicit_reason,
            "evidence_status": "deferred",
            "curation_decision": "needs_named_prerequisite",
        }

    candidate_pack_dir = artifact_source.get("candidate_pack_dir")
    if candidate_pack_dir:
        pack_dir = _artifact_path(candidate_pack_dir, repo_root)
        validation_reason = _candidate_pack_validation_reason(pack_dir)
        artifact_ready = validation_reason is None
        return {
            "artifact_kind": "candidate_pack_dir",
            "artifact_ready": artifact_ready,
            "build_mode": "candidate_pack_dir" if artifact_ready else None,
            "candidate_pack_dir_path": pack_dir,
            "candidate_pack_dir_ref": _artifact_ref(candidate_pack_dir, repo_root),
            "pack_build_reason": (
                "buildable_from_repo_candidate_pack"
                if artifact_ready
                else validation_reason
            ),
            "evidence_status": "buildable" if artifact_ready else "missing_reusable_artifact",
            "curation_decision": (
                "promote_to_candidate_pack"
                if artifact_ready
                else "discard_until_reusable_artifact"
            ),
        }

    backtest_zip = artifact_source.get("freqtrade_backtest_zip")
    if backtest_zip:
        zip_path = _artifact_path(backtest_zip, repo_root)
        validation_reason = _freqtrade_zip_validation_reason(zip_path)
        artifact_ready = validation_reason is None
        return {
            "artifact_kind": "freqtrade_backtest_zip",
            "artifact_ready": artifact_ready,
            "build_mode": "freqtrade_backtest_zip" if artifact_ready else None,
            "freqtrade_backtest_zip_path": zip_path,
            "pack_build_reason": (
                "buildable_from_reusable_artifact"
                if artifact_ready
                else validation_reason
            ),
            "evidence_status": "buildable" if artifact_ready else "missing_reusable_artifact",
            "curation_decision": (
                "promote_to_candidate_pack"
                if artifact_ready
                else "discard_until_reusable_artifact"
            ),
        }

    strategy_library_json = artifact_source.get("strategy_library_json")
    if strategy_library_json:
        manifest_path = _artifact_path(strategy_library_json, repo_root)
        if not manifest_path.exists():
            return {
                "artifact_kind": "strategy_library_json",
                "artifact_ready": False,
                "build_mode": None,
                "pack_build_reason": f"missing_artifact:{manifest_path}",
                "evidence_status": "missing_reusable_artifact",
                "curation_decision": "discard_until_reusable_artifact",
            }
        try:
            manifest = _load_json(manifest_path)
            strategies = manifest.get("strategies") or []
            if not strategies:
                raise ValueError("manifest contains no strategies")
        except Exception as exc:
            return {
                "artifact_kind": "strategy_library_json",
                "artifact_ready": False,
                "build_mode": None,
                "pack_build_reason": f"invalid_artifact:{manifest_path}:{exc}",
                "evidence_status": "missing_reusable_artifact",
                "curation_decision": "discard_until_reusable_artifact",
            }
        return {
            "artifact_kind": "strategy_library_json",
            "artifact_ready": True,
            "build_mode": "strategy_library_json",
            "strategy_library_json_path": manifest_path,
            "pack_build_reason": "buildable_from_reusable_artifact",
            "evidence_status": "buildable",
            "curation_decision": "promote_to_candidate_pack",
        }

    regime_benchmark_jsons = artifact_source.get("regime_benchmark_jsons") or []
    if regime_benchmark_jsons or artifact_kind == "regime_benchmark_json":
        benchmark_paths = [_artifact_path(path, repo_root) for path in regime_benchmark_jsons]
        missing_paths = [path for path in benchmark_paths if not path.exists()]
        artifact_ready = bool(benchmark_paths) and not missing_paths
        if artifact_ready:
            pack_build_reason = "buildable_from_reusable_artifact"
            evidence_status = "buildable"
            build_mode = "regime_benchmark_json"
        elif benchmark_paths:
            pack_build_reason = "missing_artifact:" + ",".join(
                str(path) for path in missing_paths
            )
            evidence_status = "missing_reusable_artifact"
            build_mode = None
        else:
            pack_build_reason = "missing_regime_benchmark_jsons"
            evidence_status = "missing_reusable_artifact"
            build_mode = None
        return {
            "artifact_kind": "regime_benchmark_json",
            "artifact_ready": artifact_ready,
            "build_mode": build_mode,
            "regime_benchmark_paths": benchmark_paths,
            "pack_build_reason": pack_build_reason,
            "evidence_status": evidence_status,
            "curation_decision": (
                "promote_to_regime_artifact_bundle"
                if artifact_ready
                else "discard_until_reusable_artifact"
            ),
        }

    return {
        "artifact_kind": artifact_kind,
        "artifact_ready": False,
        "build_mode": None,
        "pack_build_reason": "missing_reusable_input",
        "evidence_status": "missing_reusable_artifact",
        "curation_decision": "discard_until_reusable_artifact",
    }


def _reusable_input_refs(candidate: dict[str, Any], repo_root: Path) -> list[str]:
    refs: list[str] = []
    artifact_source = candidate.get("artifact_source", {})
    candidate_pack_dir = artifact_source.get("candidate_pack_dir")
    if candidate_pack_dir:
        refs.append(_artifact_ref(candidate_pack_dir, repo_root))
    backtest_zip = artifact_source.get("freqtrade_backtest_zip")
    if backtest_zip:
        refs.append(_artifact_ref(backtest_zip, repo_root))
    strategy_library_json = artifact_source.get("strategy_library_json")
    if strategy_library_json:
        refs.append(_artifact_ref(strategy_library_json, repo_root))
    for benchmark_json in artifact_source.get("regime_benchmark_jsons", []):
        refs.append(_artifact_ref(benchmark_json, repo_root))
    strategy_source = candidate.get("strategy_source")
    if strategy_source:
        refs.append(str(strategy_source))
    return refs


def build_candidate_registry(
    repo_root: Path | str,
    profile_selector: str | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    presets = _load_presets(repo_root)
    profile = _resolve_profile(repo_root, profile_selector)
    overrides = {
        item["candidate_id"]: item
        for item in (profile or {}).get("candidate_overrides", [])
    }

    candidates: list[dict[str, Any]] = []
    buildable_count = 0
    for preset in presets:
        candidate = _deep_merge(preset, overrides.get(preset["candidate_id"], {}))
        artifact_plan = _artifact_plan(candidate, repo_root)
        if artifact_plan["artifact_ready"]:
            buildable_count += 1
        strategy_source = candidate.get("strategy_source")
        if strategy_source:
            source_path = Path(strategy_source)
            if source_path.is_absolute() and repo_root in source_path.parents:
                candidate["strategy_source"] = str(source_path.relative_to(repo_root))
        candidate["artifact_ready"] = artifact_plan["artifact_ready"]
        candidate["selected_profile_id"] = profile["profile_id"] if profile else None
        candidate["pack_build_reason"] = artifact_plan["pack_build_reason"]
        candidate["evidence_status"] = artifact_plan["evidence_status"]
        candidate["artifact_kind"] = artifact_plan["artifact_kind"]
        candidate["curation_decision"] = artifact_plan["curation_decision"]
        candidate["archive_evidence_status"] = "not_runtime_input"
        candidate["archive_refs"] = []
        candidate["reusable_input_refs"] = _reusable_input_refs(candidate, repo_root)
        candidate["naming_contract"] = {
            "version": NAMING_CONTRACT_VERSION,
            "artifact_layers": [
                "archive_reference",
                "reusable_input",
                "candidate_pack",
                "temp_state_dir",
            ],
            "state_term_scope": "runtime_or_temp_state_only",
        }
        candidates.append(candidate)

    selection_mode = "profile_opt_in" if profile else "generic_zero_config"
    selection_label = (
        f"{profile['display_name']} ({profile['profile_id']})"
        if profile
        else "Generic zero-config factor candidate registry"
    )
    return {
        "schema_version": "factor-candidate-registry/v1",
        "selected_profile": _selected_profile_surface(profile),
        "summary": {
            "naming_contract_version": NAMING_CONTRACT_VERSION,
            "selection_mode": selection_mode,
            "selection_label": selection_label,
            "candidate_count": len(candidates),
            "buildable_count": buildable_count,
        },
        "candidates": candidates,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_pack_manifest(
    candidate_dir: Path,
    *,
    candidate_id: str,
    artifact_family: str,
    artifact_files: list[str],
    source_refs: dict[str, Any] | None = None,
) -> Path:
    manifest_path = candidate_dir / PACK_MANIFEST_FILE
    _write_json(
        manifest_path,
        {
            "schema_version": "factor-candidate-pack-manifest/v1",
            "candidate_id": candidate_id,
            "artifact_family": artifact_family,
            "artifact_files": artifact_files,
            "source_refs": source_refs or {},
        },
    )
    return manifest_path


def backfill_example_pack_manifests(repo_root: Path) -> dict[str, Any]:
    packs_root = repo_root / EXAMPLE_PACKS_DIR
    written: list[str] = []
    skipped: list[dict[str, Any]] = []
    if not packs_root.exists():
        return {
            "schema_version": "factor-candidate-pack-manifest-backfill/v1",
            "summary": {"written_count": 0, "skipped_count": 0},
            "written": written,
            "skipped": skipped,
        }

    for pack_dir in sorted(path for path in packs_root.glob("*/*") if path.is_dir()):
        missing = [name for name in REQUIRED_CANDIDATE_PACK_FILES if not (pack_dir / name).exists()]
        if missing:
            skipped.append(
                {
                    "pack_dir": str(pack_dir.relative_to(repo_root)),
                    "reason": f"missing_required_files:{','.join(missing)}",
                }
            )
            continue
        manifest_path = _write_pack_manifest(
            pack_dir,
            candidate_id=pack_dir.name,
            artifact_family="factor_candidate_pack",
            artifact_files=list(REQUIRED_CANDIDATE_PACK_FILES),
            source_refs={
                "source_candidate_pack_dir": str(pack_dir.relative_to(repo_root)),
            },
        )
        written.append(str(manifest_path.relative_to(repo_root)))

    return {
        "schema_version": "factor-candidate-pack-manifest-backfill/v1",
        "summary": {
            "written_count": len(written),
            "skipped_count": len(skipped),
        },
        "written": written,
        "skipped": skipped,
    }


def _output_ref(path: Path, output_dir: Path) -> str:
    return str(path.relative_to(output_dir))


def _closed_loop_consumption_view(
    lifecycle: dict[str, Any] | None,
) -> dict[str, Any]:
    learning = (lifecycle or {}).get("learning_admission") or {}
    live_trade = (lifecycle or {}).get("live_trade") or {}
    learning_status = learning.get("status", "unknown")
    promotion_allowed = bool(live_trade.get("promotion_allowed", False))
    trade_usable = bool(live_trade.get("trade_usable", False))
    if promotion_allowed and trade_usable:
        status = "promotion_ready"
    elif learning_status == "admitted":
        status = "observation_only_learning_admitted"
    else:
        status = "inspection_only_learning_blocked"
    return {
        "closed_loop_consumption_status": status,
        "learning_blockers": learning.get("blockers") or [],
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
    }


def _candidate_list_entry(candidate: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    artifact_plan = _artifact_plan(candidate, repo_root)
    entry: dict[str, Any] = {
        "candidate_id": candidate["candidate_id"],
        "display_name": candidate.get("display_name"),
        "family": candidate.get("family"),
        "base_timeframe": candidate.get("base_timeframe"),
        "artifact_kind": artifact_plan["artifact_kind"],
        "evidence_status": artifact_plan["evidence_status"],
        "curation_decision": artifact_plan["curation_decision"],
        "reusable_input_refs": candidate.get("reusable_input_refs", []),
    }
    if artifact_plan["build_mode"] == "candidate_pack_dir":
        pack_dir = artifact_plan["candidate_pack_dir_path"]
        expression = _load_json(pack_dir / "factor_expression.json")
        eval_summary = _load_json(pack_dir / "factor_eval_grid_summary.json")
        transfer_score = _load_json(pack_dir / "transfer_score.json")
        lifecycle = eval_summary.get("factor_profitability_lifecycle") or {}
        learning = lifecycle.get("learning_admission") or {}
        legacy_missing_lifecycle = not bool(learning)
        profitability_status = transfer_score.get("profitability_status")
        expectancy = learning.get("long_run_expectancy_after_declared_friction")
        learning_status = learning.get("status", "unknown")
        freshness = "lifecycle_current"
        if legacy_missing_lifecycle:
            legacy_candidate = {
                **candidate,
                "expected_regime": candidate.get("expected_regime")
                or expression.get("expected_regime"),
                "regime_role": candidate.get("regime_role") or expression.get("regime_role"),
                "promotion_state": candidate.get("promotion_state")
                or expression.get("promotion_state"),
                "leakage_check": candidate.get("leakage_check", "unknown"),
                "provider_state": candidate.get("provider_state", "ready"),
            }
            synthesized = pack._factor_profitability_lifecycle(
                legacy_candidate,
                eval_summary.get("aggregate_metrics") or {},
            )
            lifecycle = synthesized
            synthesized_learning = synthesized["learning_admission"]
            learning_status = synthesized_learning.get("status", "unknown")
            expectancy = synthesized_learning.get(
                "long_run_expectancy_after_declared_friction"
            )
            profitability_expectancy, profitability_blockers = (
                pack._declared_friction_expectancy(
                    eval_summary.get("aggregate_metrics") or {}
                )
            )
            if profitability_expectancy is not None and not profitability_blockers:
                profitability_status = (
                    "declared_friction_positive"
                    if profitability_expectancy > 0.0
                    else "declared_friction_non_positive"
                )
            elif profitability_expectancy is not None:
                profitability_status = "declared_friction_missing"
            else:
                profitability_status = "declared_friction_missing"
            freshness = "legacy_candidate_pack_synthesized_lifecycle"
        consumption_view = _closed_loop_consumption_view(lifecycle)
        entry.update(
            {
                "aggregate_trade_count": eval_summary["trade_density_summary"][
                    "aggregate_trade_count"
                ],
                "aggregate_label": eval_summary["trade_density_summary"][
                    "aggregate_label"
                ],
                "learning_admission_status": learning_status,
                "long_run_expectancy_after_declared_friction": expectancy,
                "transfer_status": transfer_score["status"],
                "profitability_status": profitability_status,
                "surface_freshness": freshness,
                **consumption_view,
            }
        )
    return entry


def list_buildable_candidates(
    *,
    repo_root: Path,
    candidates: list[dict[str, Any]],
    include_legacy: bool = False,
) -> dict[str, Any]:
    all_buildable = [
        _candidate_list_entry(candidate, repo_root)
        for candidate in candidates
        if candidate["artifact_ready"]
    ]
    buildable = [
        candidate
        for candidate in all_buildable
        if include_legacy
        or candidate.get("surface_freshness") != "legacy_candidate_pack_synthesized_lifecycle"
    ]
    legacy_excluded_count = len(all_buildable) - len(buildable)
    promotion_ready_count = sum(
        1
        for candidate in buildable
        if candidate.get("closed_loop_consumption_status") == "promotion_ready"
    )
    trade_usable_count = sum(1 for candidate in buildable if candidate.get("trade_usable"))
    inspection_only_count = sum(
        1
        for candidate in buildable
        if str(candidate.get("closed_loop_consumption_status", "")).startswith("inspection_only")
    )
    return {
        "schema_version": "factor-candidate-buildable-list/v1",
        "summary": {
            "buildable_count": len(buildable),
            "candidate_count": len(candidates),
            "legacy_excluded_count": legacy_excluded_count,
            "promotion_ready_count": promotion_ready_count,
            "trade_usable_count": trade_usable_count,
            "inspection_only_count": inspection_only_count,
        },
        "buildable_candidates": buildable,
    }


def verify_repo_native_pack_contracts(
    *,
    repo_root: Path,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    registered_pack_dirs: dict[str, list[str]] = {}
    for candidate in candidates:
        artifact_source = candidate.get("artifact_source", {})
        candidate_pack_dir = artifact_source.get("candidate_pack_dir")
        if not candidate_pack_dir:
            continue
        pack_ref = _artifact_ref(candidate_pack_dir, repo_root)
        registered_pack_dirs.setdefault(pack_ref, []).append(candidate["candidate_id"])

    packs: list[dict[str, Any]] = []
    registered_count = 0
    invalid_count = 0
    example_root = repo_root / EXAMPLE_PACKS_DIR
    for pack_dir in sorted(example_root.glob("*/*")):
        if not pack_dir.is_dir():
            continue
        pack_ref = _artifact_ref(pack_dir.relative_to(repo_root))
        registered_candidate_ids = sorted(registered_pack_dirs.get(pack_ref, []))
        reason = _candidate_pack_validation_reason(pack_dir)
        contract_status = "valid" if reason is None else "invalid"
        registration_status = (
            "registered" if registered_candidate_ids else "unregistered"
        )
        if registered_candidate_ids:
            registered_count += 1
        if reason is not None:
            invalid_count += 1
        packs.append(
            {
                "family_dir": str(pack_dir.parent.relative_to(example_root)),
                "candidate_id": pack_dir.name,
                "pack_dir": pack_ref,
                "registration_status": registration_status,
                "registered_candidate_ids": registered_candidate_ids,
                "contract_status": contract_status,
                "reason": reason or "ok",
            }
        )

    return {
        "schema_version": "factor-candidate-pack-contract-audit/v1",
        "summary": {
            "pack_dir_count": len(packs),
            "registered_count": registered_count,
            "unregistered_count": len(packs) - registered_count,
            "invalid_count": invalid_count,
        },
        "packs": packs,
    }


def _print_human_buildable_list(payload: dict[str, Any]) -> None:
    print(
        (
            "buildable_count={buildable_count} candidate_count={candidate_count} "
            "promotion_ready_count={promotion_ready_count} trade_usable_count={trade_usable_count} "
            "inspection_only_count={inspection_only_count} "
            "legacy_excluded_count={legacy_excluded_count}"
        ).format(
            **payload["summary"]
        )
    )
    if payload["summary"].get("legacy_excluded_count", 0):
        print(
            "hint=use --include-legacy-buildable to inspect legacy synthesized lifecycle packs"
        )
    for candidate in payload["buildable_candidates"]:
        print(
            "{candidate_id}\t{aggregate_trade_count}\t{aggregate_label}\t{learning_status}\t{consumption_status}\t{expectancy}\t{transfer_status}\t{reusable_ref}".format(
                candidate_id=candidate["candidate_id"],
                aggregate_trade_count=candidate.get("aggregate_trade_count", "n/a"),
                aggregate_label=candidate.get("aggregate_label", "n/a"),
                learning_status=candidate.get("learning_admission_status", "n/a"),
                consumption_status=candidate.get("closed_loop_consumption_status", "n/a"),
                expectancy=candidate.get(
                    "long_run_expectancy_after_declared_friction", "n/a"
                ),
                transfer_status=candidate.get("transfer_status", "n/a"),
                reusable_ref=(candidate.get("reusable_input_refs") or [""])[0],
            )
        )


def _print_human_pack_contract_audit(payload: dict[str, Any]) -> None:
    print(
        (
            "pack_dir_count={pack_dir_count} registered_count={registered_count} "
            "unregistered_count={unregistered_count} invalid_count={invalid_count}"
        ).format(**payload["summary"])
    )
    for pack in payload["packs"]:
        print(
            "{candidate_id}\t{registration_status}\t{contract_status}\t{reason}\t{pack_dir}".format(
                candidate_id=pack["candidate_id"],
                registration_status=pack["registration_status"],
                contract_status=pack["contract_status"],
                reason=pack["reason"],
                pack_dir=pack["pack_dir"],
            )
        )


def write_candidate_specs(output_dir: Path, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spec_entries: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        spec_payload = {
            key: value
            for key, value in candidate.items()
            if key
            not in {
                "artifact_ready",
                "selected_profile_id",
            }
        }
        spec_path = output_dir / "specs" / f"{candidate_id}.json"
        _write_json(spec_path, spec_payload)
        spec_entries.append(
            {
                "candidate_id": candidate_id,
                "strategy_name": candidate.get("strategy_name"),
                "spec_path": _output_ref(spec_path, output_dir),
            }
        )
    return spec_entries


def build_candidate_packs(
    *,
    repo_root: Path,
    output_dir: Path,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    built: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for candidate in candidates:
        artifact_plan = _artifact_plan(candidate, repo_root)
        if not artifact_plan["artifact_ready"]:
            skipped.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "reason": artifact_plan["pack_build_reason"],
                }
            )
            continue
        candidate_dir = output_dir / "packs" / candidate["candidate_id"]
        candidate_dir.mkdir(parents=True, exist_ok=True)
        if artifact_plan["build_mode"] == "candidate_pack_dir":
            pack_dir = artifact_plan["candidate_pack_dir_path"]
            for name in REQUIRED_CANDIDATE_PACK_FILES:
                shutil.copy2(pack_dir / name, candidate_dir / name)
            manifest_path = _write_pack_manifest(
                candidate_dir,
                candidate_id=candidate["candidate_id"],
                artifact_family="factor_candidate_pack",
                artifact_files=list(REQUIRED_CANDIDATE_PACK_FILES),
                source_refs={
                    "source_candidate_pack_dir": artifact_plan["candidate_pack_dir_ref"],
                },
            )
            eval_summary = _load_json(candidate_dir / "factor_eval_grid_summary.json")
            transfer_score = _load_json(candidate_dir / "transfer_score.json")
            built.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "strategy_name": candidate.get("strategy_name"),
                    "artifact_family": "factor_candidate_pack",
                    "pack_dir": _output_ref(candidate_dir, output_dir),
                    "pack_manifest_path": _output_ref(manifest_path, output_dir),
                    "source_candidate_pack_dir": artifact_plan["candidate_pack_dir_ref"],
                    "aggregate_trade_count": eval_summary["trade_density_summary"][
                        "aggregate_trade_count"
                    ],
                    "aggregate_label": eval_summary["trade_density_summary"][
                        "aggregate_label"
                    ],
                    "transfer_status": transfer_score["status"],
                }
            )
            continue

        if artifact_plan["build_mode"] == "freqtrade_backtest_zip":
            artifact_source = candidate.get("artifact_source", {})
            zip_path = artifact_plan["freqtrade_backtest_zip_path"]
            manifest = pack.build_manifest_from_freqtrade_backtest_zip(zip_path)
            autoresearch_status_path = artifact_source.get("autoresearch_status_json")
            autoresearch_status = (
                _load_json(Path(autoresearch_status_path).expanduser())
                if autoresearch_status_path
                and Path(autoresearch_status_path).expanduser().exists()
                else {}
            )
            bundle = pack.build_factor_candidate_pack(
                manifest=manifest,
                strategy_name=candidate.get("strategy_name"),
                candidate_spec=candidate,
                autoresearch_status=autoresearch_status,
            )
            for name, payload in bundle.items():
                _write_json(candidate_dir / f"{name}.json", payload)
            manifest_path = _write_pack_manifest(
                candidate_dir,
                candidate_id=candidate["candidate_id"],
                artifact_family="factor_candidate_pack",
                artifact_files=[f"{name}.json" for name in bundle],
                source_refs={
                    "source_backtest_zip": _artifact_ref(zip_path, repo_root)
                },
            )
            built.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "strategy_name": candidate.get("strategy_name"),
                    "artifact_family": "factor_candidate_pack",
                    "pack_dir": _output_ref(candidate_dir, output_dir),
                    "pack_manifest_path": _output_ref(manifest_path, output_dir),
                    "source_backtest_zip": _artifact_ref(zip_path, repo_root),
                    "aggregate_trade_count": bundle["factor_eval_grid_summary"][
                        "trade_density_summary"
                    ]["aggregate_trade_count"],
                    "aggregate_label": bundle["factor_eval_grid_summary"][
                        "trade_density_summary"
                    ]["aggregate_label"],
                    "learning_admission_status": bundle["factor_eval_grid_summary"][
                        "factor_profitability_lifecycle"
                    ]["learning_admission"]["status"],
                    "long_run_expectancy_after_declared_friction": bundle[
                        "factor_eval_grid_summary"
                    ]["factor_profitability_lifecycle"]["learning_admission"][
                        "long_run_expectancy_after_declared_friction"
                    ],
                    "transfer_status": bundle["transfer_score"]["status"],
                    "profitability_status": bundle["transfer_score"].get(
                        "profitability_status"
                    ),
                }
            )
            continue

        if artifact_plan["build_mode"] == "strategy_library_json":
            source_manifest_path = artifact_plan["strategy_library_json_path"]
            manifest = _load_json(source_manifest_path)
            artifact_source = candidate.get("artifact_source", {})
            autoresearch_status_path = artifact_source.get("autoresearch_status_json")
            autoresearch_status = (
                _load_json(Path(autoresearch_status_path).expanduser())
                if autoresearch_status_path
                and Path(autoresearch_status_path).expanduser().exists()
                else {}
            )
            bundle = pack.build_factor_candidate_pack(
                manifest=manifest,
                strategy_name=candidate.get("strategy_name"),
                candidate_spec=candidate,
                autoresearch_status=autoresearch_status,
            )
            for name, payload in bundle.items():
                _write_json(candidate_dir / f"{name}.json", payload)
            manifest_path = _write_pack_manifest(
                candidate_dir,
                candidate_id=candidate["candidate_id"],
                artifact_family="factor_candidate_pack",
                artifact_files=[f"{name}.json" for name in bundle],
                source_refs={
                    "source_strategy_library_json": _artifact_ref(
                        source_manifest_path, repo_root
                    )
                },
            )
            built.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "strategy_name": candidate.get("strategy_name"),
                    "artifact_family": "factor_candidate_pack",
                    "pack_dir": _output_ref(candidate_dir, output_dir),
                    "pack_manifest_path": _output_ref(manifest_path, output_dir),
                    "source_strategy_library_json": _artifact_ref(
                        source_manifest_path, repo_root
                    ),
                    "aggregate_trade_count": bundle["factor_eval_grid_summary"][
                        "trade_density_summary"
                    ]["aggregate_trade_count"],
                    "aggregate_label": bundle["factor_eval_grid_summary"][
                        "trade_density_summary"
                    ]["aggregate_label"],
                    "learning_admission_status": bundle["factor_eval_grid_summary"][
                        "factor_profitability_lifecycle"
                    ]["learning_admission"]["status"],
                    "long_run_expectancy_after_declared_friction": bundle[
                        "factor_eval_grid_summary"
                    ]["factor_profitability_lifecycle"]["learning_admission"][
                        "long_run_expectancy_after_declared_friction"
                    ],
                    "transfer_status": bundle["transfer_score"]["status"],
                    "profitability_status": bundle["transfer_score"].get(
                        "profitability_status"
                    ),
                }
            )
            continue

        if artifact_plan["build_mode"] == "regime_benchmark_json":
            benchmarks = [
                _load_json(path) for path in artifact_plan["regime_benchmark_paths"]
            ]
            bundle = regime_bundle.build_regime_artifact_bundle(
                benchmarks=benchmarks,
                candidate_id=candidate["candidate_id"],
                display_name=candidate["display_name"],
            )
            for name, payload in bundle.items():
                _write_json(candidate_dir / f"{name}.json", payload)
            manifest_path = _write_pack_manifest(
                candidate_dir,
                candidate_id=candidate["candidate_id"],
                artifact_family="regime_artifact_bundle",
                artifact_files=[f"{name}.json" for name in bundle],
                source_refs={
                    "source_benchmark_paths": [
                        _artifact_ref(path, repo_root)
                        for path in artifact_plan["regime_benchmark_paths"]
                    ]
                },
            )
            classifier_summary = bundle["regime_classifier_summary"]
            transition_summary = bundle["transition_summary"]
            cross_market_summary = bundle["cross_market_summary"]
            built.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "strategy_name": candidate.get("strategy_name"),
                    "artifact_family": "regime_artifact_bundle",
                    "pack_dir": _output_ref(candidate_dir, output_dir),
                    "pack_manifest_path": _output_ref(manifest_path, output_dir),
                    "source_benchmark_count": len(
                        artifact_plan["regime_benchmark_paths"]
                    ),
                    "covered_markets": cross_market_summary["covered_markets"],
                    "average_eval_macro_f1": classifier_summary[
                        "average_eval_macro_f1"
                    ],
                    "best_eval_macro_f1": classifier_summary["best_eval_macro_f1"],
                    "best_transition_f1": transition_summary["best_transition_f1"],
                }
            )
            continue

        skipped.append(
            {
                "candidate_id": candidate["candidate_id"],
                "reason": f"unsupported_build_mode:{artifact_plan['build_mode']}",
            }
        )

    return {
        "schema_version": "factor-candidate-pack-index/v1",
        "summary": {
            "built_count": len(built),
            "skipped_count": len(skipped),
        },
        "built_candidates": built,
        "skipped_candidates": skipped,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve generic and opt-in factor candidate specs into explicit candidate-pack artifacts."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repo root containing config/ and support/examples/factor_candidate_profiles/",
    )
    parser.add_argument(
        "--profile",
        help="Optional factor candidate profile selector for personal opt-in evidence lanes.",
    )
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--build-packs",
        action="store_true",
        help="Build candidate pack artifacts for entries with reusable evidence artifacts.",
    )
    parser.add_argument(
        "--list-buildable",
        action="store_true",
        help="Print the repo-local buildable candidate packs without reading historical board docs.",
    )
    parser.add_argument(
        "--include-legacy-buildable",
        action="store_true",
        help="Include legacy candidate-pack surfaces that require synthesized lifecycle readback.",
    )
    parser.add_argument(
        "--backfill-pack-manifests",
        action="store_true",
        help="Write pack_manifest.json into repo-native example candidate-pack directories.",
    )
    parser.add_argument(
        "--verify-pack-contracts",
        action="store_true",
        help="Audit repo-native example candidate-pack directories for manifest/member drift and registration status.",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "human"],
        default="json",
        help="Output format for read-only audit/listing modes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if args.backfill_pack_manifests:
        payload = backfill_example_pack_manifests(repo_root)
        if args.output_format == "human":
            print(
                "written_count={written_count} skipped_count={skipped_count}".format(
                    **payload["summary"]
                )
            )
            for item in payload["written"]:
                print(item)
        else:
            print(json.dumps(payload, indent=2))
        return 0
    registry = build_candidate_registry(repo_root=repo_root, profile_selector=args.profile)
    if args.verify_pack_contracts and not args.output_dir:
        payload = verify_repo_native_pack_contracts(
            repo_root=repo_root,
            candidates=registry["candidates"],
        )
        if args.output_format == "human":
            _print_human_pack_contract_audit(payload)
        else:
            print(json.dumps(payload, indent=2))
        return 0
    if args.list_buildable and not args.output_dir:
        buildable_payload = list_buildable_candidates(
            repo_root=repo_root,
            candidates=registry["candidates"],
            include_legacy=args.include_legacy_buildable,
        )
        if args.output_format == "human":
            _print_human_buildable_list(buildable_payload)
        else:
            print(json.dumps(buildable_payload, indent=2))
        return 0

    if not args.output_dir:
        raise SystemExit("--output-dir is required unless --list-buildable is used")

    output_dir = Path(args.output_dir).resolve()
    spec_entries = write_candidate_specs(output_dir, registry["candidates"])
    _write_json(output_dir / "candidate_registry.json", registry)
    _write_json(
        output_dir / "candidate_spec_index.json",
        {
            "schema_version": "factor-candidate-spec-index/v1",
            "specs": spec_entries,
        },
    )

    pack_index = {
        "schema_version": "factor-candidate-pack-index/v1",
        "summary": {
            "built_count": 0,
            "skipped_count": len(registry["candidates"]),
        },
        "built_candidates": [],
        "skipped_candidates": [
            {
                "candidate_id": candidate["candidate_id"],
                "reason": "pack_build_not_requested",
            }
            for candidate in registry["candidates"]
        ],
    }
    if args.build_packs:
        pack_index = build_candidate_packs(
            repo_root=repo_root,
            output_dir=output_dir,
            candidates=registry["candidates"],
        )
    _write_json(output_dir / "candidate_pack_index.json", pack_index)
    print(
        json.dumps(
            {
                "ok": True,
                "selection_mode": registry["summary"]["selection_mode"],
                "candidate_count": registry["summary"]["candidate_count"],
                "buildable_count": registry["summary"]["buildable_count"],
                "built_pack_count": pack_index["summary"]["built_count"],
                "output_dir": str(output_dir),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
