# Quantum Threat Timeline

Resource-cost benchmarking of Shor's and Grover's algorithms against real-world cryptosystems (RSA-2048, AES-128)- implemented from first principles, validated against published resource estimates, and projected against current quantum hardware trajectories.

## Overview

Public claims about quantum computers breaking encryption range from hype to dismissal, and published resource estimates for the same target differ by orders of magnitude depending on assumptions. This project builds a transparent, parametric resource-estimation model, checks it against a lnown published result before testing it, and reports where estimates disagree and why.

## Research question

Given realistic error-correction overheads, how many physical qubits and how much runtime would a fault-tolerant quantum computer need to break RSA-2048 or AES-128, and how dpes that compare with the current hardware trajectories?

## Progress

- [x] Stage 1: Classical core of Shor's algorithm (order finding, factor extraction)
- [ ] Stage 2: Math prerequisites and quantum building blocks (qubits, gates, tensor products, QFT) in a hand-built NumPy simulator
- [ ] Stage 3a: Shor's period-finding for N = 15 implemented by hand in NumPy
- [ ] Stage 3b: Shor's algorithm in Qiskit, factoring small semiprimes, cross-checked against 3a
- [ ] Stage 4: Grover's algorithm in NumPy, then on a toy symmetric cipher, showing the empirical √N speedup
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
.venv\Scripts\activate
python shor_classical.py
```

## Results

To be added as stages are completed.

## Known limitations

- Stage 1 uses a brute-force order finder as a stand-in for the quantum step,
  so it demonstrates the classical reduction, not a quantum speedup.
- The reduction requires N to be odd and not a prime power. For N = 9 no
  coprime base succeeds, and for N = 8 it returns the non-prime factor 4.