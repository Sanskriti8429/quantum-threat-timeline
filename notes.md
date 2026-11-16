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

## Stage 5a: Reading Gidney and Ekerå (2019)

Source: C. Gidney and M. Ekerå, "How to factor 2048 bit RSA integers in 8
hours using 20 million noisy qubits", Quantum 5, 433 (2021),
arXiv:1905.09749v3. All numbers below come from that version's text and
tables. Formulas came from extracted PDF text, so each must be checked
against the PDF before it goes into code.

### Summary

The paper costs out Shor's factoring algorithm on a stated hardware
model: a planar grid of superconducting qubits with nearest-neighbor
connectivity, a physical gate error rate of 10^-3, a surface code cycle
time of 1 microsecond and a classical reaction time of 10 microseconds.
Almost all of the cost is the modular exponentiation, which is a sequence
of controlled modular multiplications. The QFT is nearly free because it
is done semi-classically (Griffiths-Niu), interleaved with the
multiplications, with the control qubits recycled.

Four ideas cut the cost. (1) The Ekerå-Håstad variant computes a short
discrete logarithm, which needs about 1.5n exponent qubits instead of
2n, so fewer multiplications. (2) Windowed arithmetic fuses groups of
c_exp exponent qubits and c_mul multiplier qubits into table lookups, so
the number of additions falls by about c_exp * c_mul, but each lookup
costs about 2^(c_exp + c_mul) Toffolis. (3) The coset representation of
modular integers lets cheap non-modular adders (4n Toffolis when
controlled) replace modular adders (about 10n), at the price of padding
qubits and a small approximation error. (4) Oblivious carry runways split
a register into pieces that are added in parallel, which cuts depth at a
small cost in qubits and Toffolis. In the abstract circuit model this
gives 3n + 0.002 n lg n logical qubits, 0.3 n^3 + 0.0005 n^3 lg n
Toffolis and 500 n^2 + n^2 lg n measurement depth.

To turn this into physical numbers, each logical qubit is a surface code
patch of 2(d+1)^2 physical qubits, and the logical error per cycle is
assumed to be 10^(-ceil(d/2 + 1)) at a physical error rate of 10^-3
(each increase of d by 2 suppresses errors 10x). For n = 2048 the paper
uses d = 27 and a grid of 226 x 63 logical qubits, about 25% of which
make magic states (CCZ factories). A run lasts about 25 billion cycles,
which gives about 27% probability of a topological error, so a run is
repeated about 1.4 times on average. Distillation (about 6.4%),
approximation (about 0.1%) and post-processing failures add to the retry
risk. The authors search over code distances, window sizes, runway
spacing, padding and factory type, and minimize s^1.2 * t / (1 - risk),
where s is physical qubits and t is runtime per run. The result for
n = 2048 is 20 million physical qubits, 5.1 hours per run, retry risk 31%,
so about 7.4 hours expected (the title rounds to 8) and an expected
volume of 5.9 megaqubitdays, over 100x less than earlier comparable
estimates.

The authors warn that these are ballpark figures with large systematic
uncertainties: for example, doubling or halving the physical error rate
changes the qubit count by more than 10%. Their own estimates also rest
on assumptions from other papers (the CCZ factory and layout models), so
they cannot be reproduced exactly from this paper alone.

### Answers to the reading questions

1. **Why is the QFT negligible?** It is done semi-classically and
   interleaved with the multiplications. Only the control qubits for the
   current window are needed and they are recycled, and the phase shifts
   combine into one classically controlled rotation.
2. **What does each optimization trade?** Windowing trades fewer
   additions for exponentially larger lookups (2^(c_exp + c_mul)). The
   coset representation trades padding qubits and a small approximation
   error for cheaper adders. Runways trade a few extra qubits and
   Toffolis (linear in n / c_sep) and a small approximation error for
   parallel, shallower additions; they do not speed up lookups, so the
   best window sizes shrink by about 1.
3. **Why 1.5n exponent qubits?** Ekerå-Håstad computes d = p + q with two
   exponent registers of 2m and m qubits where m is about n/2, so 3m =
   1.5n, against 2n in Shor's original. Post-processing is lattice-based
   and succeeds with at least 99% probability in one run.
4. **Reaction limited.** The adder is a chain of dependent Toffolis. Each
   needs a measurement result and a classical decision before the next
   step, which takes the reaction time (10 microseconds). An addition
   therefore takes about 2(c_sep + c_pad) reaction times regardless of
   how many factories exist.
5. **Spacetime volume.** Qubits times time. The authors minimize
   s^1.2 * t / (1 - risk) so that a slight preference for fewer qubits
   is built in and expected retries are included.
6. **25 billion cycles and d = 27.** Runtime is about 4 n_e n ms, which at
   one cycle per microsecond is about 2.5e10 cycles. Then 10^-15 *
   (226 * 63 * 0.75 logical qubits) * 2.5e10 is about 27%. d = 29 would
   cut the error about 10x for about 15% more qubits.
7. **The rule of thumb.** V(p) is about V(0.1%) / (-log10(p) - 2)^3.
   Each +2 in d suppresses errors by about threshold / p (threshold about
   1%), so at p = 0.01% distances are about half as large. The
   computation packs into three dimensions (two space, one time), so
   volume scales as distance cubed: 8x smaller at 0.01% and 27x at
   0.001%. Limits: ignores rounding of d, the fixed reaction time, and a
   change of code at very low error rates; the paper calls it an
   order-of-magnitude guide for about 0.3% to 0.001%.
