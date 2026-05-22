#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "support/scripts/smoke_acceptance.sh"


def make_fake_cargo(bin_dir: Path, exit_code: int) -> None:
    cargo = bin_dir / "cargo"
    cargo.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ -n "${FAKE_CARGO_LOG:-}" ]]; then printf "%s\\n" "$*" >> "$FAKE_CARGO_LOG"; fi\n'
        'case "$*" in\n'
        '  *" update "*) printf \'{"realized_outcome": "breakeven", "feedback_records_applied": 1}\\n\' ;;\n'
        '  *" workflow-status "*" --agent"*) printf \'{"current_regime_posterior": {"source_phase": "update"}}\\n\' ;;\n'
        '  *" policy-training-status "*) printf \'{"update_runs": 1}\\n\' ;;\n'
        "  *) printf '{}\\n' ;;\n"
        "esac\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    cargo.chmod(0o755)


def run_smoke_with_fake_cargo(
    tmp_path: Path,
    *,
    state_dir: str,
    cargo_exit_code: int = 0,
    allow_repo_state: bool = False,
) -> subprocess.CompletedProcess[str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_fake_cargo(fake_bin, cargo_exit_code)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["STATE_DIR"] = state_dir
    env["OUT_DIR"] = str(tmp_path / "out")
    env["FAKE_CARGO_LOG"] = str(tmp_path / "cargo.log")
    if allow_repo_state:
        env["ICT_ENGINE_ALLOW_REPO_STATE"] = "1"
    else:
        env.pop("ICT_ENGINE_ALLOW_REPO_STATE", None)

    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )


class SmokeAcceptancePreflightTests(unittest.TestCase):
    def test_refuses_repo_local_state_dir_before_running_cargo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_smoke_with_fake_cargo(
                tmp_path, state_dir="state", cargo_exit_code=42
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("refusing repo-local STATE_DIR", result.stderr)
        self.assertIn("ICT_ENGINE_ALLOW_REPO_STATE=1", result.stderr)

    def test_allows_tmp_state_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_smoke_with_fake_cargo(
                tmp_path, state_dir=str(tmp_path / "state")
            )
            cargo_log = (tmp_path / "cargo.log").read_text(encoding="utf-8")
            out_dir = tmp_path / "out"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("smoke_acceptance: passed", result.stdout)
            self.assertIn("-- update --symbol", cargo_log)
            self.assertIn("--outcome breakeven --pnl 0", cargo_log)
            self.assertTrue((out_dir / "update_demo.out").exists())
            self.assertTrue((out_dir / "workflow_agent_after_update.out").exists())

    def test_allows_repo_local_state_dir_with_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_smoke_with_fake_cargo(
                tmp_path, state_dir="state", allow_repo_state=True
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("state_dir=state", result.stdout)


if __name__ == "__main__":
    unittest.main()
