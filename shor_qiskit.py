import math
from collections import Counter

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, transpile
from qiskit.circuit.library import QFTGate, UnitaryGate
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from shor_quantum import (build_state_before_qft, counting_probs,
                          recover_order, factors_from_order)
from sim import qft_on


def modmult_unitary(mult, N, n_work):
    """Permutation matrix sending |y> to |mult*y mod N> (y >= N untouched)."""
    dim = 2 ** n_work
    perm = np.arange(dim)
    for y in range(N):
        perm[y] = (mult * y) % N
    M = np.zeros((dim, dim))
    M[perm, np.arange(dim)] = 1.0
    return UnitaryGate(M, label=f"x{mult} mod {N}")


def shor_circuit_generic(a, N, t):
    n_work = math.ceil(math.log2(N))
    counting = list(range(t))
    work = list(range(t, t + n_work))
    qc = QuantumCircuit(t + n_work)
    qc.x(work[0])
    qc.h(counting)
    for j in range(t):
        mult = pow(a, 2 ** j, N)
        qc.append(modmult_unitary(mult, N, n_work).control(1), [counting[j]] + work)
    qc.append(QFTGate(t).inverse(), counting)
    return qc, counting


N15_TABLE = {1: (0, False), 2: (1, False), 4: (2, False), 8: (3, False),
             14: (0, True), 13: (1, True), 11: (2, True), 7: (3, True)}


def controlled_mult15(qc, mult, control, work):
    rot, negate = N15_TABLE[mult]
    if rot == 1:
        qc.cswap(control, work[2], work[3])
        qc.cswap(control, work[1], work[2])
        qc.cswap(control, work[0], work[1])
    elif rot == 2:
        qc.cswap(control, work[1], work[3])
        qc.cswap(control, work[0], work[2])
    elif rot == 3:
        qc.cswap(control, work[0], work[1])
        qc.cswap(control, work[1], work[2])
        qc.cswap(control, work[2], work[3])
    if negate:
        for w in work:
            qc.cx(control, w)


def shor_circuit_n15(a, t):
    counting = list(range(t))
    work = list(range(t, t + 4))
    qc = QuantumCircuit(t + 4)
    qc.x(work[0])
    qc.h(counting)
    for j in range(t):
        mult = pow(a, 2 ** j, 15)
        if mult != 1:
            controlled_mult15(qc, mult, counting[j], work)
    qc.append(QFTGate(t).inverse(), counting)
    return qc, counting


def qiskit_probs(qc, counting):
    sv = Statevector(qc)
    return sv.probabilities(qargs=counting)


def run_shots(qc, counting, shots=1024, seed=7):
    """Add measurements on the counting register and sample with Aer."""
    qc = qc.copy()
    creg = ClassicalRegister(len(counting), "m")
    qc.add_register(creg)
    qc.measure(counting, creg)
    sim = AerSimulator(seed_simulator=seed)
    result = sim.run(transpile(qc, sim), shots=shots).result()
    return Counter({int(k, 2): v for k, v in result.get_counts().items()})


if __name__ == "__main__":
    np.set_printoptions(precision=4, suppress=True, linewidth=120)

    print("=== A: Qiskit (generic) vs hand-built simulator ===")
    for a, N, t in ((7, 15, 8), (2, 15, 8), (11, 15, 8), (2, 21, 10)):
        qc, counting = shor_circuit_generic(a, N, t)
        p_qiskit = qiskit_probs(qc, counting)

        state, n, n_work = build_state_before_qft(a, N, t)
        state = qft_on(state, list(range(t)), n, inverse=True)
        p_mine = counting_probs(state, t, n_work)

        top = np.argsort(p_qiskit)[::-1][:4]
        print(f"N={N}, a={a}: distributions match = {np.allclose(p_qiskit, p_mine)}; "
              f"top Qiskit peaks = {[(int(m), round(float(p_qiskit[m]), 4)) for m in top]}")

    print("\n=== B: gate-level N=15 circuit vs generic circuit ===")
    for a in (2, 4, 7, 8, 11, 13, 14):
        qb, cb = shor_circuit_n15(a, 8)
        qa, ca = shor_circuit_generic(a, 15, 8)
        print(f"a={a:2d}: gate-level matches generic: "
              f"{np.allclose(qiskit_probs(qb, cb), qiskit_probs(qa, ca))}")

    print("\n=== Gate counts for the N=15, a=7, t=8 circuit (gate-level) ===")
    qc, _ = shor_circuit_n15(7, 8)
    print("before transpiling:", dict(qc.count_ops()))
    tc = transpile(qc, basis_gates=["cx", "u"], optimization_level=1)
    print("after transpiling to {cx, u}:", dict(tc.count_ops()), " depth =", tc.depth())

    print("\n=== C: sampling with Aer (1024 shots) and classical post-processing ===")
    for a, N, t, build in ((7, 15, 8, "n15"), (2, 21, 10, "generic")):
        if build == "n15":
            qc, counting = shor_circuit_n15(a, t)
        else:
            qc, counting = shor_circuit_generic(a, N, t)
        outcomes = run_shots(qc, counting)
        found = Counter()
        for m, v in outcomes.items():
            f = factors_from_order(a, recover_order(m, t, a, N), N)
            if f:
                found[f] += v
        total = sum(found.values())
        print(f"N={N}, a={a}: top outcomes {outcomes.most_common(4)}")
        print(f"   shots leading to factors: {total}/1024 = {total / 1024:.3f} {dict(found)}")