8. **Table 2's caption.** A cycle time 5x more optimistic reduces the
   expected volume 5x, so volumes from different papers are only
   comparable when their assumptions are normalized.

### Checkpoints (n = 2048, d = 27, c_exp = c_mul = 5, c_sep = 1024)

n_e = 3029 comes from the expression printed in Table 3 (to verify in the
PDF). "Recomputed" values were computed from the paper's formulas.

| Quantity | Paper | Recomputed |
|---|---|---|
| Logical error per cycle, d = 27 | 10^-15 | 10^-15 |
| Surface code cycles | about 25 billion | 2.48e10 |
| Topological error probability | about 27% | 26.5% |
| Lookup phase | about 14 ms | 13.8 ms |
| Addition phase | about 22 ms | 21.4 ms |
| One lookup addition | about 37 ms | about 36 ms |
| Lookup additions | about 0.1 n_e n = 6.2e5 | 5.0e5 (leading term 2 n n_e / 25) |
| Toffoli (CCZ) count | about 3 billion | 2.6e9 |
| Runtime, one run | about 7 h (section 2.11) | 5.0 h; Table 3 lists 5.1 h |
| Physical qubits | about 23 M (text), 20 M (Table 3) | 22.3 M (226 * 63 * 1568) |
| Expected runtime from Table 3 | title says 8 h | 5.1 / (1 - 0.31) = 7.4 h |

### Things I found inconsistent or unsure about

- Section 2.11 says about 7 hours per run, but Table 3 says 5.1 hours.
  The difference is the coefficient in Eq. (1): the paper rounds
  2/25 = 0.08 up to 0.1, a 25% difference. The 0.1 also absorbs the
  lookup term in the Toffoli count (1024 / 4096 = 25%), which is why the
  Toffoli count comes out consistent either way. My estimator should use
  the unrounded form and report both.
- Eq. (2) as extracted shows 2^(c_exp + c_pad) in the Toffoli cost of a
  lookup addition, but section 2.5 gives the lookup cost as
  2^(c_exp + c_mul). With c_pad near 44 the first would be absurd, so it
  is presumably an extraction error or typo. To check in the PDF.
- The text says about 23 million physical qubits at d = 27, but
  226 * 63 * 1568 is about 22.3 million. The paper itself says that
  section is "sloppily rounding" and the 20 million in the title comes
  from the ancillary script, which also lowers the level 1 distillation
  distance from 17 to 15.
- The title's "8 hours" is the expected runtime rounded up from about
  7.4 hours.

### What I need to reproduce this fully

The CCZ factory footprint and distillation error model (Gidney-Fowler
2019), the layout details (113w x 63 grid, 14 factories at d = 27), and
the parameter search ranges (d1 in 15 to 23, d2 in 25 to 51, c_mul and
c_exp in 4 to 6, c_sep in {512, 768, 1024, 1536, 2048}, padding offset
2 to 10, CCZ or T factory). The authors' script ("estimate costs.py") is
listed as an ancillary file on the arXiv page.

## Stage 5b: Error-correction basics behind the cost model

### Predicted

(What the math says to expect. Edit to match what I actually guessed.)

- A majority-vote repetition code should suppress errors with more
  copies below p = 0.5, do nothing at exactly 0.5, and make things worse
  above it.
- The heuristic p_L = 0.1 * (p / p_th)^((d+1)/2) with p_th = 1% should
  match the paper's 10^-(ceil(d/2)+1) at p = 10^-3 for odd d.
- Multiplying qubit-cycles by p_L should give about 27% topological
  error at d = 27, about 10x less at d = 29 and about 10x more at d = 25.
- A 10% error budget at p = 10^-3 should need d around 29.
- Distance should shrink as p falls (about half at p = 10^-4) and blow up
  as p approaches the threshold, with no solution at p = 10^-2.
- One round of 15-to-1 distillation from 10^-3 should give about
  35 * (10^-3)^3 = 3.5e-8, which is not enough for 2e-11 per state.

### Surprised me

(Keep only the ones that are true for you.)

- The paper's per-cycle logical error rule is a special case of the
  usual heuristic: p_L = 0.1 * (p / p_th)^((d+1)/2) with p = 0.1 * p_th.
- Required distance grows slowly at first and then explodes: 15, 19,
  29, 41, 55, 95, 297 for p = 1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3, 8e-3.
  The physical qubits for the 14,238 logical qubits go 7.3 M, 11.4 M,
  25.6 M, 50.2 M, 89.3 M, 262 M, 2,529 M.
- A 10x tighter error budget (10% to 1%) costs only +2 in distance
  (29 to 31).
- Two ideal rounds of 15-to-1 distillation from 10^-3 reach 1.5e-21,
  which is far more than the 2e-11 the paper needs, so real factories
  must be doing something less ideal.

### Explain to someone else

**Why correct errors at all.** A physical gate fails about once in 1000
(p = 10^-3). The paper's computation has about 2.65e14 logical
qubit-cycles and must keep the total topological failure near 10%, so
each logical qubit-cycle must fail less than about once in 10^15.

**Redundancy and threshold.** With d copies and a majority vote, the
logical error falls exponentially in d when p is below the threshold
(0.5 for this classical code), stays flat at the threshold and rises
above it. Quantum codes cannot copy states, so they spread information
over entangled qubits and measure parity checks, and they must also
handle phase errors. The surface code has a threshold of about 1%.

