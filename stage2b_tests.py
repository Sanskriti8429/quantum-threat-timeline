import numpy as np
from sim import (H, X, Z, zero_state, basis_state, apply_gate,
                 apply_controlled, probabilities, sample,
                 qft_matrix, qft_circuit)

np.set_printoptions(precision=4, suppress=True)

print("=== 1. CNOT on basis states (control = qubit 0, target = qubit 1) ===")
for index, label in enumerate(["00", "01", "10", "11"]):
    out = apply_controlled(basis_state(2, index), X, control=0, target=1, n=2)
    print(f"CNOT |{label}> -> index {np.argmax(np.abs(out))}")

print("\n=== 2. Bell state: H on qubit 0, then CNOT ===")
s = zero_state(2)
s = apply_gate(s, H, 0, 2)
s = apply_controlled(s, X, 0, 1, 2)
print("state        :", s)
print("probabilities:", probabilities(s))
print("1000 shots   :", sample(s, 1000))

print("\n=== 3. 3-qubit GHZ state ===")
s = zero_state(3)
s = apply_gate(s, H, 0, 3)
s = apply_controlled(s, X, 0, 1, 3)
s = apply_controlled(s, X, 1, 2, 3)
print("probabilities:", probabilities(s))

print("\n=== 4. Circuit QFT equals matrix QFT? ===")
for n in range(1, 6):
    F = qft_matrix(n)
    ok = all(
        np.allclose(qft_circuit(basis_state(n, i), n), F[:, i])
        for i in range(2 ** n)
    )
    print(f"n={n}: all basis inputs match: {ok}, unitary: "
          f"{np.allclose(F.conj().T @ F, np.eye(2 ** n))}")

print("\n=== 5. QFT finds a period ===")
n = 4
N = 2 ** n
x = np.zeros(N, dtype=complex)
x[0::4] = 1
x /= np.linalg.norm(x)
print("period 4, probs   :", probabilities(qft_circuit(x, n)))

x2 = np.zeros(N, dtype=complex)
x2[1::4] = 1
x2 /= np.linalg.norm(x2)
print("shifted, probs    :", probabilities(qft_circuit(x2, n)))
print("shifted, amplitudes:", qft_circuit(x2, n))