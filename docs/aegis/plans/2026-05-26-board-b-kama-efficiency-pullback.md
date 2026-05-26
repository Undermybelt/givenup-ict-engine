# Board B KAMA Efficiency Pullback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use aegis:subagent-driven-development (recommended) or aegis:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first authoritative Board B training packet and exact Gate 1 execution surface for the approved KAMA efficiency-pullback branch rooted at `TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation`.

**Architecture:** The implementation keeps regime grammar and profitability grammar separate from provenance labels. It first creates the takeover-safe packet and `/tmp` ownership surfaces, then builds a new exact IBKR runner and identity test for a fresh `M2K` cell, and only then launches Gate 1 when the compact audit and direct IBKR preflight both permit it. If `M2K` is no longer safe at launch time, the plan deterministically falls back to `MYM`, but only after rerunning the exact same collision audit and preflight checks.

**Tech Stack:** `ict-engine` repo docs and Python experiment scripts, IBKR historical probe surface via `support/scripts/auto_quant_external/fetch_external.py`, exact Gate 1 wrapper scripts under `support/docs/experiments/actionable-regime-confidence/scripts`, `/tmp` Board B claim/workdoc artifacts, and repo-side experiment packets under `support/docs/experiments/actionable-regime-confidence/`.

**Baseline / Authority Refs:** `docs/aegis/specs/2026-05-26-board-b-kama-efficiency-pullback-brief.md`, `AGENT.md`, `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`, `support/docs/experiments/actionable-regime-confidence/20260526T132732+0800-codex-ibkr-mes-kama-efficiency-pullback-training.md`, `support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_mes1m_kama_efficiency_pullback_7d_gate1_v1.py`, `support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_mes1m_kama_efficiency_pullback_gate1_identity.py`.

**Compatibility Boundary:** Preserve the approved grammar family `TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1` with deterministic fallback to `ibkr_mym1m_kama_efficiency_pullback_7d_gate1_v1`, keep `1m` as exact origin and `5m/15m/30m/1h/4h/1d` as context only, do not reopen or mutate the terminalized `MES 1m KAMA` negative sample, do not lower `5bps`, density, stability, or downstream gates, and do not collide with current active Board B owners.

**Verification:** `python3 support/scripts/factor_claim_terminalization_audit.py --compact`, `ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status'`, `python3 -m py_compile ...`, `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py`, `python3 support/scripts/auto_quant_external/fetch_external.py ibkr-historical ...`, and the exact runner command created in Task 3.

---

## Scope Check

- Fact:
  - the approved spec fixes the new grammar family to `TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1`, with deterministic `MYM` fallback if `M2K` is no longer safe.
  - the old `MES 1m KAMA` branch is terminalized negative and must remain a preserved negative sample.
  - the latest compact audit in this turn shows `active_claims=4`, `live_factor_processes=0`, `missing_run_roots=1`, and no active KAMA-family claim.
- Assumption:
  - `M2K 1m` remains the best first exact cell because it is the preferred symbol in the approved spec and no active KAMA lane currently owns it.
- Unknown:
  - whether same-turn direct IBKR probe for `M2K 202606 1m` still returns nonzero rows when implementation starts.
  - whether `M2K` stays collision-safe long enough to launch before another agent claims it.

## File Structure

- Create:
  - `support/docs/experiments/actionable-regime-confidence/20260526T${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.md`
  - `support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py`
  - `support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py`
  - `/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}/workdoc.md`
  - `/tmp/ict-engine-agent-claims/board-b-factor-refinement/${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.claim`
- Modify only if `M2K` is blocked at launch time:
  - same three repo files above, but with `mym` in the exact factor id and provenance labels instead of `m2k`
- Do not modify:
  - `support/docs/experiments/actionable-regime-confidence/20260526T132732+0800-codex-ibkr-mes-kama-efficiency-pullback-training.md`

## Risks

- A new claim may occupy `M2K` before Task 3 starts, forcing deterministic fallback to `MYM`.
- The existing `MES` KAMA runner uses old grammar and cannot be copied blindly without contract edits.
- IBKR preflight may fail on port reachability, contract resolution, or zero rows even when the lane is unclaimed.

## Retirement Track

