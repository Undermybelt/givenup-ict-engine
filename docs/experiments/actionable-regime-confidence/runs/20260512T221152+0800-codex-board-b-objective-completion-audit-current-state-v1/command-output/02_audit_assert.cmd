python3 - <<'PY'
import json
p='materials/prompt_to_artifact_checklist.json'
d=json.load(open(p))
assert d['completion_status']=='not_achieved'
assert d['promotion_allowed'] is False
assert d['trade_usable'] is False
assert d['update_goal'] is False
statuses={r['status'] for r in d['checklist']}
assert 'not_met' in statuses
print('objective_completion_audit_assert=pass completion_status=not_achieved promotion_allowed=false update_goal=false')
PY
