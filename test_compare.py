import math
import unittest

from published_estimates import ROWS, qubit_days, same_hardware_assumptions

GOOD_SOURCES = {"primary text", "cited in another", "search excerpt"}


def row(key):
    return next(r for r in ROWS if r["key"] == key)


class TestPublishedEstimates(unittest.TestCase):
    def test_volumes_match_hand_arithmetic(self):
        self.assertAlmostEqual(qubit_days(row("GE19")), 6.2, places=1)
        self.assertAlmostEqual(qubit_days(row("G25")), 4.45, places=2)
        self.assertAlmostEqual(qubit_days(row("WEB-98k")), 2.94, places=2)
        self.assertAlmostEqual(qubit_days(row("WEB-1M")), 0.333, places=3)

    def test_every_row_states_its_source(self):
        for r in ROWS:
            self.assertIn(r["source_quality"], GOOD_SOURCES, r["key"])
            self.assertTrue(r["note"], r["key"])
            self.assertGreater(r["qubits"], 0)
            self.assertGreater(r["runtime_days"], 0)

    def test_only_one_microsecond_designs_share_ge19_assumptions(self):
        same = {r["key"] for r in ROWS if same_hardware_assumptions(r)}
        self.assertEqual(same, {"GE19", "G25", "WEB-98k", "WEB-139k", "WEB-400k", "WEB-1M"})

    def test_qubit_counts_fell_while_runtimes_grew(self):
        self.assertLess(row("G25")["qubits"], row("GE19")["qubits"] / 20)
        self.assertGreater(row("G25")["runtime_days"], 10 * row("GE19")["runtime_days"])
        self.assertLess(row("WEB-98k")["qubits"], row("G25")["qubits"] / 5)

    def test_only_the_smallest_pinnacle_point_was_read_from_the_paper_itself(self):
        primary_pinnacle = [r["key"] for r in ROWS if r["key"].startswith("WEB-") and r["source_quality"] == "primary text"]
        self.assertEqual(primary_pinnacle, ["WEB-98k"])


if __name__ == "__main__":
    unittest.main(verbosity=2)