# CatBoost apply environment and post-apply fail-closed readback

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session pattern: a regime-rooted 1m Gate 1 candidate can pass Auto-Quant strongly, train CatBoost, and still remain non-tradeable after the CatBoost apply blocker is fixed.

Observed durable workflow:

1. If `pandas_path_ranker_trainer.py --apply` fails because `catboost_model.cbm` exists but the current Python cannot import `catboost`, rerun the apply step with the known CatBoost-capable Python on this host, e.g. `/opt/anaconda3/bin/python3`, rather than treating CatBoost as failed.
2. Then apply scores back into ict-engine, register the trainer artifact, enable structural path ranking runtime, and refresh `workflow-status`, `pre-bayes-status`, and `policy-training-status`.
3. Do not promote just because Gate 1 and CatBoost apply are now clean. Re-read exact-root downstream gates:
   - `exact_branch_survived=true`
   - `execution_candidate_actionable=true`
   - `pda_hybrid_alignment=true`
   - `transition_hazard < 0.60`
   - `execution_readiness >= 0.65`
4. If `analyze` after applying ranker scores hangs or is too slow, stop the runaway process and use the status/readback surfaces already written under the same state dir to classify the branch. Mark the analyze timeout separately; do not let it mask gate results.

Example terminal outcome from this session:

- Gate 1: IONQ/1m, 23 trades, +5.19%, win 82.61%, sharpe 88.65.
- CatBoost train: succeeded.
- CatBoost apply: initially failed under a Python without `catboost`, then succeeded under `/opt/anaconda3/bin/python3`.
- Post-apply readback: exact branch survived, but `actionable=false`, `execution_readiness=0.3907689527453563`, `transition_hazard=0.9778854694121671`, `pda_hybrid_alignment=false`.
- Verdict: `gate1_pass_downstream_fail_closed_after_catboost_apply`, not trade usable.

Decision rule: fixing a tooling/apply blocker only restores downstream evidence quality; it does not relax promotion gates.
