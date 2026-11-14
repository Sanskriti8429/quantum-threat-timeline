import numpy as np
from sim import qft_on
from shor_quantum import (build_state_before_qft, counting_probs,
                          recover_order, factors_from_order)

np.set_printoptions(precision=4, suppress=True, linewidth=120)


def final_probs(a, N, t, inverse=True):
    state, n, n_work = build_state_before_qft(a, N, t)
    state = qft_on(state, list(range(t)), n, inverse=inverse)
    return counting_probs(state, t, n_work)


print("=== Exercise 1: inverse QFT vs forward QFT ===")
for a, N, t in ((7, 15, 8), (2, 21, 10)):
    p_inv = final_probs(a, N, t, inverse=True)
    p_fwd = final_probs(a, N, t, inverse=False)
    print(f"N={N}, a={a}: probabilities identical: {np.allclose(p_inv, p_fwd)}")

print("\n=== Exercise 2: success probability per attempt vs t ===")
print("(probability that ONE measurement leads to the factors)")
for a, N, ts in ((7, 15, range(2, 10)), (2, 21, range(3, 12))):
    print(f"\nN={N}, a={a}")
    for t in ts:
        probs = final_probs(a, N, t)
        success = 0.0
        for m, p in enumerate(probs):
            if p > 1e-12:
                r = recover_order(m, t, a, N)
                if factors_from_order(a, r, N):
                    success += p
        n_qubits = t + int(np.ceil(np.log2(N)))
        print(f"  t={t:2d} ({n_qubits:2d} qubits, 2^t={2**t:5d}): success per attempt = {success:.3f}")

print("\n=== Exercise 3: operation counts ===")
print("  t   controlled-modmults   QFT: H   controlled-phase   swaps")
for t in (4, 8, 10, 16, 32):
    print(f"{t:3d}   {t:19d}   {t:6d}   {t * (t - 1) // 2:16d}   {t // 2:5d}")