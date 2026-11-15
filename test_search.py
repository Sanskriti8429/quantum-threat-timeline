import unittest

from estimator import Params, estimate
from search import TABLE3, objective, search


class TestSearch(unittest.TestCase):

    def test_table_3_choices_are_near_optimal(self):
        for n, row in TABLE3.items():
            d1, d2, dl, cm, ce, cs = row[:6]

            ranked = search(n)
            best = ranked[0][0]

            paper = objective(
                estimate(
                    Params(
                        n=n,
                        d1=d1,
                        d=d2,
                        c_mul=cm,
                        c_exp=ce,
                        c_sep=cs,
                        delta_off=dl
                    )
                )
            )

            self.assertLess(paper / best, 1.05, f"n={n}")

            rank = 1 + sum(
                1 for o, _, _ in ranked if o < paper
            )

            self.assertLess(
                rank / len(ranked),
                0.01,
                f"n={n}: rank {rank} of {len(ranked)}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)