"""Stage 5e part 2: lay the published estimates next to this project's model."""
import csv

from estimator import Params
from published_estimates import ROWS, qubit_days, same_hardware_assumptions
from sensitivity import best

if __name__ == "__main__":
    ge19 = next(r for r in ROWS if r["key"] == "GE19")
    ge19_volume = qubit_days(ge19)

    P, r = best(Params(n=2048))
    model = dict(key="MODEL", label="This project's model of the 2019 design, re-optimized",
                 platform="surface code (modeled)", connectivity="2D grid, nearest neighbor",
                 p=1e-3, cycle_us=1.0, reaction_us=10.0,
                 qubits=r["physical_qubits"], runtime_days=r["expected_runtime_h"] / 24,
                 source_quality="this project",
                 note="estimator.py + sensitivity.best(): d1 = %d, d2 = %d" % (P.d1, P.d))
    rows = [model] + ROWS

    print(f"{'estimate':52s} {'same hw':>7s} {'qubits':>11s} {'expected runtime':>17s} {'Mqd':>9s} "
          f"{'vs GE19 volume':>14s}  source")
    for row in rows:
        v = qubit_days(row)
        same = same_hardware_assumptions(row)
        rt = row["runtime_days"]
        rt_s = f"{rt * 24:.1f} h" if rt < 1 else f"{rt:.1f} d" if rt < 1000 else f"{rt:.2g} d"
        ratio = f"{v / ge19_volume:.2f}x" if same else "n/a"
        print(f"{row['label'][:52]:52s} {'yes' if same else 'NO':>7s} {row['qubits']:11,.0f} {rt_s:>17s} "
              f"{v:9.2f} {ratio:>14s}  {row['source_quality']}")

    with open("published_estimates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "label", "arxiv", "platform", "connectivity", "p", "cycle_us", "reaction_us",
                    "qubits", "expected_runtime_days", "megaqubit_days", "same_hw_as_GE19",
                    "source_quality", "note"])
        for row in rows:
            w.writerow([row["key"], row["label"], row.get("arxiv", ""), row["platform"], row["connectivity"],
                        row["p"], row["cycle_us"], row["reaction_us"], round(row["qubits"]),
                        round(row["runtime_days"], 4), round(qubit_days(row), 3),
                        same_hardware_assumptions(row), row["source_quality"], row["note"]])
    print("\nwrote published_estimates.csv")

    g25 = next(x for x in ROWS if x["key"] == "G25")
    print("\nGE19 -> Gidney 2025: qubits %.0fx fewer, runtime %.0fx longer, volume %.2fx lower"
          % (ge19["qubits"] / g25["qubits"], g25["runtime_days"] / ge19["runtime_days"],
             ge19_volume / qubit_days(g25)))
    web = next(x for x in ROWS if x["key"] == "WEB-98k")
    print("GE19 -> Pinnacle 98k: qubits %.0fx fewer, runtime %.0fx longer, volume %.2fx lower"
          % (ge19["qubits"] / web["qubits"], web["runtime_days"] / ge19["runtime_days"],
             ge19_volume / qubit_days(web)))
    web1m = next(x for x in ROWS if x["key"] == "WEB-1M")
    print("GE19 -> Pinnacle 1M:  qubits %.0fx fewer, runtime %.1fx %s, volume %.1fx lower"
          % (ge19["qubits"] / web1m["qubits"],
             max(web1m["runtime_days"] / ge19["runtime_days"], ge19["runtime_days"] / web1m["runtime_days"]),
             "longer" if web1m["runtime_days"] > ge19["runtime_days"] else "shorter",
             ge19_volume / qubit_days(web1m)))
    ora = next(x for x in ROWS if x["key"] == "ORA-par")
    print("Cain et al. 102k qubits at 97 days (1 ms cycle): %.2f Mqd; Gidney 2025 (1 us cycle): %.2f Mqd"
          % (qubit_days(ora), qubit_days(g25)))