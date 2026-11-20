# Quantum Threat Timeline

Resource-cost benchmarking of Shor's and Grover's algorithms against real-world
cryptosystems (RSA-2048, AES-128): implemented from first principles, validated
against published resource estimates, and projected against current quantum
hardware trajectories.

**Dashboard:** https://sanskriti8429.github.io/quantum-threat-timeline/

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
- [x] Stage 5d: Full parameter search reproducing Table 3 rows (n = 1024 to 4096), with divergences documented
- [x] Stage 5e (part 1): Sensitivity analysis over physical error rate, cycle time and reaction time, re-optimizing the design at each setting
- [x] Stage 5e (part 2): Comparison with newer published estimates (Gidney 2025; 2026 QLDPC and neutral-atom results)
- [x] Stage 5f: Grover/AES-128 counterpart: oracle cost and sequential depth
- [ ] Stage 5g (optional): Neural decoder for a small error-correcting code, compared against a classical decoder, with results fed into the estimator
- [x] Stage 6a: Public hardware roadmap data (qubit counts, error rates, cycle times), each with a source and verification status
- [x] Stage 6b: Interactive dashboard: published estimates, the estimator, and roadmap-based timeline scenarios
- [ ] Stage 6c: Written report, including implications for post-quantum migration

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

To run all tests (45 at the time of writing):

```bash
python -m unittest discover -p "test_*.py"
```

To rebuild the dashboard after changing any data:

```bash
python export_sensitivity.py
python compare.py
python distance_to_threat.py
python build_dashboard.py
```

The page is `docs/index.html` and works when opened from a file.

## Results so far

| Stage | Result |
|---|---|
| 1 | Classical reduction: 6/7, 6/11 and 18/23 of coprime bases factor N = 15, 21 and 35 (N = 8 and N = 9 fail, as expected) |
| 3a/3b | N = 15 (8 counting qubits): peaks at 0, 64, 128, 192 with probability 0.25 each, 0.75 success per shot. N = 21 (10 counting qubits): 0.818 per attempt, with a ceiling of 5/6. The Qiskit circuits match the hand-built simulator in every case tested |
| 3b | Hard-wired N = 15 circuit (a = 7, 8 counting qubits): 112 CNOTs, depth 119 after transpiling. This does not extrapolate to RSA scale (see limitations) |
| 4a/4b | Grover finds the key of a toy cipher with 12 to 804 oracle queries for 8 to 20 key bits. Measured log-log slopes against search-space size: 0.504 for Grover and 1.004 for classical brute force |
| 5c | Estimator v0 reproduces Gidney-Ekerå's section 2 numbers for n = 2048 (6.9 h, 26.5% topological error, 22.3 M qubits, retry risk 31.9% against 31%). With unrounded formulas the per-run runtime is 5.0 h against Table 3's 5.1 h, and Toffoli counts are within 5% of Table 1 for n = 1024 to 3072. The retry risk of the section 2 defaults (24.5% against 31%) was explained in stage 5d |
| 5d | With a reconstructed factory-error model (calibrated on two published anchors), the estimator reproduces Gidney-Ekerå's Table 3 rows: Toffolis within 5%, runtimes within 8%, qubits within 6%, retry risks within 3 points (n = 2048: 34% against 31%). A grid search of 28,350 parameter sets per n puts the paper's chosen parameters in the top 0.2%, within 3.6% of my optimum |
| 5e | Re-optimized for each hardware setting (n = 2048): worse physical error rates cost qubits, not time (2x10^-3: 2.7x the qubits for 12% more runtime per run). The paper's rule of thumb holds within about 30% from p = 10^-4 to 2x10^-3. A 5x faster reaction time reduces the expected volume to 0.36x, a 5x faster cycle only to 0.68x. At p = 5x10^-3 no feasible design exists in the search ranges |
| 5e (2) | Qubit-count headlines overstate spacetime gains: Gidney 2025 uses 22x fewer qubits than 2019 but its volume (qubits x expected runtime) is only 1.4x lower; the smallest Pinnacle QLDPC point uses 204x fewer qubits for 2.1x lower volume. Pinnacle's larger points (1 M qubits, about 8 hours) suggest up to about 19x lower volume, pending verification. Neutral-atom RSA-2048 designs with 11,000 to 13,000 qubits take decades; about 102,000 qubits gets to 97 days under parallelism assumptions |
| 5f | Grover on AES-128 (circuit of Grassl et al. 2016): 2,953 logical qubits but 1.19x2^86 T gates and a depth of about 2^81. One machine needs at least 4.65x10^11 years (34x the age of the universe) even assuming only one 10 us reaction time per T layer; a one-year attack needs about 2x10^23 machines and at least 1.5x10^30 physical qubits. A depth problem, unlike RSA, and about 10^26 times RSA-2048's cost in qubit-days. Two inconsistencies were found in the source's own Table 5 |
| 6a | Distance to threat (public data collected 2026-11-17): the smallest published qubit requirement is 16x the largest array demonstrated (6,100 atoms, under 13 s) and 933x Google's 105 qubits. The best logical error per round (5x10^-6, Quantinuum) is 9.7 orders of magnitude from the 10^-15 the estimates need (Google surface code: 12.2). Google's measured suppression per distance step (2.14) is 4.7x weaker than the estimates' model, and its 63 us decoder latency raises the estimated volume 3.8x. Roadmap targets are listed separately from demonstrations and give no date |
| 6b | A static dashboard with a JavaScript port of the estimator: dials for error rate, reaction time and cycle time recompute the cheapest RSA-2048 design live and compare it with the machines actually built, the published designs, and company roadmaps. It states that it gives no date, and checks its own port against the Python results on load |

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
  distillation error per CCZ state. Its retry risk (about 25% against the
  paper's 31%) differs because Table 3's n = 2048 row uses a level 1 distance
  of 15, as stage 5d showed.
- The paper's Eq. (2) is printed with 2^(c_exp + c_pad) where its own
  numbers require 2^(c_exp + c_mul); the estimator uses the latter.
- Stage 5d's factory error model and layout are reconstructions (two
  calibration anchors, assumed falloff rates, a footprint fitted to two Table 3
  rows), because the authors' spreadsheet and script were unavailable. The
  paper's parameter choices sit near the optimum of the search, but the
  objective is flat there, so this is weak evidence.
