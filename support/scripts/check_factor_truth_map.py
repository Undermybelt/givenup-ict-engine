#!/usr/bin/env python3
from __future__ import annotations

import re
import sys

from path_defaults import resolve_repo_root


ROOT = resolve_repo_root(__file__)
FACTOR_SOURCE = ROOT / "src" / "factor_lab" / "factor_definition.rs"
DOCS = [
    ROOT / "AGENT.md",
    ROOT / "support" / "docs" / "factor-catalog.md",
]


def factor_category_keys() -> list[str]:
    text = FACTOR_SOURCE.read_text()
    match = re.search(r"impl FactorCategory\s*\{.*?pub fn as_str\(self\).*?match self \{(?P<body>.*?)\n\s*\}", text, re.S)
    if not match:
        raise RuntimeError("could not parse FactorCategory::as_str()")
    keys = re.findall(r'Self::[A-Za-z0-9_]+\s*=>\s*"([^"]+)"', match.group("body"))
    if not keys:
        raise RuntimeError("FactorCategory::as_str() contains no keys")
    return keys


def main() -> int:
    keys = factor_category_keys()
    failures: list[str] = []
    for doc in DOCS:
        text = doc.read_text()
        missing = [key for key in keys if key not in text]
        if missing:
            failures.append(f"{doc.relative_to(ROOT)} missing factor keys: {', '.join(missing)}")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"factor_truth_map status=fail factors={len(keys)} docs={len(DOCS)}")
        return 1
    print(
        "factor_truth_map status=pass "
        f"factors={len(keys)} docs={len(DOCS)} keys={','.join(keys)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
