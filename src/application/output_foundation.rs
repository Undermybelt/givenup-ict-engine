use anyhow::Result;
use serde::Serialize;
use serde_json::Value;

use crate::state::WorkflowPhaseSnapshot;

pub fn redact_local_paths(text: &str) -> String {
    let bytes = text.as_bytes();
    let mut out = String::with_capacity(text.len());
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'/' {
            let rest = &text[i..];
            let is_local = rest.starts_with("/Users/")
                || rest.starts_with("/home/")
                || rest.starts_with("/tmp/")
                || rest.starts_with("/var/")
                || rest.starts_with("/private/")
                || rest.starts_with("/Volumes/");
            if is_local {
                let mut j = i;
                while j < bytes.len() {
                    let ch = bytes[j];
                    if ch.is_ascii_whitespace()
                        || matches!(
                            ch,
                            b',' | b';' | b'|' | b')' | b'(' | b'[' | b']' | b'{' | b'}'
                        )
                    {
                        break;
                    }
                    j += 1;
                }
                out.push_str("<local-path>");
                i = j;
                continue;
            }
        }
        out.push(bytes[i] as char);
        i += 1;
    }
    out
}

pub fn redact_local_paths_in_value(value: &mut Value) {
    match value {
        Value::String(text) => {
            *text = redact_local_paths(text);
        }
        Value::Array(items) => {
            for item in items {
                redact_local_paths_in_value(item);
            }
        }
        Value::Object(map) => {
            for item in map.values_mut() {
                redact_local_paths_in_value(item);
            }
        }
        _ => {}
    }
}

pub fn print_redacted_json<T: Serialize>(value: &T) -> Result<()> {
    let mut rendered = serde_json::to_value(value)?;
    redact_local_paths_in_value(&mut rendered);
    println!("{}", serde_json::to_string_pretty(&rendered)?);
    Ok(())
}

pub fn format_executor_summary_lines(executor_summaries: &[String]) -> Vec<String> {
    executor_summaries
        .iter()
        .map(|summary| summary.to_string())
        .collect()
}

pub fn short_workflow_phase_summary(phase: &WorkflowPhaseSnapshot) -> String {
    let mut parts = Vec::new();
    if let Some(direction) = &phase.selected_direction {
        parts.push(format!("direction={direction}"));
    }
    if let Some(entry) = &phase.selected_entry_quality {
        parts.push(format!("entry={entry}"));
    }
    if !phase.pre_bayes_gate_status.is_empty() {
        parts.push(format!("gate={}", phase.pre_bayes_gate_status));
    }
    if phase.pre_bayes_evidence_quality_score > 0.0 {
        parts.push(format!(
            "quality={:.3}",
            phase.pre_bayes_evidence_quality_score
        ));
    }
    if parts.is_empty() {
        phase.phase_summary.clone()
    } else {
        parts.join(" ")
    }
}
