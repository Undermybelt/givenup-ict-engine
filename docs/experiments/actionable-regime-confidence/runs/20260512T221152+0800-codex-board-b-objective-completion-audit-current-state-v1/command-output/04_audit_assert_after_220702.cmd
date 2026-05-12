python3 - <<'PY'
import json
p='materials/prompt_to_artifact_checklist.json'
d=json.load(open(p))
assert d['completion_status']=='not_achieved'
assert d['promotion_allowed'] is False
assert d['trade_usable'] is False
assert d['update_goal'] is False
assert any(r['requirement']=='execution_tree_admission' and r['status']=='not_met' for r in d['checklist'])
assert any(r['requirement']=='catboost_path_ranker' and r['status']=='partial' for r in d['checklist'])
print('objective_completion_audit_assert=pass completion_status=not_achieved catboost_partial execution_tree_not_met update_goal=false')
PY
