use anyhow::{bail, Result};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum OutputFormat {
    Json,
    Compact,
    Agent,
    Human,
}

impl OutputFormat {
    fn parse(value: &str) -> Result<Self> {
        match value.trim().to_ascii_lowercase().as_str() {
            "json" => Ok(Self::Json),
            "compact" => Ok(Self::Compact),
            "agent" => Ok(Self::Agent),
            "human" => Ok(Self::Human),
            other => bail!(
                "unsupported output format '{}'; expected json, compact, agent, or human",
                other
            ),
        }
    }
}

pub(crate) fn resolve_output_format(
    value: &str,
    compact: bool,
    agent: bool,
    human: bool,
) -> Result<OutputFormat> {
    let alias_count = compact as u8 + agent as u8 + human as u8;
    if alias_count > 1 {
        bail!("choose at most one of --compact, --agent, or --human");
    }
    if alias_count == 1 && !value.trim().is_empty() {
        bail!("do not combine --output-format with --compact/--agent/--human");
    }
    if compact {
        return Ok(OutputFormat::Compact);
    }
    if agent {
        return Ok(OutputFormat::Agent);
    }
    if human {
        return Ok(OutputFormat::Human);
    }
    if value.trim().is_empty() {
        return Ok(OutputFormat::Json);
    }
    OutputFormat::parse(value)
}

pub(crate) fn output_format_label(output_format: OutputFormat) -> &'static str {
    match output_format {
        OutputFormat::Json => "json",
        OutputFormat::Compact => "compact",
        OutputFormat::Agent => "agent",
        OutputFormat::Human => "human",
    }
}