**The surface code.** A logical qubit is a patch of data qubits and
measurement qubits. Measurement qubits check parities every cycle (1
microsecond), and a classical decoder uses the pattern of failed checks
to guess the errors. Distance d is the smallest number of physical
errors that can cause an undetected logical error. A heuristic for the
logical error per cycle is 0.1 * (p / p_th)^((d+1)/2), so each +2 in d
multiplies the error by p / p_th (0.1 at p = 10^-3, 0.01 at p = 10^-4).
A bare patch has 2 d^2 - 1 physical qubits (1,457 at d = 27); the paper
counts 2 (d+1)^2 (1,568) because it includes spacing between patches.

**Non-Clifford gates and magic states.** Clifford gates are cheap
(lattice surgery). Toffoli/CCZ gates need magic states, which factories
make by distillation. One ideal round of 15-to-1 distillation turns 15
states of error p into one of error about 35 p^3. The paper needs about
3 billion CCZ states with total error about 6.4%, so about 2e-11 each.

**Cost versus physical error rate.** For the n = 2048 workload and a 10%
budget, the required distance rises from 15 (p = 1e-4) through 29
(p = 1e-3) to 95 (p = 5e-3) and diverges at the threshold. Cost does not
scale linearly with p: the overhead explodes as p approaches p_th.

### Open question for 5d

The paper picks d = 27 (about 27% topological failure) rather than
d = 29 (2.6%). My crude model (qubits ~ (d+1)^2 raised to 1.2, lookup time
~ d, other time fixed, risk 31% to 7%) gives about 0.90 for the ratio of
d = 29 to d = 27, i.e. slightly in favour of 29. The paper's full search
must contain effects my model leaves out (factory distances, layout
granularity, number of factories). To investigate when reproducing the
parameter search.

### Limitations

- The 0.1 * (p / p_th)^((d+1)/2) rule is a heuristic fitted to
  simulations and only valid below threshold. Values near or above
  threshold (the 297 at p = 8e-3, the "none" at 1e-2, probabilities above
  1) are artifacts of the formula, not predictions.
- The repetition code is an analogy for the shape of the curve. Its
  threshold (0.5) is not the surface code's (about 1%), because the
  surface code must also handle noisy syndrome measurements and two kinds
  of error.
- Section 4 gives every logical patch the same distance. The paper's
  layout uses different distances inside the factories.
- The 35 p^3 distillation formula describes one ideal level. The paper's
  factories are different designs with their own error models
  (Gidney-Fowler 2019) and are not reproduced here.
- Decoder quality is folded into the heuristic. A better decoder changes
  p_th and the prefactor, which is where a neural decoder (stage 5g) would
  enter.

### Code

`ec_basics.py`: repetition code, surface-code logical error heuristic
checked against the paper's rule, topological error for the n = 2048
workload, required distance versus physical error rate, patch sizes and
15-to-1 distillation.

## Stage 5c: Estimator v0 (Gidney-Ekerå section 2 cost model)

### Predicted

(What the formulas say to expect. Edit to match what I actually guessed.)

- The unrounded model should give a per-run runtime near Table 3's 5.1 h,
  because Table 3 comes from the authors' script, which does not round.
  The simplified model should give about 7 h, as in section 2.11.
- A shorter runtime means fewer surface code cycles, so less topological
  error and a lower retry risk than Table 3's 31%.
- Qubit counts for n = 1024 and 2048 should overshoot Table 3, because those
  rows use d1 = 15 and my layout assumes the d1 = 17 one.
- Toffoli counts should land within a few percent of Table 1.

### Surprised me

(Keep only the ones that are true for you.)

- The paper's Eq. (2) prints 2^(c_exp + c_pad) in the Toffoli cost of a
  lookup addition, but with c_pad about 44 that gives 2.07e20 Toffolis,
  against 2.59e9 with 2^(c_exp + c_mul) (section 2.5) and 2.7e9 in Table 1.
  So it is a typo in the printed paper.
- The 7 h in section 2.11 and the 5.1 h in Table 3 differ because the text
  rounds 2/25 = 0.08 up to 0.1 in Eq. (1). Mixing the rounded and the
  unrounded figures gives misleading results: the simplified 6.89 h with
  its 31.9% risk gives 10.1 h expected, while the paper's 7.4 h uses 5.1 h.
- The detailed model reproduces the per-run runtime (4.99 h against 5.1 h)
  but not the retry risk (24.5% against 31%).
- Faster surface code cycles can make things worse: at 0.2 us the
  per-run runtime only falls from 4.99 h to 3.47 h, because the addition
  phase is limited by the 10 us reaction time, while the number of cycles
  grows about 5x.

### Explain to someone else

**What the estimator does.** It takes the modulus size n, the window sizes
c_exp and c_mul, the runway spacing c_sep, the padding offset, the code
distance d, and the cycle and reaction times. It computes the number of
lookup additions (2 n n_e / (c_exp c_mul) * (c_sep + 1) / c_sep), the
Toffoli count and measurement depth, the runtime (each lookup addition
takes a code-depth-limited lookup phase d/2 * 2^(c_exp + c_mul) cycles,
plus a reaction-limited addition phase 2 (c_sep + c_pad) reaction times,
plus about 1 ms), the logical qubit grid (113 w x 63, w = n / c_sep), the
physical qubits (grid x 2 (d+1)^2) and the error budget: topological
(runtime in cycles x 75% of the grid x 10^-(ceil(d/2)+1), as a union
bound), distillation (about 2.1e-11 per CCZ state), approximation
(2 sqrt of the deviation in Eq. 4) and classical post-processing (1%).
They are combined assuming independence into a retry risk, and the
expected runtime is the per-run runtime divided by (1 - risk).

**Results for n = 2048, d = 27.**

