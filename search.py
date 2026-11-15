import itertools

from estimator import Params, estimate

GRID = {
    "d1": (15, 17, 19, 21, 23),
    "d": tuple(range(25, 52, 2)),
    "c_mul": (4, 5, 6),
    "c_exp": (4, 5, 6),
    "c_sep": (512, 768, 1024, 1536, 2048),
    "delta_off": tuple(range(2, 11)),
}

TABLE3 = {
    1024: (15, 27, 5, 5, 5, 1024, 1.3, 9.7, 0.06),
    2048: (15, 27, 4, 5, 5, 1024, 5.1, 20.0, 0.31),
    3072: (17, 29, 6, 4, 5, 1024, 12.0, 38.0, 0.09),
    4096: (17, 31, 9, 4, 5, 1024, 22.0, 55.0, 0.05),
}


def objective(r):
    return r["physical_qubits"] ** 1.2 * r["runtime_h"] / (1 - r["retry_risk"])


def search(n):
    ranked = []

    for d1, d, cm, ce, cs, dl in itertools.product(*GRID.values()):
        P = Params(
            n=n,
            d1=d1,
            d=d,
            c_mul=cm,
            c_exp=ce,
            c_sep=cs,
            delta_off=dl
        )

        r = estimate(P)

        if r["retry_risk"] < 0.999:
            ranked.append((objective(r), P, r))

    ranked.sort(key=lambda item: item[0])
    return ranked


def describe(P):
    return (
        f"d1={P.d1} d2={P.d} dl={P.delta_off} "
        f"cmul={P.c_mul} cexp={P.c_exp} csep={P.c_sep}"
    )


if __name__ == "__main__":
    size = 1

    for values in GRID.values():
        size *= len(values)

    print(f"grid size per n: {size}")

    for n, row in TABLE3.items():
        d1, d2, dl, cm, ce, cs, t_paper, q_paper, risk_paper = row

        ranked = search(n)
        best_obj, best_P, best_r = ranked[0]

        paper_P = Params(
            n=n,
            d1=d1,
            d=d2,
            c_mul=cm,
            c_exp=ce,
            c_sep=cs,
            delta_off=dl
        )

        paper_r = estimate(paper_P)

        rank = 1 + sum(
            1 for o, _, _ in ranked
            if o < objective(paper_r)
        )

        print(f"\n=== n = {n} ===")
        print(f"search optimum : {describe(best_P)}")

        print(
            f"                 {best_r['physical_qubits']/1e6:6.1f} M qubits, "
            f"{best_r['runtime_h']:5.1f} h/run, "
            f"risk {best_r['retry_risk']:.1%}, "
            f"objective {best_obj:.3e}"
        )

        print(f"Table 3 choice : {describe(paper_P)}")

        print(
            f"   in my model : {paper_r['physical_qubits']/1e6:6.1f} M qubits, "
            f"{paper_r['runtime_h']:5.1f} h/run, "
            f"risk {paper_r['retry_risk']:.1%}, "
            f"objective {objective(paper_r):.3e}"
        )

        print(
            f"   paper says  : {q_paper:6.1f} M qubits, "
            f"{t_paper:5.1f} h/run, risk {risk_paper:.0%}"
        )

        print(
            f"Table 3 choice ranks {rank} of {len(ranked)}; "
            f"its objective is {objective(paper_r) / best_obj:.3f}x the optimum"
        )

        if n == 2048:
            print("top 5 in my model:")

            for o, P, r in ranked[:5]:
                print(
                    f"   {o / best_obj:.3f}  {describe(P)}  "
                    f"({r['physical_qubits']/1e6:.1f} M, "
                    f"{r['runtime_h']:.1f} h, "
                    f"risk {r['retry_risk']:.0%})"
                )