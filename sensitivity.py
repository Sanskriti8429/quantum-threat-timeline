"""Stage 5e: how the n = 2048 estimate moves with hardware assumptions.

For every hardware setting the code distances, window sizes and runway spacing are RE-OPTIMIZED with the
same objective as the paper (s^1.2 * t / (1 - risk)), so the numbers show what a designer would choose,
not what happens if the design is frozen.
"""
import itertools
import math
from dataclasses import replace

from estimator import Params, estimate
from search import objective

GRID = {
    "d1": tuple(range(5, 46, 2)),
    "d": tuple(range(9, 100, 2)),
    "c_mul": (4, 5, 6),
    "c_exp": (4, 5, 6),
    "c_sep": (512, 768, 1024, 1536, 2048),
    "delta_off": (4, 7, 10),
}


def best(base):
    """Optimal parameters for the hardware in `base` (a Params with n, p, cycle_us, reaction_us set)."""
    best_score, best_P, best_r = None, None, None
    for d1, d, cm, ce, cs, dl in itertools.product(*GRID.values()):
        P = replace(base, d1=d1, d=d, c_mul=cm, c_exp=ce, c_sep=cs, delta_off=dl)
        r = estimate(P)
        if r["retry_risk"] >= 0.999:
            continue
        score = objective(r)
        if best_score is None or score < best_score:
            best_score, best_P, best_r = score, P, r
    return best_P, best_r


def row(label, P, r, ref_volume=None):
    if r is None:
        return f"{label:>10s} | no feasible design in the search ranges (d1 up to 45, d2 up to 99)"
    ratio = f"{r['expected_volume_Mqd'] / ref_volume:6.2f}x" if ref_volume else "      "
    return (f"{label:>10s} | d1={P.d1:2d} d2={P.d:2d} cmul={P.c_mul} cexp={P.c_exp} csep={P.c_sep:4d} | "
            f"{r['physical_qubits'] / 1e6:7.1f} M | {r['runtime_h']:6.1f} h | {r['retry_risk']:5.1%} | "
            f"{r['expected_runtime_h']:7.1f} h | {r['expected_volume_Mqd']:7.2f} {ratio}")


HEADER = ("     setting | chosen parameters                           |  qubits  | per run | risk  "
          "| expected | volume (Mqd)")


def rule_of_thumb(p):
    """Gidney-Ekera 2.16: V(p) ~ V(0.1%) / (-log10(p) - 2)^3. Returns V(p) / V(0.1%)."""
    return 1 / (-math.log10(p) - 2) ** 3


if __name__ == "__main__":
    base = Params(n=2048)

    print("=== 1. Physical error rate (cycle 1 us, reaction 10 us), re-optimized ===")
    print(HEADER)
    ref_P, ref_r = best(base)
    ref_v = ref_r["expected_volume_Mqd"]
    results_p = {}
    for p in (1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3):
        P, r = best(replace(base, p=p))
        results_p[p] = r
        print(row(f"p={p:.0e}", P, r, ref_v))
    print("\nrule of thumb V(p)/V(0.1%) vs the model's volume ratio:")
    print("      p     rule of thumb   model")
    for p, r in results_p.items():
        if r is None:
            print(f"{p:8.0e}   {'':12s}   infeasible")
            continue
        print(f"{p:8.0e}   {rule_of_thumb(p) if p < 3.5e-3 else float('nan'):12.3f}   "
              f"{r['expected_volume_Mqd'] / ref_v:6.3f}")

    print("\n=== 2. Reaction time (p = 1e-3, cycle 1 us), re-optimized ===")
    print(HEADER)
    for rt in (1.0, 2.0, 5.0, 10.0, 20.0):
        P, r = best(replace(base, reaction_us=rt))
        print(row(f"{rt:g} us", P, r, ref_v))

    print("\n=== 3. Cycle time (p = 1e-3, reaction 10 us), re-optimized ===")
    print(HEADER)
    for ct in (0.1, 0.2, 0.5, 1.0, 2.0):
        P, r = best(replace(base, cycle_us=ct))
        print(row(f"{ct:g} us", P, r, ref_v))

    print("\n=== 4. Expected volume (Mqd), cycle time x reaction time ===")
    cycles, reactions = (0.2, 0.5, 1.0), (2.0, 5.0, 10.0)
    print("cycle \\ reaction " + "".join(f"{rt:>9g} us" for rt in reactions))
    for ct in cycles:
        vals = [best(replace(base, cycle_us=ct, reaction_us=rt))[1]["expected_volume_Mqd"]
                for rt in reactions]
        print(f"{ct:>9g} us      " + "".join(f"{v:12.2f}" for v in vals))