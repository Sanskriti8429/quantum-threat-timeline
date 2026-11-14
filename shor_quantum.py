import math
from fractions import Fraction

import numpy as np

from sim import (H, X, zero_state, basis_state, apply_gate,
                 qft_circuit, qft_on)

np.set_printoptions(precision=4, suppress=True, linewidth=120)


def controlled_modmult(state, mult, control, t, n_work, N):
    """Where counting qubit `control` is 1, replace the work value y by
    (mult * y) mod N. Values y >= N are left alone, so this is a permutation."""
    dim_w = 2 ** n_work
    perm = np.arange(dim_w)
    for y in range(N):
        perm[y] = (mult * y) % N
    assert len(set(perm.tolist())) == dim_w, "not a permutation: gcd(mult, N) != 1"

    psi = state.reshape(2 ** t, dim_w).copy()
    xs = np.arange(2 ** t)
    rows = xs[((xs >> (t - 1 - control)) & 1) == 1]
    block = psi[rows]
    moved = np.zeros_like(block)
    moved[:, perm] = block
    psi[rows] = moved
    return psi.reshape(-1)


def build_state_before_qft(a, N, t):
    n_work = math.ceil(math.log2(N))
    n = t + n_work
    state = zero_state(n)
    state = apply_gate(state, X, n - 1, n)
    for j in range(t):
        state = apply_gate(state, H, j, n)
    for j in range(t):
        mult = pow(a, 2 ** (t - 1 - j), N)
        state = controlled_modmult(state, mult, j, t, n_work, N)
    return state, n, n_work


def counting_probs(state, t, n_work):
    psi = state.reshape(2 ** t, 2 ** n_work)
    probs = (np.abs(psi) ** 2).sum(axis=1)
    return probs / probs.sum()


def recover_order(m, t, a, N):
    """Continued fractions: turn a measurement m (out of 2^t) into an order."""
    if m == 0:
        return None
    d = Fraction(m, 2 ** t).limit_denominator(N).denominator
    for k in range(1, 6):                           # d may only divide the true order
        if pow(a, d * k, N) == 1:
            return d * k
    return None


def factors_from_order(a, r, N):
    if r is None or r % 2 != 0:
        return None
    half = pow(a, r // 2, N)
    if half == N - 1:
        return None
    p, q = math.gcd(half - 1, N), math.gcd(half + 1, N)
    if p in (1, N) or q in (1, N):
        return None
    return tuple(sorted((p, q)))


def shor(a, N, t, attempts=10, seed=0):
    rng = np.random.default_rng(seed)
    state, n, n_work = build_state_before_qft(a, N, t)
    state = qft_on(state, list(range(t)), n, inverse=True)
    probs = counting_probs(state, t, n_work)

    top = np.argsort(probs)[::-1][:6]
    print(f"  qubits: {n} ({t} counting + {n_work} work)")
    print("  most likely measurements:",
          [(int(m), round(float(probs[m]), 4)) for m in top])

    for attempt in range(1, attempts + 1):
        m = int(rng.choice(len(probs), p=probs))
        r = recover_order(m, t, a, N)
        factors = factors_from_order(a, r, N)
        print(f"  attempt {attempt}: m={m:4d} -> m/2^t={m / 2 ** t:.4f} "
              f"-> r={r} -> factors={factors}")
        if factors:
            return factors
    print("  no factors found")
    return None


if __name__ == "__main__":
    print("=== Sanity checks ===")
    n = 4
    x = np.random.default_rng(1).normal(size=2 ** n) + 0j
    x /= np.linalg.norm(x)
    print("qft_on over all qubits == qft_circuit:",
          np.allclose(qft_on(x, list(range(n)), n), qft_circuit(x, n)))
    print("inverse(forward(x)) == x:",
          np.allclose(qft_on(qft_on(x, list(range(n)), n), list(range(n)), n, inverse=True), x))

    print("\n=== Work register view (N=15, a=7, t=8) ===")
    state, n, n_work = build_state_before_qft(7, 15, 8)
    psi = state.reshape(2 ** 8, 2 ** n_work)
    for y in (1, 7, 4, 13):
        xs = np.nonzero(np.abs(psi[:, y]) > 1e-9)[0]
        print(f"  work={y:2d}: counting values with nonzero amplitude: {xs[:8]} ...")

    print("\n=== N = 15, t = 8 ===")
    for a in (7, 2, 4, 11, 14):
        print(f"a = {a}")
        shor(a, 15, t=8)

    print("\n=== N = 21, a = 2, t = 10 ===")
    shor(2, 21, t=10)