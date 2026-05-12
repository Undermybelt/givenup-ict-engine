# Tardis L2 Signature Probe

Run id: `20260511T015638+0800-codex-tardis-l2-signature-probe`

This run streamed bounded public Tardis first-day direct L2/order-book samples across multiple months and exchanges. It kept only compact derived feature summaries in the repo, not full raw order-book files.

Explicit signatures tested:
- snapshot wall imbalance,
- wall cancellation without immediate price movement,
- layering-stack depth imbalance,
- incremental L2 update bursts,
- one-sided cancellation bursts.

Accessible source count: 9 / 9.
Signature candidate events: 65903.
Gate: `blocked_unlabeled_direct_l2_signatures`.
Reason: Public Tardis first-day samples can produce direct-L2 signature features, but there is no labeled/event-confirmed manipulation truth and no chronological positive/negative calibration set. Signature counts remain candidate evidence only.

These are unlabeled direct-L2 signatures, not accepted manipulation proof.
