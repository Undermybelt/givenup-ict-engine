# Crosswalk Decision Package v1

Run ID: `20260511T123100+0800-codex-crosswalk-decision-package-v1`

## Decision

- Prior pending crosswalk slots: `63`.
- Approved same-underlying `^GSPC` slot actions: `21`.
- Conditional SPY/ES=F tradable-proxy slot actions: `42`.
- Total approved or conditional crosswalk slot actions: `63`.
- Sideways protocol target slots remain deferred until rerun: `141`.
- Still fail-closed without exact source/projection: `360`.

This is a positive decision package, not another negative source sweep. It turns the 63 pending S&P 500/NBER crosswalk slots into explicit attach actions with guardrails.

## Approved Crosswalks

- `Yardeni S&P 500 -> ^GSPC` Bull/Bear: approve calendar-window projection for intraday/monthly bars, with open-ended Yardeni windows refreshed before live attachment.
- `NBER contraction months -> ^GSPC` Crisis: approve month-window projection as macro Crisis provenance for S&P 500 bars.
- `Yardeni S&P 500 -> SPY/ES=F` Bull/Bear: conditional approve as S&P 500 tradable-proxy tier only.
- `NBER contraction months -> SPY/ES=F` Crisis: conditional approve as S&P 500 tradable-proxy macro Crisis tier only.

## Sideways Protocol

- Existing accepted gate: `sideways_sourcebacked_abs_return_range_v1`.
- Rule: `sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236`.
- Existing calibration/test Wilson95 LCB: `0.988647` / `0.995568`.
- Protocol status: ready for targeted rerun, not attached.
- Critical guardrail: never infer `Sideways` as the complement of `Bull`/`Bear`/`Crisis`.

## Not Promoted

- No full-objective gate is claimed.
- No broad projection to QQQ/NDX/NQ, DJI/DIA/YM, commodities, vol, or crypto is approved here.
- Proxy tier is explicit; proxy rows are not promoted to source-native rows.
- Shared board was not modified.

## Artifacts

- `crosswalk_decision_package_v1.json`
- `approved_crosswalk_slot_actions_v1.csv`
- `deferred_or_rejected_slot_actions_v1.csv`
- `sideways_adjudication_protocol_v1.md`
- `../checks/crosswalk_decision_package_v1_assertions.out`
