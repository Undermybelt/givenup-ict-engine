# 2026-05-23 Factor Claim Audit Actionability Handoff TODO

Owner: Codex maintenance loop slice.
Scope: make factor-claim terminalization audit output more actionable without
editing claims, run roots, factor evidence, or Board state.

## Intent

The factor-claim audit should tell a downstream maintainer what blocks closure,
not only that the board needs attention. The compact output must stay
token-friendly and privacy-safe while making the next local action explicit.

## Current Todo Board

### Done

- [x] Add RED regression for summary-level actionability.
- [x] Add `blocking_reasons` to factor-claim audit summary.
- [x] Add `next_action` derived from active claims, missing run roots, and
  positive `trade_usable` / `promotion_allowed` flags.
- [x] Preserve fail-closed semantics: `needs_attention` remains exit `1`.
- [x] Preserve compact privacy boundary: no `claim_path`, raw `run_root`, or
  repo-local absolute path in compact attention claims.
- [x] Run targeted and full factor-claim audit tests.
- [x] Run py_compile and script manifest checks.
- [x] Run a real compact factor-claim audit readback.
- [x] Fix claim parsing for terminal Markdown bullets, `status=terminal*`, and
  `terminal_decision`.

### Next

- [ ] Terminalize or externalize active factor claims.
- [ ] If missing run roots appear again, restore evidence or terminalize those
  claims explicitly.
- [ ] If any `trade_usable=true` or `promotion_allowed=true` appears, review the
  positive flag against hard gates before any promotion language.
- [ ] Re-run the compact factor-claim audit after claim-board changes.

### Not Yet

- [ ] No claim file was edited in this slice.
- [ ] No factor run root was modified.
- [ ] No factor was promoted or marked trade-usable.
- [ ] No Board A/B terminal decision was changed.

## Evidence

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_summarize_marks_needs_attention_for_active_or_positive_claims -v`
  failed before implementation with `KeyError: 'blocking_reasons'`.
- GREEN targeted:
  the same test passed after adding `blocking_reasons` and `next_action`.
- Full factor-claim audit tests:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `7` tests.
- Compile:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest:
  `python3 support/scripts/check_script_manifest.py`
  passed with `entries=21`.
- Real compact factor audit:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-actionability-20260523.json`
  exited `1` as expected.
- Parser RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_treats_terminal_status_and_markdown_bullets_as_terminal -v`
  failed before implementation because `terminalized_claims` was `0` instead of
  `2`.
- Parser GREEN:
  the same targeted test passed after parsing Markdown bullet keys, treating
  `status=terminal*` as terminalized, and using `terminal_decision` as a
  decision fallback.
- Full factor-claim audit tests after parser fix:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `8` tests.
- Compile after parser fix:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest after parser fix:
  `python3 support/scripts/check_script_manifest.py`
  passed with `entries=21`.
- Real compact factor audit after parser fix:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-terminal-parser-20260523.json`
  exited `1` as expected, but active claims dropped from `8` to `3`.

## Current Readback

From `/tmp/ict-engine-factor-claims-actionability-20260523.json`:

- `summary.status=needs_attention`
- `total_claims=25`
- `terminalized_claims=17`
- `active_claims=8`
- `missing_run_roots=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `blocking_reasons=["active_claims"]`
- `next_action="terminalize or externalize active claims"`
- `attention_claim_count=8`

Attention groups:

- by owner: `Codex=1`, `Codex CLI=1`, `codex=3`, `unknown=3`
- by run-root state: `none=6`, `present=2`
- by status: `active=8`

After the parser fix, `/tmp/ict-engine-factor-claims-terminal-parser-20260523.json`
reports:

- `summary.status=needs_attention`
- `total_claims=26`
- `terminalized_claims=23`
- `active_claims=3`
- `missing_run_roots=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `blocking_reasons=["active_claims"]`
- `next_action="terminalize or externalize active claims"`
- `attention_claim_count=3`

Remaining active compact claims:

- `20260523T000747+0800-codex-tomac-tod-balanced-execution-predicate-readback.claim`
- `20260523T021624+0800-codex-historical-interrupt-profit-factor-extension-triage.claim`
- `20260523T024228+0800-codex-vst-same-root-execution-predicate-diagnosis.claim`

## Compatibility Boundary

- The audit is read-only.
- Compact output remains token-friendly.
- Compact output continues to omit raw `claim_path` and `run_root`.
- This slice is audit-actionability only; it is not factor terminalization,
  factor promotion, or release readiness.

## Resume State

Resume from this file plus
`/tmp/ict-engine-factor-claims-actionability-20260523.json`. The smallest next
safe action is to inspect the eight active compact attention claims, then
terminalize or externalize them without taking over live owner work.
