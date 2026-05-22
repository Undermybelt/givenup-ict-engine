# ICT Engine Script Guide

This file classifies `support/scripts/**` so consumers and contributors can tell
stable helpers from research or local-operator utilities. It is descriptive
governance only; no script was moved or promoted by this document.

## Public Smoke And CI Helpers

| Path | Stability | Safe default | Verification |
|---|---|---|---|
| `support/scripts/smoke_acceptance.sh` | stable first-run smoke | yes, writes under `/tmp` by default | `bash -n support/scripts/smoke_acceptance.sh`; run script |
| `support/scripts/ci/check_docs_runtime_isolation.py` | CI guard | yes, read-only | CI / direct Python run |
| `support/scripts/help_audit.py` | audit helper | yes, read-only cargo help probes | `python3 support/scripts/help_audit.py` |
| `support/scripts/done_definition_audit.py` | audit helper | yes, lightweight read-only checks by default | `python3 support/scripts/done_definition_audit.py` |
| `support/scripts/release_readiness_audit.py` | audit helper | yes, read-only local checks; remote readback opt-in | `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v` |
| `support/scripts/factor_claim_terminalization_audit.py` | audit helper | yes, read-only `/tmp` claim scanner; `--compact` emits a token-friendly attention summary | `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v` |
| `support/scripts/check_factor_truth_map.py` | docs guard | yes, read-only | `python3 support/scripts/check_factor_truth_map.py` |
| `support/scripts/check_script_manifest.py` | docs guard | yes, read-only | `python3 support/scripts/check_script_manifest.py` |
| `support/scripts/script_manifest.json` | machine-readable manifest | yes, read-only data | checked by `check_script_manifest.py` |

## Public Wrappers And Read-Only Utilities

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/search_local.py` | public wrapper | yes, shows help unless `--run` is passed | Refuses execution without a ready cleaned-data root |
| `support/scripts/search_cluster.py` | public wrapper | yes, shows help unless `--run` is passed | Refuses execution without a ready cleaned-data root |
| `support/scripts/evaluate_bottleneck.py` | public wrapper | yes, shows help unless `--run` is passed | Refuses execution without a ready cleaned-data root |
| `support/scripts/research_verdict.py` | read-only utility | yes, requires explicit paths | Emits compact JSON from result/state directories |
| `support/scripts/research/market_data_resolver.py` | read-only adoption utility | yes, requires explicit output path | Resolves generic zero-config market data lanes and optional profile selectors |
| `support/scripts/research/external_history_adoption.py` | adoption utility | yes, requires explicit input/output paths | Emits zero-config default commands plus opt-in profile reuse commands |
| `support/scripts/research/factor_candidate_resolver.py` | adoption utility | yes, requires explicit output path for writes | Lists/builds explicit factor candidate packs without reading board docs |

## Active External Bridge

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/auto_quant_external/pandas_path_ranker_trainer.py` | active bridge contract | requires explicit input/output paths | External path-ranker training/scoring helper |
| `support/scripts/auto_quant_external/path_ranker_integration.py` | active bridge contract | requires explicit state/artifact paths | Rust/Python ranker integration helper |
| `support/scripts/auto_quant_external/structural_feedback_replay_harness.py` | active bridge contract | requires explicit state paths | Replay and feedback validation helper |
| `support/scripts/auto_quant_external/tests/**` | test support | yes | Prefer `python3 -m unittest ...` if `pytest` is absent |

## Provider And Operator Bridges

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/ibkr_bridge/**` | opt-in operator bridge | no, requires local runtime/account context | Do not run against live broker context without explicit operator intent |
| `support/scripts/auto_quant_external/fetch_external.py` | opt-in data fetch bridge | network/provider dependent | Use only with explicit provider/source intent |
| `support/scripts/research/pandas_datareader_hotplug.py` | optional hotplug bridge | dependency/network dependent | Not required for zero-config Rust CLI use |

## Research Helpers

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/research/**` | active research/prototype helpers | varies by script | Inspect arguments and expected inputs before running |
| `support/scripts/auto_quant_external/pandas_*.py` | research/backtest prototypes unless named above | varies by script | Treat outputs as research evidence, not product gates |
| `support/scripts/*bbn*.py`, `support/scripts/*tomac*.py`, `support/scripts/btc_ledger_*.py` | legacy/research utilities | varies by script | Use only when a plan references the exact script |

## Archived Scripts

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/archive/**` | archived | no product dependency | Do not build new flows on archived scripts |
| `support/scripts/__pycache__/**` | generated cache | not a script surface | Do not cite as evidence |

## Rules For New Scripts

- Put public, user-facing smoke or CI helpers at `support/scripts/`.
- Put active external trainer/bridge helpers under
  `support/scripts/auto_quant_external/`.
- Put exploratory analysis under `support/scripts/research/`.
- Put retired experiments under `support/scripts/archive/`.
- Default to help/read-only behavior unless the command name and arguments make
  writes or network access explicit.
- Accept explicit input/output paths; do not assume maintainer-local paths.
- Write generated state under `/tmp` by default.
- Add a test command or smoke command to this file when adding a new public
  helper.
- Add or update `support/scripts/script_manifest.json` and run
  `python3 support/scripts/check_script_manifest.py` when changing public script
  surfaces.
- Keep heavy compile/lint/test smoke checks opt-in behind explicit flags/env;
  public audit helpers should default to low-cost read-only probes.
