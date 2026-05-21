use ict_engine::application::auto_quant::FuturesCostCatalog;

#[test]
fn default_catalog_prices_index_futures_by_contract_specs() {
    let catalog = FuturesCostCatalog::default();

    let es = catalog.profile_for("ES").expect("ES profile");
    assert_eq!(es.tick_size, 0.25);
    assert_eq!(es.tick_value, 12.5);
    assert_eq!(es.point_value(), 50.0);

    let nq = catalog
        .profile_for("nq")
        .expect("case-insensitive NQ profile");
    assert_eq!(nq.tick_size, 0.25);
    assert_eq!(nq.tick_value, 5.0);
    assert_eq!(nq.point_value(), 20.0);

    let ym = catalog
        .profile_for("YMH5")
        .expect("contract month root maps to YM");
    assert_eq!(ym.tick_size, 1.0);
    assert_eq!(ym.tick_value, 5.0);
    assert_eq!(ym.point_value(), 5.0);
}

#[test]
fn futures_cost_percent_is_instrument_aware_not_blanket_bps() {
    let catalog = FuturesCostCatalog::default();

    let es = catalog
        .round_trip_cost_percent("ES", 5200.0)
        .expect("ES cost");
    let nq = catalog
        .round_trip_cost_percent("NQ", 18000.0)
        .expect("NQ cost");
    let ym = catalog
        .round_trip_cost_percent("YM", 39000.0)
        .expect("YM cost");

    assert!(es > 0.0);
    assert!(nq > 0.0);
    assert!(ym > 0.0);
    assert!(es < 0.10, "ES should be below naive 5bps/side round trip");
    assert!(nq < 0.10, "NQ should be below naive 5bps/side round trip");
    assert!(ym < 0.10, "YM should be below naive 5bps/side round trip");
    assert_ne!(es, nq);
    assert_ne!(nq, ym);
}

#[test]
fn unknown_futures_symbol_returns_token_friendly_error() {
    let catalog = FuturesCostCatalog::default();
    let error = catalog.round_trip_cost_percent("ZZZ", 100.0).unwrap_err();
    assert_eq!(error.to_string(), "unknown futures cost profile: ZZZ");
}

#[test]
fn default_catalog_covers_common_futures_families() {
    let catalog = FuturesCostCatalog::default();

    for symbol in [
        "GC", "MGC", "SI", "CL", "MCL", "NG", "ZN", "ZB", "6E", "M6E", "ZC", "ZS", "ZW",
    ] {
        let profile = catalog
            .profile_for(symbol)
            .unwrap_or_else(|| panic!("missing {symbol}"));
        assert!(profile.tick_size > 0.0);
        assert!(profile.tick_value > 0.0);
        assert!(profile.point_value() > 0.0);
        assert!(profile.assumed_spread_ticks >= 1.0);
    }
}

#[test]
fn catalog_accepts_hotplug_override_without_private_paths() {
    let json = r#"
    {
      "profiles": [
        {
          "profile_id": "CUSTOM_ES_intraday_v1",
          "root_symbol": "ES",
          "exchange": "CME",
          "tick_size": 0.25,
          "tick_value": 12.5,
          "commission_per_contract_side": 0.50,
          "exchange_fees_per_contract_side": 1.20,
          "regulatory_fees_per_contract_side": 0.02,
          "assumed_spread_ticks": 1.0,
          "assumed_slippage_ticks_per_side": 0.25,
          "source": "user_supplied_profile",
          "notes": ["no_private_path"]
        }
      ]
    }
    "#;

    let catalog = FuturesCostCatalog::default()
        .with_json_overrides(json)
        .unwrap();
    let profile = catalog.profile_for("ES").unwrap();

    assert_eq!(profile.profile_id, "CUSTOM_ES_intraday_v1");
    assert_eq!(profile.assumed_slippage_ticks_per_side, 0.25);
    assert!(!serde_json::to_string(profile).unwrap().contains("/Users/"));
}
