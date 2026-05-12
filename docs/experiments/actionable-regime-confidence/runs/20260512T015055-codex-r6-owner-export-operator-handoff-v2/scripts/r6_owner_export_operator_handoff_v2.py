#!/usr/bin/env python3
import csv
import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "r6-owner-export-operator-handoff-v2"
PAYLOAD = ARTIFACT_DIR / "r6_owner_export_operator_handoff_v2.json"
CHANNELS = ARTIFACT_DIR / "r6_owner_export_operator_handoff_channels_v2.csv"
CHECKLIST = ARTIFACT_DIR / "r6_owner_export_operator_delivery_checklist_v2.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    payload = json.loads(PAYLOAD.read_text())
    channels = read_csv(CHANNELS)
    checklist = read_csv(CHECKLIST)

    assert payload["gate_result"] == "r6_owner_export_operator_handoff_v2=operator_packet_ready_no_request_submitted_no_controls_acquired"
    assert payload["current_cursor_preserved"] is True
    assert len(payload["request_drafts"]) == 2
    assert len(channels) == 4
    assert len(checklist) == 12
    assert payload["required_delivery"]["minimum_controls"]["required_cells"] == 17
    assert payload["required_delivery"]["minimum_controls"]["required_support_per_cell"] == 73
    assert payload["required_delivery"]["minimum_controls"]["current_source_owned_normal_controls"] == 0
    assert payload["owner_vendor_request_submitted"] is False
    assert payload["ticket_or_export_identifier_received"] is False
    assert payload["source_owned_normal_controls_acquired"] == 0
    assert payload["flip_as_control_approved"] is False
    assert payload["accepted_rows_added"] == 0
    assert payload["new_confidence_gate"] is False
    assert payload["canonical_merge_allowed"] is False
    assert payload["downstream_promotion_rerun_allowed"] is False
    assert payload["strict_full_objective_achieved"] is False
    assert payload["update_goal"] is False
    assert payload["runtime_code_changed"] is False
    assert payload["shared_intake_mutated"] is False
    assert payload["r3_r5_r6_roots_mutated"] is False
    assert payload["thresholds_relaxed"] is False
    assert payload["raw_data_committed"] is False
    assert payload["external_contact_submitted"] is False
    assert payload["trade_usable"] is False
    assert all(row["submitted_by_this_packet"] == "false" for row in channels)
    assert any(row["artifact_or_field"] == "licensed_export_reference" and row["current_status"] == "missing" for row in checklist)
    assert any(row["artifact_or_field"] == "matched_negative_normal_activity_rows.csv" and row["current_status"] == "missing" for row in checklist)

    print(f"PASS run_id={payload['run_id']}")
    print(f"PASS gate_result={payload['gate_result']}")
    print("PASS request_drafts=2")
    print("PASS send_channels=4")
    print("PASS delivery_checklist=12")
    print("PASS required_cells=17")
    print("PASS required_support_per_cell=73")
    print("PASS source_owned_normal_controls_acquired=0")
    print("PASS owner_vendor_request_submitted=false")
    print("PASS ticket_or_export_identifier_received=false")
    print("PASS flip_as_control_approved=false")
    print("PASS canonical_merge_allowed=false")
    print("PASS downstream_promotion_rerun_allowed=false")
    print("PASS strict_full_objective_achieved=false")
    print("PASS update_goal=false")
    print("PASS raw_data_committed=false")
    print("PASS external_contact_submitted=false")
    print("PASS trade_usable=false")


if __name__ == "__main__":
    main()
