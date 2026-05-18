# ICT Structure Direction Hotplug Handoff TODO

Created: 2026-05-18 23:27:29 +0800

## Goal

Make price-structure direction confirmation practical without hard-coding maintainer-local data:

- zero-config consumers keep the current public path and do not need private ICT scripts or local files;
- maintainer/local ICT structure data can be used only through an explicit opt-in hotplug;
- execution direction confirmation is owned by CISD/MSS-style directional structure, not by generic PDA cluster labels;
- transition remains observe-only unless a later confirmed direction appears;
- OB/FVG/liquidity/RB/BPR/iFVG remain directional context, confluence, invalidation, or setup quality, but cannot alone promote execution direction.

## Done

- Routed task through Hermes `sd/ict-engi-fact-rese-muta` and repo agent contracts.
- Audited existing PDA alignment path:
  - `src/domain/regime/hybrid.rs`
  - `src/pda_sequence/analysis.rs`
  - `src/pda_sequence/emitter.rs`
  - `src/pda_sequence/token.rs`
  - `tests/regime_core_first_pass.rs`
- Confirmed root bug: `transition` PDA was previously allowed to align with any hybrid family.
- Fixed fail-closed behavior:
  - `transition` no longer counts as alignment.
  - PDA summary now carries `primary_cluster_direction` and `primary_cluster_directional_confirmation_ratio`.
  - PDA emitter preserves event direction and marks CISD/MSS as directional confirmation.
  - Hybrid evidence emits `structure_direction_confirmed` and `structure_direction_confirmation_source=cisd_mss`.
- Verified:
  - `CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo test hybrid_regime_packet --test regime_core_first_pass`
  - Result: 5 passed.
  - `CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo test pda_sequence`
  - Result: 58 lib + 7 main tests passed, plus filtered integration harnesses.
- Added optional structure-direction hotplug:
  - module: `src/application/structure_direction_hotplug.rs`;
  - CLI: `analyze --structure-events <json>`;
  - no flag means no personal/local script dependency;
  - JSON events can confirm direction only through CISD/MSS/market-structure-shift style events;
  - OB/FVG/liquidity/RB/BPR remain context unless paired with confirmed direction.
- Verified hotplug:
  - `CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo test structure_direction_hotplug`
  - Result: 4 library tests plus 1 `analyze` integration-style unit test passed.
- Re-verified hybrid gate after hotplug/fmt:
  - `CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo test hybrid_regime_packet --test regime_core_first_pass`
  - Result: 5 passed.

## Now

- Review current diff and make a selective commit if the slice is coherent.
- Keep personal/local script usage opt-in; no `/Users/...` path or private dataset is required by default CLI behavior.

## Next

- Update Board B wording after tests pass: live readiness requires `structure_direction_confirmed=true`, `transition_hazard < 0.60`, and `execution_readiness >= 0.65`; PDA cluster context is advisory, not direction owner.
- Consider a later explicit MSS token kind. Current implementation marks MSS as a confirmed `StructureBreak` to avoid a breaking PDA vocabulary change in this slice.

## Decisions

- Direction owner: CISD/MSS-style confirmed structure.
- Context only: OB/FVG/liquidity/RB/BPR and generic PDA cluster family.
- Transition: always observe-only until direction confirmation exists.
- Personal/local ICT scripts: allowed as opt-in source material only; never default runtime input.

## Open Risks

- Existing scripts/docs may still mention `pda_hybrid_alignment=true` as a practical gate. Those should be corrected to `structure_direction_confirmed=true` or marked legacy context.
- The current PDA token enum reuses `StructureBreak` for MSS confirmation; a later cleanup may add an explicit MSS token, but that is a breaking PDA vocabulary change and should be handled deliberately.
