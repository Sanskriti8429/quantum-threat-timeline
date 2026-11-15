# Quantum Threat Timeline

Resource-cost benchmarking of Shor's and Grover's algorithms against real-world
cryptosystems (RSA-2048, AES-128): implemented from first principles, validated
against published resource estimates, and projected against current quantum
hardware trajectories.

## Overview

Public claims about quantum computers breaking encryption range from hype to
dismissal, and published resource estimates for the same target differ by
orders of magnitude depending on assumptions. This project builds a transparent,
parametric resource-estimation model, checks it against a known published
result before trusting it, and reports where estimates disagree and why.

## Research question

Given realistic error-correction overheads, how many physical qubits and how
much runtime would a fault-tolerant quantum computer need to break RSA-2048 or
AES-128, and how does that compare with current hardware trajectories?

## Progress

- [x] Stage 1: Classical core of Shor's algorithm (order finding, factor extraction)
- [x] Stage 2a: Math prerequisites (complex numbers, unitaries, tensor products)
- [x] Stage 2b: Gates, a multi-qubit circuit simulator, and the QFT, built by hand in NumPy
- [x] Stage 3a: Shor's period-finding for N = 15 implemented by hand in NumPy
- [x] Stage 3b: Shor's algorithm in Qiskit, factoring small semiprimes, cross-checked against 3a
- [x] Stage 4a: Grover's algorithm in NumPy (oracle, diffusion, optimal iteration count, √N scaling up to 2^20)
- [x] Stage 4b: Grover's key search on a toy symmetric cipher, with measured query counts against classical brute force
- [x] Stage 5a: Read Gidney-Ekerå (2019) and summarize its cost model
- [x] Stage 5b: Error-correction basics behind the model (logical vs. physical qubits, code distance, logical error rate, magic-state factories)
- [x] Stage 5c: Estimator v0 that reproduces the paper's section 2 hand calculations
- [ ] Stage 5d: Full parameter search reproducing Table 3 rows (n = 1024 to 4096), with divergences documented
- [ ] Stage 5e: Sensitivity analysis (physical error rate, cycle time, reaction time, code distance) and comparison with newer published estimates
- [ ] Stage 5f: Grover/AES-128 counterpart: oracle cost and sequential depth
- [ ] Stage 5g (optional): Neural decoder for a small error-correcting code, compared against a classical decoder, with results fed into the estimator
- [ ] Stage 6: Interactive dashboard and written report, including implications for post-quantum migration

## Methodology

- **Built from first principles.** Algorithms are implemented directly, not
  called from library shortcuts, so every step can be explained and tested.
- **Validate before extending.** The estimator must reproduce published
  figures before any projection is built on it. Discrepancies are reported,
  not tuned away.
- **Parametric, not point estimates.** Error-correction code family, physical
  error rate, cycle time, and connectivity are explicit inputs. Results report
  both qubit count and runtime, since the two trade off.
- **Limitations documented as found.** Each stage records what its results do
  and do not show.

## Getting started

```bash
git clone https://github.com/Sanskriti8429/quantum-threat-timeline.git
cd quantum-threat-timeline
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
python shor_classical.py
```

Stage 3b needs Qiskit. It was tested on Google Colab (Python 3.13); on some
locked-down Windows machines Qiskit's compiled library is blocked.

## Results so far

| Stage | Result |
|---|---|
| 1 | Classical reduction: 6/7, 6/11 and 18/23 of coprime bases factor N = 15, 21 and 35 (N = 8 and N = 9 fail, as expected) |
| 3a/3b | N = 15 (8 counting qubits): peaks at 0, 64, 128, 192 with probability 0.25 each, 0.75 success per shot. N = 21 (10 counting qubits): 0.818 per attempt, with a ceiling of 5/6. The Qiskit circuits match the hand-built simulator in every case tested |
| 3b | Hard-wired N = 15 circuit (a = 7, 8 counting qubits): 112 CNOTs, depth 119 after transpiling. This does not extrapolate to RSA scale (see limitations) |
| 4a/4b | Grover finds the key of a toy cipher with 12 to 804 oracle queries for 8 to 20 key bits. Measured log-log slopes against search-space size: 0.504 for Grover and 1.004 for classical brute force |
| 5c | Estimator v0 reproduces Gidney-Ekerå's section 2 numbers for n = 2048 (6.9 h, 26.5% topological error, 22.3 M qubits, retry risk 31.9% against 31%). With unrounded formulas the per-run runtime is 5.0 h against Table 3's 5.1 h, and Toffoli counts are within 5% of Table 1 for n = 1024 to 3072. The retry risk (24.5% against 31%) is not yet reproduced (stage 5d) |

## Known limitations

- Stage 1 uses a brute-force order finder as a stand-in for the quantum step,
  so it demonstrates the classical reduction, not a quantum speedup.
- The reduction requires N to be odd and not a prime power. For N = 9 no
  coprime base succeeds, and for N = 8 it returns the non-prime factor 4.
- Stage 3a's modular exponentiation is a lookup-table permutation, not a
  gate-level circuit, so it demonstrates correctness but gives no honest
  gate counts for RSA-scale arithmetic. Stage 5 addresses this.
- N = 15 is a degenerate demonstration (all its orders are powers of two);
  N = 21 shows the realistic dependence of success on register size.
- Stage 3b's gate-level N = 15 circuit is hard-wired and skips
  multiplications that are trivial for this N, so its gate counts do not
  extrapolate to RSA-scale factoring.
- Stages 2 to 4 simulate full state vectors (about 25 qubits at most) and
  model no noise or error correction.
- Stage 4a simulates the oracle by flipping the sign of a known index, so it
  demonstrates the query count, not the cost of building a real oracle.
- Grover's speedup is quadratic, needs the number of marked items to be well
  below half the search space, and parallelizes poorly.
- Stage 4b searches the keys of a toy cipher whose oracle is built by
  classical evaluation, so it demonstrates the query count, not the cost
  of a reversible cipher circuit. The 128-bit and 256-bit rows are formula
  extrapolations, not simulations.
- Grover's iteration count depends on the number of solutions: assuming one
  solution when there are 18 dropped the success probability to 0.14.
- Stage 5b uses a heuristic logical-error rule (valid only below threshold)
  and an idealized distillation formula, not the paper's factory model.
- Stage 5c implements the paper's simplified model without its parameter
  search: one code distance for the whole machine, a fixed layout and a fixed
  distillation error per CCZ state. The retry risk is about 25% against the
  paper's 31%, and qubit counts overshoot by 12% to 15% where the paper uses
  a level 1 distance of 15.
- The paper's Eq. (2) is printed with 2^(c_exp + c_pad) where its own
  numbers require 2^(c_exp + c_mul); the estimator uses the latter.