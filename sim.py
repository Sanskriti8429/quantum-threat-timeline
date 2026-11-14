import numpy as np

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def P(theta):
    """Phase gate: leaves |0> alone, multiplies |1> by e^(i*theta)."""
    return np.array([[1, 0], [0, np.exp(1j * theta)]], dtype=complex)


def zero_state(n):
    state = np.zeros(2 ** n, dtype=complex)
    state[0] = 1.0
    return state


def basis_state(n, index):
    state = np.zeros(2 ** n, dtype=complex)
    state[index] = 1.0
    return state


def apply_gate(state, gate, target, n):
    """Apply a 2x2 gate to one qubit of an n-qubit state."""
    psi = state.reshape([2] * n)
    psi = np.tensordot(gate, psi, axes=([1], [target]))
    psi = np.moveaxis(psi, 0, target)
    return psi.reshape(-1)


def apply_controlled(state, gate, control, target, n):
    """Apply a 2x2 gate to `target` only on the part of the state
    where `control` is 1."""
    psi = state.reshape([2] * n).copy()
    idx = [slice(None)] * n
    idx[control] = 1
    sub = psi[tuple(idx)]
    t = target if target < control else target - 1
    sub = np.tensordot(gate, sub, axes=([1], [t]))
    sub = np.moveaxis(sub, 0, t)
    psi[tuple(idx)] = sub
    return psi.reshape(-1)


def apply_swap(state, a, b, n):
    psi = state.reshape([2] * n)
    return np.swapaxes(psi, a, b).reshape(-1).copy()


def probabilities(state):
    return np.abs(state) ** 2


def sample(state, shots=1000):
    probs = probabilities(state)
    rng = np.random.default_rng()
    outcomes = rng.choice(len(state), size=shots, p=probs)
    return np.bincount(outcomes, minlength=len(state))


def qft_matrix(n):
    """The QFT as an explicit N x N matrix (N = 2^n)."""
    N = 2 ** n
    omega = np.exp(2j * np.pi / N)
    j, k = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    return omega ** (j * k) / np.sqrt(N)


def qft_circuit(state, n):
    """The QFT built from H, controlled-phase and swap gates."""
    for j in range(n):
        state = apply_gate(state, H, j, n)
        for k in range(j + 1, n):
            angle = np.pi / 2 ** (k - j)
            state = apply_controlled(state, P(angle), control=k, target=j, n=n)
    for i in range(n // 2):
        state = apply_swap(state, i, n - 1 - i, n)
    return state


def _qft_ops(qubits):
    m = len(qubits)
    ops = []
    for j in range(m):
        ops.append(("H", qubits[j]))
        for k in range(j + 1, m):
            ops.append(("CP", qubits[k], qubits[j], np.pi / 2 ** (k - j)))
    for i in range(m // 2):
        ops.append(("SWAP", qubits[i], qubits[m - 1 - i]))
    return ops


def qft_on(state, qubits, n, inverse=False):
    """QFT (or inverse QFT) on the listed qubits of an n-qubit state.
    The inverse is the same gates in reverse order with phases negated."""
    ops = _qft_ops(qubits)
    if inverse:
        ops = ops[::-1]
    for op in ops:
        if op[0] == "H":
            state = apply_gate(state, H, op[1], n)
        elif op[0] == "CP":
            angle = -op[3] if inverse else op[3]
            state = apply_controlled(state, P(angle), op[1], op[2], n)
        else:
            state = apply_swap(state, op[1], op[2], n)
    return state