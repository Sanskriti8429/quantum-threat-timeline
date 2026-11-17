"""Stage 6a: how far is demonstrated hardware from what the resource estimates assume?"""
import csv
import math
from dataclasses import replace

from estimator import Params
from hardware_status import DEMONSTRATED, ROADMAP, ROWS
from published_estimates import ROWS as ESTIMATES
from sensitivity import best

LOGICAL_ERROR_TARGET = 1e-15
PEAK_LOGICAL_QUBITS = 1409
TOFFOLIS = 6.5e9
ASSUMED_LAMBDA = 10.0
ASSUMED_REACTION_US = 10.0


def row(key):
    return next(r for r in ROWS if r["key"] == key)


def estimate_qubits(key):
    return next(r for r in ESTIMATES if r["key"] == key)["qubits"]


def distance_for_target(eps_ref, d_ref, lam, target):
    """Distance at which a code with logical error eps_ref at distance d_ref and suppression lam per +2
    reaches `target`, assuming the suppression keeps holding (it may not: noise floors appear)."""
    steps = math.log(eps_ref / target) / math.log(lam)
    return d_ref + 2 * steps


def color_code_qubits(d):
    return (3 * d * d - 1) // 2


def surface_qubits(d):
    return 2 * d * d - 1


if __name__ == "__main__":
    print("=== A. Physical qubits: needed vs largest demonstrated ===")
    needs = {"Pinnacle (98k, non-local)": estimate_qubits("WEB-98k"), "Gidney 2025 (0.9 M, 2D grid)": estimate_qubits("G25"),
             "Gidney-Ekera 2019 (20 M)": estimate_qubits("GE19")}
    shown = [("Caltech atoms, <13 s", row("CALT-6100")["value"]), ("Harvard atoms, 2 h continuous", 3000),
             ("Google superconducting", row("GOOG-qubits")["value"]), ("IBM Nighthawk", row("IBM-nighthawk")["value"]),
             ("Quantinuum Helios ions", row("QTNM-phys")["value"])]
    print(f"{'demonstrated':34s}{'qubits':>8s}" + "".join(f"{k.split(' (')[0]:>22s}" for k in needs))
    for label, n in shown:
        print(f"{label:34s}{n:8,d}" + "".join(f"{v / n:21,.0f}x" for v in needs.values()))

    print("\n=== B. Logical error per round: needed vs demonstrated ===")
    g, q = row("GOOG-eps7")["value"], row("QTNM-eps7")["value"]
    print(f"needed (Gidney 2025)        {LOGICAL_ERROR_TARGET:.0e}")
    print(f"Google surface code d=7     {g:.2e}   -> {math.log10(g / LOGICAL_ERROR_TARGET):.1f} orders of magnitude away")
    print(f"Quantinuum color code d=7   {q:.2e}   -> {math.log10(q / LOGICAL_ERROR_TARGET):.1f} orders of magnitude away")
    lam = row("GOOG-lambda")["value"]
    d = distance_for_target(g, 7, lam, LOGICAL_ERROR_TARGET)
    dd = math.ceil(d) | 1
    print(f"\nIf Willow's Lambda = {lam} kept holding, 1e-15 needs distance {d:.1f}, i.e. {dd}: "
          f"{surface_qubits(dd):,} qubits per logical qubit (bare patch) against "
          f"{surface_qubits(27):,} at the d = 27 the estimates assume ({surface_qubits(dd) / surface_qubits(27):.1f}x)")
    for lam_q in (5.0, 9.0, 17.0):
        d = distance_for_target(q, 7, lam_q, LOGICAL_ERROR_TARGET)
        dd = math.ceil(d) | 1
        print(f"If Quantinuum's fitted Lambda = {lam_q:>4} held (range 5-17): distance {d:.1f}, i.e. {dd} -> {color_code_qubits(dd):,} qubits per logical qubit")
    floor = 1 / row("GOOG-floor")["value"]
    print(f"BUT Google's own repetition-code floor is about {floor:.0e} per cycle: scaling to 1e-15 needs that to be fixed first.")

    print("\n=== C. What the estimates assume vs what was measured ===")
    print(f"Lambda: assumed {ASSUMED_LAMBDA:.0f} (p = 1e-3, p_th = 1e-2); Google measured {lam}  ({ASSUMED_LAMBDA / lam:.1f}x weaker suppression per +2 in distance)")
    print(f"Mapping Google's Lambda onto the estimator's p / p_th = 1/Lambda: p = {1e-2 / lam:.1e}")
    base = Params(n=2048)
    ref = best(base)[1]["expected_volume_Mqd"]
    print(f"\nEstimator, n = 2048, re-optimized (baseline 10 us reaction time: {ref:.2f} Mqd):")
    for rt in (20.0, 63.0):
        r = best(replace(base, reaction_us=rt))[1]
        print(f"  reaction time {rt:4.0f} us -> {r['expected_volume_Mqd']:6.2f} Mqd ({r['expected_volume_Mqd'] / ref:.2f}x), "
              f"{r['physical_qubits'] / 1e6:.1f} M qubits, {r['expected_runtime_h']:.1f} h expected")
    print(f"  (Google's 63 us is decoder latency at distance 5 only; the estimates assume {ASSUMED_REACTION_US:.0f} us at distance 25-29)")
    for p in (3e-3, 5e-3):
        r = best(replace(base, p=p))[1]
        label = "no feasible design in the search ranges" if r is None else f"{r['expected_volume_Mqd']:.1f} Mqd, {r['physical_qubits'] / 1e6:.0f} M qubits"
        print(f"  p = {p:.0e} (Lambda {1e-2 / p:.1f}) -> {label}")
    print(f"Two-qubit gate error alone: IonQ {row('IONQ-2q')['value']:.0e} (lab prototypes), Quantinuum {row('QTNM-2q')['value']:.1e} (Helios),")
    print("  against the estimates' p = 1e-3 for ALL operations of a surface-code cycle at 1 us: not the same quantity.")

    print("\n=== D. Roadmap targets at face value against Gidney 2025's needs ===")
    print(f"needs: {PEAK_LOGICAL_QUBITS:,} logical qubits at peak, {TOFFOLIS:.1e} Toffolis, {estimate_qubits('G25'):,.0f} physical qubits (2D grid)")
    for key, need, what in (("IBM-starling", PEAK_LOGICAL_QUBITS, "logical qubits"), ("IBM-bluejay", PEAK_LOGICAL_QUBITS, "logical qubits"),
                            ("QTNM-apollo", PEAK_LOGICAL_QUBITS, "logical qubits (lower bound)"), ("IONQ-2030", estimate_qubits("G25"), "physical qubits")):
        r = row(key)
        ratio = r["value"] / need
        print(f"{r['org']:10s} {r['target_year']}: {r['value']:>10,.0f} {what:30s} = {ratio:6.2f}x the requirement")
    print("IBM's 'operations' (1e8 by 2029, 1e9 by 2033) are not Toffolis: 6.5e9 Toffolis is 65x and 6.5x more, but the units differ.")
    print("These are company plans. None states error rates, speeds or run times, so none says when RSA-2048 could be factored.")

    with open("hardware_status.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "org", "platform", "kind", "metric", "value", "unit", "date", "target_year", "source",
                    "source_quality", "note"])
        for r in ROWS:
            w.writerow([r["key"], r["org"], r["platform"], r["kind"], r["metric"], r["value"], r["unit"], r["date"],
                        r.get("target_year", ""), r["source"], r["source_quality"], r["note"]])
    print("\nwrote hardware_status.csv")