- Historical owner kept: `TrendEfficiency -> KaufmanAdaptivePullback -> KaufmanAdaptivePullback -> ibkr_mes1m_kama_efficiency_pullback_7d_gate1_v1`
- Status: terminalized negative sample, preserved only for evidence and anti-duplication.
- Removal trigger: none in this slice; keep it as a cooled exact-root negative row.
- Verification before any future retirement: confirm the new branch has its own packet and exact-root artifacts and that no code still points to the old `MES` packet as canonical.

### Task 1: Create The New Authoritative Packet, Workdoc, And Claim

**Files:**
- Create: `support/docs/experiments/actionable-regime-confidence/20260526T${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.md`
- Create: `/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}/workdoc.md`
- Create: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.claim`

**Why this task exists:**
- The user explicitly asked for a new profitability-factor training document that later agents can take over after one hour of inactivity.
- Board B rules require a factor-local workdoc and valid `/tmp` claim before substantive work.

**Impact / Compatibility:**
- No runtime code changes yet.
- Must record the new grammar, exact factor id, and takeover rule without mutating the old `MES` KAMA packet.

**Verification:**
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- `ps -axo pid,ppid,etime,command | rg -i 'run_yf_|run_ibkr_|fetch_external\.py|auto-quant|freqtrade|tomac|provider-status'`
- `STAMP="$(date +%Y%m%dT%H%M%S%z)"; PACKET="support/docs/experiments/actionable-regime-confidence/20260526T${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.md"; TMP_ROOT="/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}"; CLAIM="/tmp/ict-engine-agent-claims/board-b-factor-refinement/${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.claim"; python3 - <<PY
from pathlib import Path
import json
repo_packet = Path("$PACKET")
workdoc = Path("$TMP_ROOT/workdoc.md")
claim = Path("$CLAIM")
assert repo_packet.exists(), repo_packet
assert workdoc.exists(), workdoc
assert claim.exists(), claim
for needle in [
    "TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1",
    "5m/15m/30m/1h/4h/1d",
    "promotion_allowed=false",
    "trade_usable=false",
]:
    assert needle in repo_packet.read_text(), needle
data = json.loads(claim.read_text())
for key in ["agent_name","owner","claimed_at","last_progress_at","scope","active_task","non_goals","write_surface","status"]:
    assert key in data and data[key], key
assert data["write_surface"] == str(workdoc), data["write_surface"]
PY`

- [ ] **Step 1: Write the failing validation script**

```bash
STAMP="$(date +%Y%m%dT%H%M%S%z)"
PACKET="support/docs/experiments/actionable-regime-confidence/20260526T${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.md"
TMP_ROOT="/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}"
CLAIM="/tmp/ict-engine-agent-claims/board-b-factor-refinement/${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.claim"
python3 - <<PY
from pathlib import Path
for path in [Path("$PACKET"), Path("$TMP_ROOT/workdoc.md"), Path("$CLAIM")]:
    assert path.exists(), path
PY
```

- [ ] **Step 2: Run the script to verify it fails**

Run:
```bash
bash /tmp/kama_packet_red.sh
```
Expected: `AssertionError` on missing packet/workdoc/claim paths.

- [ ] **Step 3: Write the minimal packet, workdoc, and claim**

Packet skeleton content:
```md
# Board B IBKR M2K KAMA Efficiency Pullback Training

- factor_id: `ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1`
- branch_path:
  `TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1`
- prior_negative_sample:
  `TrendEfficiency -> KaufmanAdaptivePullback -> KaufmanAdaptivePullback -> ibkr_mes1m_kama_efficiency_pullback_7d_gate1_v1`
