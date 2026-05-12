# Local Training Portability and Sample Sufficiency Correction v1

This note corrects the interpretation of `141554_provider_longspan_capability_matrix_v1`.

The user did not reject local long-history training. Local data such as TOMAC can be a valid development and stress-test substrate when it gives enough candles, instruments, time spans, and trade observations to discover or harden a factor. The release/consumer constraint is separate: a published consumer cannot depend on `/Users/thrill3r/Downloads/Tomac`, so any useful locally trained factor must be converted into portable ICT Engine logic, a hot-pluggable strategy/factor spec, or a provider-backed acquisition recipe that a consumer agent can run through existing provider interfaces.

Corrected direction:

- Board A should maximize K-bar span and posterior calibration evidence. Local long-history data may train candidate regime filters, but accepted evidence must still feed provider/context validation and the ordered chain: Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree.
- Board B should maximize trade observations and regime/branch-conditioned sample counts. Results like `77` NQ trades, `115` ES trades, `153` aggregate trades, or a few daily/hourly candles are smoke/support evidence only. They are not enough to claim a stable factor or profitability lane.
- Provider-backed data is the consumer/release path, not the only research substrate. If provider coverage is shorter than local history, record the gap and use the best provider span for portability validation instead of downgrading the whole lane to tiny daily-bar tests.
- A locally trained factor is useful only if it can be moved into ICT Engine or emitted as portable agent material so a consumer can obtain the same kind of advice with their own provider data and feed it back into the Bayesian belief network.

Net gate remains fail-closed:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
