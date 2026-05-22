#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
STATE_DIR="${STATE_DIR:-/tmp/ict-engine-smoke-acceptance-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT_DIR="${OUT_DIR:-${STATE_DIR}/smoke-output}"
SYMBOL="${SYMBOL:-DEMO}"
SMOKE_UPDATE_OUTCOME="${SMOKE_UPDATE_OUTCOME:-breakeven}"
SMOKE_UPDATE_PNL="${SMOKE_UPDATE_PNL:-0}"

resolve_for_guard() {
  local raw_path="$1"
  local candidate parent suffix parent_real

  if [[ "$raw_path" == /* ]]; then
    candidate="$raw_path"
  else
    candidate="$ROOT_DIR/$raw_path"
  fi

  parent="$candidate"
  suffix=""
  while [[ ! -d "$parent" && "$parent" != "/" ]]; do
    suffix="/$(basename "$parent")$suffix"
    parent="$(dirname "$parent")"
  done

  parent_real="$(cd "$parent" && pwd -P)"
  printf '%s%s\n' "$parent_real" "$suffix"
}

validate_state_dir() {
  local resolved_state

  if [[ "${ICT_ENGINE_ALLOW_REPO_STATE:-0}" == "1" ]]; then
    return
  fi

  resolved_state="$(resolve_for_guard "$STATE_DIR")"
  case "$resolved_state" in
    "$ROOT_DIR"|"$ROOT_DIR"/*)
      printf "smoke_acceptance: refusing repo-local STATE_DIR '%s' (resolved: %s); use /tmp/... or set ICT_ENGINE_ALLOW_REPO_STATE=1\n" \
        "$STATE_DIR" "$resolved_state" >&2
      exit 2
      ;;
  esac
}

validate_state_dir

mkdir -p "$OUT_DIR"
cd "$ROOT_DIR"

run() {
  local name="$1"
  shift

  printf '==> %s\n' "$name"
  "$@" >"$OUT_DIR/${name}.out" 2>"$OUT_DIR/${name}.err"
}

scan_private_output() {
  local pattern='/Users/|API[_-]?KEY|SECRET|TOKEN|PASSWORD'

  if command -v rg >/dev/null 2>&1; then
    rg -n -i "$pattern" "$OUT_DIR"
  else
    grep -ERIn "$pattern" "$OUT_DIR"
  fi
}

require_output_match() {
  local name="$1"
  local pattern="$2"
  local path="$OUT_DIR/${name}.out"

  if command -v rg >/dev/null 2>&1; then
    rg -q "$pattern" "$path"
  else
    grep -Eq "$pattern" "$path"
  fi
}

require_output_literal() {
  local name="$1"
  local literal="$2"
  local path="$OUT_DIR/${name}.out"

  if command -v rg >/dev/null 2>&1; then
    rg -q -F "$literal" "$path"
  else
    grep -Fq "$literal" "$path"
  fi
}

run provider_status \
  cargo run --quiet -- provider-status --compact
run workflow_empty \
  cargo run --quiet -- workflow-status --symbol "$SYMBOL" --state-dir "$STATE_DIR" --human
run analyze_demo \
  cargo run --quiet -- analyze --symbol "$SYMBOL" --demo --state-dir "$STATE_DIR" --human
run workflow_agent \
  cargo run --quiet -- workflow-status --symbol "$SYMBOL" --state-dir "$STATE_DIR" --refresh --agent
run pre_bayes_json \
  cargo run --quiet -- pre-bayes-status --symbol "$SYMBOL" --state-dir "$STATE_DIR" --refresh --output-format json
run update_demo \
  cargo run --quiet -- update --symbol "$SYMBOL" --state-dir "$STATE_DIR" --outcome "$SMOKE_UPDATE_OUTCOME" --pnl "$SMOKE_UPDATE_PNL"
run workflow_agent_after_update \
  cargo run --quiet -- workflow-status --symbol "$SYMBOL" --state-dir "$STATE_DIR" --refresh --agent
run policy_training_agent \
  cargo run --quiet -- policy-training-status --symbol "$SYMBOL" --state-dir "$STATE_DIR" --output-format agent

if scan_private_output; then
  printf 'smoke_acceptance: possible private path or secret leak in %s\n' "$OUT_DIR" >&2
  exit 1
fi

if ! require_output_match update_demo '"feedback_records_applied"[[:space:]]*:[[:space:]]*1'; then
  printf 'smoke_acceptance: update did not apply exactly one feedback record; inspect %s/update_demo.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_literal update_demo "\"realized_outcome\": \"$SMOKE_UPDATE_OUTCOME\""; then
  printf 'smoke_acceptance: update output did not preserve SMOKE_UPDATE_OUTCOME=%s; inspect %s/update_demo.out\n' \
    "$SMOKE_UPDATE_OUTCOME" "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_match workflow_agent_after_update '"source_phase"[[:space:]]*:[[:space:]]*"update"'; then
  printf 'smoke_acceptance: workflow-status after update did not report source_phase=update; inspect %s/workflow_agent_after_update.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_match policy_training_agent '"update_runs"[[:space:]]*:[[:space:]]*1'; then
  printf 'smoke_acceptance: policy-training-status did not report update_runs=1; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_match policy_training_agent '"export_ready"[[:space:]]*:[[:space:]]*true'; then
  printf 'smoke_acceptance: structural path-ranker target export was not inspectable; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_match policy_training_agent '"trainer_manifest_ready"[[:space:]]*:[[:space:]]*true'; then
  printf 'smoke_acceptance: structural path-ranker trainer manifest was not inspectable; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_match policy_training_agent '"runtime_selection_enabled"[[:space:]]*:[[:space:]]*false'; then
  printf 'smoke_acceptance: zero-config DEMO unexpectedly enabled path-ranker runtime; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_literal policy_training_agent "trainer_artifact=missing"; then
  printf 'smoke_acceptance: zero-config DEMO did not expose missing trainer artifact status; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_literal policy_training_agent "runtime_selection=disabled"; then
  printf 'smoke_acceptance: zero-config DEMO did not fail closed with runtime_selection=disabled; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi
if ! require_output_literal policy_training_agent "production_validation=0/30"; then
  printf 'smoke_acceptance: zero-config DEMO did not expose path-ranker validation shortfall; inspect %s/policy_training_agent.out\n' "$OUT_DIR" >&2
  exit 1
fi

printf 'smoke_acceptance: passed state_dir=%s output_dir=%s\n' "$STATE_DIR" "$OUT_DIR"
