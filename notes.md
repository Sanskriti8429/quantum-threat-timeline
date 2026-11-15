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

## Stage 3a: Shor's period finding, built by hand

### Predicted

(What the math says to expect. Edit to match what I actually guessed.)

- N=15, a=7 has order 4, so with t=8 the counting register should show
  peaks at 0, 64, 128, 192 with probability 0.25 each.
- With the work register fixed to a single value, the surviving counting
  values should be spaced 4 apart, with a different offset per work value.
- a=11 has order 2, so peaks at 0 and 128.
- m=128 gives 1/2, whose denominator is 2, but the true order is 4, so
  recovering r should need multiples of the denominator.
- a=14 should always fail, because a^(r/2) = -1 (mod 15).
- N=21, a=2 has order 6, which does not divide 1024, so most peaks should
  be blurry.

### Surprised me

(Keep only the ones that are true for you.)

- For a=14 the quantum step found the correct order every time. The failure
  is entirely classical, so re-measuring never helps; a new a is needed.
- For N=21, the peaks at m=0 and m=512 are exact while the others are
  blurry. Exact peaks happen when 3 divides s, since s * 1024 / 6 is an
  integer only then.
- The success probability for N=15 does not change with t, because its
  orders (2 and 4) are powers of two.

### Explain to someone else

**The circuit.** A counting register (t qubits) is put into a uniform
superposition. Counting qubit j then controls multiplication of a work
register by a^(2^(t-1-j)) mod N, so the work register ends up holding
a^x mod N for every x at once. The state is entangled: for each work value,
the counting register holds only the x values with that value, spaced r
apart, starting at a random offset. The inverse QFT turns that spacing into
peaks at multiples of 2^t / r, and the offset only changes phases.

**Post-processing.** A measurement m satisfies m / 2^t ~ s / r for a
random s. A continued fraction expansion (Fraction.limit_denominator(N))
recovers a denominator d that equals r or divides it, so I try small
multiples of d until a^(d*k) = 1 (mod N). Then the stage 1 gcd step gives
the factors. If a^(r/2) = -1 or r is odd, the run fails and a new a is
needed.

**Choosing t.** To separate different fractions s/r with denominators up
to N, m / 2^t must be accurate to about 1/N^2, so 2^t >= N^2, which means
t is about 2 * log2(N). For N=21, a=2 the success probability per attempt
rose from about 0.2 at t <= 5 to 0.82 at t=10, with a ceiling of 5/6.

**Operation counts.** t controlled modular multiplications, plus a QFT
with t Hadamards, t(t-1)/2 controlled-phase gates and floor(t/2) swaps.
For t=8: 8 multiplications and 8 + 28 + 4 QFT gates.

### Limitations

- `controlled_modmult` is a lookup-table permutation built by looping over
  all y < N. That is exponential in the bit length of N and is not a
  gate-level circuit. Real implementations need reversible modular
  arithmetic (adders, comparators, Toffoli gates), which dominates the
  qubit and gate counts at RSA scale. The multiplication count above is
  therefore not an honest resource number; Stage 5 has to fill this gap.
- N=15 is a degenerate case: all its orders are powers of two, so the
  peaks are always exact and success does not depend on t. N=21 shows the
  realistic behavior.
- The simulator stores 2^(t + n_work) amplitudes (15 qubits for N=21),
  so it cannot approach RSA sizes. It shows correctness, not speed.
- The multiples loop in `recover_order` is a simple heuristic; production
  code also tries neighboring measurements and combines several runs.

### Code

`shor_quantum.py` (state preparation, controlled modular multiplication,
continued-fraction post-processing, the full run), `sim.py` (now with
`qft_on` for subsets of qubits and its inverse), and
`stage3a_exercises.py` (forward vs inverse QFT, success vs t, operation
counts).

## Stage 3b: Shor's algorithm in Qiskit

### Environment

Run on Google Colab (Python 3.13, numpy 2.4.6, qiskit 2.6.2,
qiskit-aer 0.18.2), because Windows application control blocked Qiskit's
compiled library on my local machine. All earlier stages run locally
with numpy only.

### Predicted

(What the math says to expect. Edit to match what I actually guessed.)

- Qiskit's circuit uses the same unitary as my hand-built simulator, so
  the measurement distributions should match to numerical precision.
- A hard-wired gate-level circuit for N=15 should match the generic
  circuit for every valid a.
- Sampling 1024 shots should give about 0.75 success for N=15, a=7 and
  about 0.82 for N=21, a=2, t=10.
- The CNOT count should grow quadratically with t, because of the QFT.

### Surprised me

(Keep only the ones that are true for you.)

- The distributions matched my NumPy simulator in every case, so the
  hand-built QFT and the circuit were right.
- Only 2 of the controlled multiplications are non-trivial for N=15,
  because a^(2^j) = 1 (mod 15) for j >= 2.
- For N=15 the inverse QFT is more than half of the CNOTs (68 of 112).

### Explain to someone else

