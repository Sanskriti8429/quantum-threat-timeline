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

### Surprised me

### Explain to someone else