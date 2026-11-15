
import math
import unittest

from estimator import (Params, estimate, logical_error_per_cycle,
                       seconds_per_lookup_addition, lookup_additions)


def within(value, target, rel):
    return abs(value - target) <= rel * abs(target)


class TestSection2(unittest.TestCase):

    def setUp(self):
        self.P = Params()
        self.simple = estimate(self.P, simplified=True)
        self.detail = estimate(self.P, simplified=False)

    def test_logical_error_rule(self):
        self.assertEqual(logical_error_per_cycle(25), 1e-14)
        self.assertEqual(logical_error_per_cycle(27), 1e-15)
        self.assertEqual(logical_error_per_cycle(29), 1e-16)

    def test_lookup_addition_phases(self):
        lookup, addition, other = seconds_per_lookup_addition(self.P)
        self.assertTrue(within(lookup, 14e-3, 0.05))
        self.assertTrue(within(addition, 22e-3, 0.05))
        self.assertTrue(within(lookup + addition + other, 37e-3, 0.05))

    def test_simplified_matches_section_2(self):
        s = self.simple
        self.assertTrue(within(s["lookup_additions"], 0.1 * 3029 * 2048, 0.001))
        self.assertTrue(within(s["runtime_h"], 7.0, 0.03))
        self.assertTrue(abs(s["p_topological"] - 0.27) < 0.01)
        self.assertTrue(within(s["physical_qubits"], 23e6, 0.05))
        self.assertTrue(within(s["toffolis"], 2.7e9, 0.06))
        self.assertTrue(abs(s["retry_risk"] - 0.31) < 0.02)
        self.assertEqual(s["logical_qubits"], 226 * 63)

    def test_detailed_runtime_matches_table_3(self):
        self.assertTrue(within(self.detail["runtime_h"], 5.1, 0.05))

    def test_known_gap_retry_risk(self):
        self.assertTrue(0.20 < self.detail["retry_risk"] < 0.28)
        self.assertTrue(within(self.detail["expected_runtime_h"], 7.4, 0.15))


class TestOtherSizes(unittest.TestCase):

    TABLE3 = {
        1024: (27, 5, 5, 1.3, 9.7, 0.4),
        2048: (27, 4, 5, 5.1, 20, 2.7),
        3072: (29, 6, 4, 12, 38, 9.9),
        4096: (31, 9, 4, 22, 55, None)
    }

    def test_runtime_toffolis_and_qubits(self):
        for n, (d2, dl, cm, t_paper, q_paper, tof_paper) in self.TABLE3.items():
            r = estimate(Params(n=n, d=d2, delta_off=dl, c_mul=cm))
            self.assertTrue(within(r["runtime_h"], t_paper, 0.10), f"runtime n={n}")
            self.assertTrue(within(r["physical_qubits"] / 1e6, q_paper, 0.16), f"qubits n={n}")
            if tof_paper:
                self.assertTrue(within(r["toffolis"] / 1e9, tof_paper, 0.08), f"toffolis n={n}")


class TestPaperTypo(unittest.TestCase):

    def test_eq2_as_printed_is_absurd(self):
        P = Params()
        printed = lookup_additions(P) * 2 ** (P.c_exp + P.c_pad())
        self.assertGreater(printed, 1e19)


if __name__ == "__main__":
    unittest.main(verbosity=2)
