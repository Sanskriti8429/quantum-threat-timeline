import math
from dataclasses import dataclass

lg = math.log2

EPS_T_DIST = 3.5e-8
EPS_T_TOPO_15 = 1.4e-6 - EPS_T_DIST


def eps_t1(d1):
    return EPS_T_DIST + EPS_T_TOPO_15 * 10.0 ** (-(d1 - 15) / 2)


P_CCZ_17_27 = 0.064 / 3e9
C2 = P_CCZ_17_27 - 28 * eps_t1(17) ** 2
P_CCZ = P_CCZ_17_27


def p_ccz(d1, d2):
    return 28 * eps_t1(d1) ** 2 + C2 * 10.0 ** (-(d2 - 27) / 2)


P_POST = 0.01


@dataclass(frozen=True)
class Params:
    n: int = 2048
    c_exp: int = 5
    c_mul: int = 5
    c_sep: int = 1024
    delta_off: int = 10
    d: int = 27
    d1: int = 17
    cycle_us: float = 1.0
    reaction_us: float = 10.0
    n_e: int = 0

    def exponent_qubits(self):
        return self.n_e or 3 * (self.n // 2 - 1) - 40

    def c_pad(self):
        return 2 * lg(self.n) + lg(self.exponent_qubits()) + self.delta_off


def lookup_additions(P, simplified=False):
    ne = P.exponent_qubits()
    if simplified:
        return 0.1 * ne * P.n
    return 2 * P.n * ne / (P.c_exp * P.c_mul) * (P.c_sep + 1) / P.c_sep


def toffolis_per_lookup_addition(P):
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

    width = round(113 * P.d1 / 17) * math.ceil(P.n / P.c_sep)
    rows = 33 + round(1.06 * 3 * (P.c_sep + P.c_pad()) / 113)
    logical = width * rows
    physical = logical * 2 * (P.d + 1) ** 2

    cycles = runtime_s / (P.cycle_us * 1e-6)
    qubit_cycles = 0.75 * logical * cycles
    p_top = min(1.0, qubit_cycles * logical_error_per_cycle(P.d))
    p_dist = min(1.0, toffolis_for_error * p_ccz(P.d1, P.d))
    deviation = adds * P.n / (P.c_sep * 2 ** P.c_pad())
    p_approx = 2 * math.sqrt(deviation)

    risk = 1 - (1 - p_top) * (1 - p_dist) * (1 - p_approx) * (1 - P_POST)

    expected_runtime_s = runtime_s / (1 - risk) if risk < 1 else float("inf")

    return {
        "n_e": ne,
        "c_pad": P.c_pad(),
        "lookup_additions": adds,
        "toffolis": toffolis,
        "measurement_depth": meas_depth,
        "runtime_h": runtime_s / 3600,
        "cycles": cycles,
        "logical_qubits": logical,
        "physical_qubits": physical,
        "p_topological": p_top,
        "p_distillation": p_dist,
        "p_approximation": p_approx,
        "retry_risk": risk,
        "expected_runtime_h": expected_runtime_s / 3600,
        "expected_volume_Mqd": physical * expected_runtime_s / 86400 / 1e6,
    }


if __name__ == "__main__":
    print("=== n = 2048, section 2 parameters: simplified vs detailed ===")

    P = Params()
    s, d = estimate(P, simplified=True), estimate(P, simplified=False)

    lk, ad, ot = seconds_per_lookup_addition(P)

    print(
        f"phases of one lookup addition: lookup {lk*1e3:.1f} ms, "
        f"addition {ad*1e3:.1f} ms, other {ot*1e3:.0f} ms, "
        f"total {(lk+ad+ot)*1e3:.1f} ms   (paper: 14, 22, 1, 37)"
    )

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
        print(
            f"{label:26s}{fmt.format(s[key]):>14s}"
            f"{fmt.format(d[key]):>14s}   {paper}"
        )

    print("\n=== Table 3 rows (detailed mode, d1 from Table 3) ===")

    table3 = {
        1024: (15, 27, 5, 5, 1.3, 9.7, 0.06, 0.4),
        2048: (15, 27, 4, 5, 5.1, 20, 0.31, 2.7),
        3072: (17, 29, 6, 4, 12, 38, 0.09, 9.9),
        4096: (17, 31, 9, 4, 22, 55, 0.05, None),
    }

    print(
        "     n | Toffolis (G)  paper | runtime/run (h)  paper | "
        "qubits (M)  paper | retry risk  paper"
    )

    for n, (d1, d2, dl, cm, t_paper, q_paper, risk_paper, tof_paper) in table3.items():
        r = estimate(
            Params(n=n, d1=d1, d=d2, delta_off=dl, c_mul=cm)
        )

        tp = f"{tof_paper:5.1f}" if tof_paper else "  n/a"

        print(
            f"{n:6d} | {r['toffolis']/1e9:12.2f} {tp} | "
            f"{r['runtime_h']:15.1f} {t_paper:6.1f} | "
            f"{r['physical_qubits']/1e6:9.1f} {q_paper:6.1f} | "
            f"{r['retry_risk']:10.1%} {risk_paper:6.0%}"
        )