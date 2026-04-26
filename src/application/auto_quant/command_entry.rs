use super::{
    adoption::{build_auto_quant_adoption_review, persist_auto_quant_adoption_decision},
    auto_quant_bootstrap, auto_quant_readiness, auto_quant_status, auto_quant_update,
    handoff::{
        auto_quant_workspace_config, build_factor_autoresearch_handoff_payload,
        build_factor_research_handoff_payload, AutoQuantFactorAutoresearchCommandInput,
        AutoQuantFactorResearchCommandInput,
    },
    persistence::persist_handoff_payload,
    results::{
        apply_strategy_library_prior_init, load_strategy_library_manifest,
        persist_imported_library, persist_prior_init_outcome, AutoQuantPriorInitInput,
        DEFAULT_DEFAULT_PARENT_CONFIG, DEFAULT_PRIOR_STRENGTH, DEFAULT_TEMPER,
        STRATEGY_LIBRARY_FILE,
    },
    seed_evidence::{
        persist_auto_quant_seed_material_evidence, AUTO_QUANT_SEED_MATERIAL_EVIDENCE_DEFAULT_LIMIT,
    },
    AutoQuantDependencyStatus,
};
use anyhow::{anyhow, bail, Context, Result};
use serde_json::json;

use crate::bbn::trading::persistence::load_or_init_trading_network;
use crate::state::{save_state, state_exists, BBN_STATE_FILE};

