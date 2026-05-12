#!/usr/bin/env python3
from pathlib import Path

repo = Path(__file__).resolve().parents[6]

required_present = [
    "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_control_source_scan_v1.json",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_control_source_scan_v1.md",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_control_sources_v1.csv",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_fetch_readback_v1.csv",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/checks/r6_oystacher_external_control_source_scan_v1_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_source_probe_v1.json",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_source_probe_v1.md",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_sources_checked_v1.csv",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_required_cells_v1.csv",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/checks/r6_oystacher_public_normal_control_source_probe_v1_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1",
    "docs/experiments/actionable-regime-confidence/runs/20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004410-codex-r6-official-route-date-fit-check-v1",
]

required_absent = [
    "/tmp/ict-engine-board-a-r6-owner-export-v1",
]

missing_present = [p for p in required_present if not (repo / p).exists()]
unexpected_present = []
for p in required_absent:
    candidate = Path(p) if p.startswith("/") else repo / p
    if candidate.exists():
        unexpected_present.append(p)

if missing_present:
    raise SystemExit(f"missing expected present paths: {missing_present}")
if unexpected_present:
    raise SystemExit(f"expected absent paths are present: {unexpected_present}")

print("r6_board_artifact_integrity_repair_v1=pass")
