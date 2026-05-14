#!/usr/bin/env bash
set -euo pipefail

RUN_ROOT="docs/experiments/actionable-regime-confidence/runs/20260512T030206-codex-provider-autoquant-readonly-refresh-after-local-source-screens-v1"
STATE_DIR="/tmp/ict-engine-board-a-provider-refresh-20260512T030206"

mkdir -p "$RUN_ROOT/command-output"

./target/debug/ict-engine provider-status --agent \
  > "$RUN_ROOT/command-output/provider_status_agent.stdout.json" \
  2> "$RUN_ROOT/command-output/provider_status_agent.stderr.txt"
printf '%s\n' "$?" > "$RUN_ROOT/command-output/provider_status_agent.exitcode"

ICT_ENGINE_AUTO_QUANT_DIR=/Users/thrill3r/Auto-Quant \
  ./target/debug/ict-engine auto-quant-status \
  --state-dir "$STATE_DIR" \
  --output-format json \
  > "$RUN_ROOT/command-output/auto_quant_status_json.stdout.json" \
  2> "$RUN_ROOT/command-output/auto_quant_status_json.stderr.txt"
printf '%s\n' "$?" > "$RUN_ROOT/command-output/auto_quant_status_json.exitcode"
