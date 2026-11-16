import unittest
from dataclasses import replace

from estimator import Params
from sensitivity import best, rule_of_thumb

BASE = Params(n=2048)


def volume(**changes):
    P, r = best(replace(BASE, **changes))
    return r["expected_volume_Mqd"], r


class TestSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref, cls.ref_r = volume()
        cls.by_p = {p: volume(p=p) for p in (1e-4, 3e-4, 2e-3)}

    def test_volume_increases_with_physical_error_rate(self):
        v = [self.by_p[1e-4][0], self.by_p[3e-4][0], self.ref, self.by_p[2e-3][0]]
        self.assertEqual(v, sorted(v))

    def test_paper_rule_of_thumb_roughly_holds_between_1e4_and_2e3(self):
        for p in (1e-4, 3e-4, 2e-3):
            model_ratio = self.by_p[p][0] / self.ref
            self.assertLess(abs(model_ratio / rule_of_thumb(p) - 1), 0.35, f"p={p}")

    def test_worse_hardware_is_paid_in_qubits_not_time(self):
        r2 = self.by_p[2e-3][1]
        self.assertGreater(r2["physical_qubits"], 2 * self.ref_r["physical_qubits"])
        self.assertLess(r2["runtime_h"], 1.3 * self.ref_r["runtime_h"])

    def test_reaction_time_matters_more_than_cycle_time(self):
        fast_reaction, _ = volume(reaction_us=2.0)
        fast_cycle, _ = volume(cycle_us=0.2)
        self.assertLess(fast_reaction, fast_cycle)
        self.assertLess(fast_cycle, self.ref)

    def test_no_feasible_design_near_threshold(self):
        P, r = best(replace(BASE, p=5e-3))
        self.assertIsNone(r)


if __name__ == "__main__":
    unittest.main(verbosity=2)