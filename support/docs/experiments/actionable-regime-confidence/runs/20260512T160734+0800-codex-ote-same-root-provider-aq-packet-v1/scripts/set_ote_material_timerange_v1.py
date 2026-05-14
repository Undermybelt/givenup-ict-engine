from __future__ import annotations

import json
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T160734+0800-codex-ote-same-root-provider-aq-packet-v1"
)
TIMERANGE = "20260101-20260512"


def main() -> int:
    paths = [
        Path(line.strip())
        for line in (RUN_ROOT / "summaries/material_paths.txt").read_text().splitlines()
        if line.strip()
    ]
    updated = 0
    for path in paths:
        package = json.loads(path.read_text())
        package["timerange"] = TIMERANGE
        package.setdefault("notes", []).append(f"timerange_repaired_for_current_2026_data={TIMERANGE}")
        path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
        updated += 1
    lines = [
        f"{'PASS' if len(paths) == 5 else 'FAIL'} materials_seen_5={len(paths)}",
        f"{'PASS' if updated == 5 else 'FAIL'} timerange_updated_5={updated}",
        f"PASS timerange={TIMERANGE}",
    ]
    (RUN_ROOT / "checks/material_timerange_assertions.out").write_text("\n".join(lines) + "\n")
    return 0 if len(paths) == 5 and updated == 5 else 2


if __name__ == "__main__":
    raise SystemExit(main())
