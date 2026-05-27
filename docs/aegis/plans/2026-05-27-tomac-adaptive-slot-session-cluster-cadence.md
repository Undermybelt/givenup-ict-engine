# TOMAC Adaptive Slot Session-Cluster Cadence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `aegis:subagent-driven-development` (recommended) or `aegis:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the authoritative takeover-ready training packet for `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`, then run the exact same-root Auto-Quant cadence iteration only when Board B ownership is lawfully clear.

**Architecture:** Preserve the parent `AdaptiveSlotContrarian` regime-rooted profitability lineage, stage one authoritative `/tmp` workdoc plus claim pair, then drive a same-root cadence-repair wrapper and AQ readback without changing branch identity or lowering gates. The implementation is split into takeover readiness, packet normalization, and execution/readback so each slice can fail closed independently.

**Tech Stack:** `ict-engine` repo docs/workflow surfaces, `/tmp` Board B claim packets, Python runner/prep wrappers under `support/docs/experiments/actionable-regime-confidence/scripts/`, retained-local TOMAC evidence, and later Auto-Quant state/check outputs.

**Baseline / Authority Refs:** `docs/aegis/specs/2026-05-27-tomac-adaptive-slot-session-cluster-cadence-brief.md`, `docs/aegis/BASELINE-GOVERNANCE.md`, `support/docs/plans/2026-05-25-board-b-current.md`, `/tmp/ict-engine-agent-claims/board-b-factor-refinement/`, `/private/tmp/ict-engine-tomac-adaptive-slot-contrarian-exact-aq-race-repair-20260526T193259+0800/workdoc.md`, `/private/tmp/ict-engine-tomac-adaptive-slot-contrarian-exact-aq-race-repair-20260526T193259+0800/aq/checks/terminal_metrics.json`, `/private/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-prep-20260527T125200+0800/workdoc.md`, `/private/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-relaunch-20260527T170335+0800/workdoc.md`

**Compatibility Boundary:** Preserve regime-rooted grammar; keep `1m` origin with `5m/15m/30m/1h/4h/1d` context; do not collide with fresh active claims or live factor processes; do not lower `5bps`, cadence, validation, readiness, transition, ranker, or execution gates; do not claim `promotion_allowed=true` or `trade_usable=true` unless same-turn artifacts prove it.

**Verification:** `python3 support/scripts/factor_claim_terminalization_audit.py --compact`, `ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status'`, focused wrapper tests under `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py`, and exact post-run readbacks from `/tmp/.../checks` plus `/tmp/.../summaries`.

---

## Scope Check

- Fact:
  - the approved branch is `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`
  - parent exact AQ evidence is positive after hard friction but too sparse:
    `trade_count=151`, `5bps_per_side_total_profit_pct=6.16`, `trades_per_session=0.097044`
  - the relaunch packet already proved `exact_wrapper_verified_prep_complete_pending_clear_launch_window`
  - current Board B state is occupancy-heavy and may block immediate takeover or launch
- Assumption:
  - adjacent slot/session-cluster merge remains the best cadence lever inside the same root
- Unknown:
  - whether the next lawful AQ run improves cadence enough without degrading economics or downstream execution gates

This plan covers one subsystem only: lawful same-root takeover and cadence-repair iteration for the approved TOMAC branch.

## File Structure

- Create:
  - `/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp>/workdoc.md`
  - `/tmp/ict-engine-agent-claims/board-b-factor-refinement/<stamp>-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.claim`
  - `support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md`
  - `docs/aegis/work/2026-05-27-tomac-adaptive-slot-session-cluster-cadence/50-evidence.md`
- Modify when required by the same slice:
  - `docs/aegis/INDEX.md`
  - the active claim/workdoc only when performing a lawful stale takeover append
- Reuse only, no source edits unless later execution proves missing contract coverage:
  - `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_density_repair_prep_v1.py`
  - `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py`

### Task 1: Prove The Lane Is Lawful To Take Over

