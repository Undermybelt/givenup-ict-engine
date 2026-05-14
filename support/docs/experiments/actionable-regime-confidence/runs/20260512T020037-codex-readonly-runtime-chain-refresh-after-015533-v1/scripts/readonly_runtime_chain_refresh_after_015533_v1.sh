#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
state_dir="/tmp/ict-engine-board-a-readonly-runtime-20260512T020037"
run_root="$repo_root/docs/experiments/actionable-regime-confidence/runs/20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1"
cmd_root="$run_root/command-output"

mkdir -p "$cmd_root" "$state_dir"

run_cmd() {
  local name="$1"
  shift
  printf '%s\n' "$*" > "$cmd_root/$name.cmd"
  "$@" > "$cmd_root/$name.stdout.txt" 2> "$cmd_root/$name.stderr.txt"
  printf '%s\n' "$?" > "$cmd_root/$name.exit"
}

cd "$repo_root"
run_cmd provider_status_agent ./target/debug/ict-engine provider-status --agent
run_cmd provider_status_tradingview_mcp ./target/debug/ict-engine provider-status --provider tradingview_mcp --agent
run_cmd provider_status_yfinance ./target/debug/ict-engine provider-status --provider yfinance --agent
run_cmd auto_quant_status_json ./target/debug/ict-engine auto-quant-status --state-dir "$state_dir/auto-quant" --output-format json
run_cmd analyze_demo_agent ./target/debug/ict-engine analyze --symbol NQ --demo --state-dir "$state_dir" --output-format agent
run_cmd pre_bayes_status_json ./target/debug/ict-engine pre-bayes-status --symbol NQ --state-dir "$state_dir" --refresh --output-format json
run_cmd policy_training_status_json ./target/debug/ict-engine policy-training-status --symbol NQ --state-dir "$state_dir" --output-format json
run_cmd workflow_status_execution_candidate_agent ./target/debug/ict-engine workflow-status --symbol NQ --state-dir "$state_dir" --refresh --phase execution-candidate --output-format agent
run_cmd workflow_status_structural_path_bundle_agent ./target/debug/ict-engine workflow-status --symbol NQ --state-dir "$state_dir" --refresh --phase structural-recommended-path-bundle --output-format agent
run_cmd workflow_status_full_json ./target/debug/ict-engine workflow-status --symbol NQ --state-dir "$state_dir" --refresh --output-format json
run_cmd export_structural_path_ranking_target ./target/debug/ict-engine export-structural-path-ranking-target --symbol NQ --state-dir "$state_dir"
