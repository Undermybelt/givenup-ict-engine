# Direct Manipulation Coverage Readback v2

Run ID: `20260511T184630+0800-codex-direct-manipulation-coverage-readback-v2`

This readback merges existing direct `Manipulation` artifacts with the latest web source screen. It does not edit source artifacts or the shared Current Cursor.

## Decision

`direct_manipulation_coverage_readback_v2=scoped_varieties_present_full_species_blocked`

- Scoped accepted direct varieties: `5`.
- Remaining unaccepted varieties: `6`.
- Web-screen ready real matched-negative candidates: `0`.
- Spoofing/layering matched negatives available: `0`.
- Accepted rows added: `0`.
- Full objective achieved: `false`; `update_goal=false`.

## Coverage Rows

| Variety | State | Remaining Gap |
|---|---|---|
| `pump_dump_telegram_event` | `accepted_95_scoped_direct_event` | Event-confirmed suppression/cooldown signal only; does not cover spoofing, layering, quote stuffing, or order-book behavior. |
| `pump_dump_social_text_or_twitter` | `blocked_below_95` | Needs stronger direct controls or a different text/event construction before acceptance. |
| `dex_self_trade_order_lifecycle` | `accepted_95_scoped_direct_order_lifecycle` | Bounded DEX self-trade/wash-trade slice only; not spoofing/layering/quote stuffing. |
| `dex_consecutive_self_trade_order_lifecycle` | `accepted_95_scoped_direct_order_lifecycle_context` | Confirms bounded self-trade context; still not full direct Manipulation variety coverage. |
| `midsummer_bsc_wash_maker` | `accepted_95_scoped_direct_onchain_wash` | BSC wash-maker only; not centralized spoofing/layering/quote stuffing. |
| `midsummer_multichain_wash_maker` | `accepted_95_scoped_direct_onchain_wash` | Direct on-chain wash-maker evidence only; full manipulation class remains incomplete. |
| `spoofing_layering_enforcement_cases` | `positive_only_no_95_gate` | Acquire matched negative order-lifecycle/order-book rows before any spoofing/layering Wilson95 gate claim. |
| `local_spoofing_repos` | `rejected_no_replayable_positive_negative_rows` | Need exportable direct order-book/order-lifecycle rows with controls. |
| `quote_stuffing` | `missing_direct_rows` | Acquire quote-message/order-book bursts and matched normal-period controls. |
| `pinging` | `missing_direct_rows` | Acquire order-lifecycle probe rows and matched controls. |
| `bear_raid_or_painting_tape` | `missing_direct_rows` | Acquire direct event/order-flow rows and same-venue non-event controls. |

## Readback

- Existing direct accepted slices remain scoped: Telegram pump/dump, DEX self-trade, DEX consecutive self-trade, BSC wash-maker, and multichain wash-maker.
- Full direct `Manipulation` still fails because spoofing/layering has positive cases but zero matched negatives, and quote stuffing, pinging, bear raid, and painting tape remain missing.
- The latest web/GitHub/arXiv/Kaggle/HF screen adds no real matched-negative source candidate.
- This cannot be promoted into a parent-root or full objective completion claim.

## Artifacts Used

- Variety matrix: `docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json`
- Spoofing/layering readiness: `docs/experiments/actionable-regime-confidence/runs/20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/matched-row-readiness/spoofing_layering_matched_row_readiness_v1.json`
- Web source screen: `docs/experiments/actionable-regime-confidence/runs/20260511T184212-codex-direct-manipulation-web-source-screen-v1/direct-web-source-screen/direct_manipulation_web_source_screen_v1.json`
- Row intake manifest: `docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_manifest_v1.json`
