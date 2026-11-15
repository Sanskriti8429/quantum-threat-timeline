import math

import numpy as np

from grover import (uniform_state, grover_step, success_prob,
                    theory_prob, optimal_iterations)
from grover_keysearch import PLAINTEXTS, make_pairs
from toy_cipher import matching_keys

rng = np.random.default_rng(7)
n = 20
N = 2 ** n
secret = int(rng.integers(N))
all_pairs = make_pairs(secret)

print("=== Exercise 1: how many known pairs? (n = 20) ===")
print("pairs   M   k(M known)   P with k(M)   k if M=1 assumed   P with that k")
for count in (1, 2, 3):
    marked = matching_keys(n, all_pairs[:count]).tolist()
    M = len(marked)
    k_true = optimal_iterations(N, M)
    k_naive = optimal_iterations(N, 1)
    print(f"{count:5d} {M:3d} {k_true:12d} {theory_prob(N, M, k_true):13.4f} "
          f"{k_naive:18d} {theory_prob(N, M, k_naive):14.4f}")

print("\n=== Exercise 2: check the formula against a simulation (1 pair) ===")
marked = matching_keys(n, all_pairs[:1]).tolist()
M = len(marked)
k_naive = optimal_iterations(N, 1)
state = uniform_state(n)
for _ in range(k_naive):
    grover_step(state, marked)
print(f"M = {M}, k = {k_naive}: simulated P = {success_prob(state, marked):.4f}, "
      f"formula = {theory_prob(N, M, k_naive):.4f}")

print("\n=== Exercise 3: classical vs Grover ratio ===")
for bits in (8, 20, 64, 128):
    classical = 2 ** bits / 2
    grover = math.pi / 4 * 2 ** (bits / 2)
    print(f"{bits:3d}-bit key: classical/Grover query ratio = {classical / grover:.3e}")