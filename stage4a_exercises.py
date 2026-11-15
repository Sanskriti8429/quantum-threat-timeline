import math

import numpy as np

from grover import (uniform_state, grover_step, success_prob,
                    theory_prob, optimal_iterations)

print("=== Exercise 1: N=4 (n=2), one marked item ===")
state = uniform_state(2)
grover_step(state, [0])
print("P(success) after 1 iteration:", round(success_prob(state, [0]), 6))

print("\n=== Exercise 2: what if too many items are marked? (n=4, N=16) ===")
N = 16
for M in (8, 12, 16):
    marked = list(range(M))
    state = uniform_state(4)
    probs = []
    for k in range(4):
        probs.append(round(success_prob(state, marked), 4))
        grover_step(state, marked)
    print(f"M={M:2d}: P(success) after k=0,1,2,3 iterations = {probs}")

print("\n=== Exercise 3: sampling a measurement (n=10, 1000 shots) ===")
rng = np.random.default_rng(5)
N, target = 2 ** 10, 123
state = uniform_state(10)
for _ in range(optimal_iterations(N, 1)):
    grover_step(state, [target])
probs = state ** 2
probs /= probs.sum()
shots = rng.choice(N, size=1000, p=probs)
print("optimal k:", optimal_iterations(N, 1))
print("shots that hit the marked item:", int((shots == target).sum()), "/ 1000")
print("most common outcomes:", np.bincount(shots, minlength=N).argsort()[::-1][:3])