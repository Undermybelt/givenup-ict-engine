use super::*;

pub(crate) struct WorkflowStatusShellInput<'a> {
    pub(crate) symbol: &'a str,
    pub(crate) state_dir: &'a str,
    pub(crate) refresh: bool,
    pub(crate) provider_profile: Option<&'a str>,
    pub(crate) phase: Option<&'a str>,
    pub(crate) actionable_only: bool,
    pub(crate) conflicts_only: bool,
    pub(crate) latest_promotable: bool,
    pub(crate) hard_block_only: bool,
    pub(crate) hard_block_reason: Option<&'a str>,
    pub(crate) limit: Option<usize>,
    pub(crate) output_format: &'a str,
    pub(crate) stable: bool,
}

pub(crate) fn workflow_status_shell(input: WorkflowStatusShellInput<'_>) -> Result<()> {
    let WorkflowStatusShellInput {
        symbol,
        state_dir,
        refresh,
        provider_profile,
        phase,
        actionable_only,
        conflicts_only,
        latest_promotable,
        hard_block_only,
        hard_block_reason,
        limit,
        output_format,
        stable,
    } = input;
    ict_engine::application::orchestration::workflow_status_command(
        ict_engine::application::orchestration::WorkflowStatusCommandInput {
            symbol,
            state_dir,
            refresh,
            provider_profile,
            phase,
            actionable_only,
            conflicts_only,
            latest_promotable,
            hard_block_only,
            hard_block_reason,
            limit,
            output_format,
            stable,
        },
        refresh_workflow_snapshot,
    )
}

pub(crate) fn pre_bayes_status_shell(
    symbol: &str,
    state_dir: &str,
    refresh: bool,
    section: Option<&str>,
) -> Result<()> {
    ict_engine::application::orchestration::pre_bayes_status_command(
        symbol,
        state_dir,
        refresh,
        section,
        refresh_workflow_snapshot,
    )
}
