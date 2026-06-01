use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

use crate::config::shell_quote;

pub(crate) fn apply_provider_profile_to_command(
    command: &str,
    provider_profile_selector: Option<&str>,
) -> String {
    let Some(profile) = provider_profile_selector.filter(|value| !value.trim().is_empty()) else {
        return command.to_string();
    };
    let trimmed = command.trim();
    if trimmed.is_empty() || trimmed.contains(" --profile ") {
        return command.to_string();
    }
    if let Some(rest) = trimmed.strip_prefix("ask-user: ") {
        if let Some((prefix, deferred)) = rest.split_once("| then ") {
            let rewritten_deferred =
                apply_provider_profile_to_command(deferred.trim(), Some(profile));
            return format!("ask-user: {}| then {}", prefix, rewritten_deferred);
        }
        return command.to_string();
    }
    if trimmed.starts_with("ict-engine workflow-status ")
        || trimmed.starts_with("ict-engine provider-status ")
        || trimmed.starts_with("ict-engine factor-research ")
        || trimmed.starts_with("ict-engine factor-autoresearch ")
    {
        return format!("{} --profile {}", trimmed, shell_quote(profile));
    }
    command.to_string()
}

use super::readiness::{auto_quant_readiness_from_status_and_data, AutoQuantReadinessSurface};
use super::strategy_materials::{discover_strategy_materials, AutoQuantStrategyMaterialSummary};
use super::types::AutoQuantDependencyStatus;
use super::workspace_profile::apply_workspace_profile;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AutoQuantWorkspaceConfig {
    pub repo_root: String,
    pub program_md: String,
    pub prepare_script: String,
    pub run_script: String,
    pub config_json: String,
    pub strategies_dir: String,
    pub data_dir: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub profile_name: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub expected_data_files: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub strategy_seed_source_dir: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantIterationUnitContext {
    pub unit_label: String,
    pub primitive_sequence: Vec<String>,
    pub timeframe: String,
    pub direction: String,
    pub strategy_brief: String,
    pub evaluation_priority: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub consumer_evidence_profile:
        Option<crate::application::auto_quant::pda_unit_batch::AutoQuantConsumerEvidenceProfile>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantLifecycleLayer {
    pub layer_id: String,
    pub name: String,
    pub trigger_timing: String,
    pub ict_engine_mapping: String,
    pub required_evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantEntryRegimeContract {
    pub contract_id: String,
    pub primary_entry_regime: String,
    pub allowed_regime_families: Vec<String>,
    pub allowed_entry_labels: Vec<String>,
    pub excluded_entry_labels: Vec<String>,
    pub non_entry_factor_role: String,
    pub required_counter_evidence_checks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantAgentWorkflow {
    pub workflow_style: String,
    pub setup_commands: Vec<String>,
    pub environment: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entry_regime_contract: Option<AutoQuantEntryRegimeContract>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub lifecycle_layers: Vec<AutoQuantLifecycleLayer>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub evolution_inputs: Vec<String>,
    pub phases: Vec<String>,
    pub expected_artifacts: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub regression_checks: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub freeze_boundary: Vec<String>,
    pub return_to_ict_engine: Vec<String>,
    pub constraints: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AutoQuantResearchHandoffPayload {
    pub artifact_id: String,
    pub handoff_kind: String,
    pub symbol: String,
    pub state_dir: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub provider_profile_selector: Option<String>,
    pub objective: String,
    pub backend: String,
    pub data_path: String,
    pub paired_data_path: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub auxiliary_evidence_path: Option<String>,
    pub mutation_spec_path: Option<String>,
    pub iterations: Option<usize>,
    pub session_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub strategy_material_root: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub external_strategy_materials: Vec<AutoQuantStrategyMaterialSummary>,
    pub dependency_status: AutoQuantDependencyStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub readiness: Option<AutoQuantReadinessSurface>,
    pub workspace: AutoQuantWorkspaceConfig,
    pub data_ready: bool,
    pub handoff_artifact_path: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub iteration_unit: Option<AutoQuantIterationUnitContext>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_workflow: Option<AutoQuantAgentWorkflow>,
    pub suggested_commands: Vec<String>,
    pub suggested_next_steps: Vec<String>,
    pub agent_prompt: String,
    pub notes: Vec<String>,
}

pub struct AutoQuantFactorResearchCommandInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub objective: &'a str,
    pub provider_profile_selector: Option<&'a str>,
    pub paired_data: Option<&'a str>,
    pub auto_quant_profile: Option<&'a str>,
    pub auxiliary_evidence_path: Option<&'a str>,
    pub mutation_spec_path: Option<&'a str>,
    pub strategy_material_root: Option<&'a str>,
    pub state_dir: &'a str,
    pub output_format: &'a str,
}

pub struct AutoQuantFactorAutoresearchCommandInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub objective: &'a str,
    pub provider_profile_selector: Option<&'a str>,
    pub paired_data: Option<&'a str>,
    pub auto_quant_profile: Option<&'a str>,
    pub auxiliary_evidence_path: Option<&'a str>,
    pub mutation_spec_path: Option<&'a str>,
    pub strategy_material_root: Option<&'a str>,
    pub iterations: usize,
    pub session_id: Option<&'a str>,
    pub state_dir: &'a str,
}

pub struct BuildFactorResearchHandoffPayloadInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub objective: &'a str,
    pub provider_profile_selector: Option<&'a str>,
    pub paired_data: Option<&'a str>,
    pub auxiliary_evidence_path: Option<&'a str>,
    pub mutation_spec_path: Option<&'a str>,
    pub strategy_material_root: Option<&'a str>,
    pub state_dir: &'a str,
    pub dependency_status: AutoQuantDependencyStatus,
}

pub struct BuildFactorAutoresearchHandoffPayloadInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub objective: &'a str,
    pub provider_profile_selector: Option<&'a str>,
    pub paired_data: Option<&'a str>,
    pub auxiliary_evidence_path: Option<&'a str>,
    pub mutation_spec_path: Option<&'a str>,
    pub strategy_material_root: Option<&'a str>,
    pub iterations: usize,
    pub session_id: Option<&'a str>,
    pub state_dir: &'a str,
    pub dependency_status: AutoQuantDependencyStatus,
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
        data_dir: repo_root
            .join("user_data/data")
            .to_string_lossy()
            .to_string(),
        profile_name: None,
        expected_data_files: Vec::new(),
        strategy_seed_source_dir: None,
    }
}

