# ICT Engine repo audit and consumer/contributor review

Use when asked to audit the whole ICT Engine repo across architecture, function, closed loop, tests, user experience, consumer perspective, and open-source contributor perspective.

## Scope

Session path: `<ict-engine-repo>`.
Do not use subagents/delegate if the user forbids them.
Prefer read-only inspection and `/tmp/...` state dirs for smoke runs.

## Required first-pass commands

```bash
# repo + dirty tree
git status --short
git branch --show-current
git rev-parse --show-toplevel

# size/surface
python3 - <<'PY'
import os,re,collections
for ext,name in [('.rs','rust'),('.py','python'),('.md','markdown'),('.json','json')]:
    n=loc=0
    for dp,ds,fs in os.walk('.'):
        ds[:] = [d for d in ds if d not in {'.git','target','state','.venv','venv','__pycache__'} and not d.startswith('state_')]
        for f in fs:
            if f.endswith(ext):
                n+=1
                try: loc+=sum(1 for _ in open(os.path.join(dp,f),errors='ignore'))
                except Exception: pass
    print(f'{name}: files={n} loc={loc}')
PY

# CLI inventory
python3 - <<'PY'
import re
s=open('src/main.rs').read()
m=re.search(r'enum Commands \{(.*?)\n\}',s,re.S)
cmds=[]
for line in m.group(1).splitlines():
    mm=re.match(r'\s*([A-Z][A-Za-z0-9]+)\s*\{',line)
    if mm: cmds.append(mm.group(1))
print(len(cmds))
print('\n'.join(cmds))
PY
```

## Smoke audit commands

Use existing binary when present; avoids burning time on rebuild before UX checks.

```bash
./target/debug/ict-engine --help | sed -n '1,120p'
./target/debug/ict-engine analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-audit-demo --human
./target/debug/ict-engine factor-research --symbol DEMO --data examples/demo/demo-15m.json --state-dir /tmp/ict-engine-audit-demo --backend native --human
./target/debug/ict-engine workflow-status --symbol DEMO --state-dir /tmp/ict-engine-audit-demo --human
./target/debug/ict-engine provider-status --compact
./target/debug/ict-engine export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-audit-demo
./target/debug/ict-engine policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-audit-demo --human
```

Expected observations from May 2026 audit:
- `analyze --demo --human` works and prints compact desk-style output.
- `factor-research --backend native --human` works on `examples/demo/demo-15m.json`.
- `workflow-status --human` works but wording is still agent-internal.
- `provider-status --compact` is high-value for consumer readiness.
- `export-structural-path-ranking-target` does not support `--human`.
- `artifact-status --latest-only` does not support `--human`.
- missing score file in `apply-structural-path-ranking-external-scores` emits raw OS error only.

## Validation commands and caveats

```bash
cargo check --all-targets
cargo test --no-run
```

Caveats:
- `cargo check --all-targets` can take ~15-17 minutes on this repo.
- Avoid launching multiple cargo builds in the same target dir; it causes `Blocking waiting for file lock` and can make audit timing misleading.
- If a background cargo process is running, poll it instead of starting another.

## Audit findings template

Report concise sections:
1. Baseline facts: path, branch, size, command count, test count, CI shape, dirty tree.
2. Architecture: domain/application/factor_lab/bbn/market_state/state/scripts split; call out `src/main.rs` size debt.
3. Function: list major command surfaces and whether demo smoke worked.
4. Closed loop: analyze -> factor-research -> target export -> external ranker -> apply/register -> update -> workflow-status; separate completed surfaces from validation gaps.
5. Tests: Rust test volume, CI gates, Python coverage weakness, cargo timing/lock caveat.
6. Actual UX: what works in `--human`, what remains internal/opaque.
7. Consumer view: first-run clarity, data/provider readiness, state-dir pollution risk.
8. Contributor view: AGENTS/README/docs strengths, main.rs/docs/scripts debt, missing CONTRIBUTING/contract gaps.
9. Prioritized risks and next actions.

## Key pitfalls

### Dirty tree may change during audit

The user or another process may edit files while the audit runs. Run `git status --short` at start and before final. Do not revert unrelated changes. Mention if final working tree changed unexpectedly.

### Repo state vs generated state

For fair audit, write smoke state to `/tmp/...`. Do not create repo-local `state_*` dirs. Check tracked pollution:

```bash
git ls-files | grep -E '(^state/|^state_|__pycache__|\.pyc$)'
```

### Policy-training maturity wording

Do not equate feedback observations with `raw_scored_mature` rows. The engine currently reports row-level target validation; repeated feedback history may not raise `raw_scored_mature` to 30 unless target export preserves distinct candidate/path rows.

### Execution SHAP wording

`execution_tree.rs` uses deterministic structural attributions by default. Do not imply true CatBoost/XGBoost SHAP unless a real external model-SHAP provider is wired and verified.

### AGENTS.md factor status conflict

AGENTS.md may contain stale text: E/F/H can be active compute stubs in one table while still marked MISSING in design-gap rows. Audit should flag this as doc drift.

## Consumer/contributor heuristics

Consumer product maturity is lower than research maturity when:
- command surface is large (49 commands observed),
- `--human` is inconsistent,
- real data setup requires reading multiple docs,
- default state can write repo-local `state/`,
- output uses internal terms (PDA/BBN/MECE/pre-bayes) without a single current contract page.

Contributor friendliness improves when:
- `AGENTS.md`, `README.md`, `docs/first-run.md`, `docs/research-system-map.md`, and `docs/smoke-acceptance.md` are current,
- `main.rs` keeps shrinking,
- Python public wrappers are separated from archived experiments,
- command output contracts and smoke acceptance are automated.
