# CrossAssetVolCarryV1 Operational Failure Readback

Run id: `20260511T215311+0800-codex-board-b-crossasset-vol-carry-v1`.

Observed command:

```text
uv run --python 3.11 --with pandas --with numpy --with pyarrow python docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/scripts/crossasset_vol_carry_v1.py
```

Process exit: `1`.

Hard failure:

```text
RuntimeError: missing required inputs: /Users/thrill3r/Auto-Quant/user_data/data/GLD_USD-1d.feather
```

Artifact state:

- RC-SPA report: absent.
- Branch summary: absent.
- Selected rows: absent.
- Fail-closed summary: absent.
- Downstream consumable packet: absent.

Decision: `fail:missing_required_inputs`. This is an operational failure, not a scored RC-SPA rejection.

Downstream remains `not_started:no_rc_spa_report`. The existing `205047` scoped Manipulation pass remains component-only evidence and is not promotable without all four price roots passing unchanged RC-SPA.
