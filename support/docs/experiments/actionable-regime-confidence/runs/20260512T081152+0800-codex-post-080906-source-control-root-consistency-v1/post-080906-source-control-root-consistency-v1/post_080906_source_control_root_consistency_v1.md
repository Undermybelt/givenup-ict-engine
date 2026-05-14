# Post-080906 Source/Control Root Consistency v1

Gate result: `post_080906_source_control_root_consistency_v1=no_required_source_control_unlock`.

This is a read-only source/control inventory. It does not approve public paper
metadata, TSIE-derived labels, approval-package presence, or run-root existence
as source/control evidence.

## Metrics

- Board hash at readback: `7e398228e4cbcb70a665d278d44dbb6c3a6d642ee448830caa7b12f7b4ccc038`
- Board contained `080906` before writeback: `True`
- `080906` gate: `openalex_semantic_pwc_source_route_after_080700_v1=no_required_source_control_unlock`
- `080906` requests sent: `24`
- `080906` failed or parse-failed: `14`
- `080906` candidate rows: `11`
- `080906` required filename/token hits: `0`
- `080906` exact `MainRegimeV2` hits: `0`
- `080906` R5 route hits: `0`
- `080906` R3 native-subhour Crisis hits: `0`
- `080906` R6 owner/control route hits: `0`
- `080906` broad context hits: `3`
- `080446` present now: `True`
- `080446` assertion checksum: `ab6b6c82efdeff8ce5571f0fcb6f3492f3bb44e56af48b528295c430622fea7b`
- `080950` complete now: `True`
- R6 owner/export root present: `False`
- R5 recency root present: `False`
- R3 native-subhour labels: `Bear, Bull, Sideways`
- R3 Crisis present: `False`
- R6 approval present: `False`

## Decision

- Accepted rows added: `0`.
- No valid required R3/R5/R6 source/control root was acquired.
- No canonical merge, selected-data AutoQuant promotion, or downstream promotion
  rerun is allowed.
- `update_goal=false`.
