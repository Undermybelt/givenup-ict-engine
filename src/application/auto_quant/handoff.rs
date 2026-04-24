use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

use super::types::AutoQuantDependencyStatus;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AutoQuantWorkspaceConfig {
    pub repo_root: String,
    pub program_md: String,
    pub prepare_script: String,
    pub run_script: String,
    pub config_json: String,
    pub strategies_dir: String,
    pub data_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AutoQuantResearchHandoffPayload {
    pub artifact_id: String,
    pub handoff_kind: String,
    pub symbol: String,
    pub state_dir: String,
    pub objective: String,
    pub backend: String,
    pub data_path: String,
    pub paired_data_path: Option<String>,
    pub mutation_spec_path: Option<String>,
    pub iterations: Option<usize>,
    pub session_id: Option<String>,
    pub dependency_status: AutoQuantDependencyStatus,
    pub workspace: AutoQuantWorkspaceConfig,
    pub data_ready: bool,
    pub handoff_artifact_path: String,
    pub suggested_commands: Vec<String>,
    pub suggested_next_steps: Vec<String>,
    pub agent_prompt: String,
    pub notes: Vec<String>,
}

pub struct AutoQuantFactorResearchCommandInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub objective: &'a str,
    pub paired_data: Option<&'a str>,
    pub mutation_spec_path: Option<&'a str>,
    pub state_dir: &'a str,
}

pub struct AutoQuantFactorAutoresearchCommandInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub objective: &'a str,
    pub paired_data: Option<&'a str>,
    pub mutation_spec_path: Option<&'a str>,
    pub iterations: usize,
    pub session_id: Option<&'a str>,
    pub state_dir: &'a str,
}

pub fn auto_quant_workspace_config(managed_dir: &str) -> AutoQuantWorkspaceConfig {
    let repo_root = PathBuf::from(managed_dir);
    AutoQuantWorkspaceConfig {
        repo_root: repo_root.to_string_lossy().to_string(),
        program_md: repo_root.join("program.md").to_string_lossy().to_string(),
        prepare_script: repo_root.join("prepare.py").to_string_lossy().to_string(),
        run_script: repo_root.join("run.py").to_string_lossy().to_string(),
        config_json: repo_root.join("config.json").to_string_lossy().to_string(),
        strategies_dir: repo_root
            .join("user_data/strategies")
            .to_string_lossy()
            .to_string(),
        data_dir: repo_root.join("user_data/data").to_string_lossy().to_string(),
    }
}

pub fn auto_quant_data_ready(workspace: &AutoQuantWorkspaceConfig) -> bool {
    let data_dir = Path::new(&workspace.data_dir);
    if !data_dir.exists() {
        return false;
    }
    match std::fs::read_dir(data_dir) {
        Ok(entries) => {
            entries
                .filter_map(Result::ok)
                .filter(|entry| {
                    entry
                        .path()
                        .extension()
                        .and_then(|ext| ext.to_str())
                        .map(|ext| ext.eq_ignore_ascii_case("feather"))
                        .unwrap_or(false)
                })
                .count()
                >= 15
        }
        Err(_) => false,
    }
}

pub fn base_suggested_commands(
    workspace: &AutoQuantWorkspaceConfig,
    data_ready: bool,
) -> Vec<String> {
    let mut commands = vec![
        format!("python3 {}", workspace.program_md),
        format!("uv run {}", workspace.run_script),
    ];
    if !data_ready {
        commands.insert(0, format!("uv run {}", workspace.prepare_script));
    }
    commands
}