| Quantity | Simplified | Detailed | Paper |
|---|---|---|---|
| Lookup additions | 6.20e5 | 4.97e5 | 0.1 n_e n = 6.2e5 |
| Toffolis | 2.58e9 | 2.59e9 | 2.7e9 (Table 1) |
| Runtime per run | 6.89 h | 4.99 h | 7 h (sec 2.11); 5.1 h (Table 3) |
| Physical qubits | 22.3 M | 22.3 M | 23 M (text); 20 M (Table 3) |
| P(topological) | 26.5% | 19.2% | 27% |
| Retry risk | 31.9% | 24.5% | 31% (Table 3) |
| Expected runtime | 10.1 h | 6.6 h | 7.4 h |
| Expected volume | 9.4 Mqd | 6.2 Mqd | 5.9 Mqd |

**Other sizes (detailed mode, Table 3 parameters).** Toffolis are within
5% of Table 1 (0.38, 2.58, 9.52 billion against 0.4, 2.7, 9.9). Runtimes
per run are within 8% (1.2, 5.0, 11.6, 21.1 h against 1.3, 5.1, 12, 22).
Qubits match within 1% to 6% for n = 3072 and 4096 but overshoot by 15%
and 12% for n = 1024 and 2048.

**What changes when hardware changes.** At d = 27 a 5x faster cycle gives a
worse expected volume (10.3 Mqd against 6.15) because the addition phase is
reaction limited and the number of cycles grows 5x. A 5x faster reaction
time halves the volume (2.92 Mqd), and both together give 1.40 Mqd.
Table 2's remark that a 5x faster cycle reduces volume 5x applies to
designs where the cycle time is the bottleneck, which this one is not.

**d = 27 versus 29.** In this model d = 29 lowers the topological error
from 19.2% to 2.0% and the expected runtime from 6.6 h to 5.6 h while
adding 15% qubits. The paper's objective s^1.2 * t_expected is 0.9997 of
the d = 27 value, a tie, so the paper's choice of 27 comes from something
this model does not include.

### Open questions for stage 5d

1. **Retry risk gap (24.5% against 31%).** One lead, not established: if
   all logical qubits are counted in the topological error instead of 75%,
   the detailed model gives 25.6% topological error, a 30.4% risk and 7.18 h
   expected runtime. But section 2.13 says the factory qubits are
   already accounted for in the distillation error, so this may double
   count. The authors' script would settle it.
2. **Qubits for d1 = 15 rows.** Table 3 rows with d1 = 15 (n = 1024 and 2048)
   are the ones my layout overshoots, consistent with the remark in
   section 2.14 that reducing d1 from 17 to 15 changes the layout.
3. **Distillation error per CCZ.** I use the paper's 6.4% for 3e9 states at
   d1 = 17, d2 = 27 for every n. It depends on d1 and d2 and cannot be
   derived from the paper's text alone, so risks for other n are not
   validated.
4. **d = 27 versus 29** (above).

### Limitations

- v0 implements the simplified model of section 2 with no parameter search.
  The layout (113-wide pieces, 63 rows, 25% factories), a single code
  distance for the whole machine and the per-CCZ distillation error are
  fixed.
- The logical error rule 10^-(ceil(d/2)+1) holds only at a physical error
  rate of 10^-3. Other error rates need the heuristic from stage 5b.
- The topological error is a union bound (an upper bound), as in the
  paper's method.
- The 0.06% approximation error is lower than the paper's rounded 0.1%,
  as expected (2 sqrt(1e-7) = 0.063%).
- The tests use explicit tolerances (3% to 16%). One test pins the known
  retry risk gap so that it cannot be forgotten.

### Code

`estimator.py` (the model, two modes, comparison tables) and
`test_estimator.py` (the stage 5a checkpoints as seven unit tests, run
with `python -m unittest -v test_estimator`).

## Stage 5d: Level 1 distance d1 and the parameter search

### Predicted

(What the model implies. Edit to match what I actually guessed.)

- A search over the paper's parameter ranges, scored by s^1.2 * t / (1 - risk),
  should land near Table 3's choices if the model is reasonable.
- At n = 2048 the choices d1 = 15, d2 = 27 versus d1 = 17, d2 = 29 should be
  close, as in stage 5b.
- delta_off should barely matter.
- Table 3's n = 2048 row uses d1 = 15 and section 2 uses d1 = 17, so its
  distillation error and retry risk should be higher than the section 2
  defaults.

### Surprised me

(Keep only the ones that are true for you.)

- My first version charged nothing for a larger factory, and the search
  chose d1 = 23 for n = 1024. The footprint has to grow with d1.
