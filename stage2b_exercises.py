import numpy as np
from sim import (H, P, apply_gate, apply_controlled, probabilities,
                 basis_state, qft_matrix, qft_circuit)

np.set_printoptions(precision=4, suppress=True, linewidth=120)

# ---------- Exercise 1: period 3 on 16 amplitudes ----------
print("=== Exercise 1: period 3 (3 does not divide 16) ===")
n, N = 4, 16
x = np.zeros(N, dtype=complex)
x[0::3] = 1                       # ones at 0, 3, 6, 9, 12, 15
x /= np.linalg.norm(x)
print("probs:", probabilities(qft_circuit(x, n)))
print("N/r =", N / 3, "so peaks should sit near multiples of that")

# ---------- Exercise 2: gate counts ----------
def qft_counts(n):
    """Dry run of qft_circuit's loops that only counts gates."""
    hadamards = controlled_phases = 0
    for j in range(n):
        hadamards += 1
        for k in range(j + 1, n):
            controlled_phases += 1
    swaps = n // 2
    return hadamards, controlled_phases, swaps

print("\n=== Exercise 2: gate counts ===")
for n in (4, 8, 16):
    h, cp, sw = qft_counts(n)
    print(f"n={n:2d}: H={h}, controlled-phase={cp}, swaps={sw}")

# ---------- Exercise 3: remove the swaps ----------
def qft_no_swaps(state, n):
    for j in range(n):
        state = apply_gate(state, H, j, n)
        for k in range(j + 1, n):
            angle = np.pi / 2 ** (k - j)
            state = apply_controlled(state, P(angle), control=k, target=j, n=n)
    return state

def bit_reverse(index, n):
    return int(format(index, f"0{n}b")[::-1], 2)

print("\n=== Exercise 3: QFT without the final swaps ===")
for n in range(1, 6):
    F = qft_matrix(n)
    matches = all(
        np.allclose(qft_no_swaps(basis_state(n, i), n), F[:, i])
        for i in range(2 ** n)
    )
    print(f"n={n}: matches matrix QFT: {matches}")

n = 4
x = np.zeros(2 ** n, dtype=complex)
x[0::4] = 1
x /= np.linalg.norm(x)
print("no-swap probs, period 4:", probabilities(qft_no_swaps(x, n)))

F = qft_matrix(3)
col = F[:, 3]
out = qft_no_swaps(basis_state(3, 3), 3)
perm = [bit_reverse(j, 3) for j in range(8)]
print("output equals matrix column in bit-reversed order:",
      np.allclose(out, col[perm]))