# 044701 In-Flight Terminal Guard v1

Timestamp: `2026-05-12T04:57:34+0800`

Source packet:

- `docs/experiments/actionable-regime-confidence/runs/20260512T044701-codex-source-label-single-atom-qualifier-scan-v1`

Observed writer state:

- `90697`: shell wrapper active.
- `90743`: `uv run --with pandas --with numpy python ...source_label_single_atom_qualifier_scan_v1.py` active.
- `91172`: Python worker active.

Observed command-output files:

- `command-output/source_label_single_atom_qualifier_scan.exit`: `2` bytes, sha256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`, content observed as `0`.
- `command-output/source_label_single_atom_qualifier_scan.stdout.json`: `3920` bytes, sha256 `fde7df9752ca476746e7140ff4511690de4ba66a949f25a7d48ac29ca3769804`.
- `command-output/source_label_single_atom_qualifier_scan.stderr.txt`: `0` bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- `source-label-single-atom-qualifier-scan-v1/source_label_single_atom_qualifier_scan_v1.json`: `3919` bytes, sha256 `1b224fb3f052b551889531319085e1795bf892a6b1ac0997c9eadc6051972e23`.

Readback:

- The packet already has an exit file and payload files, but at least one writer process remains active against the same source packet.
- This is therefore not stable terminal evidence.
- The scan result is not consumed, not promoted, and not used for downstream reruns.

Gate:

- `diagnostic_only:044701_inflight_terminal_guard`.
- `in_progress:source_label_single_atom_qualifier_scan`.
- `fail_closed:writer_active_while_exit_and_payload_files_exist`.
- `not_consumed:unstable_terminal_packet`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

Next:

- Do not consume `044701` until all writer processes have exited and the stdout/stderr/exit/report hashes remain stable across a fresh readback. Keep `034002` as the fail-closed cursor.
