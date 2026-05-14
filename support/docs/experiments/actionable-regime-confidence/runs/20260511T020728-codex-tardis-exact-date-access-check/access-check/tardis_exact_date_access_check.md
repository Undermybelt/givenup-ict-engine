# Tardis Exact-Date Access Check

Run id: `20260511T020728+0800-codex-tardis-exact-date-access-check`

This audit probes exact-date Tardis Binance URLs for labeled pump-event candidates. It reads only small response prefixes and does not save raw market data.

- Event candidates: 12
- URL probes: 36
- Accessible without credentials: 0
- Unauthorized / authorization required responses: 33
- Manipulation input state: `credentialed_exact_date_export_required`

Decision: Exact-date Tardis Binance URLs for labeled pump events did not return usable gzip market data without credentials; the probes returned no usable market payload and require credentialed export before calibration.

Next action: Provide a Tardis API key or pre-export the exact-date Binance trades/L2 files for the labeled pump events, then rerun the Manipulation calibration gate; continue Bull/Bear/Sideways only with materially new signed-direction/sideways inputs.
