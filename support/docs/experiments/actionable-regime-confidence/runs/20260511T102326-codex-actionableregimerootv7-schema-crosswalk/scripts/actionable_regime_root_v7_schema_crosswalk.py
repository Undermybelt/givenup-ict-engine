#!/usr/bin/env python3
"""Static readback for the ActionableRegimeRootV7 schema/crosswalk."""

ROOTS = [
    "BullExpansion",
    "BearExpansion",
    "ConsolidationBalance",
    "CrisisDislocation",
    "ManipulationIntegrityEvent",
]


def main() -> None:
    print("active_candidate_taxonomy=ActionableRegimeRootV7")
    print("mandatory_roots=" + ",".join(ROOTS))
    print("watchlist_root=TransitionRotation")
    print("residual=UnknownOrMixed")
    print("accepted_95_roots_added=0")
    print("accepted_direct_manipulation_rows_added=0")
    print("gate_result=blocked_actionableregimerootv7_schema_crosswalk_materialized_no_calibration")


if __name__ == "__main__":
    main()