pub fn build_factor_research_handoff_payload(
    symbol: &str,
    data: &str,
    objective: &str,
    paired_data: Option<&str>,
    mutation_spec_path: Option<&str>,
    state_dir: &str,
    dependency_status: AutoQuantDependencyStatus,
) -> AutoQuantResearchHandoffPayload {
    let workspace = auto_quant_workspace_config(&dependency_status.managed_dir);
    let data_ready = auto_quant_data_ready(&workspace);
    let mut payload = AutoQuantResearchHandoffPayload {
        artifact_id: format!(
            "auto-quant-handoff:factor_research:{}:{}",
            symbol,
            Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
        ),
        handoff_kind: "factor_research".to_string(),
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        objective: objective.to_string(),
        backend: "auto-quant".to_string(),
        data_path: data.to_string(),
        paired_data_path: paired_data.map(str::to_string),
        mutation_spec_path: mutation_spec_path.map(str::to_string),
        iterations: None,
        session_id: None,
        dependency_status,
        workspace,
        data_ready,
        handoff_artifact_path: String::new(),
        suggested_commands: Vec::new(),
        suggested_next_steps: Vec::new(),
        agent_prompt: String::new(),
        notes: Vec::new(),
    };
    payload.suggested_commands = base_suggested_commands(&payload.workspace, payload.data_ready);
    payload.suggested_next_steps = if payload.data_ready {
        vec![
            "open Auto-Quant program.md and stage a research loop for the requested objective"
                .to_string(),
            "run Auto-Quant backtest loop and export a stable candidate package for ict-engine"
                .to_string(),
        ]
    } else {
        vec![
            "prepare Auto-Quant market data before attempting the research loop".to_string(),
            "re-run factor-research with backend=auto-quant after data becomes ready".to_string(),
        ]
    };
    payload.agent_prompt = format!(
        "Auto-Quant is the research execution backend for this request. Keep ict-engine as the control plane, preserve old factors, use {}, and export a candidate package back into ict-engine state.",
        payload.workspace.program_md
    );
    if !payload.data_ready {
        payload
            .notes
            .push("auto_quant_prepare_required_before_run".to_string());
    }
    payload.notes.push(format!(
        "requested_at={}",
        Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
    ));
    payload
}

#[allow(clippy::too_many_arguments)]
pub fn build_factor_autoresearch_handoff_payload(
    symbol: &str,
    data: &str,
    objective: &str,
    paired_data: Option<&str>,
    mutation_spec_path: Option<&str>,
    iterations: usize,
    session_id: Option<&str>,
    state_dir: &str,
    dependency_status: AutoQuantDependencyStatus,
) -> AutoQuantResearchHandoffPayload {
    let workspace = auto_quant_workspace_config(&dependency_status.managed_dir);
    let data_ready = auto_quant_data_ready(&workspace);
    let mut payload = AutoQuantResearchHandoffPayload {
        artifact_id: format!(
            "auto-quant-handoff:factor_autoresearch:{}:{}",
            symbol,
            Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
        ),
        handoff_kind: "factor_autoresearch".to_string(),
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        objective: objective.to_string(),
        backend: "auto-quant".to_string(),
        data_path: data.to_string(),
        paired_data_path: paired_data.map(str::to_string),
        mutation_spec_path: mutation_spec_path.map(str::to_string),
        iterations: Some(iterations),
        session_id: session_id.map(str::to_string),
        dependency_status,
        workspace,
        data_ready,
        handoff_artifact_path: String::new(),
        suggested_commands: Vec::new(),
        suggested_next_steps: Vec::new(),
        agent_prompt: String::new(),
        notes: Vec::new(),
    };
    payload.suggested_commands = base_suggested_commands(&payload.workspace, payload.data_ready);
    payload.suggested_next_steps = if payload.data_ready {
        vec![
            "resume or start the Auto-Quant autonomous loop with factor retention and explicit keep/discard review".to_string(),
            "export candidate/retrospective summary back to ict-engine after each iteration checkpoint".to_string(),
        ]
    } else {
        vec![
            "prepare Auto-Quant market data before attempting the autoresearch loop".to_string(),
            "re-run factor-autoresearch with backend=auto-quant after data becomes ready".to_string(),
        ]
    };
    payload.agent_prompt = format!(
        "Auto-Quant is the autoresearch execution backend for this request. Preserve existing ict-engine factors, use {}, and return a candidate package plus retrospective signals to ict-engine.",
        payload.workspace.program_md
    );
    if !payload.data_ready {
        payload
            .notes
            .push("auto_quant_prepare_required_before_run".to_string());
    }
    payload.notes.push(format!(
        "requested_at={}",
        Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
    ));
    payload
}
