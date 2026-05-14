from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T165122+0800-codex-ob-fvg-branch-matrix-six-provider-aq-v1"
)
TIMERANGE = "20260101-20260512"
EXPECTED_MATERIALS = 6


def main() -> int:
    rows = list(csv.DictReader((RUN_ROOT / "summaries/material_paths.csv").open()))
    material_paths = [Path(row["material_path"]) for row in rows if row.get("material_path")]
    updated = 0
    for path in material_paths:
        package = json.loads(path.read_text())
        package["timerange"] = TIMERANGE
        notes = package.setdefault("notes", [])
        note = f"timerange_repaired_for_current_2026_data={TIMERANGE}"
        if note not in notes:
            notes.append(note)
        path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
        updated += 1

    lines = [
        f"{'PASS' if len(material_paths) == EXPECTED_MATERIALS else 'FAIL'} materials_seen_6={len(material_paths)}",
        f"{'PASS' if updated == EXPECTED_MATERIALS else 'FAIL'} timerange_updated_6={updated}",
        f"PASS timerange={TIMERANGE}",
    ]
    (RUN_ROOT / "checks/material_timerange_assertions.out").write_text(
        "\n".join(lines) + "\n"
    )
    return 0 if len(material_paths) == EXPECTED_MATERIALS and updated == EXPECTED_MATERIALS else 2


if __name__ == "__main__":
    raise SystemExit(main())
