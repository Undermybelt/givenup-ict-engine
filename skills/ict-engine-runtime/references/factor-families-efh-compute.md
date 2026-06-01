# Factor Families E/F/H — Compute Stub Reference

Session: 2026-05-09. Source: `src/factor_lab/factor_definition.rs` (post hotplug commit).

## Family E: CrowdingHerding

**Subfactors:**
- `participation_concentration`: current volume / rolling median / volume_spike_ratio. Clamped [0,1].
- `same_side_pressure`: (bull_vol - bear_vol) / total_vol over lookback window. Clamped [-1,1].
- `crowding_relief`: 1 - (current_vol / prev_3_bar_avg).min(2)/2. Decay after spike.

**Parameters:**
| Key | Default | Notes |
|---|---|---|
| `lookback` | 20 | rolling window |
| `volume_spike_ratio` | 2.0 | normalizes participation_concentration |
| `participation_concentration_weight` | 0.40 | |
| `same_side_pressure_weight` | 0.35 | |
| `crowding_relief_weight` | 0.25 | |

**Signal formula:**
```
value = normalize_signed(
    pc_w * participation * dir_sign
  + sp_w * same_side_pressure
  - cr_w * relief * dir_sign, 1.0)
```

**Explanation format:** `pc=X.XXX;sp=X.XXX;cr=X.XXX;vol_ratio=X.XX`

## Family F: SpectralRhythm

**Subfactors:**
- `spectral_entropy`: (1 + ln(variance) / 10).clamp(0,1) — Shannon-entropy proxy from return variance.
- `cycle_energy`: longest same-direction return run / lookback. Min(1).
- `rhythm_stability`: |autocorrelation lag-1| of returns.

**Parameters:**
| Key | Default | Notes |
|---|---|---|
| `lookback` | 64 | longer window for spectral features |
| `spectral_entropy_weight` | 0.45 | high entropy = chaotic = bad for execution |
| `cycle_energy_weight` | 0.35 | |
| `rhythm_stability_weight` | 0.20 | |

**Signal formula:**
```
value = normalize_signed(
    -se_w * spectral_entropy     # negative: chaos hurts readiness
  + ce_w * cycle_energy * dir    # positive: persistent cycles favor execution
  + rs_w * rhythm_stability * dir, 1.0)
```

**Explanation format:** `se=X.XXX;ce=X.XXX;rs=X.XXX`

## Family H: SessionLiquidity

**Subfactors:**
- `session_quality`: current_vol / rolling_avg / 3.0. Clamped [0,1].
- `kill_zone_alignment`: hour-of-day lookup (UTC). Kill zones: 7-8,12-13,14-15,19-20 → 0.9; shoulder: 0.6; else 0.3.
- `session_transition_risk`: hour-of-day lookup. Boundary hours: 0.7; else 0.2.

**Parameters:**
| Key | Default | Notes |
|---|---|---|
| `lookback` | 20 | |
| `session_quality_weight` | 0.40 | |
| `kill_zone_weight` | 0.35 | |
| `transition_risk_weight` | 0.25 | |

**Signal formula:**
```
value = normalize_signed(
    sq_w * session_quality * dir
  + kz_w * kill_zone_alignment * dir
  - tr_w * transition_risk, 1.0)
```

**Explanation format:** `sq=X.XXX;kz=X.XXX;tr=X.XXX`

## Mutation Surface (E/F/H)

All three families follow the same mutation reason pattern:
- `balanced_accuracy_regressed | bull_bear_separation_*` → tune primary parameters
- `bridge_gap_*` → tune secondary weights
- `pre_bayes_gate_*` → tune lookback + primary weight

Step sizes: primary params 0.08-0.12; weights 0.12. Direction: lookback increase on regression.

## Known Limitations

- Spectral entropy uses return-variance proxy, not true FFT. Should be upgraded when execution-tree spectral_entropy is extracted as a reusable module.
- Kill-zone alignment uses UTC hour proxy. Does not handle timezone-aware sessions or exchange-specific schedules.
- Crowding detection uses volume-only signals. No order-flow or bid/ask data integration.