**Cross-check.** Version A builds each controlled multiplication as a
permutation matrix (UnitaryGate) and uses Qiskit's inverse QFT. Its
measurement distribution matches my NumPy simulator for N=15 (a=7, 2, 11)
and N=21 (a=2). Qiskit is little-endian (qubit 0 is the least significant
bit), so qubit j controls multiplication by a^(2^j); the integer value
of the counting register is then the same m as in my simulator.

**Gate-level N=15.** Multiplying by 2^s mod 15 is a cyclic rotation of the
four work bits (controlled swaps), and multiplying by -1 flips all four
bits. Every unit mod 15 is +-2^s, so this covers all the bases. After
transpiling to {CNOT, single-qubit} gates, the a=7, t=8 circuit has 112
CNOTs, 141 single-qubit gates, and depth 119. The CNOT count splits as
5 controlled swaps x 8 + 4 + 68 for the inverse QFT.

**Scaling with t (a=7).** CNOTs = 44 + t(t-1) + 3*floor(t/2): 62, 83, 112,
149, 194 for t = 4, 6, 8, 10, 12. The 44 is fixed (two non-trivial
controlled multiplications); the rest is the QFT, which grows like t^2.

**Sampling.** Aer sampling of 1024 shots with the same classical
post-processing gave 764/1024 = 0.746 for N=15, a=7 (theory 0.75) and
838/1024 = 0.818 for N=21, a=2, t=10 (matches the exact value 0.818).

### Limitations

- The N=15 circuit is hard-wired. The rotation trick works because
  15 = 2^4 - 1 and does not generalize to other N.
- It skips the multiplications that equal 1 (mod 15). That uses the fact
  that the order divides 4, which is close to knowing the answer in
  advance. This is a known criticism of "factored 15" demonstrations
  (Smolin, Smith and Vargo, 2013, "Oversimplifying quantum factoring";
  I should read it before citing it). The CNOT counts here cannot be
  extrapolated to RSA-2048.
- The inverse QFT is over half the CNOTs only because the arithmetic is
  trivial for N=15. At RSA scale modular arithmetic dominates.
- Version A uses a lookup-table unitary, with the same limitation as
  stage 3a: it shows correctness, not honest resource counts.
- Everything here is exact or sampled statevector simulation, so it is
  limited to about 25 qubits and does not model noise or error
  correction.

### Code

`shor_qiskit.py`: generic and N=15 gate-level circuits, cross-check
against `shor_quantum.py` / `sim.py`, gate counts, and Aer sampling.

## Stage 4a: Grover's algorithm in NumPy

### Predicted

(What the math says to expect. Edit to match what I actually guessed.)

- With one marked item among N, each iteration rotates the state by
  2*theta, where theta = arcsin(sqrt(M/N)), so
  P(success after k iterations) = sin^2((2k+1) * theta).
- For N=8 this gives 0.7813, 0.9453 and 0.3301 after 1, 2 and 3
  iterations, so the third iteration should already overshoot.
- For N=16 the best k is 3; one more iteration should lower the
  probability, and it should come back up later, since it is a rotation.
- With M marked items the optimal k should be about (pi/4)*sqrt(N/M), so
  quadrupling M should halve k.
- Quadrupling N should double Grover's k and quadruple the classical
  average (N+1)/2, giving log-log slopes of about 0.5 and 1.
- For N=4 with one marked item, theta = pi/6, so one iteration should
  give probability exactly 1.
- If half or more of the items are marked, Grover should give no benefit
  or make things worse.

### Surprised me

(Keep only the ones that are true for you.)

- The simulated probabilities matched sin^2((2k+1)*theta) to four
  decimals at every step, so the rotation picture is exact, not an
  approximation.
- At N=16 the probability reaches 0.9613 at k=3, falls to 0.0204 at k=6,
  then climbs to 0.9922 at k=9. More queries can hurt.
- With M=12 of 16 items marked, a single iteration drops the success
  probability from 0.75 to 0.0.
- At n=20, 804 queries find the item, against about 524,288 on average
  for classical search, roughly 650 times fewer.

### Explain to someone else

**The two steps.** The oracle flips the sign of the marked amplitudes,
which does not change any measurement probability by itself. The diffusion
step replaces every amplitude a by 2*mean - a. After the sign flip the
marked amplitude is far below the mean, so diffusion pushes it far above,
while all the others shrink slightly. Repeating this concentrates the
amplitude on the marked items.

**The geometry.** The state stays in a plane spanned by "marked" and
"unmarked". Each iteration rotates it by 2*theta toward "marked", where
sin(theta) = sqrt(M/N). After k iterations the success probability is
sin^2((2k+1)*theta), maximized near k = (pi/4)*sqrt(N/M). Because it is a
rotation, running past the optimum lowers the probability again.

**Diffusion from gates.** Inversion about the mean equals H on every
qubit, then a sign flip of |0...0>, then H on every qubit, then an overall
-1. I verified this against the NumPy version using sim.py. This is the
form a real circuit uses.

**Scaling.** For M=1, n = 4, 6, ..., 20 gave k = 3, 6, 12, 25, 50, 100,
201, 402, 804. Each +2 in n doubles k. The log-log slope of k against N is
0.505, against 1 for classical search. This is a quadratic speedup, not
exponential. Unstructured search cannot be done in fewer than about
sqrt(N) queries (BBBV lower bound; I should read it before citing).

