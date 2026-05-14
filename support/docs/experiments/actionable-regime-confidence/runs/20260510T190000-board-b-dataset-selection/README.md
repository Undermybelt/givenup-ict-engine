# Board B dataset selection checkpoint

Loop ID: `20260510T190000+0800-board-b-dataset-selection`

Board A is already `accepted_95` via `SessionLiquidityCoreViable`, but Board B remains blocked by `user_selected_historical_data_missing`.

Recommended option: `live_nq_ltf_15m_recorded` because it is the exact dataset path emitted by `ict-engine workflow-status` for the deferred factor-research command.

Packet: `board-b-handoff/dataset_selection_packet.json`
