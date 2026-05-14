timeout_seconds=180
uv run --with redis --with ib_async --with pandas --with requests python scripts/auto_quant_external/fetch_external.py ibkr-historical --symbol SPY --sec-type STK --exchange SMART --primary-exchange ARCA --currency USD --bar-size 1\ hour --duration 5\ Y --what-to-show TRADES --port 4002 --client-id 46 --output /tmp/ict-provider-longspan-20260512T141554+0800/ibkr_spy_1h_5y.csv 
