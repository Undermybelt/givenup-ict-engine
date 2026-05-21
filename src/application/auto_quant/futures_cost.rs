use anyhow::{bail, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FuturesCostProfile {
    pub profile_id: String,
    pub root_symbol: String,
    pub exchange: String,
    pub tick_size: f64,
    pub tick_value: f64,
    pub commission_per_contract_side: f64,
    pub exchange_fees_per_contract_side: f64,
    pub regulatory_fees_per_contract_side: f64,
    pub assumed_spread_ticks: f64,
    pub assumed_slippage_ticks_per_side: f64,
    pub source: String,
    pub notes: Vec<String>,
}

impl FuturesCostProfile {
    pub fn point_value(&self) -> f64 {
        self.tick_value / self.tick_size
    }

    pub fn round_trip_cost_points(&self) -> f64 {
        let point_value = self.point_value();
        let cash_cost = 2.0
            * (self.commission_per_contract_side
                + self.exchange_fees_per_contract_side
                + self.regulatory_fees_per_contract_side);
        let cash_cost_points = cash_cost / point_value;
        let spread_points = self.assumed_spread_ticks * self.tick_size;
        let slippage_points = 2.0 * self.assumed_slippage_ticks_per_side * self.tick_size;
        cash_cost_points + spread_points + slippage_points
    }

    pub fn round_trip_cost_percent(&self, representative_price: f64) -> Result<f64> {
        if representative_price <= 0.0 {
            bail!("representative price must be positive");
        }
        Ok(self.round_trip_cost_points() / representative_price * 100.0)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FuturesCostCatalog {
    pub profiles: Vec<FuturesCostProfile>,
}

impl Default for FuturesCostCatalog {
    fn default() -> Self {
        Self {
            profiles: vec![
                profile(
                    "ES",
                    "CME_ES_default_v1",
                    "CME",
                    0.25,
                    12.5,
                    CostAssumption::standard_index(),
                ),
                profile(
                    "MES",
                    "CME_MES_default_v1",
                    "CME",
                    0.25,
                    1.25,
                    CostAssumption::micro(),
                ),
                profile(
                    "NQ",
                    "CME_NQ_default_v1",
                    "CME",
                    0.25,
                    5.0,
                    CostAssumption::standard_index(),
                ),
                profile(
                    "MNQ",
                    "CME_MNQ_default_v1",
                    "CME",
                    0.25,
                    0.5,
                    CostAssumption::micro(),
                ),
                profile(
                    "YM",
                    "CBOT_YM_default_v1",
                    "CBOT",
                    1.0,
                    5.0,
                    CostAssumption::standard_index(),
                ),
                profile(
                    "MYM",
                    "CBOT_MYM_default_v1",
                    "CBOT",
                    1.0,
                    0.5,
                    CostAssumption::micro(),
                ),
                profile(
                    "RTY",
                    "CME_RTY_default_v1",
                    "CME",
                    0.1,
                    5.0,
                    CostAssumption::standard_index(),
                ),
                profile(
                    "M2K",
                    "CME_M2K_default_v1",
                    "CME",
                    0.1,
                    0.5,
                    CostAssumption::micro(),
                ),
                profile(
                    "GC",
                    "COMEX_GC_default_v1",
                    "COMEX",
                    0.1,
                    10.0,
                    CostAssumption::standard_commodity(),
                ),
                profile(
                    "MGC",
                    "COMEX_MGC_default_v1",
                    "COMEX",
                    0.1,
                    1.0,
                    CostAssumption::micro(),
                ),
                profile(
                    "SI",
                    "COMEX_SI_default_v1",
                    "COMEX",
                    0.005,
                    25.0,
                    CostAssumption::standard_commodity(),
                ),
                profile(
                    "SIL",
                    "COMEX_SIL_default_v1",
                    "COMEX",
                    0.005,
                    5.0,
                    CostAssumption::micro(),
                ),
                profile(
                    "HG",
                    "COMEX_HG_default_v1",
                    "COMEX",
                    0.0005,
                    12.5,
                    CostAssumption::standard_commodity(),
                ),
                profile(
                    "CL",
                    "NYMEX_CL_default_v1",
                    "NYMEX",
                    0.01,
                    10.0,
                    CostAssumption::standard_commodity(),
                ),
                profile(
                    "MCL",
                    "NYMEX_MCL_default_v1",
                    "NYMEX",
                    0.01,
                    1.0,
                    CostAssumption::micro(),
                ),
                profile(
                    "NG",
                    "NYMEX_NG_default_v1",
                    "NYMEX",
                    0.001,
                    10.0,
                    CostAssumption::standard_commodity(),
                ),
                profile(
                    "ZN",
                    "CBOT_ZN_default_v1",
                    "CBOT",
                    0.015625,
                    15.625,
                    CostAssumption::rates(),
                ),
                profile(
                    "ZB",
                    "CBOT_ZB_default_v1",
                    "CBOT",
                    0.03125,
                    31.25,
                    CostAssumption::rates(),
                ),
                profile(
                    "ZF",
                    "CBOT_ZF_default_v1",
                    "CBOT",
                    0.0078125,
                    7.8125,
                    CostAssumption::rates(),
                ),
                profile(
                    "6E",
                    "CME_6E_default_v1",
                    "CME",
                    0.00005,
                    6.25,
                    CostAssumption::fx(),
                ),
                profile(
                    "M6E",
                    "CME_M6E_default_v1",
                    "CME",
                    0.00005,
                    1.25,
                    CostAssumption::micro(),
                ),
                profile(
                    "6J",
                    "CME_6J_default_v1",
                    "CME",
                    0.0000005,
                    6.25,
                    CostAssumption::fx(),
                ),
                profile(
                    "M6J",
                    "CME_M6J_default_v1",
                    "CME",
                    0.0000005,
                    0.625,
                    CostAssumption::micro(),
                ),
                profile(
                    "6B",
                    "CME_6B_default_v1",
                    "CME",
                    0.0001,
                    6.25,
                    CostAssumption::fx(),
                ),
                profile(
                    "M6B",
                    "CME_M6B_default_v1",
                    "CME",
                    0.0001,
                    0.625,
                    CostAssumption::micro(),
                ),
                profile(
                    "6A",
                    "CME_6A_default_v1",
                    "CME",
                    0.00005,
                    5.0,
                    CostAssumption::fx(),
                ),
                profile(
                    "6C",
                    "CME_6C_default_v1",
                    "CME",
                    0.00005,
                    5.0,
                    CostAssumption::fx(),
                ),
                profile(
                    "6S",
                    "CME_6S_default_v1",
                    "CME",
                    0.0001,
                    12.5,
                    CostAssumption::fx(),
                ),
                profile(
                    "ZC",
                    "CBOT_ZC_default_v1",
                    "CBOT",
                    0.25,
                    12.5,
                    CostAssumption::agriculture(),
                ),
                profile(
                    "ZS",
                    "CBOT_ZS_default_v1",
                    "CBOT",
                    0.25,
                    12.5,
                    CostAssumption::agriculture(),
                ),
                profile(
                    "ZW",
                    "CBOT_ZW_default_v1",
                    "CBOT",
                    0.25,
                    12.5,
                    CostAssumption::agriculture(),
                ),
            ],
        }
    }
}

impl FuturesCostCatalog {
    pub fn profile_for(&self, symbol_or_contract: &str) -> Option<&FuturesCostProfile> {
        let root = normalize_futures_root(symbol_or_contract);
        self.profiles
            .iter()
            .find(|profile| profile.root_symbol == root)
    }

    pub fn round_trip_cost_percent(
        &self,
        symbol_or_contract: &str,
        representative_price: f64,
    ) -> Result<f64> {
        let profile = self.profile_for(symbol_or_contract).ok_or_else(|| {
            anyhow::anyhow!(
                "unknown futures cost profile: {}",
                normalize_futures_root(symbol_or_contract)
            )
        })?;
        profile.round_trip_cost_percent(representative_price)
    }

    pub fn with_json_overrides(mut self, json: &str) -> Result<Self> {
        let overrides: FuturesCostCatalog = serde_json::from_str(json)?;
        for profile in overrides.profiles {
            if let Some(existing) = self
                .profiles
                .iter_mut()
                .find(|existing| existing.root_symbol == profile.root_symbol)
            {
                *existing = profile;
            } else {
                self.profiles.push(profile);
            }
        }
        Ok(self)
    }
}

fn normalize_futures_root(symbol_or_contract: &str) -> String {
    let upper = symbol_or_contract.trim().to_ascii_uppercase();
    for root in [
        "MES", "MNQ", "MYM", "M2K", "MGC", "MCL", "M6E", "M6J", "M6B", "RTY", "SIL", "ES", "NQ",
        "YM", "GC", "SI", "HG", "CL", "NG", "ZN", "ZB", "ZF", "6E", "6J", "6B", "6A", "6C", "6S",
        "ZC", "ZS", "ZW",
    ] {
        if upper.starts_with(root) {
            return root.to_string();
        }
    }
    let letters: String = upper
        .chars()
        .take_while(|ch| ch.is_ascii_alphabetic())
        .collect();
    letters
}

#[derive(Debug, Clone, Copy)]
struct CostAssumption {
    commission_per_contract_side: f64,
    exchange_fees_per_contract_side: f64,
    regulatory_fees_per_contract_side: f64,
    assumed_spread_ticks: f64,
    assumed_slippage_ticks_per_side: f64,
}

impl CostAssumption {
    fn standard_index() -> Self {
        Self::new(1.00, 1.40, 0.02, 1.0, 0.5)
    }

    fn standard_commodity() -> Self {
        Self::new(1.00, 1.50, 0.02, 1.0, 0.5)
    }

    fn rates() -> Self {
        Self::new(1.00, 0.90, 0.02, 1.0, 0.5)
    }

    fn fx() -> Self {
        Self::new(1.00, 1.60, 0.02, 1.0, 0.5)
    }

    fn agriculture() -> Self {
        Self::new(1.00, 1.40, 0.02, 1.0, 0.5)
    }

    fn micro() -> Self {
        Self::new(0.39, 0.35, 0.02, 1.0, 0.5)
    }

    fn new(
        commission_per_contract_side: f64,
        exchange_fees_per_contract_side: f64,
        regulatory_fees_per_contract_side: f64,
        assumed_spread_ticks: f64,
        assumed_slippage_ticks_per_side: f64,
    ) -> Self {
        Self {
            commission_per_contract_side,
            exchange_fees_per_contract_side,
            regulatory_fees_per_contract_side,
            assumed_spread_ticks,
            assumed_slippage_ticks_per_side,
        }
    }
}

fn profile(
    root_symbol: &str,
    profile_id: &str,
    exchange: &str,
    tick_size: f64,
    tick_value: f64,
    cost: CostAssumption,
) -> FuturesCostProfile {
    FuturesCostProfile {
        profile_id: profile_id.to_string(),
        root_symbol: root_symbol.to_string(),
        exchange: exchange.to_string(),
        tick_size,
        tick_value,
        commission_per_contract_side: cost.commission_per_contract_side,
        exchange_fees_per_contract_side: cost.exchange_fees_per_contract_side,
        regulatory_fees_per_contract_side: cost.regulatory_fees_per_contract_side,
        assumed_spread_ticks: cost.assumed_spread_ticks,
        assumed_slippage_ticks_per_side: cost.assumed_slippage_ticks_per_side,
        source: "ict_engine_default_assumption_v1".to_string(),
        notes: vec![
            "generic_zero_config_default".to_string(),
            "contract_specs_follow_exchange_tick_ladders".to_string(),
            "broker_exchange_regulatory_fees_are_overrideable_assumptions".to_string(),
        ],
    }
}
