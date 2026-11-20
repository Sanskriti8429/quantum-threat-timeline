"""Stage 6b: precompute the estimator over a grid of hardware assumptions for the dashboard.

For every (physical error rate, reaction time, cycle time) the design is re-optimized (as in stage 5e) and the
result is saved to sensitivity.csv. The dashboard's sliders snap to these grid points: nothing is interpolated.
Uses a smaller search grid than sensitivity.py (delta_off fixed, fewer runway spacings); on the seven points where
both were run, the two grids gave the same optimum to within 0.01%.
"""
import csv
import itertools
import time
from dataclasses import replace

import sensitivity
from estimator import Params
from sensitivity import best

P_VALUES = (1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3)
REACTION_US = (1.0, 2.0, 5.0, 10.0, 20.0, 63.0)
CYCLE_US = (0.1, 0.5, 1.0, 2.0)

FAST_GRID = {
    "d1": tuple(range(5, 46, 2)),
    "d": tuple(range(9, 100, 2)),
    "c_mul": (4, 5, 6),
    "c_exp": (4, 5, 6),
    "c_sep": (768, 1024, 1536, 2048),
    "delta_off": (7,),
}

COLUMNS = ["p", "reaction_us", "cycle_us", "feasible", "d1", "d2", "c_mul", "c_exp", "c_sep",
           "physical_qubits", "runtime_h", "retry_risk", "expected_runtime_h", "expected_volume_Mqd"]


def export(path="sensitivity.csv"):
    sensitivity.GRID.update(FAST_GRID)
    base = Params(n=2048)
    rows = []
    t0 = time.time()
    for p, rt, ct in itertools.product(P_VALUES, REACTION_US, CYCLE_US):
        P, r = best(replace(base, p=p, reaction_us=rt, cycle_us=ct))
        if r is None:
            rows.append([p, rt, ct, 0] + [""] * 10)
        else:
            rows.append([p, rt, ct, 1, P.d1, P.d, P.c_mul, P.c_exp, P.c_sep, round(r["physical_qubits"]),
                         round(r["runtime_h"], 4), round(r["retry_risk"], 5),
                         round(r["expected_runtime_h"], 4), round(r["expected_volume_Mqd"], 5)])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print(f"wrote {path}: {len(rows)} hardware settings in {time.time() - t0:.0f} s")
    return rows


if __name__ == "__main__":
    export()