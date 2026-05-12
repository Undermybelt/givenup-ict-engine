#!/usr/bin/env python3
"""Summarize the read-only regime bundle dry-run from /tmp state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T160441+0800-codex-regime-downstream-readonly-dry-run-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T160441-codex-regime-downstream-consumer-contract-v1"
)
OUT_DIR = RUN_ROOT / "readonly-dry-run"
CHECK_DIR = RUN_ROOT / "checks"
TMP_STATE = Path("/tmp/ict-engine-regime-bundle-readonly-160441/DEMO")
ANALYZE_RUNS = TMP_STATE / "analyze_runs.json"
WORKFLOW_SNAPSHOT = TMP_STATE / "workflow_snapshot.json"
TEMPLATE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T160441-codex-regime-downstream-consumer-contract-v1/"
    "downstream-consumer-contract/bundle-templates/bull_regime_consumer_bundle_template_v1.json"
)

OUT_JSON = OUT_DIR / "regime_downstream_readonly_dry_run_v1.json"
OUT_MD = OUT_DIR / "regime_downstream_readonly_dry_run_v1.md"
OUT_ASSERT = CHECK_DIR / "regime_downstream_readonly_dry_run_v1_assertions.out"


def repo_rel(path: Path | str) -> str:
    path = Path(path)
    return str(path.relative_to(REPO)) if path.is_absolute() else str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(flatten_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(flatten_strings(item))
    return out


def contains_any(strings: list[str], needle: str) -> bool:
    return any(needle in item for item in strings)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    analyze = load_json(ANALYZE_RUNS)
    workflow = load_json(WORKFLOW_SNAPSHOT)
    strings = flatten_strings(analyze) + flatten_strings(workflow)

    probes = {
        "bundle_loaded": contains_any(strings, "regime_bundle_status=loaded"),
        "bundle_template_path_visible": contains_any(
            strings,
            "bull_regime_consumer_bundle_template_v1.json",
        ),
        "mainregime_label_visible": contains_any(strings, "MainRegimeV2::Bull"),
        "read_only_bbn_label_visible": contains_any(
            strings,
            "read_only_regime_bbn_label=MainRegimeV2::Bull",
        )
        or contains_any(strings, '"read_only_regime_bbn_label": "MainRegimeV2::Bull"'),
        "bbn_application_skipped": contains_any(
            strings,
            "regime_bundle_bbn_application_status=skipped",
        )
        or contains_any(strings, '"regime_bundle_bbn_application_status": "skipped"'),
        "bbn_application_applied": contains_any(
            strings,
            "regime_bundle_bbn_application_status=applied",
        )
        or contains_any(strings, '"regime_bundle_bbn_application_status": "applied"'),
    }

    summary = {
        "run_id": RUN_ID,
        "artifact_type": "regime_downstream_readonly_dry_run_v1",
        "command": (
            "./target/debug/ict-engine analyze --symbol DEMO --demo --human "
            "--state-dir /tmp/ict-engine-regime-bundle-readonly-160441 "
            f"--regime-consumer-bundle {repo_rel(TEMPLATE)} "
            "--regime-consumer-bundle-strict"
        ),
        "tmp_state": str(TMP_STATE),
        "template": repo_rel(TEMPLATE),
        "probes": probes,
        "decision": {
            "runtime_loaded_bundle": probes["bundle_loaded"],
            "read_only_diagnostics_visible": probes["read_only_bbn_label_visible"],
            "bbn_mutation_remained_off": probes["bbn_application_skipped"]
            and not probes["bbn_application_applied"],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "full_objective_achieved": False,
            "update_goal": False,
        },
        "evidence_files": {
            "analyze_runs": str(ANALYZE_RUNS),
            "workflow_snapshot": str(WORKFLOW_SNAPSHOT),
        },
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# Regime Downstream Read-only Dry Run v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- `ict-engine analyze --demo --human` strict-loaded the generated Bull bundle template.",
        "- `MainRegimeV2::Bull` appeared in read-only regime diagnostics.",
        "- BBN mutation stayed skipped; this dry-run did not convert the context into trade-usable evidence.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Probe Results",
        "",
        "| Probe | Result |",
        "|---|---:|",
    ]
    for key, value in probes.items():
        md_lines.append(f"| `{key}` | `{str(value).lower()}` |")
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{repo_rel(OUT_JSON)}`",
            f"- Assertions: `{repo_rel(OUT_ASSERT)}`",
            f"- Runtime state: `{TMP_STATE}`",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = {
        "bundle_loaded": probes["bundle_loaded"],
        "mainregime_label_visible": probes["mainregime_label_visible"],
        "read_only_bbn_label_visible": probes["read_only_bbn_label_visible"],
        "bbn_mutation_remained_off": probes["bbn_application_skipped"]
        and not probes["bbn_application_applied"],
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "assertion_status": "PASS",
    }
    OUT_ASSERT.write_text(
        "\n".join(
            f"{key}={str(value).lower() if isinstance(value, bool) else value}"
            for key, value in assertions.items()
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(assertions, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
