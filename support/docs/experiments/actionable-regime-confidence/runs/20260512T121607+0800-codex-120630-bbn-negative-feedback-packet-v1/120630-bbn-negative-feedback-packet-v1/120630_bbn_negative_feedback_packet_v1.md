# 120630 BBN Negative Feedback Packet v1

Run id: `20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1`
Source downstream run: `20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Result
- Rows: `237`; wins `81`; losses `156`; win rate `0.341772`; loss rate `0.658228`.
- Branches: `{'Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1': {'rows': 164, 'wins': 63, 'losses': 101, 'breakeven': 0, 'win_rate': 0.384146, 'loss_rate': 0.615854, 'total_pnl': 348.541397, 'avg_pnl': 2.125252}, 'Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1': {'rows': 73, 'wins': 18, 'losses': 55, 'breakeven': 0, 'win_rate': 0.246575, 'loss_rate': 0.753425, 'total_pnl': -532.540152, 'avg_pnl': -7.295071}}`.
- Provider reliability candidates: `{'binance_public': {'rows': 52, 'win_rate': 0.346154, 'loss_rate': 0.653846, 'suggested_reliability_weight': 0.346154, 'negative_sample_weight': 0.653846}, 'bybit_public': {'rows': 51, 'win_rate': 0.352941, 'loss_rate': 0.647059, 'suggested_reliability_weight': 0.352941, 'negative_sample_weight': 0.647059}, 'ibkr_paxos_long_midpoint': {'rows': 44, 'win_rate': 0.340909, 'loss_rate': 0.659091, 'suggested_reliability_weight': 0.340909, 'negative_sample_weight': 0.659091}, 'kraken_public': {'rows': 32, 'win_rate': 0.3125, 'loss_rate': 0.6875, 'suggested_reliability_weight': 0.3125, 'negative_sample_weight': 0.6875}, 'tvr_default_binance': {'rows': 37, 'win_rate': 0.27027, 'loss_rate': 0.72973, 'suggested_reliability_weight': 0.27027, 'negative_sample_weight': 0.72973}, 'yfinance': {'rows': 21, 'win_rate': 0.47619, 'loss_rate': 0.52381, 'suggested_reliability_weight': 0.47619, 'negative_sample_weight': 0.52381}}`.
- Pre-Bayes gate: `pass_neutralized`; active structural regime `range` confidence `0.5250864595751618`.
- CatBoost/path-ranker: raw scored mature `237/30`, production validation `237/30`, runtime `enabled_candidate_set_ready`.
- Execution tree: ready `False`, actionable `False`, review `observe`, readiness `0.32853919817900823`.

## BBN Feedback Candidate
- This packet is candidate evidence for likelihood/CPD calibration, not direct prior overwrite.
- Context: `entry_quality=medium,factor_alignment=mixed,factor_uncertainty=low`.
- Current CPD: `{'parents': ['entry_quality', 'factor_alignment', 'factor_uncertainty'], 'parent_state_names': ['medium', 'mixed', 'low'], 'parent_indexes': [1, 1, 0], 'states': ['win', 'breakeven', 'loss'], 'current_probs': [0.427961, 0.275927, 0.296112]}`.
- Empirical outcome: `{'states': ['win', 'breakeven', 'loss'], 'probs': [0.341772, 0.0, 0.658228], 'rows': 237}`.

## Decision
- Gate: `120630_bbn_negative_feedback_packet_v1=candidate_likelihood_feedback_only_no_promotion`.
- Feed this into chronological/cross-context BBN calibration and CatBoost hard-negative queues.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_packet_v1.json`
- Provider/branch CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_by_provider_branch_v1.csv`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/120630-bbn-negative-feedback-packet-v1/prompt_to_artifact_checklist_120630_bbn_negative_feedback_packet_v1.csv`
