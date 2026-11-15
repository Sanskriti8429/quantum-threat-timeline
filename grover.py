import math
import time

import numpy as np

from sim import H, apply_gate


def uniform_state(n):
    N = 2 ** n
    return np.full(N, 1 / np.sqrt(N))


def oracle(state, marked):
    """Phase oracle: flip the sign of every marked basis state."""
    state[marked] *= -1
    return state


def diffusion(state):
    """Inversion about the mean: a -> 2*mean - a."""
    mean = state.mean()
    state[:] = 2 * mean - state
    return state


def grover_step(state, marked):
    return diffusion(oracle(state, marked))


def success_prob(state, marked):
    return float((state[marked] ** 2).sum())


def theory_prob(N, M, k):
    theta = math.asin(math.sqrt(M / N))
    return math.sin((2 * k + 1) * theta) ** 2


def optimal_iterations(N, M):
    theta = math.asin(math.sqrt(M / N))
    return max(0, round(math.pi / (4 * theta) - 0.5))


def diffusion_gates(state, n):
    """H^n, flip the sign of |0...0>, H^n, then an overall -1.
    This equals 2|s><s| - I, the inversion about the mean."""
    state = state.astype(complex)
    for q in range(n):
        state = apply_gate(state, H, q, n)
    state[0] *= -1
    for q in range(n):
        state = apply_gate(state, H, q, n)
    return -state


if __name__ == "__main__":
    np.set_printoptions(precision=4, suppress=True, linewidth=120)

    print("=== 1. Trace: n=3 (N=8), marked item 5 ===")
    n, marked = 3, [5]
    state = uniform_state(n)
    print("start            :", state)
    for k in range(1, 4):
        oracle(state, marked)
        print(f"k={k} after oracle   :", state)
        diffusion(state)
        print(f"k={k} after diffusion:", state)
        print(f"     P(success) = {success_prob(state, marked):.4f}   "
              f"theory = {theory_prob(8, 1, k):.4f}")

    print("\n=== 2. Overshoot: n=4 (N=16), M=1 ===")
    state = uniform_state(4)
    for k in range(0, 11):
        print(f"k={k:2d}: P(success) = {success_prob(state, [3]):.4f}   "
              f"theory = {theory_prob(16, 1, k):.4f}")
        grover_step(state, [3])
    print("optimal k =", optimal_iterations(16, 1))

    print("\n=== 3. Gate-built diffusion equals inversion about the mean ===")
    n = 4
    rng = np.random.default_rng(0)
    s = rng.normal(size=2 ** n)
    s /= np.linalg.norm(s)
    print("match:", np.allclose(diffusion_gates(s, n), diffusion(s.copy())))

    print("\n=== 4. Several marked items: n=8 (N=256) ===")
    N = 256
    for M in (1, 4, 16, 64):
        marked = list(range(M))
        k = optimal_iterations(N, M)
        state = uniform_state(8)
        for _ in range(k):
            grover_step(state, marked)
        print(f"M={M:3d}: optimal k = {k:2d}  (pi/4*sqrt(N/M) = "
              f"{math.pi / 4 * math.sqrt(N / M):5.2f})   "
              f"P(success) = {success_prob(state, marked):.4f}")

    print("\n=== 5. Scaling with search space size (M=1) ===")
    print("  n          N   Grover k   classical (N+1)/2   P(success)   time")
    rng = np.random.default_rng(1)
    ns, ks = [], []
    for n in range(4, 21, 2):
        N = 2 ** n
        marked = [int(rng.integers(N))]
        k = optimal_iterations(N, 1)
        t0 = time.time()
        state = uniform_state(n)
        for _ in range(k):
            grover_step(state, marked)
        p = success_prob(state, marked)
        print(f"{n:3d} {N:10d} {k:10d} {(N + 1) / 2:19.1f} {p:12.4f} {time.time() - t0:6.2f}s")
        ns.append(n)
        ks.append(k)
    slope = np.polyfit(np.array(ns) * math.log(2), np.log(ks), 1)[0]
    print(f"log-log slope of Grover queries vs N: {slope:.3f}  (classical = 1, sqrt = 0.5)")