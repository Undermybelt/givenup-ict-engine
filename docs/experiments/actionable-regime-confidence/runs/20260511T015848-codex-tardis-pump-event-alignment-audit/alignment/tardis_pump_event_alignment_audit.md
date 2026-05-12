# Tardis Pump Event Alignment Audit

Run id: `20260511T015848+0800-codex-tardis-pump-event-alignment-audit`

This audit checks whether the labeled Binance pump-and-dump events can be aligned with public no-key Tardis first-day direct L2/order-book data. It does not save raw Tardis data.

Counts:
- Binance pump events: 520
- Binance first-day pump events: 15
- Candidate pairs present in Tardis metadata: 452
- Candidate pairs available on exact event date: 9
- Public first-day aligned labeled direct-L2 events: 0

Decision: `pump_labels_do_not_align_with_public_tardis_first_day_l2`. Accepted 95: `False`. Blocker: Pump-and-dump labels are useful event supervision, and Tardis has direct L2 fields, but the public no-key first-day Tardis samples do not align with any Binance pump event that also has Tardis symbol availability on the event date.

Next action: Use a credentialed historical Tardis/Binance export for the nine Binance pump events whose symbols are available on their exact event dates, or provide another labeled direct L2/L3/order-lifecycle manipulation dataset before rerunning the unchanged gate.