pub fn auto_quant_workspace_config_for_state(
    managed_dir: &str,
    state_dir: &str,
) -> AutoQuantWorkspaceConfig {
    let mut workspace = auto_quant_workspace_config(managed_dir);
    if let Err(err) = apply_workspace_profile(state_dir, &mut workspace) {
        workspace
            .expected_data_files
            .push(format!("profile_apply_error:{err:#}"));
    }
    workspace
}

pub fn auto_quant_prepare_command(workspace: &AutoQuantWorkspaceConfig) -> String {
    format!("uv run --with ta-lib {}", workspace.prepare_script)
}

pub fn auto_quant_prepare_cli_command(state_dir: &str) -> String {
    format!("ict-engine auto-quant-prepare --state-dir {state_dir}")
}

pub fn auto_quant_run_command(workspace: &AutoQuantWorkspaceConfig) -> String {
    let script_name = Path::new(&workspace.run_script)
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("run.py");
    format!(
        "cd {} && ./.venv/bin/python {}",
        shell_quote(&workspace.repo_root),
        shell_quote(script_name)
    )
}

pub fn auto_quant_data_ready(workspace: &AutoQuantWorkspaceConfig) -> bool {
    let data_dir = Path::new(&workspace.data_dir);
    if !data_dir.exists() {
        return false;
    }
    if !workspace.expected_data_files.is_empty() {
        return workspace
            .expected_data_files
            .iter()
            .all(|filename| data_dir.join(filename).exists());
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

pub fn auto_quant_handoff_data_ready(
    workspace: &AutoQuantWorkspaceConfig,
    data_path: &str,
    paired_data_path: Option<&str>,
) -> bool {
    if !auto_quant_data_ready(workspace) {
        return false;
    }
    if !Path::new(data_path).exists() {
        return false;
    }
    if let Some(paired) = paired_data_path {
        if !paired.trim().is_empty() && !Path::new(paired).exists() {
            return false;
        }
    }
    workspace.expected_data_files.is_empty()
        && default_workspace_contains_requested_data(workspace, data_path)
        || !workspace.expected_data_files.is_empty()
}

fn default_workspace_contains_requested_data(
    workspace: &AutoQuantWorkspaceConfig,
    data_path: &str,
) -> bool {
    let Some(stem) = Path::new(data_path)
        .file_stem()
        .and_then(|value| value.to_str())
    else {
        return false;
    };
    let normalized_stem = normalize_workspace_data_key(stem);
    std::fs::read_dir(&workspace.data_dir)
        .map(|entries| {
            entries.filter_map(Result::ok).any(|entry| {
                let path = entry.path();
                let is_feather = path
                    .extension()
                    .and_then(|ext| ext.to_str())
                    .map(|ext| ext.eq_ignore_ascii_case("feather"))
                    .unwrap_or(false);
                let Some(candidate_stem) = path.file_stem().and_then(|value| value.to_str()) else {
                    return false;
                };
                is_feather
                    && normalize_workspace_data_key(candidate_stem).starts_with(&normalized_stem)
            })
        })
        .unwrap_or(false)
}

fn normalize_workspace_data_key(value: &str) -> String {
    value
        .chars()
        .filter(|ch| ch.is_ascii_alphanumeric())
        .flat_map(|ch| ch.to_lowercase())
        .collect()
}

fn path_safe_fragment(value: &str) -> String {
    let mut fragment = String::new();
    let mut last_was_separator = false;
    for ch in value.chars() {
        let next = if ch.is_ascii_alphanumeric() {
            last_was_separator = false;
            Some(ch.to_ascii_lowercase())
        } else if !last_was_separator {
            last_was_separator = true;
            Some('_')
        } else {
            None
        };
        if let Some(ch) = next {
            fragment.push(ch);
        }
    }
    fragment.trim_matches('_').to_string()
}

fn build_auto_quant_agent_workflow(
    payload: &AutoQuantResearchHandoffPayload,
) -> AutoQuantAgentWorkflow {
    let lane_root = PathBuf::from(&payload.state_dir)
        .join("auto-quant/workspaces")
        .join(path_safe_fragment(&payload.artifact_id));
    let user_data = lane_root.join("user_data");
    let strategies_dir = user_data.join("strategies");
    let results_tsv = lane_root.join("results.tsv");
    let plan_path = lane_root.join("plan.md");
    let review_path = lane_root.join("review.md");
    let run_log = lane_root.join("run.log");
    let failure_patterns_path = lane_root.join("failure_patterns.md");
    let layer_updates_path = lane_root.join("harness_layer_updates.md");
    let regression_path = lane_root.join("regression_review.md");

    AutoQuantAgentWorkflow {
        workflow_style: "plan_work_review".to_string(),
        setup_commands: vec![
            format!("mkdir -p {}", shell_quote(&strategies_dir.to_string_lossy())),
            format!(
                "cp {} {}",
                shell_quote(&payload.workspace.config_json),
                shell_quote(&lane_root.join("config.json").to_string_lossy())
            ),
            format!(
                "printf 'commit\\tevent\\tstrategy_name\\tsharpe\\tmax_dd\\tnote\\n' > {}",
                shell_quote(&results_tsv.to_string_lossy())
            ),
        ],
        environment: vec![
            format!(
                "AUTO_QUANT_WORKSPACE={}",
                lane_root.to_string_lossy()
            ),
            format!(
                "AUTO_QUANT_DATA_DIR={}",
                payload.workspace.data_dir
            ),
            format!(
                "AUTO_QUANT_CONFIG={}",
                lane_root.join("config.json").to_string_lossy()
            ),
            format!(
                "AUTO_QUANT_USER_DATA={}",
                user_data.to_string_lossy()
            ),
            format!(
                "AUTO_QUANT_STRATEGIES_DIR={}",
                strategies_dir.to_string_lossy()
            ),
            format!(
                "AUTO_QUANT_RESULTS_TSV={}",
                results_tsv.to_string_lossy()
            ),
        ],
        entry_regime_contract: Some(trend_expansion_entry_regime_contract()),
        lifecycle_layers: vec![
            AutoQuantLifecycleLayer {
                layer_id: "h3_environment_contract".to_string(),
                name: "Environment Contract Layer".to_string(),
                trigger_timing: "before interaction / before Auto-Quant iteration".to_string(),
                ict_engine_mapping: "make provider, data, cost, strategy-file, trend/expansion entry, and adoption boundaries explicit before running a lane".to_string(),
                required_evidence: vec![
                    "plan.md names provider/data/cost contracts and immutable evaluation files".to_string(),
                    "plan.md names TrendExpansion as the only entry regime and maps every non-trend factor to exclusion or counter-evidence".to_string(),
                    "handoff payload keeps shared Auto-Quant config/data read-only under AUTO_QUANT_WORKSPACE".to_string(),
                ],
            },
            AutoQuantLifecycleLayer {
                layer_id: "h5_procedural_skill".to_string(),
                name: "Procedural Skill Layer".to_string(),
                trigger_timing: "task conditioning / lane planning".to_string(),
                ict_engine_mapping: "retrieve or write compact factor procedure guidance from prior measured trajectories while preserving the trend/expansion-only entry gate".to_string(),
                required_evidence: vec![
                    "failure_patterns.md records recurring measured failures and reusable procedures".to_string(),
                    "plan.md classifies each candidate idea as entry, non-trend exclusion, or trend counter-evidence before strategy edits".to_string(),
                    "plan.md maps each entry candidate idea to at most three active strategy files".to_string(),
                ],
            },
            AutoQuantLifecycleLayer {
                layer_id: "h2_action_realization".to_string(),
                name: "Action Realization Layer".to_string(),
                trigger_timing: "after strategy edit, before measured run/adoption".to_string(),
                ict_engine_mapping: "validate executable artifacts and trend/expansion entry guards before run.py/adoption review instead of letting malformed strategy, missing data, or non-trend regimes enter promotion".to_string(),
                required_evidence: vec![
                    "review.md confirms each measured iteration edited the matching strategy file before run.py".to_string(),
                    "review.md confirms entries require expansion or trend_continuation evidence and block compression/reversion/manipulation/unknown states".to_string(),
                    "run.log/results.tsv show the action was executable and measured".to_string(),
                ],
            },
            AutoQuantLifecycleLayer {
                layer_id: "h4_trajectory_regulation".to_string(),
                name: "Trajectory Regulation Layer".to_string(),
                trigger_timing: "after measured run / between iterations".to_string(),
                ict_engine_mapping: "detect repeated no-survivor loops, no-fill results, non-trend over-entry, stale data reuse, and budget exhaustion before another same-shape iteration".to_string(),
                required_evidence: vec![
                    "review.md records keep/discard/fork/stop decisions from measured output".to_string(),
                    "regression_review.md checks that non-trend helper factors block or down-rank entries rather than becoming standalone entry signals".to_string(),
                    "regression_review.md checks over-trigger, valid-candidate blocking, misleading guidance, and repeated failure loops".to_string(),
                ],
            },
        ],
        evolution_inputs: vec![
            "current Auto-Quant handoff artifact and ict-engine objective".to_string(),
            "previous run.log/results.tsv/terminal metrics for this lineage when available".to_string(),
            "failure_patterns.md derived from measured trajectories, not from chat-only speculation".to_string(),
            "TrendExpansion entry contract: only expansion or trend_continuation evidence can authorize entries; all other labels are exclusion or counter-evidence".to_string(),
            "skills/auto-quant-handoff-harness/SKILL.md Life-Harness four-layer contract".to_string(),
        ],
        phases: vec![
            format!(
                "plan: read Auto-Quant AGENTS.md, README.md, program.md, prepare.py, run.py, _template.py.example, the ict-engine handoff, and the Life-Harness layer contract; write {} with objective, lane scope, data paths, candidate ideas, TrendExpansion entry classification, lifecycle-layer mapping, verification commands, and stop conditions before editing strategies",
                plan_path.to_string_lossy()
            ),
            format!(
                "failure-mining: inspect prior measured trajectories when present and write {} with dominant deterministic failure patterns, earliest detectable lifecycle layer, and why each pattern is mechanical rather than hidden-oracle reasoning",
                failure_patterns_path.to_string_lossy()
            ),
            format!(
                "work: create or evolve at most 3 active non-underscore entry strategies inside the lane strategies directory; each entry must require expansion or trend_continuation evidence, while compression/reversion/manipulation/unknown evidence may only filter, block, or down-rank; keep config, run.py, prepare.py, and shared data read-only; record each targeted layer update in {}",
                layer_updates_path.to_string_lossy()
            ),
            format!(
                "review: run the measured Auto-Quant command with the environment above, inspect {}, update results.tsv, and write {} with keep/discard evidence, lifecycle safety rationale, and remaining failure modes before exporting anything back",
                run_log.to_string_lossy(),
                review_path.to_string_lossy()
            ),
        ],
        expected_artifacts: vec![
            plan_path.to_string_lossy().to_string(),
            failure_patterns_path.to_string_lossy().to_string(),
            layer_updates_path.to_string_lossy().to_string(),
            run_log.to_string_lossy().to_string(),
            results_tsv.to_string_lossy().to_string(),
            strategies_dir.join("*.py").to_string_lossy().to_string(),
            review_path.to_string_lossy().to_string(),
            regression_path.to_string_lossy().to_string(),
            "strategy_library.json or an ict-engine adoption bundle when a measured candidate survives review".to_string(),
        ],
        regression_checks: vec![
            "over_trigger: identify any lifecycle rule that would block a previously valid measured strategy".to_string(),
            "valid_action_blocking: confirm malformed/missing artifacts are blocked before run or adoption, while executable candidate files still run".to_string(),
            "entry_regime_regression: confirm entries only occur on expansion or trend_continuation evidence and non-trend labels only block/down-rank".to_string(),
            "misleading_guidance: confirm plan/work/review text does not imply promotion_allowed or trade_usable from backtest-only evidence".to_string(),
            "loop_regression: stop or change branch when repeated measured runs produce the same no-fill/no-survivor/no-data failure".to_string(),
        ],
        freeze_boundary: vec![
            "The model weights, provider data, benchmark/evaluation logic, ict-engine promotion gates, TrendExpansion entry contract, and Auto-Quant run.py/prepare.py/config contract remain fixed.".to_string(),
            "After a candidate package is returned, ict-engine adoption and practical-readiness evaluation must use the frozen returned artifacts; do not keep editing the harness while claiming evaluation evidence.".to_string(),
        ],
        return_to_ict_engine: vec![
            "run auto-quant-adoption-review against the persisted handoff artifact before any downstream adoption decision".to_string(),
            "report measured trade_count, win_rate, profit_factor, drawdown, cost assumptions, and artifact paths; do not summarize from memory".to_string(),
            "return dominant failure patterns, lifecycle layer assignment, implemented changes, safety rationale, regression review, and remaining failure modes".to_string(),
            "treat Auto-Quant success as candidate evidence only until ict-engine promotion gates explicitly pass".to_string(),
        ],
        constraints: vec![
            "Follow Life-Harness runtime interface adaptation: adapt the harness around deterministic failures, not model weights, provider data, evaluation rules, or ict-engine promotion gates".to_string(),
            "Only TrendExpansion entries are allowed: an entry signal must be backed by expansion or trend_continuation evidence; compression, reversion, manipulation, transition, range, and unknown evidence are exclusion or counter-evidence only".to_string(),
            "Do not mutate shared Auto-Quant repo-root config.json, user_data/strategies, user_data/data, or results.tsv when AUTO_QUANT_WORKSPACE is available".to_string(),
            "Do not run Claude Code Harness plugin installers, hooks, MCP setup, or bundled binaries from this handoff".to_string(),
            "trade_usable is not implied by Auto-Quant run success, sparse positive results, or a generated strategy file".to_string(),
            "preserve unrelated ict-engine and Auto-Quant working tree changes".to_string(),
        ],
    }
}

fn trend_expansion_entry_regime_contract() -> AutoQuantEntryRegimeContract {
    AutoQuantEntryRegimeContract {
        contract_id: "trend_expansion_entry_only_v1".to_string(),
        primary_entry_regime: "TrendExpansion".to_string(),
        allowed_regime_families: vec!["trend".to_string()],
        allowed_entry_labels: vec!["expansion".to_string(), "trend_continuation".to_string()],
        excluded_entry_labels: vec![
            "compression".to_string(),
            "reversion".to_string(),
            "manipulation".to_string(),
            "transition".to_string(),
            "range".to_string(),
            "unknown".to_string(),
        ],
        non_entry_factor_role: "exclude_non_trend_or_counter_evidence".to_string(),
        required_counter_evidence_checks: vec![
            "compression/reversion labels block entry unless later evidence reclassifies the state as expansion or trend_continuation".to_string(),
            "manipulation/transition labels remain no-entry counter-evidence until resolved into a trend family".to_string(),
            "unknown or low-confidence regime evidence blocks entry and stays observation-only".to_string(),
        ],
    }
}

fn requested_data_missing_notes(
    data_path: &str,
    paired_data_path: Option<&str>,
    state_dir: &str,
) -> Vec<String> {
    let mut notes = Vec::new();
    if !Path::new(data_path).exists() {
        notes.push(format!(
            "auto_quant_requested_data_missing: flag=--data path={} expected=cleaned candle JSON/CSV with timestamp/open/high/low/close fields or columns recovery=ict-engine auto-quant-prepare --state-dir {}",
            data_path,
            shell_quote(state_dir)
        ));
    }
    if let Some(path) = paired_data_path.filter(|value| !value.trim().is_empty()) {
        if !Path::new(path).exists() {
            notes.push(format!(
                "auto_quant_requested_data_missing: flag=--paired-data path={} expected=cleaned candle JSON/CSV with timestamp/open/high/low/close fields or columns recovery=ict-engine auto-quant-prepare --state-dir {}",
                path,
                shell_quote(state_dir)
            ));
        }
    }
    notes
}

pub fn auto_quant_active_strategy_count(workspace: &AutoQuantWorkspaceConfig) -> usize {
    let strategies_dir = Path::new(&workspace.strategies_dir);
    if !strategies_dir.exists() {
        return workspace
            .strategy_seed_source_dir
            .as_deref()
            .map(|path| {
                let mut fallback = workspace.clone();
                fallback.strategies_dir = path.to_string();
                fallback.strategy_seed_source_dir = None;
                auto_quant_active_strategy_count(&fallback)
            })
            .unwrap_or(0);
    }
    match std::fs::read_dir(strategies_dir) {
        Ok(entries) => entries
            .filter_map(Result::ok)
            .filter(|entry| {
                let path = entry.path();
                let is_python = path
                    .extension()
                    .and_then(|ext| ext.to_str())
                    .map(|ext| ext.eq_ignore_ascii_case("py"))
                    .unwrap_or(false);
                let is_active = entry
                    .file_name()
                    .to_str()
                    .map(|name| !name.starts_with('_'))
                    .unwrap_or(false);
                is_python && is_active
            })
            .count()
            .max(
                workspace
                    .strategy_seed_source_dir
                    .as_deref()
                    .map(|path| {
                        let mut fallback = workspace.clone();
                        fallback.strategies_dir = path.to_string();
                        fallback.strategy_seed_source_dir = None;
                        auto_quant_active_strategy_count(&fallback)
                    })
                    .unwrap_or(0),
            ),
        Err(_) => 0,
    }
}

fn auto_quant_strategy_template_path(workspace: &AutoQuantWorkspaceConfig) -> String {
    PathBuf::from(&workspace.strategies_dir)
        .join("_template.py.example")
        .to_string_lossy()
        .to_string()
}

fn strategy_material_full_path(root: &str, material_path: &str) -> String {
    PathBuf::from(root)
        .join(material_path)
        .to_string_lossy()
        .to_string()
}

fn format_strategy_material_summary(material: &AutoQuantStrategyMaterialSummary) -> String {
    let mut parts = vec![format!("{} [{}]", material.name, material.strategy_path)];
    if let Some(csv_path) = &material.evidence_csv_path {
        parts.push(format!("csv={csv_path}"));
    }
    if material.trade_rows > 0 {
        parts.push(format!("trades={}", material.trade_rows));
    }
    if let Some(total_net_pnl) = material.total_net_pnl {
        parts.push(format!("net_pnl={total_net_pnl:.2}"));
    }
    if material.tp_count > 0 || material.sl_count > 0 || material.be_count > 0 {
        parts.push(format!(
            "tp/sl/be={}/{}/{}",
            material.tp_count, material.sl_count, material.be_count
        ));
    }
    if let Some(average_score) = material.average_score {
        parts.push(format!("avg_score={average_score:.2}"));
    }
    parts.join(", ")
}

pub fn base_suggested_commands(
    workspace: &AutoQuantWorkspaceConfig,
    state_dir: &str,
    data_ready: bool,
    active_strategy_count: usize,
    auxiliary_evidence_path: Option<&str>,
    strategy_material_root: Option<&str>,
    external_strategy_materials: &[AutoQuantStrategyMaterialSummary],
) -> Vec<String> {
    let mut commands = vec![format!("cat {}", workspace.program_md)];
    if let Some(path) = auxiliary_evidence_path.filter(|value| !value.trim().is_empty()) {
        commands.push(format!("cat {}", shell_quote(path)));
    }
    if active_strategy_count == 0 {
        commands.push(format!(
            "cat {}",
            auto_quant_strategy_template_path(workspace)
        ));
        if let Some(root) = strategy_material_root.filter(|value| !value.trim().is_empty()) {
            for material in external_strategy_materials.iter().take(2) {
                let strategy_path = strategy_material_full_path(root, &material.strategy_path);
                commands.push(format!("sed -n '1,160p' {}", shell_quote(&strategy_path)));
                if let Some(csv_path) = &material.evidence_csv_path {
                    let csv_path = strategy_material_full_path(root, csv_path);
                    commands.push(format!("head -n 20 {}", shell_quote(&csv_path)));
                }
            }
        }
    }
    if !data_ready {
        commands.push(auto_quant_prepare_cli_command(state_dir));
    } else {
        commands.push(auto_quant_run_command(workspace));
    }
    commands
}

pub fn suggested_next_steps_for_handoff(
    handoff_kind: &str,
    data_ready: bool,
    active_strategy_count: usize,
    has_external_strategy_materials: bool,
) -> Vec<String> {
    let seed_step = if has_external_strategy_materials {
        "read Auto-Quant program.md, the strategy template, and the attached external strategy material summaries, then create 2-3 active non-underscore strategy files across different paradigms before any run.py execution"
            .to_string()
    } else {
        "read Auto-Quant program.md plus the strategy template, then create 2-3 active non-underscore strategy files across different paradigms before any run.py execution"
            .to_string()
    };
    match (handoff_kind, data_ready, active_strategy_count == 0) {
        ("factor_autoresearch", false, _) => vec![
            "prepare Auto-Quant market data before attempting the autoresearch loop".to_string(),
            "re-run factor-autoresearch with backend=auto-quant after data becomes ready".to_string(),
        ],
        (_, false, _) => vec![
            "prepare Auto-Quant market data before attempting the research loop".to_string(),
            "re-run factor-research with backend=auto-quant after data becomes ready".to_string(),
        ],
        ("factor_autoresearch", true, true) => vec![
            seed_step.clone(),
            "after seeding, run the Auto-Quant loop, keep or discard only from measured backtest results, and export candidate plus retrospective checkpoints back to ict-engine".to_string(),
        ],
        (_, true, true) => vec![
            seed_step,
            "after seeding, run Auto-Quant backtests, keep the best measured candidate, and export the candidate package back to ict-engine".to_string(),
        ],
        ("factor_autoresearch", true, false) => vec![
            "resume or start the Auto-Quant autonomous loop with factor retention and explicit keep/discard review".to_string(),
            "export candidate/retrospective summary back to ict-engine after each iteration checkpoint".to_string(),
        ],
        (_, true, false) => vec![
            "open Auto-Quant program.md and stage a research loop for the requested objective".to_string(),
            "run Auto-Quant backtest loop and export a stable candidate package for ict-engine".to_string(),
        ],
    }
}

fn build_auto_quant_agent_prompt(
    handoff_kind: &str,
    objective: &str,
    workspace: &AutoQuantWorkspaceConfig,
    active_strategy_count: usize,
    auxiliary_evidence_path: Option<&str>,
    strategy_material_root: Option<&str>,
    external_strategy_materials: &[AutoQuantStrategyMaterialSummary],
) -> String {
    let template_path = auto_quant_strategy_template_path(workspace);
    let external_materials_summary = if external_strategy_materials.is_empty() {
        String::new()
    } else {
        let root = strategy_material_root.unwrap_or("<external-strategy-material-root>");
        let materials = external_strategy_materials
            .iter()
            .take(3)
            .map(format_strategy_material_summary)
            .collect::<Vec<_>>()
            .join(" | ");
        format!(
            " Read-only external strategy materials from {} are attached as seed inspiration only; do not execute those scripts directly or carry their absolute-path runtime dependencies into the managed Auto-Quant workspace. Highest-evidence materials: {}.",
            root, materials
        )
    };
    let auxiliary_instruction = auxiliary_evidence_path
        .filter(|value| !value.trim().is_empty())
        .map(|path| {
            format!(
                " Auxiliary/options evidence is attached at {}; treat it as a static market overlay for options_hedging and dealer-positioning judgment rather than inventing a proxy from scratch.",
                path
            )
        })
        .unwrap_or_default();
    let seed_instruction = if active_strategy_count == 0 {
        format!(
            "If {} has no active non-underscore .py strategies, first read {}, create 2-3 seed strategies across different paradigms, prefer archived winners or minimal descendants when available, and only then run {}.{}{}",
            workspace.strategies_dir,
            template_path,
            auto_quant_run_command(workspace),
            external_materials_summary,
            auxiliary_instruction,
        )
    } else {
        format!(
            "Run {} on the current active strategy set, review measured results, and iterate only from backtest evidence.{}{}",
            auto_quant_run_command(workspace),
            external_materials_summary,
            auxiliary_instruction,
        )
    };
    match handoff_kind {
        "factor_autoresearch" => format!(
            "Auto-Quant is the autoresearch execution backend for this request. Keep ict-engine as the control plane, preserve existing ict-engine factors, work the '{}' objective, and read {} before acting. {} Never treat 'no strategies found' as completion. Keep, discard, fork, or kill only from measured results and return a candidate package plus retrospective signals to ict-engine.",
            objective, workspace.program_md, seed_instruction
        ),
        _ => format!(
            "Auto-Quant is the research execution backend for this request. Keep ict-engine as the control plane, preserve old factors, work the '{}' objective, and read {} before acting. {} Never treat 'no strategies found' as completion. Export the best measured candidate package back into ict-engine state.",
            objective, workspace.program_md, seed_instruction
        ),
    }
}

pub fn build_factor_research_handoff_payload(
    input: BuildFactorResearchHandoffPayloadInput<'_>,
) -> AutoQuantResearchHandoffPayload {
    let BuildFactorResearchHandoffPayloadInput {
        symbol,
        data,
        objective,
        provider_profile_selector,
        paired_data,
        auxiliary_evidence_path,
        mutation_spec_path,
        strategy_material_root,
        state_dir,
        dependency_status,
    } = input;
    let workspace =
        auto_quant_workspace_config_for_state(&dependency_status.managed_dir, state_dir);
    let external_strategy_materials = discover_strategy_materials(strategy_material_root, 3);
    let mut payload = AutoQuantResearchHandoffPayload {
        artifact_id: format!(
            "auto-quant-handoff:factor_research:{}:{}",
            symbol,
            Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
        ),
        handoff_kind: "factor_research".to_string(),
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        provider_profile_selector: provider_profile_selector.map(str::to_string),
        objective: objective.to_string(),
        backend: "auto-quant".to_string(),
        data_path: data.to_string(),
        paired_data_path: paired_data.map(str::to_string),
        auxiliary_evidence_path: auxiliary_evidence_path.map(str::to_string),
        mutation_spec_path: mutation_spec_path.map(str::to_string),
        iterations: None,
        session_id: None,
        strategy_material_root: strategy_material_root.map(str::to_string),
        external_strategy_materials,
        dependency_status,
        readiness: None,
        workspace,
        data_ready: false,
        handoff_artifact_path: String::new(),
        iteration_unit: None,
        agent_workflow: None,
        suggested_commands: Vec::new(),
        suggested_next_steps: Vec::new(),
        agent_prompt: String::new(),
        notes: Vec::new(),
    };
    let profile_source = payload.clone();
    super::workspace_profile::apply_handoff_workspace_profile(
        &profile_source,
        &mut payload.workspace,
    );
    payload.data_ready = auto_quant_handoff_data_ready(
        &payload.workspace,
        &payload.data_path,
        payload.paired_data_path.as_deref(),
    );
    let active_strategy_count = auto_quant_active_strategy_count(&payload.workspace);
    payload.readiness = Some(auto_quant_readiness_from_status_and_data(
        &payload.dependency_status,
        &payload.state_dir,
        payload.workspace.clone(),
        payload.data_ready,
    ));
    payload.suggested_commands = base_suggested_commands(
        &payload.workspace,
        &payload.state_dir,
        payload.data_ready,
        active_strategy_count,
        payload.auxiliary_evidence_path.as_deref(),
        payload.strategy_material_root.as_deref(),
        &payload.external_strategy_materials,
    );
    payload.suggested_next_steps = suggested_next_steps_for_handoff(
        &payload.handoff_kind,
        payload.data_ready,
        active_strategy_count,
        !payload.external_strategy_materials.is_empty(),
    );
    payload.agent_prompt = build_auto_quant_agent_prompt(
        &payload.handoff_kind,
        &payload.objective,
        &payload.workspace,
        active_strategy_count,
        payload.auxiliary_evidence_path.as_deref(),
        payload.strategy_material_root.as_deref(),
        &payload.external_strategy_materials,
    );
    payload.agent_workflow = Some(build_auto_quant_agent_workflow(&payload));
    if !payload.data_ready {
        payload
            .notes
            .push("auto_quant_prepare_required_before_run".to_string());
        payload.notes.extend(requested_data_missing_notes(
            &payload.data_path,
            payload.paired_data_path.as_deref(),
            &payload.state_dir,
        ));
    }
    if active_strategy_count == 0 {
        payload
            .notes
            .push("auto_quant_seed_strategies_required".to_string());
    }
    payload.notes.push(format!(
        "auto_quant_active_strategy_count={active_strategy_count}"
    ));
    if let Some(path) = &payload.auxiliary_evidence_path {
        payload
            .notes
            .push(format!("auto_quant_auxiliary_evidence_path={path}"));
    }
    if let Some(root) = &payload.strategy_material_root {
        payload
            .notes
            .push(format!("auto_quant_strategy_material_root={root}"));
        payload.notes.push(format!(
            "auto_quant_external_strategy_material_count={}",
            payload.external_strategy_materials.len()
        ));
    }
    for material in payload.external_strategy_materials.iter().take(3) {
        payload.notes.push(format!(
            "auto_quant_external_strategy_material={}",
            format_strategy_material_summary(material)
        ));
    }
    payload.notes.push(format!(
        "requested_at={}",
        Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
    ));
    payload
}

pub fn build_factor_autoresearch_handoff_payload(
    input: BuildFactorAutoresearchHandoffPayloadInput<'_>,
) -> AutoQuantResearchHandoffPayload {
    let BuildFactorAutoresearchHandoffPayloadInput {
        symbol,
        data,
        objective,
        provider_profile_selector,
        paired_data,
        auxiliary_evidence_path,
        mutation_spec_path,
        strategy_material_root,
        iterations,
        session_id,
        state_dir,
        dependency_status,
    } = input;
    let workspace =
        auto_quant_workspace_config_for_state(&dependency_status.managed_dir, state_dir);
    let external_strategy_materials = discover_strategy_materials(strategy_material_root, 3);
    let mut payload = AutoQuantResearchHandoffPayload {
        artifact_id: format!(
            "auto-quant-handoff:factor_autoresearch:{}:{}",
            symbol,
            Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
        ),
        handoff_kind: "factor_autoresearch".to_string(),
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        provider_profile_selector: provider_profile_selector.map(str::to_string),
        objective: objective.to_string(),
        backend: "auto-quant".to_string(),
        data_path: data.to_string(),
        paired_data_path: paired_data.map(str::to_string),
        auxiliary_evidence_path: auxiliary_evidence_path.map(str::to_string),
        mutation_spec_path: mutation_spec_path.map(str::to_string),
        iterations: Some(iterations),
        session_id: session_id.map(str::to_string),
        strategy_material_root: strategy_material_root.map(str::to_string),
        external_strategy_materials,
        dependency_status,
        readiness: None,
        workspace,
        data_ready: false,
        handoff_artifact_path: String::new(),
        iteration_unit: None,
        agent_workflow: None,
        suggested_commands: Vec::new(),
        suggested_next_steps: Vec::new(),
        agent_prompt: String::new(),
        notes: Vec::new(),
    };
    let profile_source = payload.clone();
    super::workspace_profile::apply_handoff_workspace_profile(
        &profile_source,
        &mut payload.workspace,
    );
    payload.data_ready = auto_quant_handoff_data_ready(
        &payload.workspace,
        &payload.data_path,
        payload.paired_data_path.as_deref(),
    );
    let active_strategy_count = auto_quant_active_strategy_count(&payload.workspace);
    payload.readiness = Some(auto_quant_readiness_from_status_and_data(
        &payload.dependency_status,
        &payload.state_dir,
        payload.workspace.clone(),
        payload.data_ready,
    ));
    payload.suggested_commands = base_suggested_commands(
        &payload.workspace,
        &payload.state_dir,
        payload.data_ready,
        active_strategy_count,
        payload.auxiliary_evidence_path.as_deref(),
        payload.strategy_material_root.as_deref(),
        &payload.external_strategy_materials,
    );
    payload.suggested_next_steps = suggested_next_steps_for_handoff(
        &payload.handoff_kind,
        payload.data_ready,
        active_strategy_count,
        !payload.external_strategy_materials.is_empty(),
    );
    payload.agent_prompt = build_auto_quant_agent_prompt(
        &payload.handoff_kind,
        &payload.objective,
        &payload.workspace,
        active_strategy_count,
        payload.auxiliary_evidence_path.as_deref(),
        payload.strategy_material_root.as_deref(),
        &payload.external_strategy_materials,
    );
    payload.agent_workflow = Some(build_auto_quant_agent_workflow(&payload));
    if !payload.data_ready {
        payload
            .notes
            .push("auto_quant_prepare_required_before_run".to_string());
        payload.notes.extend(requested_data_missing_notes(
            &payload.data_path,
            payload.paired_data_path.as_deref(),
            &payload.state_dir,
        ));
    }
    if active_strategy_count == 0 {
        payload
            .notes
            .push("auto_quant_seed_strategies_required".to_string());
    }
    payload.notes.push(format!(
        "auto_quant_active_strategy_count={active_strategy_count}"
    ));
    if let Some(path) = &payload.auxiliary_evidence_path {
        payload
            .notes
            .push(format!("auto_quant_auxiliary_evidence_path={path}"));
    }
    if let Some(root) = &payload.strategy_material_root {
        payload
            .notes
            .push(format!("auto_quant_strategy_material_root={root}"));
        payload.notes.push(format!(
            "auto_quant_external_strategy_material_count={}",
            payload.external_strategy_materials.len()
        ));
    }
    for material in payload.external_strategy_materials.iter().take(3) {
        payload.notes.push(format!(
            "auto_quant_external_strategy_material={}",
            format_strategy_material_summary(material)
        ));
    }
    payload.notes.push(format!(
        "requested_at={}",
        Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
    ));
    payload
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::types::AutoQuantDependencyStatus;

    fn healthy_dependency_status_for(managed_dir: &str) -> AutoQuantDependencyStatus {
        AutoQuantDependencyStatus {
            repo_url: "repo".to_string(),
            managed_dir: managed_dir.to_string(),
            tracked_branch: "master".to_string(),
            pinned_ref: None,
            current_commit: None,
            upstream_commit: None,
            bootstrap_needed: false,
            config_present: true,
            managed_repo_present: true,
            healthy: true,
            update_available: false,
            required_files: Vec::new(),
            notes: Vec::new(),
            adapter_version: "v1".to_string(),
            last_sync: None,
        }
    }

    #[test]
    fn research_handoff_attaches_read_only_strategy_material_summary() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("prepared-{index}.feather")), "ready").unwrap();
        }

        let material_root = temp.path().join("Tomac Material Library");
        std::fs::create_dir_all(&material_root).unwrap();
        std::fs::write(
            material_root.join("trend_runner.py"),
            "class TrendRunner: pass\n",
        )
        .unwrap();
        std::fs::write(
            material_root.join("trend_runner_results.csv"),
            "Time,Net PnL,Result,Score\n2024-01-01,12.5,TP,4.5\n2024-01-02,-2.5,BE,3.5\n",
        )
        .unwrap();

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: Some(material_root.to_str().unwrap()),
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        assert_eq!(payload.external_strategy_materials.len(), 1);
        assert_eq!(
            payload.external_strategy_materials[0]
                .evidence_csv_path
                .as_deref(),
            Some("trend_runner_results.csv")
        );
        assert!(payload
            .agent_prompt
            .contains("do not execute those scripts directly"));
        assert!(payload
            .notes
            .iter()
            .any(|note| note.starts_with("auto_quant_external_strategy_material_count=1")));
        assert!(payload.suggested_commands.iter().any(|command| {
            command.starts_with("sed -n '1,160p' ")
                && command.contains("'")
                && command.contains("Tomac Material Library/trend_runner.py")
        }));
    }

    #[test]
    fn autoresearch_handoff_preserves_iterations_and_session_id() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("prepared-{index}.feather")), "ready").unwrap();
        }

        let payload =
            build_factor_autoresearch_handoff_payload(BuildFactorAutoresearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: Some("mutation.json"),
                strategy_material_root: None,
                iterations: 3,
                session_id: Some("session-123"),
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        assert_eq!(payload.handoff_kind, "factor_autoresearch");
        assert_eq!(payload.iterations, Some(3));
        assert_eq!(payload.session_id.as_deref(), Some("session-123"));
        assert_eq!(payload.mutation_spec_path.as_deref(), Some("mutation.json"));
        assert!(payload
            .agent_prompt
            .contains("Keep, discard, fork, or kill only from measured results"));
    }

    #[test]
    fn handoff_suggested_commands_use_repo_prepare_wrapper_for_missing_data() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();

        let missing_data =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "generic",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });
        assert!(missing_data
            .suggested_commands
            .iter()
            .any(|command| command.contains("ict-engine auto-quant-prepare --state-dir")));

        let requested_data = temp.path().join("demo.json");
        std::fs::write(&requested_data, "[]").unwrap();
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&data_dir).unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("demo-{index}.feather")), "ready").unwrap();
        }
        std::fs::write(strategies_dir.join("SeedAlpha.py"), "class SeedAlpha: pass").unwrap();

        let ready = build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
            symbol: "NQ",
            data: requested_data.to_str().unwrap(),
            objective: "generic",
            provider_profile_selector: None,
            paired_data: None,
            auxiliary_evidence_path: None,
            mutation_spec_path: None,
            strategy_material_root: None,
            state_dir: temp.path().to_str().unwrap(),
            dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
        });
        assert!(ready
            .suggested_commands
            .iter()
            .any(|command| command.contains("./.venv/bin/python run.py")));
    }

    #[test]
    fn handoff_requires_requested_data_path_even_when_workspace_cache_is_ready() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        std::fs::write(strategies_dir.join("SeedAlpha.py"), "class SeedAlpha: pass").unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("prepared-{index}.feather")), "ready").unwrap();
        }

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: temp.path().join("missing-primary.json").to_str().unwrap(),
                objective: "generic",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        assert!(!payload.data_ready);
        assert_eq!(
            payload
                .readiness
                .as_ref()
                .map(|value| value.status.as_str()),
            Some("dependency_ready_data_missing")
        );
        assert!(payload
            .suggested_commands
            .iter()
            .any(|command| command.contains("ict-engine auto-quant-prepare --state-dir")));
    }

    #[test]
    fn handoff_notes_name_missing_requested_data_schema_and_prepare_recovery() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        std::fs::write(strategies_dir.join("SeedAlpha.py"), "class SeedAlpha: pass").unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("prepared-{index}.feather")), "ready").unwrap();
        }
        let missing_data = temp.path().join("missing-primary.csv");

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: missing_data.to_str().unwrap(),
                objective: "generic",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });
        let notes = payload.notes.join(" | ");

        assert!(!payload.data_ready);
        assert!(notes.contains("missing-primary.csv"), "{notes}");
        assert!(notes.contains("cleaned candle JSON/CSV"), "{notes}");
        assert!(notes.contains("timestamp/open/high/low/close"), "{notes}");
        assert!(
            notes.contains("ict-engine auto-quant-prepare --state-dir"),
            "{notes}"
        );
        assert!(payload
            .suggested_commands
            .iter()
            .any(|command| command.contains("ict-engine auto-quant-prepare --state-dir")));
    }

    #[test]
    fn handoff_does_not_treat_unrelated_default_workspace_feathers_as_requested_data_ready() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        std::fs::write(strategies_dir.join("SeedAlpha.py"), "class SeedAlpha: pass").unwrap();
        for pair in ["BTC_USDT", "ETH_USDT", "SOL_USDT", "BNB_USDT", "AVAX_USDT"] {
            for timeframe in ["1h", "4h", "1d"] {
                std::fs::write(
                    data_dir.join(format!("{pair}-{timeframe}.feather")),
                    "ready",
                )
                .unwrap();
            }
        }
        let requested_data = temp.path().join("yf_crwd_5m.csv");
        std::fs::write(&requested_data, "timestamp,open,high,low,close,volume\n").unwrap();

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "YF_AI_SECURITY_CRWD5M_PDA_MTF_SOFT_CONFIRMATION_DOWNSTREAM",
                data: requested_data.to_str().unwrap(),
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        assert!(!payload.data_ready);
        assert_eq!(
            payload
                .readiness
                .as_ref()
                .map(|value| value.status.as_str()),
            Some("dependency_ready_data_missing")
        );
        assert!(payload
            .suggested_commands
            .iter()
            .any(|command| command.contains("ict-engine auto-quant-prepare --state-dir")));
    }

    #[test]
    fn factor_research_handoff_output_uses_synthetic_profile_for_existing_local_data() {
        let temp = tempfile::tempdir().unwrap();
        let state_dir = temp.path().join("state");
        let managed_dir = state_dir.join(".deps/auto-quant");
        let default_strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&default_strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('default')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(managed_dir.join("prepare_external.py"), "print('external')").unwrap();
        std::fs::write(managed_dir.join("run_tomac.py"), "print('tomac')").unwrap();
        std::fs::write(
            default_strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        std::fs::write(
            default_strategies_dir.join("TomacSeed.py"),
            "class TomacSeed: pass",
        )
        .unwrap();
        for pair in ["BTC_USDT", "ETH_USDT", "SOL_USDT", "BNB_USDT", "AVAX_USDT"] {
            for timeframe in ["1h", "4h", "1d"] {
                std::fs::write(
                    data_dir.join(format!("{pair}-{timeframe}.feather")),
                    "generic-ready",
                )
                .unwrap();
            }
        }
        let requested_data = temp
            .path()
            .join("TOMAC_TOD_CAP65_REDUCED_NQ_ANCHOR.continuous-1m.json");
        std::fs::write(
            &requested_data,
            r#"[{"date":"2025-10-27T14:47:00Z","open":1.0,"high":2.0,"low":0.5,"close":1.5,"volume":10.0}]"#,
        )
        .unwrap();

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "TOMAC_TOD_CAP65_REDUCED_WINDOW_DOWNSTREAM_NQ_ANCHOR",
                data: requested_data.to_str().unwrap(),
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: state_dir.to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        assert_eq!(
            payload.workspace.profile_name.as_deref(),
            Some("synthetic_ohlcv")
        );
        assert!(payload
            .workspace
            .prepare_script
            .ends_with("prepare_external.py"));
        assert!(payload.workspace.run_script.ends_with("run_tomac.py"));
        assert!(payload.workspace.config_json.ends_with("config.tomac.json"));
        assert!(payload
            .workspace
            .strategies_dir
            .ends_with("strategies_external"));
        assert!(payload
            .readiness
            .as_ref()
            .unwrap()
            .workspace
            .run_script
            .ends_with("run_tomac.py"));
        assert!(payload.agent_prompt.contains("run_tomac.py"));
        assert!(!payload.agent_prompt.contains("python run.py"));
        assert!(!payload.data_ready);
    }

    #[test]
    fn handoff_payload_can_carry_iteration_unit_context() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();

        let mut payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });
        payload.iteration_unit = Some(AutoQuantIterationUnitContext {
            unit_label: "NQ:15m:long:order_block".to_string(),
            primitive_sequence: vec!["order_block".to_string()],
            timeframe: "15m".to_string(),
            direction: "long".to_string(),
            strategy_brief: "Iterate one order_block long unit. Optimize win rate first."
                .to_string(),
            evaluation_priority: vec![
                "win_rate".to_string(),
                "sharpe".to_string(),
                "return".to_string(),
            ],
            consumer_evidence_profile: None,
        });

        let unit = payload.iteration_unit.as_ref().unwrap();
        assert_eq!(unit.primitive_sequence, vec!["order_block".to_string()]);
        assert_eq!(unit.evaluation_priority[0], "win_rate");
    }

    #[test]
    fn handoff_payload_carries_auxiliary_evidence_path_into_commands_and_prompt() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("prepared-{index}.feather")), "ready").unwrap();
        }
        let auxiliary_path = temp.path().join("family-g-aux.json");
        std::fs::write(&auxiliary_path, "{}").unwrap();

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "generic",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: Some(auxiliary_path.to_str().unwrap()),
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        assert_eq!(
            payload.auxiliary_evidence_path.as_deref(),
            Some(auxiliary_path.to_str().unwrap())
        );
        assert!(payload
            .suggested_commands
            .iter()
            .any(|command| command.contains("family-g-aux.json")));
        assert!(payload
            .agent_prompt
            .contains("Auxiliary/options evidence is attached"));
        assert!(payload
            .notes
            .iter()
            .any(|note| note.contains("auto_quant_auxiliary_evidence_path=")));
    }
}
