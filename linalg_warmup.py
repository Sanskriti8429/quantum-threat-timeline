import numpy as np

ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def probs(state):
    return np.round(np.abs(state) ** 2, 6)


print("=== 1. Complex numbers ===")
z1 = 1 + 2j
z2 = 3 - 1j
z = z1 * z2
print("(1+2i)(3-i) =", z)
print("conjugate   =", z.conjugate())
print("|z|^2       =", abs(z) ** 2)

print("e^(i*pi)   =", np.round(np.exp(1j * np.pi), 10))
print("e^(i*pi/2) =", np.round(np.exp(1j * np.pi / 2), 10))
print("e^(i*2pi)  =", np.round(np.exp(1j * 2 * np.pi), 10))

angles = np.random.uniform(0, 2 * np.pi, 10)
print("all phases have magnitude 1:", np.allclose(np.abs(np.exp(1j * angles)), 1))

print("\n=== 2. Unitary matrices ===")
print("H unitary:", np.allclose(H.conj().T @ H, np.eye(2)))
print("Z unitary:", np.allclose(Z.conj().T @ Z, np.eye(2)))

plus = H @ ket0
print("probs of H|0>      :", probs(plus))
print("probs of Z H|0>    :", probs(Z @ plus))
print("H H |0>            :", np.round(H @ H @ ket0, 6))
print("H Z H |0>          :", np.round(H @ Z @ H @ ket0, 6))

print("\n=== 3. Tensor products ===")
print("kron(|0>,|1>)        :", np.round(np.kron(ket0, ket1), 6))
print("kron(H|0>,|0>)       :", np.round(np.kron(H @ ket0, ket0), 6))
two_plus = np.kron(H @ ket0, H @ ket0)
print("kron(H|0>,H|0>)      :", np.round(two_plus, 6))
print("its probabilities    :", probs(two_plus))

print("\nMemory for an n-qubit state vector (complex128, 16 bytes each):")
for n in range(10, 36, 5):
    gib = (2 ** n) * 16 / 2 ** 30
    print(f"  n={n:2d}: {gib:12.6f} GiB")

print("\n=== 4. Product-state test (entanglement) ===")


def product_test(s):
    return s[0] * s[3] - s[1] * s[2]


bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
print("test on kron(H|0>,H|0>):", np.round(product_test(two_plus), 6))
print("test on (|00>+|11>)/sqrt2:", np.round(product_test(bell), 6))