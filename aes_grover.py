"""Stage 5f: logical and physical cost of Grover key search on AES, from Grassl et al. (2016).

Source: Grassl, Langenberg, Roetteler, Steinwandt, "Applying Grover's algorithm to AES: quantum resource
estimates", arXiv:1512.04965v1, Tables 2-5 (read in full). Clifford+T gate set, no connectivity limits,
circuit designed to MINIMIZE QUBITS. Jaques et al. (EUROCRYPT 2020) give lower-depth oracles; their AES
estimates were corrected in a 2023 revision that this project could not access, so they are not used.
"""
import math

SECONDS_PER_YEAR = 365.25 * 24 * 3600
AGE_OF_UNIVERSE_YEARS = 1.38e10
GRASSL = {
    128: dict(r=3, t_box=1_060_864, c_box=1_380_420, tdepth_box=50_688, depth_box=110_799, qubits_box=984,
              extra_t=12_204 + 1_000,
              table5=dict(t=(1.19, 86), c=(1.55, 86), tdepth=(1.06, 80), depth=(1.16, 81), qubits=2953)),
    192: dict(r=4, t_box=1_204_224, c_box=1_567_296, tdepth_box=44_352, depth_box=96_956, qubits_box=1_112,
              extra_t=16_300 + 1_512,
              table5=dict(t=(1.81, 118), c=(1.17, 119), tdepth=(1.21, 112), depth=(1.33, 113), qubits=4449)),
    256: dict(r=5, t_box=1_505_280, c_box=1_956_099, tdepth_box=59_904, depth_box=130_929, qubits_box=1_336,
              extra_t=20_396 + 2_024,
              table5=dict(t=(1.41, 151), c=(1.83, 151), tdepth=(1.44, 144), depth=(1.57, 145), qubits=6681)),
}


def iterations(k):
    return math.floor(math.pi / 4 * 2 ** (k / 2))


def totals(k):
    g = GRASSL[k]
    it = iterations(k)
    return dict(
        iterations=it,
        t_count=it * (2 * g["r"] * g["t_box"] + g["extra_t"]),
        clifford=it * 2 * g["r"] * g["c_box"],
        t_depth=it * 2 * g["tdepth_box"],
        depth=it * 2 * g["depth_box"],
        logical_qubits=g["r"] * g["qubits_box"] + 1,
    )


def table5_value(pair):
    mantissa, exponent = pair
    return mantissa * 2.0 ** exponent


def single_machine_years(k, reaction_us=10.0, depth_reduction=1.0):
    """Lower bound: one reaction time per T layer (feed-forward), nothing else counted."""
    return totals(k)["t_depth"] / depth_reduction * reaction_us * 1e-6 / SECONDS_PER_YEAR


def min_distance(logical_qubits, runtime_s, cycle_us=1.0, p=1e-3, p_th=1e-2, budget=0.1):
    cycles = runtime_s / (cycle_us * 1e-6)
    for d in range(3, 400, 2):
        if logical_qubits * cycles * 0.1 * (p / p_th) ** ((d + 1) / 2) <= budget:
            return d
    return None


def parallel_plan(k, target_years, reaction_us=10.0, cycle_us=1.0):
    """S independent machines, each searching 1/S of the keys: time falls as 1/sqrt(S), total work grows as sqrt(S)."""
    t1_years = single_machine_years(k, reaction_us)
    s_machines = max(1.0, (t1_years / target_years) ** 2)
    runtime_s = t1_years / math.sqrt(s_machines) * SECONDS_PER_YEAR
    lq = totals(k)["logical_qubits"]
    d = min_distance(lq, runtime_s, cycle_us)
    per_machine = lq * 2 * (d + 1) ** 2
    return dict(machines=s_machines, runtime_years=runtime_s / SECONDS_PER_YEAR, d=d,
                qubits_per_machine=per_machine, total_physical_qubits=s_machines * per_machine,
                total_t_count=math.sqrt(s_machines) * totals(k)["t_count"])


def depth_limited_log2_gates(k, log2_max_depth):
    """Total gates when the depth is capped: G_seq * D_seq / D (S machines, S = (D_seq / D)^2)."""
    t = totals(k)
    return math.log2(t["t_count"] + t["clifford"]) + math.log2(t["depth"]) - log2_max_depth


if __name__ == "__main__":
    print("=== 1. Does the arithmetic of Table 5 reproduce from Tables 2-4? ===")
    print("key   quantity           recomputed (x 2^e)   Table 5 (x 2^e)    ratio paper/recomputed")
    for k in (128, 192, 256):
        t = totals(k)
        paper = GRASSL[k]["table5"]
        for name, key in (("T gates", "t"), ("Clifford gates", "c"), ("T-depth", "tdepth"), ("overall depth", "depth")):
            mine_key = {"t": "t_count", "c": "clifford", "tdepth": "t_depth", "depth": "depth"}[key]
            e = paper[key][1]
            mine = t[mine_key] / 2.0 ** e
            print(f"{k:3d}   {name:16s} {mine:8.3f} x 2^{e:<4d}   {paper[key][0]:6.2f} x 2^{e:<4d}   "
                  f"{paper[key][0] / mine:6.3f}")
        print(f"{k:3d}   logical qubits     {t['logical_qubits']:8d}              {paper['qubits']:6d}")

    print("\n=== 2. One machine, run back to back (lower bound: one reaction time per T layer) ===")
    for k in (128, 192, 256):
        for rt in (10.0, 1.0):
            y = single_machine_years(k, rt)
            print(f"AES-{k}: reaction {rt:4.1f} us -> {y:.2e} years  ({y / AGE_OF_UNIVERSE_YEARS:.2e} x age of the universe)")

    print("\n=== 3. AES-128: how much would a shorter circuit help? (single machine, 10 us) ===")
    for f in (1, 10, 100, 1000, 10 ** 6):
        y = single_machine_years(128, 10.0, f)
        print(f"depth reduced {f:>7,d}x -> {y:.2e} years")

    print("\n=== 4. AES-128 with many machines (Grover parallelizes only as sqrt(S)) ===")
    print("target     machines S    d    qubits/machine*   total physical qubits*   total T gates")
    for label, years in (("100 years", 100.0), ("1 year", 1.0), ("1 day", 1 / 365.25), ("1 hour", 1 / 8766)):
        r = parallel_plan(128, years)
        print(f"{label:9s} {r['machines']:11.2e}  {r['d']:3d}  {r['qubits_per_machine']:14.2e}   "
              f"{r['total_physical_qubits']:19.2e}     {r['total_t_count']:.2e}")
    print("* data patches only: magic-state factories and routing are not counted, so these are lower bounds")

    print("\n=== 5. Capping the circuit depth: total gates = G_seq * D_seq / MAXDEPTH ===")
    t = totals(128)
    print(f"sequential: {math.log2(t['t_count'] + t['clifford']):.1f} = log2(gates), {math.log2(t['depth']):.1f} = log2(depth)")
    for e in (40, 64, 81):
        print(f"MAXDEPTH = 2^{e}: total gates 2^{depth_limited_log2_gates(128, e):.1f}")