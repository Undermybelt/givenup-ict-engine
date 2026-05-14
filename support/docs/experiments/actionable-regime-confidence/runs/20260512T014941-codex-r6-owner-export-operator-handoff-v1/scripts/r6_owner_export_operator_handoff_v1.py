#!/usr/bin/env python3
import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
PACKET = RUN_ROOT / "r6-owner-export-operator-handoff-v1" / "r6_owner_export_operator_handoff_v1.json"


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    data = json.loads(PACKET.read_text())
    source = data["source_artifacts"]
    policy = data["policy_state"]
    result = data["result"]
    current_root = data["current_root_state"]

    repo_root = RUN_ROOT.parents[4]

    check("run_id", data["run_id"] == "20260512T014941-codex-r6-owner-export-operator-handoff-v1")
    check("gate_result", data["gate_result"] == "r6_owner_export_operator_handoff_v1=operator_submission_packet_ready_no_request_sent_no_controls_acquired")
    check("source_request_bundle_present", (repo_root / source["sendable_request_bundle_v3"]).is_dir())
    check("current_send_channel_preflight_present", (repo_root / source["current_send_channel_preflight_v1"]).is_dir())
    check("operator_action_queue_present", (RUN_ROOT / "r6-owner-export-operator-handoff-v1" / "r6_owner_export_operator_action_queue_v1.csv").is_file())
    check("post_arrival_drop_contract_present", (RUN_ROOT / "r6-owner-export-operator-handoff-v1" / "r6_owner_export_post_arrival_drop_contract_v1.csv").is_file())
    check("post_arrival_validation_commands_present", (RUN_ROOT / "r6-owner-export-operator-handoff-v1" / "r6_owner_export_post_arrival_validation_commands_v1.csv").is_file())
    check("required_control_cells", data["operator_handoff_summary"]["required_oystacher_control_cells"] == 17)
    check("request_drafts_listed", len(data["request_drafts"]) == 2)
    check("owner_request_not_submitted", policy["owner_or_vendor_request_submitted"] is False)
    check("no_ticket_or_export_identifier", policy["ticket_or_export_identifier_received"] is False)
    check("no_source_owned_controls", policy["source_owned_normal_controls_acquired"] == 0)
    check("flip_not_approved", policy["flip_as_control_approved"] is False)
    check("r6_owner_export_root_absent", current_root["r6_owner_export_root_present"] is False)
    check("canonical_merge_false", policy["canonical_merge_allowed"] is False)
    check("downstream_chain_rerun_false", policy["downstream_chain_rerun_allowed"] is False)
    check("strict_full_objective_false", result["strict_full_objective_achieved"] is False)
    check("update_goal_false", result["update_goal"] is False)
    check(
        "no_mutation_claims",
        result["runtime_code_changed"] is False
        and result["shared_intake_mutated"] is False
        and result["r3_root_mutated"] is False
        and result["r5_root_mutated"] is False
        and result["r6_owner_export_root_mutated"] is False
        and result["thresholds_relaxed"] is False
        and result["raw_data_committed"] is False
        and result["external_contact_submitted"] is False,
    )
    check("trade_usable_false", result["trade_usable"] is False)


if __name__ == "__main__":
    main()
