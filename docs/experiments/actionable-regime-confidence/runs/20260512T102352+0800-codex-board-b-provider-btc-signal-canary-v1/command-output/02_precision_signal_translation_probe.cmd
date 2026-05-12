/Users/thrill3r/Auto-Quant/.venv/bin/python - <<'PY'
from freqtrade.exchange.exchange_utils import amount_to_contract_precision
import ccxt
stake=9900.0
price=68600.29
amount=stake/price
print(f"ccxt_DECIMAL_PLACES={ccxt.DECIMAL_PLACES}")
print(f"ccxt_SIGNIFICANT_DIGITS={ccxt.SIGNIFICANT_DIGITS}")
print(f"ccxt_TICK_SIZE={ccxt.TICK_SIZE}")
print(f"sample_stake={stake}")
print(f"sample_price={price}")
print(f"raw_amount={amount}")
print(f"amount_precision_old_8_tick_size={amount_to_contract_precision(amount, 8, ccxt.TICK_SIZE, 1)}")
print(f"amount_precision_fixed_1e-8_tick_size={amount_to_contract_precision(amount, 0.00000001, ccxt.TICK_SIZE, 1)}")
print("root_cause=old synthetic precision amount=8 is an 8-unit tick in ccxt TICK_SIZE mode, so sub-unit BTC entries rounded to zero stake and _enter_trade returned None")
PY