**Files:**
- Create: `docs/aegis/work/2026-05-27-tomac-adaptive-slot-session-cluster-cadence/50-evidence.md`
- Modify: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/<active-claim>.claim` only if stale takeover is actually lawful
- Modify: `/private/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-relaunch-20260527T170335+0800/workdoc.md` only if stale takeover is actually lawful

**Why this task exists:**
- The user explicitly forbids duplicating another agent’s lane.
- Current Board B truth is unstable, so takeover legality must be proven from current-turn artifacts, not inferred from older chat state.

**Impact / Compatibility:**
- Read-only until the stale-safe takeover test passes.
- Must not create a new active claim if the prior cadence lane is still fresh or a matching live process exists.

**Verification:**
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- `ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status|session_cluster_cadence'`
- `python3 - <<'PY'
import json
from pathlib import Path
claim = Path('/tmp/ict-engine-agent-claims/board-b-factor-refinement/ACTIVE_CLAIM.claim')
data = json.loads(claim.read_text())
assert data['scope'].find('SessionClusterCadenceRepair') != -1
assert 'last_progress_at' in data
PY`

- [ ] **Step 1: Write the failing takeover-check script**

```bash
cat > /tmp/check_tomac_cadence_takeover.sh <<'SH'
#!/bin/zsh
set -euo pipefail
python3 support/scripts/factor_claim_terminalization_audit.py --compact > /tmp/tomac_cadence_audit.json || true
ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status|session_cluster_cadence' > /tmp/tomac_cadence_ps.txt || true
python3 - <<'PY'
import json
from pathlib import Path
audit_path = Path('/tmp/tomac_cadence_audit.json')
if not audit_path.exists():
    raise SystemExit(2)
audit = json.loads(audit_path.read_text())
claims = audit.get('attention_claims', [])
matches = [c for c in claims if 'SessionClusterCadenceRepair' in c.get('scope', '')]
assert matches, 'no cadence claim found'
claim = matches[0]
assert claim.get('stale_safe_takeover_candidate') is True, claim
assert audit['summary']['live_factor_processes'] == 0, audit['summary']
PY
SH
chmod +x /tmp/check_tomac_cadence_takeover.sh
```

- [ ] **Step 2: Run the takeover-check script to verify it fails while the lane is still blocked**

Run: `/tmp/check_tomac_cadence_takeover.sh`
Expected: FAIL on either `stale_safe_takeover_candidate` or `live_factor_processes`

- [ ] **Step 3: Record current evidence without mutating the lane**

```markdown
# Takeover Readiness Evidence

- audit command: `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- process guard command:
  `ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status|session_cluster_cadence'`
- current result:
  - takeover not yet lawful until the exact cadence claim becomes stale-safe
  - no duplicate claim or workdoc may be created before that point
```

- [ ] **Step 4: Re-run verification and confirm the lane is still blocked or lawfully clear**

Run:
`sed -n '1,120p' docs/aegis/work/2026-05-27-tomac-adaptive-slot-session-cluster-cadence/50-evidence.md`
Expected: Contains current audit/process truth and no false takeover claim

- [ ] **Step 5: Commit**

```bash
git add docs/aegis/work/2026-05-27-tomac-adaptive-slot-session-cluster-cadence/50-evidence.md
git commit -m "docs: record tomac cadence takeover readiness"
```

### Task 2: Create The Canonical Takeover Packet Once The Lane Is Actually Free

**Files:**
- Create: `/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp>/workdoc.md`
- Create: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/<stamp>-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.claim`
- Create: `support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md`
- Modify: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/<active-claim>.claim`

**Why this task exists:**
- The user asked for a new profitability-factor training document that later agents can take over after one hour of inactivity.
- The repo needs one canonical packet pointing at the exact same-root cadence child.

**Impact / Compatibility:**
- Must only run after Task 1 proves lawful takeover.
- The new packet becomes the authoritative owner surface; old fresh owner remains authoritative until takeover conditions pass.

**Verification:**
- `python3 - <<'PY'
from pathlib import Path
import json
workdoc = Path('/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-STAMP/workdoc.md')
claim = Path('/tmp/ict-engine-agent-claims/board-b-factor-refinement/STAMP-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.claim')
repo_packet = Path('support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md')
assert workdoc.exists(), workdoc
assert claim.exists(), claim
assert repo_packet.exists(), repo_packet
text = workdoc.read_text()
for needle in [
    'SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1',
    '1m',
    '5m,15m,30m,1h,4h,1d',
    'promotion_allowed=false',
    'trade_usable=false',
]:
    assert needle in text, needle
