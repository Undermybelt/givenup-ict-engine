# Bayi-Hu Event/Social Manipulation Gate

Run id: `20260511T021647+0800-codex-bayi-hu-event-social-manipulation-gate`

This bounded gate used directly downloadable Bayi-Hu P&D event and message-label files. It kept only counts and split metadata in the repo; no raw event/message files were committed.

Support:
- Positive P&D events: 1335
- Exchanges: 14
- Coins: 277
- Chronological split positive events: train 667, calibration 334, test 334
- Manual message labels: 5146, counts {'0': 3654, '1': 847, '2': 630, '?': 15}
- Predicted pump-message rows: 36696

Decision: `event_social_positive_events_available_negative_controls_missing`. Accepted 95: `False`. Blocker: Bayi-Hu provides directly downloadable positive pump/dump event and message-label evidence, but this source does not include explicit negative event controls or aligned market features. A calibrated 95% Manipulation precision gate cannot be computed without them.

Next action: Add explicit negative controls or aligned market features for the Bayi-Hu event windows, then rerun the unchanged chronological Manipulation gate.