- The stage 5c retry risk gap (24.5% against Table 3's 31%) is explained by
  d1: the table's n = 2048 row uses d1 = 15, not the section 2 value of 17.
  My stage 5c lead (counting all logical qubits in the topological error)
  was not needed.
- All four Table 3 choices land in the top 0.2% of the 21,000 to 28,000 grid
  points, within 3.6% of my optimum.

### Explain to someone else

**What the factory paper gives.** Gidney and Fowler (2019): the CCZ factory
is 12d x 6d and makes one CCZ every 5.5d cycles, with suppression 28 eps^2
in the level 1 T-state error eps. The level 1 T factory is 15-to-1
distillation (35 eps^3). Distillation limited, the T-state error is 3.5e-8
and the CCZ error 3.4e-14. At minimal distances (d0 = 7, d1 = 15, d2 = 31)
the T-state error is about 1.4e-6 and the CCZ error about 5.3e-11. Raising
d1 from 15 to 19 grows the footprint by about 20% and lets the factory
produce about 1e12 states before an error.

**What it does not give.** How topological error falls with d1 and d2,
and how the layout changes with d1, are in a supplementary spreadsheet I
could not retrieve.

**My reconstruction.** Distillation error per CCZ state:
p_ccz = 28 * eps_T1(d1)^2 + C2 * 10^(-(d2 - 27)/2), where eps_T1(d1) =
3.5e-8 + 1.365e-6 * 10^(-(d1 - 15)/2) and C2 is calibrated so that
(d1, d2) = (17, 27) gives the 6.4% over 3e9 states of Gidney-Ekerå 2.12.
Assumed: the topological part falls 10x per +2 in d1, and the CCZ-factory
term falls 10x per +2 in d2. Checks: (15, 31) gives 5.5e-11 (paper 5.3e-11),
and the distillation floor gives 3.4e-14. At (19, 31) it gives 2.7e-13
against the paper's order of magnitude of 1e-12.

**Layout.** Piece width scales with d1 (113 at d1 = 17), fitted to the lower
qubit counts of the d1 = 15 rows. Rows scale with c_sep + c_pad, which is an
untested extrapolation.

**Table 3 rows in the model (detailed mode, d1 from the table).**

| n | Toffolis (G) | runtime per run (h) | qubits (M) | retry risk |
|---|---|---|---|---|
| 1024 | 0.38 (paper 0.4) | 1.2 (1.3) | 9.9 (9.7) | 6.1% (6%) |
| 2048 | 2.58 (2.7) | 5.0 (5.1) | 19.8 (20) | 34.1% (31%) |
| 3072 | 9.52 (9.9) | 11.6 (12) | 38.4 (38) | 10.4% (9%) |
| 4096 | 22.23 (n/a) | 21.1 (22) | 58.3 (55) | 4.9% (5%) |

**Search (28,350 grid points per n, objective s^1.2 * t / (1 - risk)).**

| n | rank of Table 3 choice | objective vs optimum | optimum differs from Table 3 in |
|---|---|---|---|
| 1024 | 5 | 1.000x | delta_off only (7 vs 5), no effect |
| 2048 | 59 of 26,325 | 1.036x | d1 = 17, d2 = 29 instead of 15, 27 |
| 3072 | 18 of 25,737 | 1.005x | c_sep = 1536 instead of 1024 |
| 4096 | 9 of 21,035 | 1.000x | delta_off only (7 vs 9) |

At n = 2048 my optimum is 25.6 M qubits, 5.1 h per run and 3.8% risk, while
Table 3's choice is 19.8 M, 5.0 h and 34% risk. The objective differs by
3.6%, the same near-tie between d = 27 and d = 29 as in stage 5b.

### How much weight this deserves

- It supports the paper: all four chosen parameter sets sit in the top 0.2%
  of my grid, with a model that was not tuned to select them.
- It limits what that proves: the objective is flat over a wide region
  (delta_off barely matters; many combinations are within 1%), so matching
  the exact choices is weak evidence. My rankings also depend on the two
  layout assumptions and the two-anchor distillation model, and I have not
  yet tested how much they move when those change.

### Limitations

- p_ccz is a reconstruction from two anchors with assumed falloff rates,
  about a factor of 4 off at the one order-of-magnitude check (d1 = 19).
- Width proportional to d1 is fitted to two Table 3 rows, so those qubit
  comparisons are not independent. Rows scaling with c_sep is untested, and
  the factory count per piece is fixed at 14 regardless of d2.
- The physical error rate is fixed at 1e-3, with the paper's cycle and
  reaction times. The model's n = 2048 retry risk is 34% against 31%.
- The authors' script and spreadsheet were not available, so this does not
  reproduce their code, only the numbers their papers publish.

### Code

`estimator.py` (now with d1, the two-term CCZ error and a d1-dependent
layout), `search.py` (grid search over d1, d2, c_mul, c_exp, c_sep and
delta_off) and the tests `test_estimator.py` (9 tests) and `test_search.py`
(1 test).

## Stage 5e (part 1): Sensitivity to hardware assumptions (n = 2048)

### Predicted

(What the model implies. Edit to match what I actually guessed.)

- A worse physical error rate should be paid mostly in qubits (larger code
  distances), because the runtime is set by the reaction time.
- The paper's rule of thumb V(p) ~ V(0.1%) / (-log10 p - 2)^3 should hold
  roughly, over the limited range the paper claims for it.
- A faster reaction time should help more than a faster cycle time, because
  the addition phase is reaction limited and the cycle time only shrinks the
  lookup phase.
- Close to the threshold (1%) no design should be feasible.
- Re-optimizing the design for a faster cycle should recover the volume that
  the frozen d = 27 design of stage 5c lost.

### Surprised me

(Keep only the ones that are true for you.)

- From p = 1e-3 to 2e-3 the qubit count is 2.7x higher but the runtime per
  run only 12% longer; at 3e-3 it is 6.8x the qubits for 24% more time.
- The paper's rule of thumb holds within about 30% from p = 1e-4 to 2e-3 in
  my model (-28%, -14%, +12%), and breaks at 3e-3 (+46%).
- A 10x faster cycle (0.1 us) only reduces the expected volume to 0.58x,
  while a 5x faster reaction time (2 us) reduces it to 0.36x.
- Freezing the design misleads: in stage 5c a 5x faster cycle at d = 27 made
  the volume worse, but re-optimizing the design makes it better (0.68x).

### Explain to someone else

**Method.** The estimator takes the physical error rate p. The logical error
per cycle is 0.1 * (p / p_th)^((d+1)/2) with p_th = 1%, which equals the
paper's 10^-(ceil(d/2)+1) at p = 1e-3 for odd d. The level 1 distillation
error is 35 p^3 (injected states assumed to have error about p) plus a
topological part scaled with (p / 1e-3)^((d1+1)/2), and the CCZ factory's own
topological term is scaled the same way with d2. For each hardware setting
the code distances d1 and d2, the window sizes c_mul and c_exp, the runway
spacing c_sep and the padding offset are re-optimized with the paper's
objective s^1.2 * t / (1 - risk), over d1 in 5 to 45, d2 in 9 to 99,
c_mul and c_exp in 4 to 6, c_sep in 512 to 2048 and delta_off in {4, 7, 10}.

**Physical error rate (cycle 1 us, reaction 10 us).**

| p | chosen (d1, d2) | qubits | per run | expected volume | vs 1e-3 | rule of thumb |
|---|---|---|---|---|---|---|
| 1e-4 | 7, 13 | 2.3 M | 4.0 h | 0.51 Mqd | 0.09x | 0.125 |
| 3e-4 | 11, 19 | 7.4 M | 4.4 h | 1.38 | 0.24x | 0.283 |
| 1e-3 | 17, 29 | 25.6 M | 5.1 h | 5.69 | 1.00x | 1 |
| 2e-3 | 23, 41 | 68.0 M | 5.7 h | 18.58 | 3.27x | 2.93 |
| 3e-3 | 33, 55 | 173.1 M | 6.3 h | 57.99 | 10.19x | 6.995 |
| 5e-3 | no feasible design in the search ranges | | | | | |

**Reaction time (p = 1e-3, cycle 1 us).** 1 us: 16.3 M qubits, 1.9 h per
run, 1.45 Mqd (0.26x). 2 us: 22.3 M, 1.9 h, 2.06 Mqd (0.36x). 5 us: 3.66 Mqd
(0.64x). 10 us: baseline (5.69 Mqd). 20 us: 25.6 M, 8.1 h, 9.06 Mqd (1.59x).

**Cycle time (p = 1e-3, reaction 10 us).** 0.1 us: 3.29 Mqd (0.58x). 0.2 us:
3.85 Mqd (0.68x). 0.5 us: 4.61 Mqd (0.81x). 1 us: baseline. 2 us: 7.10 Mqd
(1.25x).

**Cycle x reaction, expected volume in Mqd.**

| cycle \ reaction | 2 us | 5 us | 10 us |
|---|---|---|---|
| 0.2 us | 1.26 | 2.28 | 3.85 |
| 0.5 us | 1.71 | 2.92 | 4.61 |
| 1 us | 2.06 | 3.66 | 5.69 |

**What it says.**
1. Worse hardware is paid for in qubits, not time, because the runtime is set
   by the reaction time and extra code distance mostly costs space.
2. For this design the reaction time (classical decoding and control latency)
   is a better lever than the cycle time. Moving the cycle time from 1 us
   to 0.2 us gives about 1.5x less volume, not 5x. Stage 5a noted Table 2's
   caption linking a 5x faster cycle to 5x less volume; I should reread its
   exact wording and scope before treating this as a contradiction.
3. The design has to be re-optimized for each setting; freezing it, as in
   the stage 5c exercise, gives misleading answers.

### How far to trust each result

- Most robust: the orderings (reaction beats cycle; error rate costs qubits
  more than time) and the rule-of-thumb agreement near p = 1e-3.
- Extrapolated: the p-dependence of every topological term and the 35 p^3
  distillation floor. At p >= 2e-3 the optimum uses d1 = 23 to 33, where
  the qubit count rests on my assumption that the layout width scales with
  d1, which I fitted only between d1 = 15 and 17. At p = 1e-4 the optimum is
  d1 = 7, far below any calibration point.
- Search-range edges: the reaction time 1 us row (c_sep = 2048, windows 4 and
  4) and the cycle time 0.1 us row (windows 6 and 6) sit at the edge of the
  ranges, so they are probably conservative.

### Limitations

- All results are properties of a model of the paper's design (planar grid,
  nearest-neighbor connectivity, surface code, lookup-addition arithmetic).
  No physical error rate or timing was measured from hardware.
