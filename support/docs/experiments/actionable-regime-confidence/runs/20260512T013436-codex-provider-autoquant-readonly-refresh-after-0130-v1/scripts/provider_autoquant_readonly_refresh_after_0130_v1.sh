#!/usr/bin/env bash
set -u

RUN_ROOT="docs/experiments/actionable-regime-confidence/runs/20260512T013436-codex-provider-autoquant-readonly-refresh-after-0130-v1"
OUT="$RUN_ROOT/command-output"
STATE_DIR="/tmp/ict-engine-board-a-provider-autoquant-readonly-refresh-20260512T013436"
AQ_STATE_DIR="/tmp/ict-engine-board-a-provider-autoquant-readonly-refresh-20260512T013436-autoquant"

mkdir -p "$OUT" "$RUN_ROOT/provider-autoquant-readonly-refresh-after-0130-v1" "$RUN_ROOT/checks"

run_cmd() {
  name="$1"
  shift
  "$@" > "$OUT/$name.out" 2> "$OUT/$name.err"
  code=$?
  printf '%s\n' "$code" > "$OUT/$name.exit"
}

run_cmd provider_status_agent ./target/debug/ict-engine provider-status --agent
run_cmd provider_status_ibkr_agent ./target/debug/ict-engine provider-status --provider ibkr --agent
run_cmd provider_status_tradingview_mcp_agent ./target/debug/ict-engine provider-status --provider tradingview_mcp --agent
run_cmd provider_status_yfinance_agent ./target/debug/ict-engine provider-status --provider yfinance --agent
run_cmd provider_status_kraken_public_agent ./target/debug/ict-engine provider-status --provider kraken_public --agent
run_cmd provider_status_kraken_cli_agent ./target/debug/ict-engine provider-status --provider kraken_cli --agent
run_cmd auto_quant_status ./target/debug/ict-engine auto-quant-status --state-dir "$AQ_STATE_DIR" --output-format json
run_cmd auto_quant_bootstrap ./target/debug/ict-engine auto-quant-bootstrap --state-dir "$AQ_STATE_DIR"
run_cmd auto_quant_status_after_bootstrap ./target/debug/ict-engine auto-quant-status --state-dir "$AQ_STATE_DIR" --output-format json
run_cmd auto_quant_prepare ./target/debug/ict-engine auto-quant-prepare --state-dir "$AQ_STATE_DIR"
run_cmd auto_quant_status_after_prepare ./target/debug/ict-engine auto-quant-status --state-dir "$AQ_STATE_DIR" --output-format json
run_cmd analyze_live_nq_yfinance ./target/debug/ict-engine analyze-live --symbol NQ --futures-symbol NQ=F --spot-symbol QQQ --options-symbol QQQ --options-volatility-proxy-symbol '^VIX' --futures-backend yfinance --aux-backend yfinance --state-dir "$STATE_DIR" --output-format json
run_cmd pre_bayes_status ./target/debug/ict-engine pre-bayes-status --symbol NQ --state-dir "$STATE_DIR" --refresh --output-format json
run_cmd policy_training_status ./target/debug/ict-engine policy-training-status --symbol NQ --state-dir "$STATE_DIR" --output-format json
run_cmd workflow_status_execution_candidate ./target/debug/ict-engine workflow-status --symbol NQ --state-dir "$STATE_DIR" --phase execution-candidate --agent
run_cmd export_structural_path_ranking_target ./target/debug/ict-engine export-structural-path-ranking-target --symbol NQ --state-dir "$STATE_DIR"
