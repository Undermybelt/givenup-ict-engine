# TSIE Negative Packet Reconciliation After 062409 v1

Run id: `20260512T062657+0800-codex-tsie-negative-packet-reconciliation-after-062409-v1`

Gate result: `tsie_negative_packet_reconciliation_after_062409_v1=tsie_packets_counted_or_scoped_no_required_root_no_promotion`

## Scope

This packet reconciles TSIE follow-up artifacts observed after the `062409` R3/R5 source-selection readback. It is a ledger reconciliation only: it does not copy files into `/tmp/ict-engine-native-subhour-source-label-intake`, `/tmp/ict-engine-source-panel-recency-extension`, or `/tmp/ict-engine-board-a-r6-owner-export-v1`; it does not approve source/control evidence, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Packet Disposition

| Root | Disposition | Counting |
|---|---|---|
| `20260512T062201+0800-codex-r3-hf-tsie-provenance-decision-v1` | TSIE provenance/policy rejection: labels are rule-based/OHLCV-derived proxy labels, not independent source-owned `MainRegimeV2` evidence. | Count once as provenance negative evidence. |
| `20260512T062205+0800-codex-r3-hf-tsie-raw-download-verify-v1` | Transport-attempt packet with report and assertions; it recorded CAS/Xet raw download failures. Later full-parquet presence elsewhere supersedes only its raw-availability snapshot, not its non-promotion decision. | Count once as historical transport-attempt evidence only; not latest raw-availability evidence. |
| `20260512T062256+0800-codex-r3-hf-tsie-native-subhour-failclosed-v1` | Fail-closed eligibility decision: public/native-subhour fields exist, but labels are generated from price/volatility/RSI/volume logic, no direct `Crisis` semantic, and trap labels do not cleanly map to `MainRegimeV2`. | Count once as R3 policy failure evidence. |
| `20260512T062440+0800-codex-r3-tsie-parquet-transport-retry-after-061855-v1` | Transport retry downloaded only a 1 MB range in that run, confirmed the dataset-server row API cap, and did not intake raw data. | Count once as transport retry evidence only. |

## Local Raw Readback

- Full TSIE parquet exists in `/private/tmp/ict-engine-r3-hf-tsie-native-subhour-intake-v1/raw/tft_dataset_labeled.parquet` with SHA-256 `8b6f25f8b2aba162af2eac30b1a8a9df662fc5dd04878e933f42c8df4eaa6158`.
- The same SHA-256 exists at `/private/tmp/ict-engine-r3-tsie-native-subhour-source-v1/tft_dataset_labeled.parquet`.
- `/private/tmp/ict-engine-r3-hf-tsie-raw-v1/0000.parquet` is a zero-byte failed transport artifact with SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- None of these paths is a required Board A target root.

## Decision

The TSIE branch remains non-promoting even when full parquet evidence is locally available. Blocking reasons are policy and validation blockers, not only transport: rule/OHLCV-generated labels, no direct `Crisis` semantic, single IDX context, no accepted `MainRegimeV2` equivalence, exact active R3 target cells absent, and prior full-parquet gates accepted `0` roots.

Required roots remain absent:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, source-owned R3 native-subhour labels with accepted `MainRegimeV2` equivalence, or a genuinely new cross-timeframe `MainRegimeV2` export. Do not rerun provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion until a required target root unlocks.
