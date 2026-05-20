from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import pandas_datareader_hotplug as bridge  # noqa: E402


class PandasDatareaderHotplugTests(unittest.TestCase):
    def test_capabilities_are_zero_config_and_opt_in(self) -> None:
        bundle = bridge.capability_bundle()

        self.assertTrue(bundle["ok"])
        self.assertTrue(bundle["zero_config"])
        self.assertFalse(bundle["trade_usable"])
        self.assertEqual(bundle["default_runtime"], "disabled_until_user_opt_in")
        self.assertIn("fred", bundle["sources"])
        self.assertIn("famafrench", bundle["sources"])
        self.assertIn("macro_regime_rates", bundle["personal_default_sets"])

    def test_demo_mode_returns_embedded_rows_without_dependency(self) -> None:
        bundle = bridge.demo_bundle(limit=2)

        self.assertTrue(bundle["ok"])
        self.assertEqual(bundle["source"], "demo")
        self.assertFalse(bundle["trade_usable"])
        self.assertEqual(bundle["data_grade"], "fixture_only")
        self.assertEqual(bundle["row_count"], 2)
        self.assertFalse(bundle["provenance"]["network"])

    def test_fetch_mode_without_symbol_fails_as_validation(self) -> None:
        args = bridge.build_parser().parse_args(["--source", "fred"])
        bundle = bridge.fetch_source(args)

        self.assertFalse(bundle["ok"])
        self.assertEqual(bundle["error"]["category"], "validation")
        self.assertIn("--symbol", bundle["error"]["message"])

    def test_main_writes_explicit_output_path_only(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "nested" / "capabilities.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = bridge.main(["--capabilities", "--output", str(output)])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["bridge"], "pandas_datareader_hotplug")
            self.assertEqual(
                json.loads(stdout.getvalue())["bridge"], "pandas_datareader_hotplug"
            )


if __name__ == "__main__":
    unittest.main()
