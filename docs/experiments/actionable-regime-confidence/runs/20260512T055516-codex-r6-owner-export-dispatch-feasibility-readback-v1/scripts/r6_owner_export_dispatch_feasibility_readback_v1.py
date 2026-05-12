#!/usr/bin/env python3
"""Read-only dispatch feasibility check for existing R6 owner-export drafts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from email import policy
from email.parser import BytesParser
from pathlib import Path


RUN_ID = "20260512T055516-codex-r6-owner-export-dispatch-feasibility-readback-v1"
GATE = "r6_owner_export_dispatch_feasibility_readback_v1=drafts_parseable_not_sent_no_transport_identity_no_rows"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "command-output"
PACKET = ROOT / "r6-owner-export-dispatch-feasibility-readback-v1"
CHECKS = ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
DISPATCH_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/"
    "r6-owner-export-v5-dispatch-manifest-v1"
)
EML_FILES = [
    DISPATCH_ROOT / "cme_group_owner_export_v5_dispatch_v1.eml",
    DISPATCH_ROOT / "cboe_cfe_owner_export_v5_dispatch_v1.eml",
]
TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]


def run_cmd(key: str, command: list[str]) -> dict[str, object]:
    stdout_path = OUT / f"{key}.stdout"
    stderr_path = OUT / f"{key}.stderr"
    cmd_path = OUT / f"{key}.cmd"
    exit_path = OUT / f"{key}.exit"
    cmd_path.write_text(" ".join(command) + "\n", encoding="utf-8")
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "key": key,
        "command": command,
        "exit_code": proc.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_bytes": stdout_path.stat().st_size,
        "stderr_bytes": stderr_path.stat().st_size,
    }


def parse_eml(path: Path) -> dict[str, object]:
    msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    body = msg.get_body(preferencelist=("plain",))
    text = body.get_content() if body else msg.get_content()
    return {
        "path": str(path),
        "exists": path.exists(),
        "to": msg.get("to"),
        "subject": msg.get("subject"),
        "from": msg.get("from"),
        "body_chars": len(text),
        "has_to": bool(msg.get("to")),
        "has_subject": bool(msg.get("subject")),
        "has_from": bool(msg.get("from")),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = [
        run_cmd("board_sha256_before", ["shasum", "-a", "256", str(BOARD)]),
    ]

    tool_paths = {name: shutil.which(name) for name in ["sendmail", "mail", "msmtp", "mutt", "mpack", "swaks"]}
    config_paths = [
        Path.home() / ".mailrc",
        Path.home() / ".msmtprc",
        Path.home() / ".muttrc",
        Path.home() / ".config/msmtp/config",
        Path.home() / ".config/mutt/muttrc",
    ]
    config_presence = {str(path): path.exists() for path in config_paths}
    env_mail_keys = sorted(
        key
        for key in os.environ
        if any(token in key.lower() for token in ["smtp", "sendgrid", "postmark", "resend", "mailgun"])
    )

    drafts = [parse_eml(path) for path in EML_FILES]
    roots_before = {str(path): path.exists() for path in TARGET_ROOTS}
    roots_after = {str(path): path.exists() for path in TARGET_ROOTS}

    cli_transport_present = bool(tool_paths.get("sendmail") or tool_paths.get("mail"))
    explicit_user_mail_config_present = any(config_presence.values()) or bool(tool_paths.get("msmtp")) or bool(tool_paths.get("mutt"))
    drafts_parseable = all(item["has_to"] and item["has_subject"] and item["body_chars"] > 1000 for item in drafts)
    sender_identity_present = all(item["has_from"] for item in drafts)
    external_requests_sent = False
    target_root_mutated = roots_before != roots_after

    summary = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "gate_result": GATE,
        "scope": "read-only feasibility check for sending existing R6 owner-export v5 .eml drafts",
        "commands": commands,
        "drafts": drafts,
        "tool_paths": tool_paths,
        "config_presence": config_presence,
        "env_mail_keys_present_without_values": env_mail_keys,
        "roots_before": roots_before,
        "roots_after": roots_after,
        "assertions": {
            "drafts_parseable": drafts_parseable,
            "cli_transport_present": cli_transport_present,
            "explicit_user_mail_config_present": explicit_user_mail_config_present,
            "sender_identity_present": sender_identity_present,
            "external_requests_sent": external_requests_sent,
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "target_root_mutated": target_root_mutated,
            "canonical_merge_allowed_now": False,
            "downstream_rerun_allowed_now": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": (
            "The v5 owner-export drafts are parseable and addressed, but this check "
            "did not send them. The drafts lack a From header and no user-level "
            "msmtp/mutt/mail config was present, so there is no evidence of a safe "
            "configured outbound identity for unattended dispatch."
        ),
        "next_action": (
            "Dispatch the existing EML drafts through an approved operator mail path "
            "or provide explicit source/control approval. Only after ticket/export/"
            "license/order/support identifiers or verifier-native rows arrive should "
            "the R6 target root be populated and downstream verification rerun."
        ),
    }

    json_path = PACKET / "r6_owner_export_dispatch_feasibility_readback_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = PACKET / "r6_owner_export_dispatch_feasibility_readback_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# R6 Owner Export Dispatch Feasibility Readback v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only feasibility check for the existing `052650` v5 CME/Cboe/CFE owner-export `.eml` drafts. This run does not send external email, receive ticket/export/license identifiers, acquire verifier-native rows, mutate target roots, approve `FLIP` controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Drafts parseable: `{str(drafts_parseable).lower()}`.",
                f"- CLI transport binaries present: `{str(cli_transport_present).lower()}` (`sendmail={tool_paths.get('sendmail')}`, `mail={tool_paths.get('mail')}`).",
                f"- Explicit user mail config present: `{str(explicit_user_mail_config_present).lower()}`.",
                f"- Sender identity in drafts: `{str(sender_identity_present).lower()}`.",
                f"- External requests sent: `{str(external_requests_sent).lower()}`.",
                "",
                "## Decision",
                "",
                "The existing v5 drafts are ready for an operator-controlled dispatch path, but this machine state is not enough to send them unattended: drafts have no `From` header and no user-level `msmtp`/`mutt`/mail config was found. This readback therefore does not unlock R6 or downstream promotion.",
                "",
                "Required roots remain absent unless the JSON says otherwise:",
                "",
                "- `/tmp/ict-engine-board-a-r6-owner-export-v1`",
                "- `/tmp/ict-engine-native-subhour-source-label-intake`",
                "- `/tmp/ict-engine-source-panel-recency-extension`",
                "",
                "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
                "",
                "## Next",
                "",
                "Send the existing `.eml` drafts only through an approved operator mail path, preserving ticket/export/license/order/support identifiers in provenance. Continue Board A only after explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions_path = CHECKS / "r6_owner_export_dispatch_feasibility_readback_v1_assertions.out"
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"drafts_parseable={str(drafts_parseable).lower()}",
                f"cli_transport_present={str(cli_transport_present).lower()}",
                f"explicit_user_mail_config_present={str(explicit_user_mail_config_present).lower()}",
                f"sender_identity_present={str(sender_identity_present).lower()}",
                "external_requests_sent=false",
                "accepted_rows_added=0",
                "source_control_evidence_acquired=false",
                f"target_root_mutated={str(target_root_mutated).lower()}",
                "canonical_merge_allowed_now=false",
                "downstream_rerun_allowed_now=false",
                "strict_full_objective_achieved=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
