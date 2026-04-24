use anyhow::Result;
use super::adoption::{
    build_auto_quant_adoption_review, persist_auto_quant_adoption_decision,
};
use super::handoff::{
    build_factor_autoresearch_handoff_payload, build_factor_research_handoff_payload,
    AutoQuantFactorAutoresearchCommandInput, AutoQuantFactorResearchCommandInput,
};
use super::persistence::persist_handoff_payload;
use super::{auto_quant_bootstrap, auto_quant_status, auto_quant_update, AutoQuantDependencyStatus};

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
    let status = auto_quant_status(state_dir)?;
    println!("{}", serde_json::to_string_pretty(&status)?);
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

pub fn auto_quant_factor_research_command(
    input: AutoQuantFactorResearchCommandInput<'_>,
) -> Result<()> {
    let AutoQuantFactorResearchCommandInput {
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        state_dir,
    } = input;
    let dependency_status = ensure_dependency_ready(state_dir, None, None)?;
    let mut payload = build_factor_research_handoff_payload(
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        state_dir,
        dependency_status,
    );
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
        iterations,
        session_id,
        state_dir,
    } = input;
    let dependency_status = ensure_dependency_ready(state_dir, None, None)?;
    let mut payload = build_factor_autoresearch_handoff_payload(
        symbol,
        data,
        objective,
        paired_data,
        mutation_spec_path,
        iterations,
        session_id,
        state_dir,
        dependency_status,
    );
    let handoff_path = persist_handoff_payload(state_dir, &payload)?;
    payload.handoff_artifact_path = handoff_path;
    println!("{}", serde_json::to_string_pretty(&payload)?);
    Ok(())
}
