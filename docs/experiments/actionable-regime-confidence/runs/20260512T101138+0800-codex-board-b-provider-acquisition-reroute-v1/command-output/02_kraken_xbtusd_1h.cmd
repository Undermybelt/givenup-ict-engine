uv run --with pandas --with requests python scripts/auto_quant_external/fetch_external.py kraken-kline --market spot --pair XBTUSD --interval 1h --output $ROOT/provider-data/kraken_XBTUSD_1h.csv
