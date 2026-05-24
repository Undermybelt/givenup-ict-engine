import unittest

from support.scripts.auto_quant_external import fetch_external


class IbkrHistoricalChunkingTests(unittest.TestCase):
    def test_one_minute_thirty_day_request_is_split_into_daily_chunks(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("1 min", "30 D")

        self.assertEqual(len(chunks), 30)
        self.assertEqual({chunk.duration for chunk in chunks}, {"1 D"})

    def test_five_minute_three_month_request_is_split_into_weekly_chunks(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("5 mins", "3 M")

        self.assertGreaterEqual(len(chunks), 12)
        self.assertEqual({chunk.duration for chunk in chunks}, {"1 W"})

    def test_daily_two_year_request_stays_single_chunk(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("1 day", "2 Y")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].duration, "2 Y")

    def test_bar_size_matching_is_case_and_whitespace_insensitive(self) -> None:
        chunks = fetch_external._ibkr_historical_chunk_plan("  1   MIN  ", "30 D")

        self.assertEqual(len(chunks), 30)
        self.assertEqual({chunk.duration for chunk in chunks}, {"1 D"})


if __name__ == "__main__":
    unittest.main()
