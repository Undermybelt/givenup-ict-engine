# Wash Trading Dataset Acquisition Probe

Run id: `20260511T020111+0800-codex-wash-trading-dataset-acquisition-probe`

## Purpose

Probe whether a second direct/event manipulation dataset can be acquired without credentials and used to improve the active MainRegimeV2 `Manipulation` root gate.

## Sources Checked

| Source | Link | Local result | Gate usability |
|---|---|---|---|
| Mendeley Data: Detecting Crypto Wash Trades via Machine Learning | `https://data.mendeley.com/datasets/4hyxfwzpgg/3` | Public metadata page found. Static page metadata says it contains labeled ML samples from on-chain transactions. No raw row-level files were acquired through no-auth `curl`/public API probes. | candidate only; not usable until raw row-level samples are acquired |
| GitHub repository: `niuniu-zhang/nft_wash_trading` | `https://github.com/niuniu-zhang/nft_wash_trading` | Repository is reachable. README says raw labeled datasets and generated ML samples are not included; only aggregate `data/results/*.csv` outputs are included. | aggregate metrics are not calibration input |
| Mendeley public API | `https://api.mendeley.com/datasets/...` | No-auth calls returned `401 Unauthorized`. | acquisition blocked |
| Mendeley page/API variants under `data.mendeley.com` | `https://data.mendeley.com/datasets/4hyxfwzpgg/3` | Page HTML loaded and exposed dataset metadata, but file list was JS-loaded and direct guessed endpoints returned HTML/404/400 rather than raw data. | acquisition blocked |

## Result

- Candidate direct/event manipulation source found: yes.
- Raw row-level samples acquired: no.
- GitHub raw samples available: no.
- Usable calibration-grade `Manipulation` input set created: no.
- Accepted 95 `Manipulation`: false.

This probe does not move the gate. It is useful because it identifies a plausible second event/on-chain manipulation source, but the active gate requires the actual row-level samples, chronological split, and held-out calibration/test evidence.

## Next

Acquire the Mendeley raw files through a valid browser/UI download path, API token, author-provided files, or another public mirror; then run an unchanged `Manipulation` gate over row-level wash labels and engineered features. If those files remain unavailable, continue searching for directly downloadable event/social/on-chain manipulation datasets or L2/L3/MBO/order-lifecycle datasets.