- The topological error terms use the standard (p / p_th)^((d+1)/2) scaling
  with p_th = 1% and a prefactor of 0.1, which holds below threshold and
  becomes unreliable near it and at very small distances.
- The sensitivity analysis varies one hardware assumption at a time (plus
  the cycle x reaction grid). Connectivity, decoder speed as a separate
  parameter and the code family are not varied.
- The 25% factory share, the 14 factories per piece and the parameter ranges
  are fixed from the paper's n = 2048 design.

### Code

`estimator.py` (now with the physical error rate p), `sensitivity.py`
(re-optimizing search over hardware settings, rule-of-thumb check) and
`test_sensitivity.py` (5 tests; the full suite is 15 tests and takes about
12 seconds).

## Stage 5e (part 2): Comparison with newer published estimates

### Predicted

(What the arithmetic implies. Edit to match what I actually guessed.)

- Qubit-count reductions overstate spacetime improvements, because runtimes
  grew as qubits fell.
- At about 1 M qubits the QLDPC design should run about as fast as the 2019
  design while using far fewer qubits, if its larger points hold up.
- Estimates at a 1 ms cycle cannot be compared by qubit-days with 1 us ones.
- Neutral-atom designs with 11,000 to 14,000 qubits should be very slow for
  RSA-2048.

