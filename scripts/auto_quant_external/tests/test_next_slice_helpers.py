from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import entry_drought_diagnostic_v2 as drought  # noqa: E402
import external_regime_changepoint_labels as changepoint  # noqa: E402


class ChangePointHelperTests(unittest.TestCase):
    def test_cluster_breakpoints_merges_nearby_votes(self) -> None:
        clusters = changepoint.cluster_breakpoints(
            {
                "pelt": [10, 30, 60],
                "binseg": [11, 29, 61],
                "window": [30, 89],
            },
            tolerance=2,
        )

        self.assertEqual([item["bar_index"] for item in clusters], [10, 30, 60, 89])
        self.assertEqual(clusters[0]["vote_count"], 2)
        self.assertEqual(clusters[1]["vote_count"], 3)

    def test_transition_proximity_peaks_around_breakpoints(self) -> None:
        index = pd.date_range("2025-01-01", periods=8, freq="h", tz="UTC")
        proximity = changepoint.build_transition_proximity(index, [3], window=2)

        self.assertEqual(proximity.iloc[3], 1.0)
        self.assertEqual(proximity.iloc[1], 0.0)
        self.assertGreater(proximity.iloc[2], 0.0)
        self.assertGreater(proximity.iloc[4], 0.0)


class EntryDroughtHelperTests(unittest.TestCase):
    def test_gate_ablations_flag_density_bottleneck(self) -> None:
        gate_df = pd.DataFrame(
            {
                "session": [True] * 8,
                "trend": [True] * 8,
                "strict_gate": [True, True, True, True, False, False, False, False],
            },
            index=pd.date_range("2025-01-01", periods=8, freq="D", tz="UTC"),
        )

        ablations = drought.analyze_gate_ablations(gate_df)
        suspect_gates = [item["gate"] for item in drought.find_suspect_gates(ablations)]

        self.assertEqual(ablations[0]["gate"], "strict_gate")
        self.assertIn("strict_gate", suspect_gates)
        self.assertEqual(drought.classify_density_issue(gate_df, ablations), "over_gating_issue")


if __name__ == "__main__":
    unittest.main()
