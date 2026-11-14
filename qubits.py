import numpy as np

# Basis states as column vectors
ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)

# Hadamard gate
H = np.array([[1, 1],
              [1, -1]], dtype=complex) / np.sqrt(2)


def measure(state, shots=1000):
    """Sample measurement outcomes from a state vector.
    Probability of each basis state is |amplitude|^2."""
    probs = np.abs(state) ** 2
    rng = np.random.default_rng()
    outcomes = rng.choice(len(state), size=shots, p=probs)
    return np.bincount(outcomes, minlength=len(state))


if __name__ == "__main__":
    plus = H @ ket0
    print("H|0> =", plus)

    twice = H @ H @ ket0
    print("H H |0> =", twice)

    counts = measure(plus, 1000)
    print("measuring H|0> 1000 times -> counts for 0 and 1:", counts)