### Surprised me

(Keep only the ones that are true for you.)

- Gidney 2025 uses 22x fewer qubits than 2019 but runs 16x longer, so the
  volume (qubits x expected runtime) only falls 1.39x. Pinnacle's smallest
  point (98,000 qubits, about a month) uses 204x fewer qubits and runs 97x
  longer, so its volume falls 2.11x.
- Pinnacle's larger points, if they hold up, cut the volume much more:
  0.97 Mqd (139,000 qubits, a week), 0.40 Mqd (400,000, a day) and 0.33 Mqd
  (1 M, 8 hours), against 6.2 Mqd in 2019 and 4.45 Mqd in 2025. At 1 M
  qubits the runtime is about the same as 2019's 7.4 h, with 20x fewer qubits.
- I had told myself the neutral-atom paper needed "hundreds of days" at
  11,000 to 14,000 qubits. That was wrong. The paper's Figure 3b gives about
  1.0e4 days (13,255 qubits) and 4.3e4 days (11,033 qubits), i.e. decades, and
  97 days needs about 102,000 qubits with parallel Toffolis (a preliminary
  estimate). I took the earlier claim from a search snippet without checking.
- My estimator's re-optimized 2019 design (5.69 Mqd) is within 8% of the
  paper's 6.2 Mqd.

### Explain to someone else

**Why spacetime volume.** Qubit count alone is misleading because designs
trade qubits for time. The comparison uses expected volume = qubits x expected
runtime in megaqubit-days (Mqd), and only compares rows with the same
physical-error rate (1e-3), cycle time (1 us) and reaction time (10 us). The
1 ms-cycle rows are in the table but their volumes are not compared.

**Published estimates (expected runtime, RSA-2048).**

| Estimate | Qubits | Runtime | Mqd | vs 2019 |
|---|---|---|---|---|
| This project's model of the 2019 design | 25.6 M | 5.3 h | 5.69 | 0.92x |
| Gidney and Ekerå 2019 | 20 M | 7.4 h | 6.20 | 1.00x |
| Gidney 2025 | 897,864 | 4.96 d | 4.45 | 0.72x |
| Pinnacle, smallest point | 98,000 | ~1 month | 2.94 | 0.47x |
| Pinnacle, one-week point | 139,000 | ~7 d | 0.97 | 0.16x |
| Pinnacle, one-day point | 400,000 | ~1 d | 0.40 | 0.06x |
| Pinnacle, 1 M-qubit point | 1,000,000 | ~8 h | 0.33 | 0.05x |

**What changed in each design.** Gidney 2025 keeps the 2D nearest-neighbor
surface code but uses approximate residue arithmetic, yoked (denser) storage
for idle qubits, and magic state cultivation, with six factories. It reports
897,864 qubits, 12.07 h per shot, 9.2 expected shots and 4.96 days. Pinnacle
(Webster et al., arXiv:2602.11457) uses QLDPC generalized bicycle codes,
processing units with magic engines, and needs interactions across a whole
code block rather than only nearest neighbors. Cain et al. (arXiv:2603.28627)
use high-rate lifted-product qLDPC codes on reconfigurable neutral atoms with
a 1 ms cycle and non-local connectivity.

**1 ms-cycle rows (not compared by volume).** Pinnacle at 1 ms: 9.5 M qubits
for a month (13 M in version 1). Zhou et al.: 19 M qubits, about 5.6 days
(cited in other papers). Cain et al.: 11,033 qubits ~4.3e4 days; 13,255
qubits ~1.0e4 days; about 102,000 qubits 97 days.

### Verification status of each row

- Read in the paper itself: Gidney and Ekerå 2019, Gidney 2025, Pinnacle's
  smallest point (abstract and Fig. 1 caption; the 98,000 is as quoted by
  Cain et al.), and Cain et al.'s 102,000-qubit, 97-day point.
- Read from the extracted text of Cain et al.'s Figure 3b, to verify in the
  figure: the 4.3e4 and 1.0e4 day values.
- From search excerpts, to verify in Pinnacle's results table (version 2): the
  139,000, 400,000 and 1 M points and the 9.5 M qubits at 1 ms.
- Cited in other papers, not read: Zhou et al.
- Found but not read: arXiv:2605.03951 (a modular atomic processor).

### Limitations

- "Same hardware assumptions" only means the same error rate, cycle time and
  reaction time. GE19 and Gidney 2025 assume a 2D grid with nearest-neighbor
  connections; Pinnacle needs interactions across a code block; Cain et al.
  assume reconfigurable atoms. Those differences are not in the numbers.
- Pinnacle is a preprint whose numbers changed between versions (v1 to v2),
  and I have not checked whether it has been peer reviewed. The Cain et al.
  time-efficient point is called preliminary by its authors.
- Gidney 2025 itself says another order-of-magnitude reduction would need
  different physical assumptions; Pinnacle changes the code family and the
  connectivity.
- My estimator models only the 2019 architecture. This stage lines up published
  numbers and assumptions and does not reproduce the newer designs.
- Expected runtimes include retries but are reported differently by each paper
  (Gidney rounds 4.96 days up to "a week").

### Code

`published_estimates.py` (dataset with a source and verification status for
every row), `compare.py` (table, ratios and `published_estimates.csv`) and
`test_compare.py` (5 tests).

## Stage 5f: Grover on AES-128, a depth problem

### Predicted

(What the formulas imply. Edit to match what I actually guessed.)

- Grover's quadratic speedup is real but the iterations are strictly
  sequential, so AES-128 should be limited by circuit depth, not by qubits.
