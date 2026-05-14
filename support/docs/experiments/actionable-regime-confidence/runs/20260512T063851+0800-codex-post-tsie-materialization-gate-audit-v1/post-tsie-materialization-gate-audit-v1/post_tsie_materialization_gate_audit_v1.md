# Post TSIE Materialization Gate Audit v1

Run id: `20260512T063851+0800-codex-post-tsie-materialization-gate-audit-v1`

Gate result: `post_tsie_materialization_gate_audit_v1=target_root_present_but_crisis_absent_policy_blocked_no_downstream`

Board sha256 before artifact: `57b14e94b35423f985eb01fe37a35ef9f8b6ff3813d289a7a935d7872e7c5d24`

## Readback

- R3 root present: `True`.
- R3 required files present: `True`.
- Mapped rows from provenance: `5032903`.
- Accepted mapping-confidence labels: `Bear, Bull, Sideways`.
- Missing MainRegimeV2 labels: `Crisis`.
- Rows SHA-256 from provenance: `72406e48b000f91ed2b3c3e132651537339afb2a8ed2e3ce43b5007abf38f62f`.

## Gate Decision

The R3 filesystem root is now present, but this audit does not treat it as a promotion unlock. `063215` already classified the TSIE materializer as proxy-blocked, and `063155` still leaves `Crisis` absent while canonical merge and downstream promotion remain false.

