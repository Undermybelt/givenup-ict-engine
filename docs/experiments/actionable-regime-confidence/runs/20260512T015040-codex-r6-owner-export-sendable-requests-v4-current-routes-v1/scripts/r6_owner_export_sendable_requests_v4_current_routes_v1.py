#!/usr/bin/env python3
"""Read-only reproduction helper for the R6 owner-export request v4 packet."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "r6-owner-export-sendable-requests-v4-current-routes-v1"
REPORT = ARTIFACT_DIR / "r6_owner_export_sendable_requests_v4_current_routes_v1.json"


def main() -> int:
    with REPORT.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    print(data["gate_result"])
    print(f"required_cells={data['required_cells']}")
    print(f"valid_source_owned_normal_controls_found={data['valid_source_owned_normal_controls_found']}")
    print(f"owner_vendor_request_submitted={data['owner_vendor_request_submitted']}")
    print(f"strict_full_objective_achieved={data['decisions']['strict_full_objective_achieved']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
