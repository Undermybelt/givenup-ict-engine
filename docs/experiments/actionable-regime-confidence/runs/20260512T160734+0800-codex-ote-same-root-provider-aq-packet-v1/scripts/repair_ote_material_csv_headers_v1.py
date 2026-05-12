from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T160734+0800-codex-ote-same-root-provider-aq-packet-v1"
)


def main() -> int:
    material_paths = [
        Path(line.strip())
        for line in (RUN_ROOT / "summaries/material_paths.txt").read_text().splitlines()
        if line.strip()
    ]
    rows = []
    failures = []
    for material_path in material_paths:
        package = json.loads(material_path.read_text())
        src = Path(package["data_path"])
        df = pd.read_csv(src)
        if "timestamp" not in df.columns:
            if "date" not in df.columns:
                failures.append(f"{src}: missing date/timestamp column")
                continue
            df = df.rename(columns={"date": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        dst = src.with_suffix(".aq.csv")
        df.to_csv(dst, index=False)
        package["data_path"] = str(dst)
        package.setdefault("notes", []).append("data_path_repaired_for_ict_engine_loader=timestamp_header")
        material_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
        rows.append(
            {
                "material": str(material_path),
                "source_csv": str(src),
                "aq_csv": str(dst),
                "rows": int(len(df)),
                "header": ",".join(df.columns[:6]),
            }
        )

    out = RUN_ROOT / "summaries/csv_header_repair_v1.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["material", "source_csv", "aq_csv", "rows", "header"])
        writer.writeheader()
        writer.writerows(rows)

    assertions = [
        ("materials_seen_5", len(material_paths) == 5),
        ("materials_repaired_5", len(rows) == 5),
        ("failures_empty", not failures),
        ("all_headers_timestamp", all(row["header"].startswith("timestamp,") for row in rows)),
    ]
    lines = [f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in assertions]
    if failures:
        lines.extend(f"FAILURE {failure}" for failure in failures)
    (RUN_ROOT / "checks/csv_header_repair_assertions.out").write_text("\n".join(lines) + "\n")
    return 0 if all(ok for _, ok in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