- context_frames: `5m/15m/30m/1h/4h/1d`
- promotion_allowed: `false`
- trade_usable: `false`
```

Claim JSON skeleton:
```json
{
  "agent_name": "codex-ibkr-m2k-kama-efficiency-pullback-training-${STAMP}",
  "owner": "codex",
  "claimed_at": "$(date +%Y-%m-%dT%H:%M:%S%z)",
  "last_progress_at": "$(date +%Y-%m-%dT%H:%M:%S%z)",
  "scope": "Board B IBKR profitability-factor training on the exact M2K 1m KAMA efficiency pullback branch using a 1m origin and full MTF context targets.",
  "active_task": "Create the authoritative packet, workdoc, and exact M2K KAMA runner before any Gate 1 launch.",
  "non_goals": [
    "Do not reopen the terminalized MES KAMA exact root.",
    "Do not lower 5bps, density, yearly stability, or downstream gates.",
    "Do not switch away from M2K unless a fresh collision audit forces MYM fallback."
  ],
  "factor_id": "ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1",
  "branch_path": "TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1",
  "write_surface": "/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}/workdoc.md",
  "tmp_root": "/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}",
  "status": "active_prep",
  "latest_report": "/tmp/ict-engine-ibkr-m2k-kama-efficiency-pullback-${STAMP}/workdoc.md",
  "promotion_allowed": false,
  "trade_usable": false,
  "update_goal": false
}
```

- [ ] **Step 4: Run verification to make it pass**

Run:
```bash
STAMP="$(date +%Y%m%dT%H%M%S%z)"
CLAIM="/tmp/ict-engine-agent-claims/board-b-factor-refinement/${STAMP}-codex-ibkr-m2k-kama-efficiency-pullback-training.claim"
python3 support/scripts/factor_claim_terminalization_audit.py --compact
python3 - <<PY
from pathlib import Path
import json
claim = json.loads(Path("$CLAIM").read_text())
assert claim["factor_id"] == "ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1"
assert "TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation" in Path(claim["write_surface"]).read_text()
PY
```
Expected: audit still may report other active claims, but the new claim is valid and the assertions pass.

- [ ] **Step 5: Commit the repo-visible packet only**

```bash
git add support/docs/experiments/actionable-regime-confidence/20260526T*-codex-ibkr-m2k-kama-efficiency-pullback-training.md
git commit -m "Add Board B M2K KAMA pullback training packet"
```

### Task 2: Build The New Exact Runner And Identity Test

**Files:**
- Create: `support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py`
- Create: `support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py`

**Why this task exists:**
- The approved grammar differs from the old `MES` KAMA script, so implementation needs a new exact runner rather than a silent reuse of the old branch contract.
- The identity test must lock the new branch path and factor id.

**Impact / Compatibility:**
- Adds a new exact-root runner without disturbing the old `MES` KAMA negative sample.
- Must keep `M2K`, `1m`, `7 D`, `IBKR`, and new grammar consistent across strategy metadata, material JSON, and labels.

**Verification:**
- `python3 -m py_compile support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py`
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py`

- [ ] **Step 1: Write the failing identity test**

```python
from pathlib import Path
import importlib.util
import unittest

SCRIPT = Path(__file__).with_name("run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py")
EXPECTED_FACTOR_ID = "ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1"
EXPECTED_BRANCH = (
    "TrendExpansion -> MtfTrendAlignment -> "
    "KAMAEfficiencyPullbackContinuation -> "
    "ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1"
)

class M2kKamaGate1IdentityTest(unittest.TestCase):
    def test_identity_contract(self) -> None:
        spec = importlib.util.spec_from_file_location("m2k_kama_gate1", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertEqual(module.base.FACTOR_ID, EXPECTED_FACTOR_ID)
        self.assertEqual(module.base.BRANCH_PATH, EXPECTED_BRANCH)
        self.assertEqual(module.base.ROOT_SYMBOL, "M2K")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py
```
Expected: file import failure because the runner does not exist yet.

- [ ] **Step 3: Write the minimal runner**

Start from the old `MES` KAMA runner pattern and change these exact fields:
```python
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-m2k1m-kama-efficiency-pullback-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260520T005518+0800-codex-ibkr-m2k1m-liquidity-sweep-reject-short-7d-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_m2k_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_M2K1M_KAMA_EFFICIENCY_PULLBACK_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1"
base.BRANCH_PATH = "TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1"
base.ROOT_SYMBOL = "M2K"
base.PRODUCT = "equity_index"
base.EXCHANGE = "CME"
base.MULTIPLIER = "5"
base.LAST_TRADE_DATE = "202606"
```

Material metadata block must include:
```python
"consumer_evidence_profile": {
    "branch_path": base.BRANCH_PATH,
    "regime_profit_branch_path": base.BRANCH_PATH,
    "main_regime": "TrendExpansion",
    "sub_regime": "MtfTrendAlignment",
    "sub_sub_regime_or_profit_factor": "KAMAEfficiencyPullbackContinuation",
    "profit_factor": base.FACTOR_ID,
    "root_symbol": "M2K",
    "root_timeframe": "1m",
    "provider": "IBKR",
}
```

- [ ] **Step 4: Run compile and identity verification**

Run:
```bash
python3 -m py_compile support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py
python3 support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py
```
Expected: `py_compile` exits `0`; test prints `Ran 1 test` and `OK`.

- [ ] **Step 5: Commit only the new runner and test**