fn ensure_dependency_ready(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> Result<AutoQuantDependencyStatus> {
    let status = auto_quant_status(state_dir)?;
    if status.bootstrap_needed {
        auto_quant_bootstrap(state_dir, repo_url, tracked_branch)
    } else {
        Ok(status)
    }
}

pub fn auto_quant_status_command(state_dir: &str) -> Result<()> {
    let readiness = auto_quant_readiness(state_dir)?;
    println!("{}", serde_json::to_string_pretty(&readiness)?);
    Ok(())
}

pub fn auto_quant_bootstrap_command(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> Result<()> {
    let status = auto_quant_bootstrap(state_dir, repo_url, tracked_branch)?;
    println!("{}", serde_json::to_string_pretty(&status)?);
    Ok(())
}

pub fn auto_quant_update_command(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
    target_ref: Option<&str>,
) -> Result<()> {
    let report = auto_quant_update(state_dir, repo_url, tracked_branch, target_ref)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

pub fn auto_quant_adoption_review_command(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
) -> Result<()> {
    let review = build_auto_quant_adoption_review(symbol, state_dir, artifact_id)?;
    println!("{}", serde_json::to_string_pretty(&review)?);
    Ok(())
}

pub fn auto_quant_adoption_decision_command(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    decision: &str,
    rationale: &str,
    requested_by: &str,
) -> Result<()> {
    let artifact = persist_auto_quant_adoption_decision(
        symbol,
        state_dir,
        artifact_id,
        decision,
        rationale,
        requested_by,
    )?;
    println!("{}", serde_json::to_string_pretty(&artifact)?);
    Ok(())
}

pub fn auto_quant_seed_evidence_command(
    symbol: &str,
    state_dir: &str,
    strategy_material_root: &str,
    limit: usize,
) -> Result<()> {
    let dependency_status = ensure_dependency_ready(state_dir, None, None)?;
    let workspace = auto_quant_workspace_config(&dependency_status.managed_dir);
    let artifact = persist_auto_quant_seed_material_evidence(
        symbol,
        state_dir,
        Some(strategy_material_root),
        &workspace,
        limit,
    )?
    .ok_or_else(|| {
        anyhow!(
            "no external strategy materials with usable evidence were found under '{}'",
            strategy_material_root
        )
    })?;
    println!("{}", serde_json::to_string_pretty(&artifact)?);
    Ok(())
}

fn maybe_persist_seed_material_evidence(
    symbol: &str,
    state_dir: &str,
    strategy_material_root: Option<&str>,
    dependency_status: &AutoQuantDependencyStatus,
) -> Result<Option<String>> {
    let workspace = auto_quant_workspace_config(&dependency_status.managed_dir);
    let artifact = persist_auto_quant_seed_material_evidence(
        symbol,
        state_dir,
        strategy_material_root,
        &workspace,
        AUTO_QUANT_SEED_MATERIAL_EVIDENCE_DEFAULT_LIMIT,
    )?;
    Ok(artifact.map(|item| item.artifact_id))
}

pub fn auto_quant_factor_research_command(
    input: AutoQuantFactorResearchCommandInput<'_>,
) -> Result<()> {
    let AutoQuantFactorResearchCommandInput {
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        strategy_material_root,
        state_dir,
    } = input;
    let dependency_status = ensure_dependency_ready(state_dir, None, None)?;
    let seed_evidence_artifact_id = maybe_persist_seed_material_evidence(
        symbol,
        state_dir,
        strategy_material_root,
        &dependency_status,
    )
    .map_err(|err| {
        eprintln!(
            "warning: failed to persist auto-quant seed material evidence for {}: {err:#}",
            symbol
        );
        err
    })
    .ok()
    .flatten();
    let mut payload = build_factor_research_handoff_payload(
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        strategy_material_root,
        state_dir,
        dependency_status,
    );
    if let Some(artifact_id) = seed_evidence_artifact_id {
        payload.notes.push(format!(
            "auto_quant_seed_material_evidence_artifact_id={}",
            artifact_id
        ));
    }
    let handoff_path = persist_handoff_payload(state_dir, &payload)?;
    payload.handoff_artifact_path = handoff_path;
    println!("{}", serde_json::to_string_pretty(&payload)?);
    Ok(())
}

pub fn auto_quant_factor_autoresearch_command(
    input: AutoQuantFactorAutoresearchCommandInput<'_>,
) -> Result<()> {
    let AutoQuantFactorAutoresearchCommandInput {
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        strategy_material_root,
        iterations,
        session_id,
        state_dir,
    } = input;
    let dependency_status = ensure_dependency_ready(state_dir, None, None)?;
    let seed_evidence_artifact_id = maybe_persist_seed_material_evidence(
        symbol,
        state_dir,
        strategy_material_root,
        &dependency_status,
    )
    .map_err(|err| {
        eprintln!(
            "warning: failed to persist auto-quant seed material evidence for {}: {err:#}",
            symbol
        );
        err
    })
    .ok()
    .flatten();
    let mut payload = build_factor_autoresearch_handoff_payload(
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        strategy_material_root,
        iterations,
        session_id,
        state_dir,
        dependency_status,
    );
    if let Some(artifact_id) = seed_evidence_artifact_id {
        payload.notes.push(format!(
            "auto_quant_seed_material_evidence_artifact_id={artifact_id}"
        ));
    }
    let handoff_path = persist_handoff_payload(state_dir, &payload)?;
    payload.handoff_artifact_path = handoff_path;
    println!("{}", serde_json::to_string_pretty(&payload)?);
    Ok(())
}

/// Inputs for `auto_quant_prior_init_command`. Pulled out so the
/// CLI surface can default sensibly without burning a large positional
/// signature.
pub struct AutoQuantPriorInitCommandInput<'a> {
    pub symbol: &'a str,
    pub state_dir: &'a str,
    /// Optional path to a `strategy_library.json`. If `None`, the
    /// command falls back to the canonical state copy
    /// (`<state_dir>/<symbol>/auto_quant_strategy_library.json`)
    /// produced by a prior `auto-quant-results-import`.
    pub library_path: Option<&'a str>,
    /// If `Some`, restrict prior init to these strategy names.
    pub strategy_filter: Option<&'a [String]>,
    /// `temper ∈ [0, 1]`. Defaults to `DEFAULT_TEMPER`.
    pub temper: Option<f64>,
    /// Defaults to `DEFAULT_PRIOR_STRENGTH`.
    pub prior_strength: Option<f64>,
    /// Length-3 parent config `[entry_quality, factor_alignment,
    /// factor_uncertainty]`. Defaults to `[0, 0, 0]`.
    pub parent_config: Option<Vec<usize>>,
    /// If `true`, compute and emit the diff but do not persist the
    /// mutated trading network.
    pub dry_run: bool,
}

/// Validate a `strategy_library.json` produced by Auto-Quant's
/// `export_strategy_library.py`, persist a canonical copy in the
/// symbol's state directory, and emit an
/// `auto_quant_strategy_library_validated` ledger entry.
pub fn auto_quant_results_import_command(
    symbol: &str,
    state_dir: &str,
    library_path: &str,
) -> Result<()> {
    let manifest = load_strategy_library_manifest(library_path)
        .with_context(|| format!("loading strategy library from '{}'", library_path))?;
    let persisted = persist_imported_library(state_dir, symbol, &manifest, library_path)?;

    let summary = json!({
        "command": "auto-quant-results-import",
        "symbol": symbol,
        "library_source": library_path,
        "library_state_path": persisted.state_path,
        "library_artifact_id": persisted.artifact_id,
        "manifest_version": manifest.manifest_version,
        "auto_quant_pinned_ref": manifest.auto_quant_pinned_ref,
        "n_total_strategies": persisted.n_total_strategies,
        "n_ok": persisted.n_ok,
        "n_error": persisted.n_error,
        "n_not_run": persisted.n_not_run,
        "n_meta_invalid": manifest.validation_errors.len(),
    });
    println!("{}", serde_json::to_string_pretty(&summary)?);
    Ok(())
}

/// Apply tempered Beta-Binomial pseudo-counts derived from a
/// previously-imported Auto-Quant strategy library to the trading
/// network's `trade_outcome` CPT row identified by `parent_config`.
pub fn auto_quant_prior_init_command(input: AutoQuantPriorInitCommandInput<'_>) -> Result<()> {
    let AutoQuantPriorInitCommandInput {
        symbol,
        state_dir,
        library_path,
        strategy_filter,
        temper,
        prior_strength,
        parent_config,
        dry_run,
    } = input;

    let library_state_path =
        crate::state::artifact_state_path(state_dir, symbol, STRATEGY_LIBRARY_FILE);
    let resolved_path = match library_path {
        Some(p) => p.to_string(),
        None => {
            if !state_exists(state_dir, symbol, STRATEGY_LIBRARY_FILE) {
                bail!(
                    "no library found at '{}' and no --library override given; \
                     run `ict-engine auto-quant-results-import` first",
                    library_state_path
                );
            }
            library_state_path.clone()
        }
    };
    let manifest = load_strategy_library_manifest(&resolved_path)
        .with_context(|| format!("loading strategy library from '{}'", resolved_path))?;

    let temper = temper.unwrap_or(DEFAULT_TEMPER);
    let prior_strength = prior_strength.unwrap_or(DEFAULT_PRIOR_STRENGTH);
    let parent_config =
        parent_config.unwrap_or_else(|| DEFAULT_DEFAULT_PARENT_CONFIG.to_vec());

    let mut network = load_or_init_trading_network(symbol, state_dir)?;
    let outcome = apply_strategy_library_prior_init(
        &mut network,
        AutoQuantPriorInitInput {
            manifest: &manifest,
            strategy_filter,
            parent_config: parent_config.clone(),
            temper,
            prior_strength,
        },
    )?;

    if !dry_run && !outcome.strategies_applied.is_empty() {
        save_state(state_dir, symbol, BBN_STATE_FILE, &network)
            .context("persisting updated trading network after prior init")?;
    }

    let library_artifact_id = resolve_library_artifact_id(state_dir, symbol)
        .unwrap_or_else(|| resolved_path.clone());

    let persisted = persist_prior_init_outcome(
        state_dir,
        symbol,
        &outcome,
        &library_artifact_id,
        &resolved_path,
        dry_run,
    )?;

    let summary = json!({
        "command": "auto-quant-prior-init",
        "symbol": symbol,
        "library_path": resolved_path,
        "library_artifact_id": library_artifact_id,
        "prior_init_artifact_id": persisted.artifact_id,
        "prior_init_state_path": persisted.state_path,
        "prior_init_history_path": persisted.history_path,
        "dry_run": dry_run,
        "temper": temper,
        "prior_strength": prior_strength,
        "parent_config": outcome.parent_config,
        "initial_probs": outcome.initial_probs,
        "final_probs": outcome.final_probs,
        "strategies_applied": outcome.strategies_applied,
        "strategies_skipped": outcome.strategies_skipped,
    });
    println!("{}", serde_json::to_string_pretty(&summary)?);
    Ok(())
}

/// Look up the most recently appended `auto_quant_strategy_library_validated`
/// entry's artifact_id so we can pin lineage in the prior_init ledger entry.
fn resolve_library_artifact_id(state_dir: &str, symbol: &str) -> Option<String> {
    let ledger: Vec<crate::state::ArtifactLedgerEntry> =
        crate::state::load_state_or_default(state_dir, symbol, crate::state::ARTIFACT_LEDGER_FILE)
            .ok()?;
    ledger
        .into_iter()
        .rev()
        .find(|entry| entry.artifact_kind == super::results::ARTIFACT_KIND_LIBRARY)
        .map(|entry| entry.artifact_id)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::results::{
        StrategyLibraryEntry, StrategyLibraryManifest, StrategyLibraryMetadata,
        StrategyLibraryValidationMetrics,
    };

    fn write_manifest_to(temp: &std::path::Path, manifest: &StrategyLibraryManifest) -> String {
        let path = temp.join("strategy_library.json");
        std::fs::write(&path, serde_json::to_string_pretty(manifest).unwrap()).unwrap();
        path.to_string_lossy().into_owned()
    }

    fn ok_strategy(name: &str, trade_count: u32, win_rate_pct: f64) -> StrategyLibraryEntry {
        StrategyLibraryEntry {
            name: name.to_string(),
            file_path: format!("user_data/strategies_ibkr/{name}.py"),
            metadata: StrategyLibraryMetadata {
                strategy: name.to_string(),
                mutation_id: format!("mut-{name}"),
                ..Default::default()
            },
            status: "ok".to_string(),
            validation_metrics: Some(StrategyLibraryValidationMetrics {
                trade_count,
                win_rate_pct,
                ..Default::default()
            }),
            ..Default::default()
        }
    }

    #[test]
    fn import_then_prior_init_dry_run_does_not_mutate_network_state() {
        let temp = tempfile::tempdir().unwrap();
        let state_dir = temp.path().to_str().unwrap();
        let manifest = StrategyLibraryManifest {
            manifest_version: "1.0".to_string(),
            strategies: vec![ok_strategy("S1", 100, 65.0)],
            ..Default::default()
        };
        let path = write_manifest_to(temp.path(), &manifest);

        auto_quant_results_import_command("NQ", state_dir, &path).unwrap();
        assert!(state_exists(state_dir, "NQ", STRATEGY_LIBRARY_FILE));
        assert!(!state_exists(state_dir, "NQ", BBN_STATE_FILE));

        auto_quant_prior_init_command(AutoQuantPriorInitCommandInput {
            symbol: "NQ",
            state_dir,
            library_path: None,
            strategy_filter: None,
            temper: Some(0.5),
            prior_strength: Some(4.0),
            parent_config: None,
            dry_run: true,
        })
        .unwrap();
        assert!(!state_exists(state_dir, "NQ", BBN_STATE_FILE));
    }

    #[test]
    fn prior_init_persists_network_when_not_dry_run() {
        let temp = tempfile::tempdir().unwrap();
        let state_dir = temp.path().to_str().unwrap();
        let manifest = StrategyLibraryManifest {
            manifest_version: "1.0".to_string(),
            strategies: vec![ok_strategy("S1", 100, 75.0)],
            ..Default::default()
        };
        let path = write_manifest_to(temp.path(), &manifest);

        auto_quant_results_import_command("NQ", state_dir, &path).unwrap();
        auto_quant_prior_init_command(AutoQuantPriorInitCommandInput {
            symbol: "NQ",
            state_dir,
            library_path: None,
            strategy_filter: None,
            temper: Some(0.5),
            prior_strength: Some(4.0),
            parent_config: None,
            dry_run: false,
        })
        .unwrap();
        assert!(state_exists(state_dir, "NQ", BBN_STATE_FILE));
    }

    #[test]
    fn prior_init_errors_without_library_when_no_state_present() {
        let temp = tempfile::tempdir().unwrap();
        let state_dir = temp.path().to_str().unwrap();
        let err = auto_quant_prior_init_command(AutoQuantPriorInitCommandInput {
            symbol: "NQ",
            state_dir,
            library_path: None,
            strategy_filter: None,
            temper: None,
            prior_strength: None,
            parent_config: None,
            dry_run: true,
        })
        .unwrap_err();
        assert!(err.to_string().contains("auto-quant-results-import"));
    }
}
