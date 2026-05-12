# Owner Normal-Control Export Request v1

Preferred branch: source-owned normal/non-manipulation controls.

Required target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.

Required files:
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

Minimum support:
- `73` valid source-owned normal controls for each of the 17 required cells.

Source route:
- CME/NYMEX/COMEX/CME Globex cells: CME DataMine Market Depth/FIX-FAST or licensed equivalent.
- VIX/CFE cells: Cboe/CFE DataShop or Depth-of-Book licensed equivalent.

Do not use same-exhibit `FLIP` rows as controls unless the explicit exception template is approved.