Promotion remains blocked: source/control evidence acquired `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Active Same-Scope Processes

| PID | Stat | Elapsed | Command |
|---:|---|---:|---|
| `9138` | `Ss` | `01:52` | `/bin/zsh -lc sleep 180; ps -axo pid,ppid,stat,etime,%cpu,%mem,command / rg -i '98181/062902/063155/063217/native-subhour-source-label-intake/r3_hf_tsie_native_intraday/public_source_candidate_sweep/shasum/wc -l/auto-quant/catboost/pre-bayes/bbn/execution-tree/apply_patch/target/debug/ict-engine' / rg -v 'rg -i' // true; echo '--- board-hash'; shasum -a 256 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md; echo '--- tail'; tail -n 240 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md; echo '--- root stats'; if [ -e /tmp/ict-engine-native-subhour-source-label-intake ]; then find /tmp/ict-engine-native-subhour-source-label-intake -maxdepth 2 -type f -print -exec ls -lhT {} \; 2>/dev/null / sed -n '1,80p'; else echo absent; fi; echo '--- terminal files'; find docs/experiments/actionable-regime-confidence/runs/20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1 docs/experiments/actionable-regime-confidence/runs/20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1 docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1 -maxdepth 4 -type f -print 2>/dev/null / sort / sed -n '1,280p'` |
| `10250` | `Ss` | `01:14` | `/bin/zsh -lc sleep 240; ps -axo pid,ppid,stat,lstart,etime,command / rg '062902/063155/063217/native_subhour/source-label-intake/target/debug/ict-engine/cargo/rustc/python/duckdb/uv run/shasum/sed -n 1,8p' / rg -v 'rg ' // true; echo '--- target root stat'; find /tmp/ict-engine-native-subhour-source-label-intake -maxdepth 2 -type f -print -exec ls -lhT {} \; 2>/dev/null / sed -n '1,120p'; echo '--- board'; sha256sum docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md` |
| `11581` | `Ss` | `00:45` | `/bin/zsh -lc wc -l /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv; shasum -a 256 /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json; jq -S . /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json / sed -n '1,240p'` |
| `11990` | `Ss` | `00:39` | `/bin/zsh -lc sleep 90; ps -axo pid,etime,command / rg -i "062902/063155/063215/063217/063707/063733/063734/063851/public-source-candidate/native_subhour/source-label-intake/shasum/target/debug/ict-engine/auto.?quant/catboost/path.?rank/execution-tree/apply_patch/docs/plans/2026-05-10-regime-conditional" / rg -v "rg -i"; printf '\n--- hash ---\n'; shasum -a 256 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md; printf '\n--- latest ids ---\n'; rg -n "062902/063155/063215/063217/063707/063733/063734/063851/target-root/materialization/quarantine/post-tsie" docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md / tail -n 220; printf '\n--- tail ---\n'; tail -n 140 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md; printf '\n--- dirs ---\n'; find docs/experiments/actionable-regime-confidence/runs -maxdepth 1 -type d \( -name '*062902*' -o -name '*063155*' -o -name '*063215*' -o -name '*063217*' -o -name '*063707*' -o -name '*063733*' -o -name '*063734*' -o -name '*063851*' -o -name '*0639*' \) -print / sort` |
| `12015` | `Rs` | `00:39` | `/usr/bin/perl /usr/bin/shasum -a 256 /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json` |
| `12364` | `R` | `00:33` | `/usr/bin/perl /usr/bin/shasum -a 256 /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv /tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json` |
| `12450` | `Ss` | `00:32` | `/bin/zsh -lc while ps -p 7411 >/dev/null 2>&1 // ps -p 9391 >/dev/null 2>&1 // ps -p 2532 >/dev/null 2>&1; do sleep 20; done; echo active_checks_settled; ps -axo pid,ppid,etime,stat,command / rg -i '063155/063217/062902/source-label-intake/native_subhour/target/debug/ict-engine/cargo/rustc/python/shasum/docs/plans/2026-05-10/apply_patch' / rg -v 'rg -i' // true; printf '\n--- hash ---\n'; shasum -a 256 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md; printf '\n--- board hits ---\n'; rg -n '063155/063217/063215/native_subhour/source-label-intake/target_root_mutated/Crisis/count_once:063155/count_once:063217/public_source_candidate_sweep' docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md / tail -n 220 // true; printf '\n--- tail ---\n'; tail -n 160 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md` |
| `12648` | `Ss` | `00:28` | `/bin/zsh -lc while ps -p 9391 >/dev/null 2>&1 // ps -p 11581 >/dev/null 2>&1 // ps -p 12015 >/dev/null 2>&1; do sleep 20; done; echo settled2; ps -axo pid,ppid,stat,lstart,etime,command / rg -i '062902/063155/063217/063/native_subhour/source-label-intake/public-source/target/debug/ict-engine/cargo/rustc/python/duckdb/pyarrow/uv run/shasum/auto-quant/catboost/pre-bayes/bbn/execution-tree/path-ranker' / rg -v 'rg -i' // true; echo '--- board'; shasum -a 256 docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md; echo '--- target root'; find /tmp/ict-engine-native-subhour-source-label-intake -maxdepth 3 -type f -print 2>/dev/null / sort / xargs -r ls -lhT` |
| `12865` | `Ss` | `00:20` | `/bin/zsh -lc while ps -p 9391 >/dev/null 2>&1; do sleep 20; done; echo public_source_sweep_settled; find docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1 -maxdepth 4 -type f -print 2>/dev/null / sort / sed -n '1,240p'; ps -axo pid,ppid,stat,etime,command / rg -i '063217/063155/062902/native_subhour/source-label-intake/actionable-regime/target/debug/ict-engine/auto.?quant/catboost/bbn/pre-bayes/execution-tree/python/duckdb/uv run' / rg -v 'rg -i' // true` |
| `12921` | `Ss` | `00:19` | `/bin/zsh -lc sleep 90; ps -eo pid,ppid,stat,etime,command / rg -i '063217/public_source_candidate/native-subhour-intake/source-label-intake/target/debug/ict-engine/cargo/rustc/python/duckdb/uv run/shasum/auto.?quant/catboost/pre-bayes/bbn/execution-tree/workflow-status/find docs/experiments/actionable' / rg -v 'rg -i/zsh -lc ps'; printf '\n--- root stat ---\n'; find /tmp/ict-engine-native-subhour-source-label-intake -maxdepth 2 -type f -print -exec ls -lh {} \; 2>/dev/null / sed -n '1,80p'; printf '\n--- board ---\n'; sha256sum docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md` |
| `13035` | `Ss` | `00:16` | `/bin/zsh -lc while ps -axo command / rg -q '/tmp/ict-engine-native-subhour-source-label-intake.*(wc -l/shasum/jq/head)' ; do date '+%Y-%m-%dT%H:%M:%S%z readback_active'; sleep 10; done; echo readback_processes_settled` |
| `13171` | `Ss` | `00:11` | `/bin/zsh -lc sleep 90\012ps -axo pid,ppid,stat,etime,%cpu,%mem,command / rg -i '9391/063217/native-subhour-source-label-intake/source-label-intake/shasum/wc -l/jq -S/062902/063155/public_source_sweep/target/debug/ict-engine/auto.?quant/catboost/pre.?bayes/bbn/path.?rank/execution.?tree/apply_patch' / rg -v 'rg -i'` |
| `13373` | `Ss` | `00:05` | `/bin/zsh -lc sleep 90; ps -axo pid,ppid,stat,etime,command / rg '063155/063217/062902/native-subhour-source-label-intake/shasum/wc -l/public_source_candidate_sweep/r3_tsie_native_subhour/r3_hf_tsie_native/auto-quant/catboost/pre-bayes/bbn/execution-tree' / rg -v 'rg '` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T063851+0800-codex-post-tsie-materialization-gate-audit-v1/post-tsie-materialization-gate-audit-v1/post_tsie_materialization_gate_audit_v1.json`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063851+0800-codex-post-tsie-materialization-gate-audit-v1/post-tsie-materialization-gate-audit-v1/post_tsie_materialization_required_roots_v1.csv`
- Active processes CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063851+0800-codex-post-tsie-materialization-gate-audit-v1/post-tsie-materialization-gate-audit-v1/post_tsie_materialization_active_processes_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T063851+0800-codex-post-tsie-materialization-gate-audit-v1/checks/post_tsie_materialization_gate_audit_v1_assertions.out`

## Next

Do not run canonical merge or provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion from this TSIE root. Continue only from explicit source/control approval, real R6 owner/export rows with controls, source-owned R5 recency rows, or a new verifier-native R3 source that covers all required MainRegimeV2 labels.
