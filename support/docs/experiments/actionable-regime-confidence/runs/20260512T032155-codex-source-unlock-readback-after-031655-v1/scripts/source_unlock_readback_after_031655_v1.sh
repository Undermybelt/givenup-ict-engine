#!/usr/bin/env bash
set -euo pipefail

test ! -e /tmp/ict-engine-board-a-r6-owner-export-v1
test ! -e /tmp/ict-engine-native-subhour-source-label-intake
test ! -e /tmp/ict-engine-source-panel-recency-extension
test -d /tmp/ict-engine-source-label-equivalence-intake
test -f /tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv
test -f /tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json
test -d /tmp/ict-engine-direct-manipulation-row-intake
test -f /tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv
test -f /tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv
test -f /tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json
test -f /private/tmp/r6_oystacher_approval_decision_package_v1.json.valid

jq -e '
  .assertions.approval_present == false and
  .assertions.flip_controls_accepted_under_current_contract == false and
  .assertions.canonical_merge_allowed_now == false and
  .assertions.downstream_rerun_allowed_now == false and
  .assertions.strict_full_objective_achieved == false and
  .assertions.trade_usable == false and
  .assertions.update_goal == false
' /private/tmp/r6_oystacher_approval_decision_package_v1.json.valid >/dev/null

jq -e '
  .limitations[] | select(. == "daily source-label equivalence rows do not satisfy native sub-hour validation")
' /tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json >/dev/null

echo "PASS source_unlock_readback_after_031655_v1"
