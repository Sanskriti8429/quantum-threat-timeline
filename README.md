# Quantum Threat Timeline

Resource-cost benchmarking of Shor's and Grover's algorithms against real-world cryptosystems (RSA-2048, AES-128)- implemented from first principles, validated against published resource estimates, and projected against current quantum hardware trajectories.

## Overview

Public claims about quantum computers breaking encryption range from hype to dismissal, and published resource estimates for the same target differ by orders of magnitude depending on assumptions. This project builds a transparent, parametric resource-estimation model, checks it against a lnown published result before testing it, and reports where estimates disagree and why.

## Research question

Given realistic error-correction overheads, how many physical qubits and how much runtime would a fault-tolerant quantum computer need to break RSA-2048 or AES-128, and how dpes that compare with the current hardware trajectories?

## Progress

- [x] Stage 1: Classical core of Shor's algorithm (order finding, factor extraction)
- [x] Stage 2: Math prerequisites and quantum building blocks (qubits, gates, tensor products, QFT) in a hand-built NumPy simulator
- [x] Stage 3a: Shor's period-finding for N = 15 implemented by hand in NumPy
- [x] Stage 3b: Shor's algorithm in Qiskit, factoring small semiprimes, cross-checked against 3a
- [x] Stage 4a: Grover's algorithm in NumPy (oracle, diffusion, optimal iteration count, √N scaling up to 2^20)
- [x] Stage 4b: Grover's key search on a toy symmetric cipher, with measured query counts against classical brute force
- [ ] Stage 5: Fault-tolerant resource estimator (physical qubits, gate counts, circuit depth, runtime), validated against Gidney-Ekerå (2019), with sensitivity analysis over code distance, physical error rate, and cycle time
- [ ] Stage 5b: Neural decoder for a small error-correcting code, compared against a classical decoder
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

## Results

To be added as stages are completed.

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
- Stages 3a/3b simulate full state vectors (about 25 qubits at most) and
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