```bash
git add support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py \
        support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_m2k1m_kama_efficiency_pullback_gate1_identity.py
git commit -m "Add M2K KAMA pullback Gate 1 runner"
```

### Task 3: Run Fresh Occupancy Audit, Direct IBKR Probe, And Exact Gate 1

**Files:**
- Use: `support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py`
- Generate: `support/docs/experiments/actionable-regime-confidence/runs/${STAMP}-codex-ibkr-m2k1m-kama-efficiency-pullback-7d-gate1-v1/...`
- Fallback only if blocked: corresponding `mym` packet/runner/test names from Tasks 1-2

**Why this task exists:**
- The user asked to continue training with AutoQuant, but only on a non-duplicate lane and only with evidence-first gates.
- Direct IBKR probe is the authoritative row-truth preflight before exact Gate 1.

**Impact / Compatibility:**
- Must not launch if compact audit shows a conflicting fresh claim for this exact lane.
- Must stop and regenerate packet/runner names for `MYM` only if `M2K` becomes occupied or row-blocked for reasons specific to the cell.

**Verification:**
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- `python3 support/scripts/auto_quant_external/fetch_external.py ibkr-historical --symbol M2K --sec-type FUT --exchange CME --currency USD --last-trade-date 202606 --multiplier 5 --bar-size '1 min' --duration '2 D' --client-id 54 --output /tmp/ibkr_m2k_202606_1m_2d_preflight.csv`
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py`
- `rg -n "decision|promotion_allowed|trade_usable|downstream_allowed|pre_bayes_allowed|bbn_allowed|catboost_allowed|execution_tree_allowed" support/docs/experiments/actionable-regime-confidence/runs/*-codex-ibkr-m2k1m-kama-efficiency-pullback-7d-gate1-v1/checks support/docs/experiments/actionable-regime-confidence/runs/*-codex-ibkr-m2k1m-kama-efficiency-pullback-7d-gate1-v1/summaries`

- [ ] **Step 1: Write the guarded launch wrapper**

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact > /tmp/kama_audit.json || true
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/tmp/kama_audit.json").read_text())
blocked = [
    c for c in data.get("attention_claims", [])
    if "kama" in (c.get("scope","").lower() + " " + str(c.get("agent_name","")).lower())
]
if blocked:
    raise SystemExit("blocked_by_kama_claim")
PY
```

- [ ] **Step 2: Run the wrapper to verify early failure works**

Run:
```bash
bash /tmp/kama_launch_guard.sh
```
Expected: exits nonzero if a same-family KAMA claim appears; otherwise exits `0`.

- [ ] **Step 3: Run direct IBKR preflight and exact Gate 1**

Run:
```bash
python3 support/scripts/auto_quant_external/fetch_external.py ibkr-historical \
  --symbol M2K \
  --sec-type FUT \
  --exchange CME \
  --currency USD \
  --last-trade-date 202606 \
  --multiplier 5 \
  --bar-size '1 min' \
  --duration '2 D' \
  --client-id 54 \
  --output /tmp/ibkr_m2k_202606_1m_2d_preflight.csv

python3 support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1.py
```

- [ ] **Step 4: Verify terminal truth**

Run:
```bash
rg -n "decision|promotion_allowed|trade_usable|downstream_allowed|pre_bayes_allowed|bbn_allowed|catboost_allowed|execution_tree_allowed" \
  support/docs/experiments/actionable-regime-confidence/runs/*-codex-ibkr-m2k1m-kama-efficiency-pullback-7d-gate1-v1/checks \
  support/docs/experiments/actionable-regime-confidence/runs/*-codex-ibkr-m2k1m-kama-efficiency-pullback-7d-gate1-v1/summaries
```
Expected: a terminal decision exists; any `promotion_allowed` or `trade_usable` claim remains `false` unless the artifacts explicitly prove otherwise.

- [ ] **Step 5: Commit only durable repo-side readback**

```bash
git add support/docs/experiments/actionable-regime-confidence/20260526T*-codex-ibkr-m2k-kama-efficiency-pullback-training.md
git commit -m "Record M2K KAMA pullback Gate 1 readback"
```

## Self-Review

- The plan implements only the approved scope: one new Board B KAMA family branch, one exact cell, one deterministic fallback.
- It preserves the old `MES` negative sample and explicitly forbids reopening it.
- Verification is exact and current-turn oriented.
- The implementation path stays evidence-first and collision-safe.
