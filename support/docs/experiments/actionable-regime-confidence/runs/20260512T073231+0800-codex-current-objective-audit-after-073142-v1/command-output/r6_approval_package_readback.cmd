jq -r '.gate_result, (.assertions | to_entries[] | [.key,.value] | @tsv), (.row_counts | to_entries[] | [.key,.value] | @tsv)' /private/tmp/r6_oystacher_approval_decision_package_v1.json.valid
