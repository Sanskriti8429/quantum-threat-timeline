import math
from math import comb

import numpy as np

np.set_printoptions(precision=3, suppress=True, linewidth=120)


def rep_logical_error(d, p):
    """Probability that more than half of d (odd) copies of a bit are flipped,
    when each flips independently with probability p."""
    return sum(comb(d, k) * p ** k * (1 - p) ** (d - k) for k in range(d // 2 + 1, d + 1))


P_TH = 1e-2


def surface_logical_error(d, p, prefactor=0.1):
    """Common heuristic: logical error per cycle ~ 0.1 * (p / p_th)^((d+1)/2)."""
    return prefactor * (p / P_TH) ** ((d + 1) / 2)


def paper_logical_error(d):
    """The paper's assumption at p = 1e-3: 10^-(ceil(d/2) + 1) per logical qubit per cycle."""
    return 10.0 ** (-(math.ceil(d / 2) + 1))


def min_distance(p, qubit_cycles, budget):
    """Smallest odd d with qubit_cycles * logical_error(d) <= budget."""
    for d in range(3, 400, 2):
        if qubit_cycles * surface_logical_error(d, p) <= budget:
            return d
    return None


def patch_qubits_paper(d):
    return 2 * (d + 1) ** 2


def patch_qubits_bare(d):
    return 2 * d ** 2 - 1
def distill_15_to_1(p_in):
    return 35 * p_in ** 3


if __name__ == "__main__":
    print("=== 1. Repetition code (majority vote): logical error vs d ===")
    print("   p      " + "".join(f"d={d:<8d}" for d in (1, 3, 5, 9, 15, 25)))
    for p in (0.01, 0.1, 0.3, 0.5, 0.6):
        row = "".join(f"{rep_logical_error(d, p):<10.2e}" for d in (1, 3, 5, 9, 15, 25))
        print(f"{p:5.2f}   {row}")
    rng = np.random.default_rng(0)
    flips = rng.random((200000, 5)) < 0.1
    print("Monte Carlo d=5, p=0.1 :", (flips.sum(axis=1) >= 3).mean(),
          " exact:", round(rep_logical_error(5, 0.1), 5))

    print("\n=== 2. Surface code: paper's rule vs the heuristic (p = 1e-3) ===")
    for d in (15, 21, 25, 27, 29):
        print(f"d={d:2d}: paper {paper_logical_error(d):.0e}   "
              f"heuristic {surface_logical_error(d, 1e-3):.0e}")

    print("\nLogical error per cycle vs d, for several physical error rates:")
    print("      p        d=5       d=11      d=21      d=31")
    for p in (1e-4, 1e-3, 3e-3, 1e-2, 2e-2):
        row = "".join(f"{surface_logical_error(d, p):<10.1e}" for d in (5, 11, 21, 31))
        print(f"{p:8.0e}   {row}")

    print("\n=== 3. Reproducing the paper's topological-error estimate (n=2048) ===")
    n, ne = 2048, 3 * (2048 // 2 - 1) - 40
    cycles = 4 * ne * n * 1000
    logical_qubits = 226 * 63 * 0.75
    qubit_cycles = logical_qubits * cycles
    print(f"cycles = {cycles:.3e}, logical qubits (non-factory) = {logical_qubits:.0f}, "
          f"qubit-cycles = {qubit_cycles:.3e}")
    for d in (25, 27, 29):
        print(f"d={d}: P(topological error) = {qubit_cycles * paper_logical_error(d):.1%}")

    print("\n=== 4. Distance needed for a 10% error budget, same workload ===")
    print("      p     min d   logical qubit (paper 2(d+1)^2)   x 14238 logical qubits")
    for p in (1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3, 8e-3, 1e-2):
        d = min_distance(p, qubit_cycles, 0.10)
        if d is None:
            print(f"{p:8.0e}   none: at p >= threshold no distance helps")
        else:
            q = patch_qubits_paper(d)
            print(f"{p:8.0e}   {d:4d}   {q:12d}   {q * 14238 / 1e6:24.1f} M")

    print("\n=== 5. Patch sizes ===")
    for d in (3, 11, 27):
        print(f"d={d:2d}: bare rotated patch {patch_qubits_bare(d):5d}, paper {patch_qubits_paper(d):5d}")

    print("\n=== 6. Magic-state distillation (15-to-1) ===")
    p_in = 1e-3
    err = p_in
    for rnd in range(1, 4):
        err = distill_15_to_1(err)
        print(f"after round {rnd}: error per state = {err:.2e}  (inputs used: 15^{rnd} = {15 ** rnd})")
    print(f"Paper: about 3e9 CCZ states with total distillation error 6.4% "
          f"-> about {0.064 / 3e9:.1e} per state")