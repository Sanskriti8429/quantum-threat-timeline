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