### Limitations

- The oracle here flips the sign of an index I already know. It
  demonstrates the query count only, not the cost of building a real
  oracle that evaluates a function reversibly. Stage 4b uses a cipher as
  the function, and Stage 5 has to price the circuit.
- The classical column (N+1)/2 is a formula, not a measurement. Stage 4b
  measures classical brute force empirically.
- Grover needs the number of marked items M to be known, or estimated, and
  well below N/2. At M = N/2 it gives no gain, and above that it can hurt.
- The statevector holds all 2^n amplitudes, so the simulation is limited
  to about n = 25.
- Grover's speedup is quadratic, and it parallelizes poorly: S machines
  searching in parallel only give about a sqrt(S) speedup. That is why it
  weakens a symmetric key's security by half the bits and not more.

### Code

`grover.py` (oracle, diffusion, iteration count, gate-built diffusion,
scaling study) and `stage4a_exercises.py` (N=4, too many marked items,
measurement sampling).

## Stage 4b: Grover's key search on a toy cipher

### Predicted

(What the math says to expect. Edit to match what I actually guessed.)

- Three known plaintext/ciphertext pairs give 48 bits of constraint, more
  than the key length n <= 20, so only the true key should match (M = 1).
- Grover's query counts should equal the stage 4a table: 12, 25, 50, 100,
  201, 402, 804 for n = 8, 10, ..., 20.
- Classical brute force in random order should need about (N+1)/2 queries.
  A mean over 100 trials should be within roughly 10% of that.
- Log-log slopes should be about 0.5 for Grover and 1 for classical.
- With only 1 pair at n = 20, about 1 + 2^20 / 2^16 = 17 keys should match,
  so assuming M = 1 would make Grover rotate past the target.
- For a 128-bit key the classical/Grover ratio should be around 10^19.

### Surprised me

(Keep only the ones that are true for you.)

- The toy cipher mixes well: flipping one key bit changes 8.02 of 16
  ciphertext bits on average, and one plaintext bit changes 7.76.
- Measured classical means (122.8, 528.9, 1898.7, ...) scatter by up to
  about 7% around (N+1)/2, but the slope across n is still 1.004.
- With 1 pair, M = 18 (17 false matches plus the true key). Running the
  iteration count for M = 1 (804) gives success probability only 0.1398,
  matching the formula exactly.

### Explain to someone else

**The attack.** Given known pairs (P_i, C_i) from one secret key, define
f(k) = 1 if Enc_k(P_i) = C_i for every i. Grover searches over all 2^n
keys for f(k) = 1. Each pair constrains 16 bits, so 3 pairs fix a key of
up to 48 bits.

**The oracle in the simulation.** I evaluate the cipher on every key
classically once (matching_keys), then the oracle flips the sign of those
keys. A real oracle would evaluate the cipher reversibly in superposition.
A "query" here is one oracle call.

**Results.** Grover found the key every time (success 0.9995 or higher)
with 12, 25, 50, 100, 201, 402, 804 queries for n = 8 ... 20. Classical
brute force in random order took about N/2 (mean over 100 trials, measured
by the position of the key in a random permutation, which equals the
number of cipher evaluations). The log-log slopes are 0.504 and 1.004,
confirming the quadratic speedup on a real key-search problem.

**Extrapolation (formulas only, not simulated).** A 128-bit key needs
about (pi/4) * 2^64 = 2^63.7 sequential Grover iterations against 2^127
classically, so Grover roughly halves the key length in bits: AES-128
drops to about 64 bits and AES-256 to about 128 bits of query complexity.

**Sensitivity to M.** The iteration count depends on the number of
solutions. Underestimating M rotates the state past the target: with
M = 18 and the M = 1 count, success was 0.1398.

### Limitations

- The cipher is a toy with a simple key schedule and is not secure. It
  only gives Grover a real function to search; Grover's query count
  depends on N and M, not on the cipher's internals.
- The oracle is built by classically evaluating all keys. A real oracle
  is a reversible cipher circuit, and its cost (qubits, gates, depth,
  uncomputation) is not counted here. Query counts are therefore not
  runtimes. Stage 5 has to price the oracle.
- Classical query counts are measured through a precomputed table of
  matching keys, not by calling the cipher once per guess. The count is
  the same.
- Grover needs M known or estimated. Algorithms exist for unknown M
  (Boyer, Brassard, Hoyer and Tapp, 1998; I should read it before citing).
- Grover parallelizes poorly: S machines give only about a sqrt(S)
  speedup in time while total work grows.
- The statevector holds 2^n amplitudes, so the simulation stops near
  n = 25. The 56/128/256-bit rows are formula extrapolations.

### Code

`toy_cipher.py` (16-bit SPN, key schedule, known-pair key matching),
`grover_keysearch.py` (Grover vs classical search, scaling slopes,
extrapolation), and `stage4b_exercises.py` (number of known pairs, wrong
M, query ratios).