data = json.loads(claim.read_text())
for key in ['agent_name','owner','claimed_at','last_progress_at','scope','active_task','non_goals','write_surface','run_root','status','latest_report']:
    assert key in data, key
PY`

- [ ] **Step 1: Write the failing validation script with concrete takeover paths**

```bash
STAMP=$(date +%Y%m%dT%H%M%S%z)
cat > /tmp/validate_tomac_cadence_takeover.sh <<SH
#!/bin/zsh
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
workdoc = Path('/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-${STAMP}/workdoc.md')
assert workdoc.exists(), workdoc
PY
SH
chmod +x /tmp/validate_tomac_cadence_takeover.sh
```

- [ ] **Step 2: Run validation to verify it fails before the packet exists**

Run: `/tmp/validate_tomac_cadence_takeover.sh`
Expected: FAIL with missing workdoc path

- [ ] **Step 3: Write the minimal takeover packet**

```markdown
# Workdoc - TOMAC Adaptive Slot Session-Cluster Cadence Takeover

- created_at: `<timestamp>`
- owner: `codex`
- route: `aegis/writing-plans -> later execution`
- factor_id: `tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`
- parent_factor_id: `tomac_nq_tod_contrarian_slot120_h240_lb80_e75_wr56_rv1_exact_v1`
- branch_path:
  `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`
- origin_timeframe: `1m`
- context_timeframes: `5m,15m,30m,1h,4h,1d`
- non_goals:
  - do not reroot away from `AdaptiveSlotContrarian`
  - do not lower `5bps`, cadence, validation, readiness, transition, or execution gates
  - do not claim `promotion_allowed=true` or `trade_usable=true` without same-turn evidence
- current_decision:
  `takeover_packet_created_pending_exact_aq_cadence_iteration`
- promotion_allowed=false
- trade_usable=false
- update_goal=false
```

- [ ] **Step 4: Re-run validation and repo packet grep**

Run:
`rg -n "SessionClusterCadenceRepair|tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1|promotion_allowed=false|trade_usable=false" /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-${STAMP}/workdoc.md support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md`
Expected: All required lines present

- [ ] **Step 5: Commit**

```bash
git add support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md
git commit -m "docs: add tomac cadence takeover packet"
```

### Task 3: Reconfirm Wrapper Contract Before Launch

**Files:**
- Modify: `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py` only if a missing guard is proven
- Modify: the matching runner/prep wrapper only if a focused failing test proves a contract gap

**Why this task exists:**
- The spec depends on a safe exact-wrapper prep surface. That must be reconfirmed in the current turn before launch.

**Impact / Compatibility:**
- Prefer readback only.
- If code changes become necessary, they are repair-track only and must preserve same-root identity.

**Verification:**
- `python3 -m unittest support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py -v`
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py --help`

**Repair Track**
- Root cause being addressed: stale or missing prep-surface contract for the exact cadence child
- Canonical owner being changed: the exact cadence prep wrapper and its focused test
- Smallest necessary change: only the guard/help/prep behavior needed to preserve safe launch semantics
- Compatibility boundary: no AQ launch on `--help`; no branch-root drift
- Task-level verification: unittest passes and `--help` exits cleanly

**Retirement Track**
- Old owner/fallback: manual operator guesswork about whether the wrapper is safe
- Whether it is still active: yes, unless the focused wrapper contract is re-proven
- Only reason to keep it: none after the focused prep contract is re-verified
- Trigger for deletion or convergence: green focused test plus clean help/prep readback
- Verification before removal: wrapper test and help output

- [ ] **Step 1: Run the focused wrapper test first**

Run:
`python3 -m unittest support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py -v`
Expected: PASS, or a focused failure naming the exact contract gap

- [ ] **Step 2: Run wrapper help to verify the guard**

Run:
`python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py --help`
Expected: usage text and exit `0` with no run-root creation

- [ ] **Step 3: If red, make the minimal repair only**

```python
def run_cli(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return main(args)
```

- [ ] **Step 4: Re-run test and help until both are green**

Run the same commands from Steps 1 and 2
Expected: PASS and clean help output

- [ ] **Step 5: Commit**

