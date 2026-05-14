# Unauthenticated Root Label Source Probe Readback

Run id: `20260511T084353+0800-codex-unauth-root-label-source-probe`

## Result

- Active taxonomy: `MainRegimeV2`.
- Roots: `Bull`, `Bear`, `Sideways`, `Crisis`; `Manipulation` remains a separate direct-event overlay.
- Accepted new MainRegimeV2 root-label slots: `0`.
- Accepted new direct `Manipulation` sources: `0`.
- Attached root-label slots remain `48/612`.
- Missing/rejected root-label slots remain `564/612`.
- Gate result: `blocked_unauth_root_label_source_probe_no_new_slots`.

## Evidence Consumed

- `20260511T084131` root-label source acquisition probe: no new unauthenticated source labels for the 564 missing slots.
- `20260511T084023` unauthenticated HF/source metadata probe: no accepted independent label panel.
- `20260511T083150` Dune probe: Dune schema is promising, but no authenticated export exists in this environment.

## Next

External blocker: provide or authenticate a real independent source-label panel/export for the 564 missing MainRegimeV2 root-label slots, or provide `DUNE_API_KEY` / public Dune export rows for direct `Manipulation` wash-trade windows.

Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
