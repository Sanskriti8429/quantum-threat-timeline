import math
import unittest

from aes_grover import (AGE_OF_UNIVERSE_YEARS, GRASSL, depth_limited_log2_gates, iterations,
                        parallel_plan, single_machine_years, table5_value, totals)


def within(value, target, rel):
    return abs(value - target) <= rel * abs(target)


class TestGrassl(unittest.TestCase):
    def test_gate_counts_and_qubits_reproduce_table_5(self):
        for k in (128, 192, 256):
            t, paper = totals(k), GRASSL[k]["table5"]
            self.assertTrue(within(t["t_count"], table5_value(paper["t"]), 0.01), f"T count AES-{k}")
            self.assertTrue(within(t["clifford"], table5_value(paper["c"]), 0.01), f"Clifford AES-{k}")
            self.assertEqual(t["logical_qubits"], paper["qubits"], f"qubits AES-{k}")

    def test_aes_256_depths_reproduce_table_5(self):
        t, paper = totals(256), GRASSL[256]["table5"]
        self.assertTrue(within(t["t_depth"], table5_value(paper["tdepth"]), 0.01))
        self.assertTrue(within(t["depth"], table5_value(paper["depth"]), 0.01))

    def test_table_5_depth_mantissas_look_swapped_between_aes_128_and_aes_192(self):
        t128, t192 = totals(128), totals(192)
        self.assertAlmostEqual(t128["t_depth"] / 2.0 ** 80, 1.21, delta=0.01)
        self.assertAlmostEqual(t128["depth"] / 2.0 ** 81, 1.33, delta=0.01)
        self.assertAlmostEqual(t192["t_depth"] / 2.0 ** 112, 1.06, delta=0.01)
        self.assertAlmostEqual(t192["depth"] / 2.0 ** 113, 1.16, delta=0.01)

    def test_iterations(self):
        self.assertTrue(within(iterations(128), math.pi / 4 * 2 ** 64, 1e-12))


class TestPhysicalBounds(unittest.TestCase):
    def test_single_machine_is_far_longer_than_the_age_of_the_universe(self):
        self.assertGreater(single_machine_years(128, 10.0), 30 * AGE_OF_UNIVERSE_YEARS)
        self.assertGreater(single_machine_years(128, 1.0), 3 * AGE_OF_UNIVERSE_YEARS)

    def test_depth_reduction_scales_linearly(self):
        self.assertAlmostEqual(single_machine_years(128, 10.0, 1000) * 1000, single_machine_years(128, 10.0), delta=1e-6 * single_machine_years(128, 10.0))

    def test_grover_parallelizes_as_square_root(self):
        a, b = parallel_plan(128, 100.0), parallel_plan(128, 1.0)
        self.assertAlmostEqual(b["machines"] / a["machines"], 100 ** 2, delta=1)      # 100x faster -> 10^4 x machines
        self.assertAlmostEqual(b["total_t_count"] / a["total_t_count"], 100, delta=1e-6)  # total work only 100x
        self.assertLess(b["d"], 40)

    def test_capping_depth_trades_gates_for_depth(self):
        self.assertAlmostEqual(depth_limited_log2_gates(128, 60) - depth_limited_log2_gates(128, 61), 1.0, places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)