- Since stage 5e the estimator takes the physical error rate as an input, but
  its dependence on it is an extrapolation (the standard error-suppression
  scaling and an assumed 35p^3 distillation floor), and its qubit counts at
  p >= 2x10^-3 rest on a factory footprint assumption fitted only between
  d1 = 15 and 17. Orderings are more trustworthy than absolute numbers away
  from p = 10^-3.
- All estimates are for one architecture (planar surface code with
  nearest-neighbor connectivity); other codes and hardware are compared in
  part 2, not modeled.
- Stage 5e part 2 compares published numbers only: the estimator models just
  the 2019 architecture. Three Pinnacle points and the neutral-atom
  Figure 3b values are flagged as not yet verified against the papers, and
  designs with different connectivity assumptions are compared only through
  their quoted error rate, cycle time and reaction time.
- Estimates from preprints change between versions (Pinnacle's 1 ms design
  went from 13 M to 9.5 M qubits), so every figure carries its version.
- Stage 5f uses the 2015 circuit of Grassl et al., which minimizes qubits;
  lower-depth oracles exist (Jaques et al.) but their corrected estimates
  were not accessible, so a sensitivity table stands in for them. Physical
  figures are lower bounds (no factories, routing or connectivity limits).
- The source's own Table 5 has depth mantissas that look swapped between
  AES-128 and AES-192; this project uses recomputed values.
- Stage 6a's hardware data comes from search excerpts of papers, company
  releases and press coverage; no page was opened in full, and coverage of
  vendors is partial. Roadmap rows are statements of intent and are kept
  apart from demonstrated results. Several rows (the Quantinuum October 2026
  paper, IBM's 2026 delivery status, the Caltech atom count) still need
  checking against their sources.
- Hardware comparisons across platforms are loose (different codes, speeds
  and noise models), and extrapolating measured error suppression to 10^-15
  assumes no noise floors, which Google's own data already shows.
- The dashboard's model is a JavaScript port of `estimator.py`, checked on the
  page against the Python export at five sampled points. It uses a reduced
  search grid, and its "open items" list shows which rows are still unverified.