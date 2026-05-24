import sys
import unittest
from pathlib import Path


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from help_audit import (  # noqa: E402
    DEFAULT_BUILD_TIMEOUT_SECONDS,
    EXPECTED_NO_OUTPUT_MODE_COMMANDS,
    build_timeout_seconds,
    none_output_mode_policy,
    output_mode_support,
    parse_options,
)


class HelpAuditTest(unittest.TestCase):
    def test_output_mode_support_detects_format_and_aliases(self):
        help_text = """
Usage: ict-engine example [OPTIONS]

Options:
      --output-format <OUTPUT_FORMAT>  Output format: json, compact, agent, human
      --human                         Print human-readable output
      --agent                         Print agent-readable output
      --compact                       Print compact output
  -h, --help                          Print help
"""

        support = output_mode_support(parse_options(help_text))

        self.assertEqual(
            support,
            {
                "output_format": True,
                "human": True,
                "agent": True,
                "compact": True,
            },
        )


    def test_output_mode_support_records_missing_aliases(self):
        help_text = """
Usage: ict-engine provider-status [OPTIONS]

Options:
      --agent    Emit agent-readable status
      --compact  Emit compact status
  -h, --help     Print help
"""

        support = output_mode_support(parse_options(help_text))

        self.assertEqual(
            support,
            {
                "output_format": False,
                "human": False,
                "agent": True,
                "compact": True,
            },
        )

    def test_none_output_mode_policy_reports_unclassified_commands(self):
        rows = [
            {"command": "train", "output_mode_status": "none"},
            {"command": "unexpected-readonly", "output_mode_status": "none"},
            {"command": "analyze", "output_mode_status": "full"},
        ]

        policy = none_output_mode_policy(rows)

        self.assertEqual(policy["expected_count"], len(EXPECTED_NO_OUTPUT_MODE_COMMANDS))
        self.assertEqual(policy["observed_count"], 2)
        self.assertIn("unexpected-readonly", policy["unclassified_none_commands"])
        self.assertIn("update", policy["missing_expected_commands"])
        self.assertFalse(policy["matches_expected"])

    def test_none_output_mode_policy_matches_expected_set(self):
        rows = [
            {"command": command, "output_mode_status": "none"}
            for command in sorted(EXPECTED_NO_OUTPUT_MODE_COMMANDS)
        ] + [{"command": "analyze", "output_mode_status": "full"}]

        policy = none_output_mode_policy(rows)

        self.assertEqual(policy["unclassified_none_commands"], [])
        self.assertEqual(policy["missing_expected_commands"], [])
        self.assertTrue(policy["matches_expected"])

    def test_build_timeout_seconds_reads_positive_env(self):
        import os

        old = os.environ.get("ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS")
        try:
            os.environ["ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS"] = "600"
            self.assertEqual(build_timeout_seconds(), 600)
        finally:
            if old is None:
                os.environ.pop("ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS", None)
            else:
                os.environ["ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS"] = old

    def test_build_timeout_seconds_falls_back_for_invalid_env(self):
        import os

        old = os.environ.get("ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS")
        try:
            os.environ["ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS"] = "not-int"
            self.assertEqual(build_timeout_seconds(), DEFAULT_BUILD_TIMEOUT_SECONDS)
            os.environ["ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS"] = "0"
            self.assertEqual(build_timeout_seconds(), DEFAULT_BUILD_TIMEOUT_SECONDS)
        finally:
            if old is None:
                os.environ.pop("ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS", None)
            else:
                os.environ["ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS"] = old


if __name__ == "__main__":
    unittest.main()
