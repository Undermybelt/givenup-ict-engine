# ICT Engine Command Output Contract

This contract records the current CLI output surface from real `--help` probes.
It is a remediation target, not a claim that every command is already
consistent.

## Output Modes

| Mode | Intended use | Contract |
|---|---|---|
| `json` | archival/debug automation | Structured, stable keys where possible |
| `compact` | low-token terminal or agent summaries | Short output, no large ledgers |
| `agent` | machine-readable agent handoff | Structured output for automation |
| `human` | operator readback | Concise terminal explanation |

Commands that support `--output-format` should document accepted values in
`--help`. Alias flags must not be combined with `--output-format`.

## Generated Matrix

Verified from `python3 support/scripts/help_audit.py` on 2026-05-22 against a
freshly built local `ict-engine` binary. The script parsed 53 subcommands from
real `--help` output: 30 full output-mode surfaces, 0 partial surfaces, and 23
commands with no output-mode flags.

| Command | `--output-format` | `--human` | `--agent` | `--compact` | Status |
|---|---:|---:|---:|---:|---|
| `analyze` | yes | yes | yes | yes | Meets contract |
| `analyze-live` | yes | yes | yes | yes | Meets contract; provider/network dependent |
| `validate-market-state` | yes | yes | yes | yes | Tested exception: human/compact supported; json/agent request fails clearly until a stable validation schema exists |
| `train` | no | no | no | no | No output-mode flags |
| `backtest` | yes | yes | yes | yes | Meets contract |
| `update` | no | no | no | no | No output-mode flags |
| `factor-research` | yes | yes | yes | yes | Meets contract |
| `factor-candidate-packs` | yes | yes | yes | yes | Meets two-mode alias contract; compact/agent map to JSON |
| `factor-candidate-admission-targets` | yes | yes | yes | yes | Meets two-mode alias contract; compact/agent map to JSON |
| `regime-confidence-assets` | yes | yes | yes | yes | Meets two-mode alias contract; compact/agent map to JSON |
| `factor-asset-closure-intake` | yes | yes | yes | yes | Meets two-mode alias contract; compact/agent map to JSON |
| `auto-quant-promote-canonical-setup` | no | no | no | no | No output-mode flags |
| `factor-mutation-status` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short mutation status summary |
| `factor-autoresearch` | no | no | no | no | No output-mode flags |
| `env` | yes | yes | yes | yes | Meets contract; machine modes preserve redacted JSON and human summarizes set/unset counts without printing values |
| `auto-quant-status` | yes | yes | yes | yes | Meets contract |
| `auto-quant-futures-cost` | yes | yes | yes | yes | Meets contract |
| `auto-quant-bootstrap` | no | no | no | no | No output-mode flags |
| `auto-quant-update` | no | no | no | no | No output-mode flags |
| `auto-quant-prepare` | no | no | no | no | No output-mode flags |
| `auto-quant-adoption-review` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short adoption review summary, including optional `sidecar_status` when `--sidecar-handoff` is supplied |
| `auto-quant-adoption-decision` | no | no | no | no | No output-mode flags |
| `factor-autoresearch-status` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short autoresearch status summary |
| `research-verdict` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short verdict summary |
| `evidence-quality-breakdown` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short evidence-quality summary |
| `factor-backtest` | yes | yes | yes | yes | Meets contract |
| `clean-futures` | no | no | no | no | No output-mode flags |
| `futures-sop` | no | no | no | no | No output-mode flags |
| `expansion-sop` | no | no | no | no | No output-mode flags |
| `market-data-harness` | yes | yes | yes | yes | Meets action-aware contract; plan/fetch machine modes preserve redacted JSON, human summarizes plan/fetch while fetch still exits nonzero on collected failures |
| `factor-pipeline-debug` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short pipeline debug summary |
| `workflow-status` | yes | yes | yes | yes | Meets contract |
| `pre-bayes-status` | yes | yes | yes | yes | Meets contract; `--agent` maps to JSON-compatible agent output |
| `policy-training-status` | yes | yes | yes | yes | Meets alias contract |
| `register-structural-path-ranking-trainer-artifact` | no | no | no | no | No output-mode flags |
| `clear-structural-path-ranking-trainer-artifact` | no | no | no | no | No output-mode flags |
| `enable-structural-path-ranking-runtime` | no | no | no | no | No output-mode flags |
| `disable-structural-path-ranking-runtime` | no | no | no | no | No output-mode flags |
| `export-structural-path-ranking-target` | yes | yes | yes | yes | Meets contract |
| `apply-structural-path-ranking-external-scores` | yes | yes | yes | yes | Meets contract |
| `provider-status` | yes | yes | yes | yes | Meets legacy-compatible contract; `--human` maps to compact and `--jsonl` remains available |
| `pre-bayes-diff` | yes | yes | yes | yes | Meets contract; compact/agent preserve redacted JSON and human prints a short diff summary |
| `artifact-status` | yes | yes | yes | yes | Meets contract |
| `artifact-lineage` | yes | yes | yes | yes | Meets contract |
| `artifact-diff` | yes | yes | yes | yes | Meets contract |
| `auto-quant-seed-evidence` | no | no | no | no | No output-mode flags |
| `auto-quant-agent-material-batch` | no | no | no | no | No output-mode flags |
| `auto-quant-agent-material-dispatch` | no | no | no | no | No output-mode flags |
| `auto-quant-agent-material-rank` | no | no | no | no | No output-mode flags |
| `auto-quant-results-import` | no | no | no | no | No output-mode flags |
| `auto-quant-consume-live-signals` | no | no | no | no | No output-mode flags |
| `auto-quant-ingest-real-trades` | no | no | no | no | No output-mode flags |
| `auto-quant-prior-init` | no | no | no | no | No output-mode flags |

## Required Behavior For New Read-Only Commands

New read-only status/export commands should support:

```text
--output-format json|compact|agent|human
--compact
--agent
--human
```

If a command intentionally does not support all modes, document the reason here
and add a test that the unsupported mode fails with a clear error.

## Known Gaps

1. The generated matrix is complete for discovered top-level subcommands and
   the current `none` surfaces are policy-classified in
   `support/scripts/help_audit.py` as an explicit expected set. CI/local audit
   should fail if an unclassified `none` command appears or if an expected item
   disappears without policy update.
2. No discovered command is partial by help-derived output-mode support.
3. `provider-status --human` intentionally maps to compact human output rather
   than the default pretty JSON catalog, preserving its existing low-token human
   guidance behavior.
