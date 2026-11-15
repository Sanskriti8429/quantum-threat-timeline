import math
import time

import numpy as np

from grover import uniform_state, grover_step, success_prob, optimal_iterations
from toy_cipher import encrypt, matching_keys

PLAINTEXTS = [0x1234, 0xBEEF, 0xC0DE]


def make_pairs(secret_key):
    return [(p, int(encrypt(p, secret_key)[0])) for p in PLAINTEXTS]


def grover_key_search(marked, n, rng):
    """Grover search over all 2^n keys. Returns (found key, oracle queries,
    probability of success). One oracle call per iteration."""
    N = 2 ** n
    k = optimal_iterations(N, len(marked))
    state = uniform_state(n)
    queries = 0
    for _ in range(k):
        grover_step(state, marked)
        queries += 1
    probs = state ** 2
    probs /= probs.sum()
    guess = int(rng.choice(N, p=probs))
    return guess, queries, success_prob(state, marked)


def classical_search_queries(is_marked, rng):
    """Brute force in a random key order: cipher evaluations until a hit."""
    order = rng.permutation(len(is_marked))
    return int(np.argmax(is_marked[order])) + 1


if __name__ == "__main__":
    rng = np.random.default_rng(2026)

    print("=== 0. Sanity checks on the toy cipher ===")
    keys = rng.integers(0, 2 ** 16, size=4000, dtype=np.int64).astype(np.uint64)
    flipped = keys ^ np.uint64(1)
    diff = encrypt(0x1234, keys) ^ encrypt(0x1234, flipped)
    bits = np.array([bin(int(v)).count("1") for v in diff])
    print(f"flip 1 key bit -> ciphertext bits that change: mean {bits.mean():.2f} of 16")
    pt_flip = encrypt(0x1234, keys) ^ encrypt(0x1235, keys)
    bits = np.array([bin(int(v)).count("1") for v in pt_flip])
    print(f"flip 1 plaintext bit -> ciphertext bits that change: mean {bits.mean():.2f} of 16")

    print("\n=== 1. Grover vs classical brute force on the toy cipher ===")
    print("  n        N  M  Grover q  P(success)  found?   classical q (mean of 100)   (N+1)/(M+1)")
    ns, grover_q, classical_q = [], [], []
    for n in range(8, 21, 2):
        N = 2 ** n
        secret = int(rng.integers(N))
        pairs = make_pairs(secret)
        t0 = time.time()
        marked = matching_keys(n, pairs)
        guess, q, p = grover_key_search(marked.tolist(), n, rng)
        found = guess in set(marked.tolist())
        is_marked = np.zeros(N, dtype=bool)
        is_marked[marked] = True
        c = np.mean([classical_search_queries(is_marked, rng) for _ in range(100)])
        print(f"{n:3d} {N:8d} {len(marked):2d} {q:9d} {p:11.4f} {str(found):>7s} "
              f"{c:20.1f} {(N + 1) / (len(marked) + 1):17.1f}   [{time.time() - t0:.1f}s]")
        ns.append(n)
        grover_q.append(q)
        classical_q.append(c)

    x = np.array(ns) * math.log(2)
    print("\nlog-log slope, Grover queries vs N   :",
          round(np.polyfit(x, np.log(grover_q), 1)[0], 3), " (sqrt = 0.5)")
    print("log-log slope, classical queries vs N:",
          round(np.polyfit(x, np.log(classical_q), 1)[0], 3), " (linear = 1)")

    print("\n=== 2. Extrapolating the formulas to real key sizes ===")
    for bits in (56, 128, 256):
        g = math.pi / 4 * 2 ** (bits / 2)
        c = 2 ** bits / 2
        print(f"{bits:3d}-bit key: Grover ~ {g:.3e} sequential oracle calls "
              f"(2^{math.log2(g):.1f}), classical ~ {c:.3e} (2^{bits - 1})")