- The gate counts and qubit counts of Grassl et al.'s Table 5 should
  reproduce from its Tables 2 to 4 and its own formulas.
- One machine should need far longer than the age of the universe.
- Parallelizing over S machines should only help as 1/sqrt(S), so a
  one-year attack should need an enormous number of machines.
- Compared with RSA-2048's 4.45 Mqd, AES-128 should be vastly more
  expensive to attack with Grover.

### Surprised me

(Keep only the ones that are true for you.)

- Grassl et al.'s Table 5 does not reproduce exactly: the T and Clifford
  gate counts and the qubit counts match for all three key sizes (within
  0.5%), and the AES-256 depths match, but the depth mantissas of the AES-128
  and AES-192 rows look swapped (my AES-128 values 1.215 x 2^80 and
  1.328 x 2^81 equal the printed AES-192 mantissas 1.21 and 1.33, and my
  AES-192 values 1.063 and 1.162 equal the printed AES-128 ones 1.06 and
  1.16). The text of the same paper also gives the AES-192 T-count as
  3.75e36 = 1.81 x 2^114, while its table says 1.81 x 2^118 and my
  recomputation gives 6.0e35, which matches the table.
- Even if a circuit were a million times shallower, one machine would still
  need about 4.65e5 years.
- A one-year attack needs about 2.2e23 machines, and the total number of T
  gates grows from 9.2e25 to 4.3e37.

### Explain to someone else

**Source and setting.** Grassl, Langenberg, Roetteler and Steinwandt,
arXiv:1512.04965 (the 2015 version, read in full). Clifford+T gates
(Toffoli = 7 T gates), no connectivity limits, a circuit designed to
minimize qubits, not depth. With r = 3 plaintext-ciphertext pairs the
oracle runs 3 AES-128 circuits side by side. One circuit has 1,060,864 T
gates, 1,380,420 Clifford gates, T-depth 50,688, depth 110,799 and
984 qubits. The oracle needs 3 x 984 + 1 = 2,953 logical qubits. Each
Grover iteration costs 6 x 1,060,864 + 13,204 T gates, and there are
floor(pi/4 * 2^64) iterations, so 1.19 x 2^86 T gates in total.

**Lower bound on the runtime of one machine.** I assume one reaction time
(10 us) per T layer, with nothing else counted. The T-depth (recomputed as
iterations x 2 x 50,688) is 1.215 x 2^80, which gives 4.65e11 years, about
34 times the age of the universe (4.65e10 years at a 1 us reaction time).
AES-192 needs 1.75e21 years and AES-256 1.01e31 years.

**A shallower circuit.** Depth reduced 10x: 4.65e10 years; 1,000x: 4.65e8
years; 1,000,000x: 4.65e5 years. Jaques et al. (EUROCRYPT 2020) give
lower-depth oracles at the cost of more qubits, but their AES estimates
were corrected in a 2023 revision that I could not access, so this table
is a sensitivity bound, not their numbers.

**Parallelizing.** With S machines each searching a share of the keys, time
falls as 1/sqrt(S) and total work grows as sqrt(S).

| target | machines | code distance | qubits per machine* | total qubits* | total T gates |
|---|---|---|---|---|---|
| 100 years | 2.2e19 | 37 | 8.5e6 | 1.9e26 | 4.3e35 |
| 1 year | 2.2e23 | 33 | 6.8e6 | 1.5e30 | 4.3e37 |
| 1 day | 2.9e28 | 29 | 5.3e6 | 1.5e35 | 1.6e40 |
| 1 hour | 1.7e31 | 27 | 4.6e6 | 7.7e37 | 3.8e41 |

*Data patches only (no magic-state factories or routing), so these are
lower bounds.

**Capping the depth.** With a depth limit D the total number of gates is
G_seq * D_seq / D: 2^87.9 gates at depth 2^81, 2^104.9 at 2^64, 2^128.9
at 2^40. I derived this myself; it is the kind of argument behind
depth-limited security categories. I have not read NIST's own text, so its
exact formula and parameters should be checked before citing it.

**Against RSA-2048.** RSA-2048 costs about 4.45 Mqd (Gidney 2025). A
one-year AES-128 attack needs at least 1.5e30 qubits for a year, about
5e26 Mqd, roughly 1e26 times more. RSA is a space problem that new ideas
made cheaper (20 million qubits to under a million in six years). AES-128
under Grover is a depth problem: the speedup is quadratic and parallelizes
badly, so the obstacle is time.

### Limitations

- One reaction time per T layer is a lower bound. Better T-gate schemes or
  a faster reaction time would reduce it (tenfold at 1 us).
- Grassl's circuit minimizes qubits. Shallower designs exist; the corrected
  numbers of Jaques et al. were not accessible, so only the sensitivity
  table above covers them.
- Data patches only: no factories, routing or connectivity limits, and the
  error heuristic from stage 5b is used at very small error rates.
- Grover needs the number of solutions to be known (here 1, with 3 pairs
  making the key unique).
- This covers key search only. "Infeasible in this model" is not a security
  proof, and other attacks on AES are not considered.
- I used my recomputed depths, not the printed Table 5 values for AES-128
  and AES-192; they differ by about 13%, which does not change the
  conclusions. I read only the 2015 version, so a later version may fix the
  table.

### Code

`aes_grover.py` (Grassl's tables, recomputation of Table 5, runtime lower
bounds, parallelization and depth-cap tradeoffs) and `test_aes_grover.py`
(8 tests; the full suite is 28 tests).