```bash
git add support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py
git commit -m "fix: verify tomac cadence prep wrapper contract"
```

### Task 4: Run The Exact Same-Root AQ Cadence Iteration Only When Board B Is Clear

**Files:**
- Create: `/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp>/aq/`
- Modify: `/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp>/workdoc.md`
- Modify: `support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md`

**Why this task exists:**
- This is the actual evidence-producing slice that either validates the cadence child or fail-closes it with current-turn AQ artifacts.

**Impact / Compatibility:**
- Must only run after Tasks 1-3 are green and Board B is clear of conflicting live writers.
- Must preserve exact same-root identity in every packet and readback.

**Verification:**
- Preflight:
  - `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  - `ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status|session_cluster_cadence'`
- Launch:
  - `python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py --root /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp> --compact-root /Users/thrill3r/projects-ict-engine/ict-engine/support/docs/experiments/actionable-regime-confidence/runs/<stamp>-codex-tomac-adaptive-slot-session-cluster-cadence-takeover-v1`
- Post-run:
  - `rg -n "decision|promotion_allowed|trade_usable|trade_count|5bps|trades_per_session|execution_readiness|transition_hazard" /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp>/checks /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-<stamp>/summaries`

- [ ] **Step 1: Write the failing launch wrapper script**

```bash
cat > /tmp/run_tomac_cadence_exact_aq.sh <<'SH'
#!/bin/zsh
set -euo pipefail
python3 support/scripts/factor_claim_terminalization_audit.py --compact > /tmp/tomac_cadence_launch_audit.json || true
python3 - <<'PY'
import json
from pathlib import Path
audit = json.loads(Path('/tmp/tomac_cadence_launch_audit.json').read_text())
assert audit['summary']['live_factor_processes'] == 0, audit['summary']
PY
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py --root "$1" --compact-root "$2"
SH
chmod +x /tmp/run_tomac_cadence_exact_aq.sh
```

- [ ] **Step 2: Run it while blocked to verify RED**

Run:
`/tmp/run_tomac_cadence_exact_aq.sh /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-TEST /Users/thrill3r/projects-ict-engine/ict-engine/support/docs/experiments/actionable-regime-confidence/runs/TEST`
Expected: FAIL early if live factor processes still exist

- [ ] **Step 3: Launch the exact iteration when the audit is clear**

Run:
`/tmp/run_tomac_cadence_exact_aq.sh /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-${STAMP} /Users/thrill3r/projects-ict-engine/ict-engine/support/docs/experiments/actionable-regime-confidence/runs/${STAMP}-codex-tomac-adaptive-slot-session-cluster-cadence-takeover-v1`

Expected: runner exits and writes current-turn `checks/` and `summaries/` artifacts

- [ ] **Step 4: Read back and classify the result without upgrading claims prematurely**

Run:
`rg -n "decision|promotion_allowed|trade_usable|trade_count|5bps|trades_per_session|execution_readiness|transition_hazard" /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-${STAMP}/checks /tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-takeover-${STAMP}/summaries`
Expected: enough artifact truth to classify the child as either still fail-closed or materially improved

- [ ] **Step 5: Commit**

```bash
git add support/docs/experiments/actionable-regime-confidence/2026-05-27-codex-tomac-adaptive-slot-session-cluster-cadence-takeover.md docs/aegis/work/2026-05-27-tomac-adaptive-slot-session-cluster-cadence/50-evidence.md
git commit -m "docs: record tomac cadence aq readback"
```

## Self-Review

- Spec coverage: the plan covers takeover legality, canonical packet creation, wrapper contract verification, and exact AQ cadence iteration.
- Placeholder scan: no `TODO` or `TBD`; variable timestamps are introduced through concrete shell commands.
- Type consistency: branch labels, factor ids, and verification commands stay identical across tasks.
- Compatibility check: regime-rooted grammar, provenance separation, and no-relaxation invariants are explicit.
- Verification check: each task has exact commands and expected outcomes.
- Dual-track check: wrapper repair/retirement is explicit; stale owner retirement is handled through takeover append rather than duplicate ownership.

## Execution Handoff

Plan complete and saved to `docs/aegis/plans/2026-05-27-tomac-adaptive-slot-session-cluster-cadence.md`.

Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints
