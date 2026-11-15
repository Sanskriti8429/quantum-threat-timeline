"""Estimator v0: the simplified cost model of Gidney & Ekera (2019), section 2.

Reproduces the hand calculations of section 2 for n = 2048 and applies the same
formulas to other n. It is NOT the paper's full parameter search (that is stage 5d).
Assumptions fixed here: physical error rate 1e-3, the n = 2048 layout (113-wide
pieces, 63 rows, 25% of the grid is magic-state factories), one code distance d
for everything, and the paper's distillation error per CCZ state.
"""
import math
from dataclasses import dataclass

lg = math.log2

P_CCZ = 0.064 / 3e9
P_POST = 0.01


@dataclass(frozen=True)
class Params:
    n: int = 2048
    c_exp: int = 5
    c_mul: int = 5
    c_sep: int = 1024
    delta_off: int = 10
    d: int = 27
    cycle_us: float = 1.0
    reaction_us: float = 10.0
    n_e: int = 0

    def exponent_qubits(self):
        return self.n_e or 3 * (self.n // 2 - 1) - 40

    def c_pad(self):
        return 2 * lg(self.n) + lg(self.exponent_qubits()) + self.delta_off

def lookup_additions(P, simplified=False):
    """Eq. (1). `simplified` uses the paper's rounded 0.1 * n_e * n."""
    ne = P.exponent_qubits()
    if simplified:
        return 0.1 * ne * P.n
    return 2 * P.n * ne / (P.c_exp * P.c_mul) * (P.c_sep + 1) / P.c_sep


def toffolis_per_lookup_addition(P):
    """2n + n*c_pad/c_sep + 2^(c_exp + c_mul)  (the paper prints c_pad in the
    exponent; section 2.5 and the measurement-depth formula use c_mul)."""
    return 2 * P.n + P.n * P.c_pad() / P.c_sep + 2 ** (P.c_exp + P.c_mul)


def measurement_depth_per_lookup_addition(P):
    return 2 * P.c_sep + 2 * P.c_pad() + 2 ** (P.c_exp + P.c_mul)

def seconds_per_lookup_addition(P):
    lookup = P.cycle_us * 1e-6 * P.d / 2 * 2 ** (P.c_exp + P.c_mul)
    addition = 2 * (P.c_sep + P.c_pad()) * P.reaction_us * 1e-6
    other = 1e-3
    return lookup, addition, other

def logical_error_per_cycle(d):
    return 10.0 ** (-(math.ceil(d / 2) + 1))
def estimate(P, simplified=False):
    ne = P.exponent_qubits()
    adds = lookup_additions(P, simplified)
    if simplified:
        toffolis = 0.2 * ne * P.n ** 2 + 0.0003 * ne * P.n ** 2 * lg(P.n)
    else:
        toffolis = adds * toffolis_per_lookup_addition(P)
    meas_depth = adds * measurement_depth_per_lookup_addition(P)

    if simplified:
        runtime_s = 4 * ne * P.n * 1e-3
        toffolis_for_error = 3e9
    else:
        runtime_s = adds * sum(seconds_per_lookup_addition(P))
        toffolis_for_error = toffolis

    width = 113 * math.ceil(P.n / P.c_sep)
    logical = width * 63
    physical = logical * 2 * (P.d + 1) ** 2

    cycles = runtime_s / (P.cycle_us * 1e-6)
    qubit_cycles = 0.75 * logical * cycles
    p_top = min(1.0, qubit_cycles * logical_error_per_cycle(P.d))
    p_dist = min(1.0, toffolis_for_error * P_CCZ)
    deviation = adds * P.n / (P.c_sep * 2 ** P.c_pad())
    p_approx = 2 * math.sqrt(deviation)
    risk = 1 - (1 - p_top) * (1 - p_dist) * (1 - p_approx) * (1 - P_POST)

    expected_runtime_s = runtime_s / (1 - risk)
    return {
        "n_e": ne, "c_pad": P.c_pad(),
        "lookup_additions": adds, "toffolis": toffolis, "measurement_depth": meas_depth,
        "runtime_h": runtime_s / 3600, "cycles": cycles,
        "logical_qubits": logical, "physical_qubits": physical,
        "p_topological": p_top, "p_distillation": p_dist,
        "p_approximation": p_approx, "retry_risk": risk,
        "expected_runtime_h": expected_runtime_s / 3600,
        "expected_volume_Mqd": physical * expected_runtime_s / 86400 / 1e6,
    }


if __name__ == "__main__":
    print("=== n = 2048, section 2 parameters: simplified vs detailed ===")
    P = Params()
    s, d = estimate(P, simplified=True), estimate(P, simplified=False)
    lk, ad, ot = seconds_per_lookup_addition(P)
    print(f"phases of one lookup addition: lookup {lk*1e3:.1f} ms, addition {ad*1e3:.1f} ms, "
          f"other {ot*1e3:.0f} ms, total {(lk+ad+ot)*1e3:.1f} ms   (paper: 14, 22, 1, 37)")
    rows = [
        ("lookup additions", "lookup_additions", "{:.3e}", "0.1 n_e n = 6.2e5"),
        ("Toffolis", "toffolis", "{:.3e}", "2.7e9 (Table 1)"),
        ("runtime per run (h)", "runtime_h", "{:.2f}", "7 (sec 2.11); 5.1 (Table 3)"),
        ("logical qubits (grid)", "logical_qubits", "{:,.0f}", "226 x 63 = 14,238"),
        ("physical qubits", "physical_qubits", "{:.3e}", "23M (text); 20M (Table 3)"),
        ("P(topological error)", "p_topological", "{:.1%}", "27%"),
        ("P(distillation error)", "p_distillation", "{:.1%}", "6.4%"),
        ("P(approximation error)", "p_approximation", "{:.2%}", "0.1%"),
        ("retry risk", "retry_risk", "{:.1%}", "31% (Table 3)"),
        ("expected runtime (h)", "expected_runtime_h", "{:.2f}", "7.4 (0.31 days)"),
        ("expected volume (Mqd)", "expected_volume_Mqd", "{:.2f}", "5.9 (Table 3)"),
    ]
    print(f"\n{'quantity':26s}{'simplified':>14s}{'detailed':>14s}   paper")
    for label, key, fmt, paper in rows:
        print(f"{label:26s}{fmt.format(s[key]):>14s}{fmt.format(d[key]):>14s}   {paper}")

    print("\n=== Table 3 parameters for several n (detailed mode) ===")
    table3 = {1024: (27, 5, 5, 1.3, 9.7, 0.4), 2048: (27, 4, 5, 5.1, 20, 2.7),
              3072: (29, 6, 4, 12, 38, 9.9), 4096: (31, 9, 4, 22, 55, None)}
    print("     n |  Toffolis (G)  paper | runtime/run (h)  paper | qubits (M)  paper")
    for n, (d2, dl, cm, t_paper, q_paper, tof_paper) in table3.items():
        r = estimate(Params(n=n, d=d2, delta_off=dl, c_mul=cm))
        tp = f"{tof_paper:5.1f}" if tof_paper else "  n/a"
        print(f"{n:6d} | {r['toffolis']/1e9:13.2f} {tp} | {r['runtime_h']:15.1f} {t_paper:6.1f} | "
              f"{r['physical_qubits']/1e6:10.1f} {q_paper:6.1f}")