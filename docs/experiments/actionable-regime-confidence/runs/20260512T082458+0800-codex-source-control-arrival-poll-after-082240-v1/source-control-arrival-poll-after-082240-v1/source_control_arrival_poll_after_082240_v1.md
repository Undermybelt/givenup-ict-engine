# Source/Control Arrival Poll After 082240 v1

Run id: `20260512T082458+0800-codex-source-control-arrival-poll-after-082240-v1`

Gate result: `source_control_arrival_poll_after_082240_v1=no_new_required_root_no_owner_credentials_no_unlock`

## Scope

Bounded read-only poll after the registered `082240` current objective audit and the `082215`
RECAP novel PDF retry. This poll checks whether any required source/control root or local owner
credential surface arrived before another acquisition or downstream step.

This poll does not retry CourtListener storage, does not mutate R3/R5/R6 target roots, does not
approve public RECAP/PACER provenance, does not approve same-exhibit `FLIP` rows as controls, and
does not run direct verifier, split calibration, canonical merge, selected-data AutoQuant,
Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.

## Readback

| Check | Result |
|---|---|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | `absent` |
| `/tmp/ict-engine-source-panel-recency-extension` | `absent` |
| `/tmp/ict-engine-native-subhour-source-label-intake` | `present_non_promoting` |
| `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid` | `present_non_approving` |
| Relevant owner/export credential env names | `0` |
| `databento` CLI | `absent` |
| `dbn` CLI | `absent` |
| Python `databento` | `absent` |
| Python `dbn` | `absent` |
| Python `pyarrow` | `absent` |
| Python `pandas` | `present` |
| Python `requests` | `present` |
| `kaggle` CLI | `present` |
| `uv` | `present` |
| `cargo` | `present` |

The R3 native-subhour intake still contains only `native_subhour_source_label_rows.csv` and
`native_subhour_source_label_provenance.json`. It is not a valid Crisis/MainRegimeV2 unlock under
the latest Board A contract. The R6 approval decision package remains present but does not provide
approval for canonical merge or downstream rerun.

## Decision

No new required source/control root arrived. No owner-approved/authenticated FINRA,
venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle export is available locally.
No credential env-name hint for those owner routes is present. Therefore R6 owner/export unlock,
R5 recency unlock, and R3 native-subhour promotion all remain false.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false;
canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false;
strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated
FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE exchange order-lifecycle export with both
positives and matched normal controls, or explicit same-exhibit `FLIP`-as-control approval, before
any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN,
CatBoost/path-ranking, or execution-tree promotion.
