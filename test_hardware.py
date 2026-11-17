import math
import unittest

from distance_to_threat import (LOGICAL_ERROR_TARGET, color_code_qubits, distance_for_target, row,
                                surface_qubits)
from hardware_status import DEMO_CUTOFF, DEMONSTRATED, ORG, PAPER, ROADMAP, ROWS, SECONDARY

METRICS = {"logical_error_per_round", "lambda", "cycle_us", "decoder_latency_us",
           "cycles_between_correlated_errors", "physical_qubits", "logical_qubits", "two_qubit_error",
           "logical_two_qubit_error", "continuous_hours"}


class TestDataset(unittest.TestCase):
    def test_every_row_is_labelled_dated_and_sourced(self):
        keys = [r["key"] for r in ROWS]
        self.assertEqual(len(keys), len(set(keys)))
        for r in ROWS:
            self.assertIn(r["kind"], {DEMONSTRATED, ROADMAP}, r["key"])
            self.assertIn(r["source_quality"], {PAPER, ORG, SECONDARY}, r["key"])
            self.assertTrue(r["source"].startswith("http"), r["key"])
            self.assertIn(r["metric"], METRICS, r["key"])
            self.assertRegex(r["date"], r"^\d{4}-\d{2}(-\d{2})?$", r["key"])
            self.assertTrue(r["note"], r["key"])

    def test_demonstrated_results_are_in_the_past_and_roadmap_rows_have_target_years(self):
        for r in ROWS:
            if r["kind"] == DEMONSTRATED:
                self.assertLessEqual(r["date"], DEMO_CUTOFF[:len(r["date"])], r["key"])
                self.assertNotIn("target_year", r, r["key"])
            else:
                self.assertGreaterEqual(r["target_year"], 2026, r["key"])

    def test_roadmap_rows_come_from_the_organizations_or_press_and_say_so(self):
        roadmap = [r for r in ROWS if r["kind"] == ROADMAP]
        self.assertEqual({r["key"] for r in roadmap}, {"IBM-starling", "IBM-bluejay", "QTNM-apollo", "IONQ-2030"})
        for r in roadmap:
            self.assertNotEqual(r["source_quality"], PAPER, r["key"])      # a plan is not a peer-reviewed result


class TestGaps(unittest.TestCase):
    def test_logical_error_gaps(self):
        self.assertAlmostEqual(math.log10(row("GOOG-eps7")["value"] / LOGICAL_ERROR_TARGET), 12.16, delta=0.05)
        self.assertAlmostEqual(math.log10(row("QTNM-eps7")["value"] / LOGICAL_ERROR_TARGET), 9.70, delta=0.05)

    def test_distance_needed_at_the_measured_suppression(self):
        d = distance_for_target(row("GOOG-eps7")["value"], 7, row("GOOG-lambda")["value"], LOGICAL_ERROR_TARGET)
        self.assertAlmostEqual(d, 80.6, delta=0.2)
        self.assertEqual(surface_qubits(81), 13_121)

    def test_color_code_qubit_formula_matches_the_reported_counts(self):
        self.assertEqual([color_code_qubits(d) for d in (3, 5, 7)], [13, 37, 73])

    def test_google_floor_is_far_above_the_target(self):
        floor = 1 / row("GOOG-floor")["value"]
        self.assertGreater(floor / LOGICAL_ERROR_TARGET, 1e5)

    def test_assumed_suppression_is_much_stronger_than_measured(self):
        self.assertGreater(10.0 / row("GOOG-lambda")["value"], 4.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)