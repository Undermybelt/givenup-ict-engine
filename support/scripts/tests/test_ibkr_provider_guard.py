import unittest
from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory
from pathlib import Path

from support.scripts.auto_quant_external.ibkr_provider_guard import (
    classify_ibkr_ladder_artifacts,
    classify_ibkr_ladder_state,
    count_provider_rows,
    main,
)


class IbkrProviderGuardTest(unittest.TestCase):
    def test_provider_status_ready_but_all_fetches_empty_blocks_aq(self) -> None:
        verdict = classify_ibkr_ladder_state(
            provider_status_exit=0,
            fetch_exits={"1m_7d": 3, "5m_1m": 3, "1d_1y": 3},
            row_counts={"1m": 0, "5m": 0, "1d": 0},
            material_count=0,
            ranked_row_count=0,
        )

        self.assertEqual(verdict.decision, "provider_blocked_no_rows_no_materials")
        self.assertFalse(verdict.provider_rows_ready)
        self.assertFalse(verdict.allow_material_build)
        self.assertFalse(verdict.allow_auto_quant)
        self.assertFalse(verdict.factor_verdict)
        self.assertFalse(verdict.cooldown_recommended)
        self.assertIn("provider-status", verdict.reason)

    def test_repeated_zero_row_ladders_recommend_provider_cooldown(self) -> None:
        verdict = classify_ibkr_ladder_state(
            provider_status_exit=0,
            fetch_exits={"1m_7d": 3, "5m_1m": 3, "1d_1y": 3},
            row_counts={"1m": 0, "5m": 0, "1d": 0},
            material_count=0,
            ranked_row_count=0,
            recent_blocked_ladders=3,
        )

        self.assertEqual(verdict.decision, "provider_cooldown_after_repeated_no_rows")
        self.assertTrue(verdict.cooldown_recommended)
        self.assertFalse(verdict.allow_material_build)
        self.assertFalse(verdict.allow_auto_quant)
        self.assertFalse(verdict.factor_verdict)
        self.assertIn("recent blocked IBKR ladders=3", verdict.reason)

    def test_any_real_rows_allows_material_stage(self) -> None:
        verdict = classify_ibkr_ladder_state(
            provider_status_exit=0,
            fetch_exits={"1m_7d": 0, "5m_1m": 3},
            row_counts={"1m": 1200, "5m": 0},
            material_count=0,
            ranked_row_count=0,
        )

        self.assertEqual(verdict.decision, "provider_rows_ready")
        self.assertTrue(verdict.provider_rows_ready)
        self.assertTrue(verdict.allow_material_build)
        self.assertFalse(verdict.cooldown_recommended)
        self.assertFalse(verdict.factor_verdict)

    def test_count_provider_rows_accepts_ibkr_ts_column(self) -> None:
        with TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "ibkr_rows.csv"
            csv_path.write_text(
                "ts,open,high,low,close\n"
                "2026-05-20T13:30:00+00:00,1,2,1,2\n"
                "2026-05-20T13:31:00+00:00,2,3,2,3\n",
                encoding="utf-8",
            )

            self.assertEqual(count_provider_rows(csv_path), 2)

    def test_classify_artifacts_uses_exit_files_and_csv_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider_exit = root / "provider.exit"
            fetch_exit = root / "fetch_1m.exit"
            rows_csv = root / "rows.csv"
            provider_exit.write_text("0\n", encoding="utf-8")
            fetch_exit.write_text("0\n", encoding="utf-8")
            rows_csv.write_text(
                "ts,open,high,low,close\n"
                "2026-05-20T13:30:00+00:00,1,2,1,2\n",
                encoding="utf-8",
            )

            verdict = classify_ibkr_ladder_artifacts(
                provider_status_exit_file=provider_exit,
                fetch_exit_files={"1m": fetch_exit},
                row_csvs={"1m": rows_csv},
                material_count=0,
                ranked_row_count=0,
            )

            self.assertEqual(verdict.decision, "provider_rows_ready")
            self.assertTrue(verdict.allow_material_build)

    def test_cli_fail_on_blocked_returns_nonzero_for_repeated_zero_row_ladder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider_exit = root / "provider.exit"
            fetch_exit = root / "fetch_1m.exit"
            missing_rows = root / "missing.csv"
            provider_exit.write_text("0\n", encoding="utf-8")
            fetch_exit.write_text("3\n", encoding="utf-8")

            out = StringIO()
            with redirect_stdout(out):
                exit_code = main([
                    "--provider-status-exit-file", str(provider_exit),
                    "--fetch-exit", f"1m={fetch_exit}",
                    "--row-csv", f"1m={missing_rows}",
                    "--material-count", "0",
                    "--ranked-row-count", "0",
                    "--recent-blocked-ladders", "3",
                    "--fail-on-blocked",
                ])

            self.assertEqual(exit_code, 2)
            self.assertIn("provider_cooldown_after_repeated_no_rows", out.getvalue())

    def test_cli_requires_known_good_preflight_before_fresh_stock_ladder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider_exit = root / "provider.exit"
            missing_known_good = root / "spy_known_good.csv"
            provider_exit.write_text("0\n", encoding="utf-8")

            out = StringIO()
            with redirect_stdout(out):
                exit_code = main([
                    "--provider-status-exit-file", str(provider_exit),
                    "--known-good-row-csv", f"SPY={missing_known_good}",
                    "--require-known-good-preflight",
                    "--fail-on-blocked",
                ])

            self.assertEqual(exit_code, 2)
            self.assertIn("known_good_preflight_missing_no_rows", out.getvalue())


if __name__ == "__main__":
    unittest.main()
