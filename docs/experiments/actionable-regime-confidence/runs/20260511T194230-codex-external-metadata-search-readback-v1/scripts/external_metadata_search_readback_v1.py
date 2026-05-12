#!/usr/bin/env python3
"""Static readback notes for the Board A external metadata search slice.

The authoritative artifacts in this run directory are written as checked-in
JSON/CSV/Markdown/readback files. This script is intentionally non-networked.
"""

from __future__ import annotations

import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = RUN_ROOT / "external-metadata-search-readback" / "external_metadata_search_readback_v1.json"


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    decision = payload["decision"]
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
