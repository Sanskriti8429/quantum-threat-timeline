# Quantum Threat Timeline: Project Notes

## Stage-1: Classical core of Shor's algorithm

Shor's algorithm is mostly classical. The only part that needs a quantum computer is finding the **order** of a number. Everything else is ordinary arithmetic.

### Order finding

For a number `a` coprime to `N`, the order `r` is the smallest positive integer such that `a^r = 1 (mod N)`. Example: for `a=7, N=15`, the powers of 7 mod 15 go 7 -> 4 -> 13 -> 1, so `r= 4`.

Classically this means checking powers one at a time, which becomes infeasible for large `N` (like a 2048-bit RSA modulus). No known classical
algorithm finds `r` efficiently. This is the gap that the quantum step of
Shor's algorithm (period finding via the Quantum Fourier Transform) fills.

### From order to factors

If `r` is even and `a^(r/2)` is not congruent to -1 (mod N), then
`gcd(a^(r/2) - 1, N)` and `gcd(a^(r/2) + 1, N)` give nontrivial factors of
`N`. This works because `a^r - 1 = 0 (mod N)` factors as
`(a^(r/2) - 1)(a^(r/2) + 1) = 0 (mod N)`.

For a randomly chosen `a`, this succeeds with probability at least 1/2.
Verified empirically: N=15 gives 6/7 coprime `a` succeeding, N=21 gives
6/11, and N=35 gives 18/23.

### Failure modes and limitations

- **N=9 (= 3^2, a prime power):** 0/5 coprime `a` succeed. The guarantee
  doesn't apply to prime powers, so real implementations must check
  classically that `N` is not a prime power.
- **N=8 (even):** some `a` "succeed" but return `(2, 4)`, which is not a
  prime factorization. Real implementations require `N` to be odd.

### Cost to remember for later

The operation that matters for resource estimation is **modular
exponentiation**, `a^x mod N` (in code, `pow(a, x, N)`). Doing it reversibly
on qubits is the expensive part of the circuit and will dominate the qubit
and gate counts in the Stage 5 estimator.

### Code

See `shor_classical.py`: a brute-force order finder standing in for the
quantum period-finding step, plus factor extraction and a sweep over all `a`
for a given `N`.

## Stage 2a: Complex numbers, unitaries, tensor products

### Predicted

(What the math says to expect before running. Edit to match what I actually
guessed.)

- `H|0>` gives equal amplitudes, so measuring it should give about 50/50.
- Applying `H` twice should return `|0>`, because `H` is its own inverse.
- `Z` only flips the sign of the `|1>` amplitude, so I expected the
  measurement probabilities of `Z H|0>` to stay `[0.5, 0.5]`.
- `H Z H |0>` was the open question: a sign that changes no probabilities
  by itself might still change the result after a second `H`.
- `H|0> ⊗ H|0>` should give four equal probabilities of 0.25.
- The memory needed for an n-qubit state doubles with every added qubit.

### Surprised me

(Keep only the ones that are true for you.)

- `H H |0>` printed `-2.2e-17` instead of exactly 0. That is floating-point
  rounding, so comparisons need `np.allclose`, never `==`.
- `Z` changed nothing in the measurement probabilities, yet `H Z H |0>`
  gave `|1>` while `H H |0>` gave `|0>`. A sign I could not see in the
  probabilities flipped the final answer.
- n = 30 qubits needs 16 GiB for the state vector alone, and n = 35 needs
  512 GiB.

### Explain to someone else

**Phase.** A qubit amplitude is a complex number, and `e^(i*theta)` is a
complex number of magnitude 1 at angle `theta`. Multiplying an amplitude by
it changes its direction but not its magnitude, so measurement probabilities
(`|amplitude|^2`) do not change. Phase only matters when amplitudes combine,
because the same sign flip makes them add or cancel. This is interference,
and it is how Shor's algorithm cancels wrong periods and boosts the right
one. The Quantum Fourier Transform is built entirely out of phases.

**Unitary.** A gate is a matrix `U` with `U† U = I`, where `U†` is the
conjugate transpose. That guarantees the total probability stays 1 and that
every gate can be undone. It is also why Shor's modular exponentiation must
be built reversibly, which is what makes it expensive.

**Why n qubits need 2^n numbers.** One qubit is a length-2 vector. Combining
qubits with the tensor product multiplies the lengths, so n qubits have
2^n amplitudes, one for each of the 2^n basis states. Memory doubles with
every added qubit: 0.5 GiB at n = 25 and 16 GiB at n = 30 (16 bytes per
complex number). That is why classical simulators stop at roughly 25 to 30
qubits, and why hand-built NumPy simulation only works for small examples.

**Entanglement.** A two-qubit state `[c00, c01, c10, c11]` that is a product
of two single-qubit states `a ⊗ b` has `c00 = a0*b0`, `c01 = a0*b1`,
`c10 = a1*b0` and `c11 = a1*b1`. Then `c00*c11 = a0*b0*a1*b1 = c01*c10`, so
`c00*c11 - c01*c10 = 0` for every product state. For the Bell state
`(|00> + |11>)/sqrt(2)` we have `c00 = c11 = 1/sqrt(2)` and
`c01 = c10 = 0`, so the quantity is 1/2, not 0. No pair of single-qubit
states multiplies to give it, so the two qubits cannot be described
separately. Measuring either qubit gives 0 or 1 at random, but the second
qubit's result always matches the first. The state belongs to the pair, not
to either qubit, and algorithms like Shor's use that kind of correlation.

