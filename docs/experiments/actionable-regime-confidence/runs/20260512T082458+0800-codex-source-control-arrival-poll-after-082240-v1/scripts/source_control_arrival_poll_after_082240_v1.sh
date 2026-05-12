#!/usr/bin/env bash
set -euo pipefail

for path in \
  /tmp/ict-engine-board-a-r6-owner-export-v1 \
  /tmp/ict-engine-source-panel-recency-extension \
  /tmp/ict-engine-native-subhour-source-label-intake \
  /private/tmp/r6_oystacher_approval_decision_package_v1.json.valid
do
  if [ -e "${path}" ]; then
    printf '%s\tEXISTS\n' "${path}"
  else
    printf '%s\tABSENT\n' "${path}"
  fi
done

env | cut -d= -f1 | rg -i 'CME|CBOE|CFE|FINRA|CAT|DATABENTO|BARCHART|POLYGON|NASDAQ|IBKR|TRADINGVIEW|KRAKEN|ALPACA|OPRA|CFTC|COURTLISTENER|PACER|RECAP' | sort || true

command -v databento || true
command -v dbn || true
command -v kaggle || true
command -v uv || true
command -v cargo || true

python3 - <<'PY'
mods = ['databento', 'dbn', 'pyarrow', 'pandas', 'requests']
for name in mods:
    try:
        __import__(name)
        print(f'{name}=present')
    except Exception as exc:
        print(f'{name}=absent:{type(exc).__name__}')
PY