### Code

`qubits.py` (single-qubit state vector, Hadamard gate, measurement sampling)
and `linalg_warmup.py` (complex numbers, unitarity checks, tensor products,
memory scaling, product-state test).

## Stage 2b: Gates, a circuit simulator, and the QFT

### Predicted

(What the math says to expect. Edit to match what I actually guessed.)

- CNOT with qubit 0 as control flips the target only when the control is 1,
  so `|10>` goes to `|11>` and `|11>` goes to `|10>`.
- H on qubit 0 followed by CNOT should give the Bell state, with only the
  outcomes 00 and 11 at probability 0.5 each. The 3-qubit version (GHZ) should
  give only 000 and 111.
- The circuit QFT built from Hadamards, controlled-phase gates and swaps
  should equal the full QFT matrix.
- A state with period 4 on 16 amplitudes should give a QFT with peaks at
  multiples of N/r = 4.
- Shifting where the pattern starts should change phases but not
  probabilities.

### Surprised me

(Keep only the ones that are true for you.)

- The circuit matched the matrix for every basis input for n = 1 to 5, even
  though it uses only about n^2/2 gates instead of an N x N matrix.
- The shifted period-4 state gave exactly the same probabilities, with the
  offset appearing only as phases (1, i, -1, -i) on the peaks.

### Explain to someone else

**Gates and controlled gates.** Gates acting on one qubit of an n-qubit
register are 2x2 unitaries applied along one axis of the state, with the
other qubits untouched. A controlled gate applies the 2x2 gate only to the
part of the state where the control qubit is 1. CNOT is a controlled X, and
it is what creates entanglement: H then CNOT turns |00> into the Bell state.

**The QFT.** On N = 2^n amplitudes, the QFT maps amplitude pattern x to
F[j,k] = e^(2*pi*i*j*k/N) / sqrt(N). A state that repeats with period r
turns into peaks at multiples of N/r, and the starting offset of the
pattern only changes phases. That is why measuring the QFT output reveals
the period without needing to know where the pattern starts, and it is the
quantum step in Shor's algorithm.

**Why the circuit is cheap.** The circuit uses n Hadamards, n(n-1)/2
controlled-phase gates, and floor(n/2) swaps, which grows like n^2. The
matrix has 4^n entries. The circuit is what makes the QFT efficient, and
the gate counts feed the Stage 5 resource estimator.

**Gate counts (from `stage2b_exercises.py`):**

| n | Hadamards | Controlled-phase | Swaps |
|---|---|---|---|
| 4 | 4 | 6 | 2 |
| 8 | 8 | 28 | 4 |
| 16 | 16 | 120 | 8 |

### Period 3 (not a divisor of 16)

The probability concentrates on indices 0, 5 and 11, the integers nearest
to multiples of N/r = 16/3 (0, 5.33, 10.67). Index 0 has probability 0.375
(6 ones in the input, so 6/16), indices 5 and 11 have 0.2336 each, and the
remaining ~0.16 is spread as small tails. The peaks are blurry because 3
does not divide 16, so no integer sits exactly on a multiple of N/r.

The period can still be recovered classically. For a measured value m, the
continued fraction expansion of m/16 gives a nearby fraction with a small
denominator: 5/16 has the convergent 1/3, and 11/16 has 2/3, so both give
r = 3. This is the classical post-processing step of Shor's algorithm. A
larger register makes the peaks sharper, which is why real implementations
use about twice as many qubits in the period register as bits in N.

### What happens without the final swaps

Without the swaps the circuit matches the matrix QFT only for n = 1. For
n >= 2 the output equals the matrix QFT with its indices in bit-reversed
order (verified numerically). The period-4 peaks moved from 0, 4, 8, 12 to
0, 1, 2, 3, because reversing the 4-bit forms of 0, 4, 8, 12 gives
0, 2, 1, 3.

This matters for resource counting. The swaps cost n/2 gates (three CNOTs
each) and can be skipped if the measured bits are read in reverse order
classically, so many resource estimates leave them out. The estimator
should therefore treat swaps as an optional parameter.

### Limitations

- The simulator stores all 2^n amplitudes, so it is only practical up to
  about 25 qubits. It demonstrates correctness on small examples and says
  nothing about speed at RSA scale.
- Gate counts here are for the exact QFT. Large-scale estimates use
  approximate QFTs and different arithmetic constructions, which we
  cover in Stage 5.

### Code

`sim.py` (state vectors, gates, controlled gates, swap, QFT as matrix and
circuit), `stage2b_tests.py` (CNOT, Bell, GHZ, QFT verification, period
finding), and `stage2b_exercises.py` (period 3, gate counts, no-swap QFT).