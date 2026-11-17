"""Stage 6a: public hardware data, with demonstrated results kept apart from roadmap targets.

Every row records its KIND, its DATE, its SOURCE and how well that source was checked:
  kind "demonstrated"    a measured result reported by the source
  kind "roadmap target"  a plan with a date; a statement of intent, not a result
  source_quality:
    "peer-reviewed paper (excerpt)"  published paper; only an abstract or excerpt returned by search was read
    "organization release (excerpt)" the organization's own press release or university release, read as a search excerpt
    "secondary report"               a news outlet or aggregator reporting someone else's result or plan
None of these pages was opened in full for this stage. Verify a row against its source before citing it.
Data collected 2026-11-17. Coverage is partial: no Google roadmap, Microsoft, PsiQuantum, Rigetti or others.
"""

DEMONSTRATED = "demonstrated"
ROADMAP = "roadmap target"
PAPER = "peer-reviewed paper (excerpt)"
ORG = "organization release (excerpt)"
SECONDARY = "secondary report"

ROWS = [
    # ---- Google Quantum AI, Willow (superconducting) ----
    dict(key="GOOG-eps7", org="Google Quantum AI", platform="superconducting", kind=DEMONSTRATED,
         metric="logical_error_per_round", value=1.43e-3, unit="per cycle", date="2024-12-09",
         source="https://arxiv.org/abs/2408.13687", source_quality=PAPER,
         note="Distance-7 surface code memory, 101 qubits (49 data, 48 measure, 4 leakage removal) on a 105-qubit "
              "processor; 0.143% +- 0.003% per cycle (neural-network decoder). Nature, doi 10.1038/s41586-024-08449-y."),
    dict(key="GOOG-lambda", org="Google Quantum AI", platform="superconducting", kind=DEMONSTRATED,
         metric="lambda", value=2.14, unit="suppression per +2 in distance", date="2024-12-09",
         source="https://arxiv.org/abs/2408.13687", source_quality=PAPER,
         note="Lambda = 2.14 +- 0.02 (neural-network decoder; 2.04 with ensembled matching)."),
    dict(key="GOOG-cycle", org="Google Quantum AI", platform="superconducting", kind=DEMONSTRATED,
         metric="cycle_us", value=1.1, unit="microseconds", date="2024-12-09",
         source="https://arxiv.org/abs/2408.13687", source_quality=PAPER, note="Surface code cycle duration."),
    dict(key="GOOG-decoder", org="Google Quantum AI", platform="superconducting", kind=DEMONSTRATED,
         metric="decoder_latency_us", value=63.0, unit="microseconds", date="2024-12-09",
         source="https://arxiv.org/abs/2408.13687", source_quality=PAPER,
         note="Average real-time decoder latency at distance 5 on the 72-qubit processor, up to a million cycles. "
              "Larger distances need more decoding."),
    dict(key="GOOG-floor", org="Google Quantum AI", platform="superconducting", kind=DEMONSTRATED,
         metric="cycles_between_correlated_errors", value=3e9, unit="cycles", date="2024-12-09",
         source="https://arxiv.org/abs/2408.13687", source_quality=PAPER,
         note="Repetition codes up to distance 29 are limited by rare correlated error events, about once per hour "
              "or 3e9 cycles (a floor near 3e-10 per cycle)."),
    dict(key="GOOG-qubits", org="Google Quantum AI", platform="superconducting", kind=DEMONSTRATED,
         metric="physical_qubits", value=105, unit="qubits", date="2024-12-09",
         source="https://arxiv.org/abs/2408.13687", source_quality=PAPER, note="Willow processor used for the distance-7 code."),
    # ---- IBM (superconducting) ----
    dict(key="IBM-nighthawk", org="IBM", platform="superconducting", kind=DEMONSTRATED,
         metric="physical_qubits", value=120, unit="qubits", date="2025-11-12",
         source="https://www.tomshardware.com/tech-industry/semiconductors/ibm-unveils-new-120-qubit-processor-and-software-stack",
         source_quality=SECONDARY, note="Nighthawk, 120-qubit square-lattice processor, announced 2025-11-12."),
    dict(key="IBM-starling", org="IBM", platform="superconducting qLDPC", kind=ROADMAP,
         metric="logical_qubits", value=200, unit="logical qubits (and 1e8 'quantum operations')", date="2025-06-10",
         target_year=2029,
         source="https://thequantuminsider.com/2025/06/10/ibm-offers-roadmap-toward-large-scale-fault-tolerant-quantum-computer-at-new-ibm-quantum-data-center/",
         source_quality=SECONDARY,
         note="Starling: 200 logical qubits, 100 million quantum operations, Poughkeepsie. Announced 2025-06-10 "
              "(reproduction of IBM's release). Delivery status as of 2026-11 not checked."),
    dict(key="IBM-bluejay", org="IBM", platform="superconducting qLDPC", kind=ROADMAP,
         metric="logical_qubits", value=2000, unit="logical qubits (and 1e9 'quantum operations')", date="2025-06-10",
         target_year=2033,
         source="https://thequantuminsider.com/2025/06/10/ibm-offers-roadmap-toward-large-scale-fault-tolerant-quantum-computer-at-new-ibm-quantum-data-center/",
         source_quality=SECONDARY, note="Blue Jay: 2,000 logical qubits, 1 billion operations, 2033 or later."),
    # ---- Quantinuum (trapped ions) ----
    dict(key="QTNM-phys", org="Quantinuum", platform="trapped ions", kind=DEMONSTRATED,
         metric="physical_qubits", value=98, unit="qubits", date="2025-11-05",
         source="https://thequantuminsider.com/2025/11/06/illuminating-helios-quantinuums-shiny-new-quantum-computer-gets-sunny-reception/",
         source_quality=SECONDARY, note="Helios, 98 fully connected trapped-ion qubits."),
    dict(key="QTNM-2q", org="Quantinuum", platform="trapped ions", kind=DEMONSTRATED,
         metric="two_qubit_error", value=1 - 0.99921, unit="error per gate", date="2025-11-05",
         source="https://thequantuminsider.com/2025/11/06/illuminating-helios-quantinuums-shiny-new-quantum-computer-gets-sunny-reception/",
         source_quality=SECONDARY, note="Two-qubit gate fidelity 99.921% across all pairs (company figure); single-qubit 99.9975%."),
    dict(key="QTNM-eps7", org="Quantinuum", platform="trapped ions", kind=DEMONSTRATED,
         metric="logical_error_per_round", value=5e-6, unit="per round", date="2026-10-19",
         source="https://postquantum.com/industry-news/quantinuum-color-code-helios/", source_quality=SECONDARY,
         note="Color code on Helios: 5.5e-4 (d=3), 3.8e-5 (d=5), 5e-6 (d=7) per round; 13, 37, 73 physical qubits per "
              "logical qubit. Company announcement of 2026-10-19; the underlying paper was not read."),
    dict(key="QTNM-gate", org="Quantinuum", platform="trapped ions", kind=DEMONSTRATED,
         metric="logical_two_qubit_error", value=7e-5, unit="per logical gate (d=5)", date="2026-10-19",
         source="https://postquantum.com/industry-news/quantinuum-color-code-helios/", source_quality=SECONDARY,
         note="Logical two-qubit Clifford error 7e-4 (d=3) and 7e-5 (d=5) against 9.5e-4 for unencoded qubits; fitted "
              "Lambda about 9 (+8, -4). Distance-7 gates not run: two 73-qubit blocks do not fit on 98 qubits."),
    dict(key="QTNM-lambda", org="Quantinuum", platform="trapped ions", kind=DEMONSTRATED,
         metric="lambda", value=9.0, unit="fitted suppression, logical gates, color code", date="2026-10-19",
         source="https://postquantum.com/industry-news/quantinuum-color-code-helios/", source_quality=SECONDARY,
         note="Uncertainty +8 / -4, from only two distances; a color code, so not directly comparable with a surface-code Lambda."),
    dict(key="QTNM-apollo", org="Quantinuum", platform="trapped ions", kind=ROADMAP,
         metric="logical_qubits", value=100, unit="'hundreds' of logical qubits, 'thousands' of physical", date="2025-11-05",
         target_year=2029,
         source="https://www.hpcwire.com/2025/11/05/quantinuum-introduces-helios-quantum-system-as-roadmap-advances-toward-apollo/",
         source_quality=SECONDARY,
         note="Apollo: universal fault-tolerant system planned for 2029 with thousands of physical and hundreds of "
              "logical qubits; Sol in 2027. 'Hundreds' is recorded as 100 (a lower bound, not a quote). The company "
              "states it may not achieve the roadmap on this timeline or at all."),
    # ---- IonQ (trapped ions) ----
    dict(key="IONQ-2q", org="IonQ", platform="trapped ions (electronic qubit control)", kind=DEMONSTRATED,
         metric="two_qubit_error", value=1e-4, unit="error per gate", date="2025-10-21",
         source="https://ionq.com/news/ionq-achieves-landmark-result-setting-new-world-record-in-quantum-computing",
         source_quality=ORG, note="99.99% two-qubit gate fidelity on prototypes in IonQ's R&D labs; previous record 99.97% (2024)."),
    dict(key="IONQ-2030", org="IonQ", platform="trapped ions (electronic qubit control)", kind=ROADMAP,
         metric="physical_qubits", value=2_000_000, unit="physical qubits (and 80,000 logical)", date="2025-10-21",
         target_year=2030,
         source="https://ionq.com/news/ionq-announces-third-quarter-2025-financial-results", source_quality=ORG,
         note="Company target: 2 million physical qubits and 80,000 logical qubits in 2030; 256-qubit systems to be "
              "demonstrated in 2026. No error rates, speeds or run times are stated in the excerpts."),
    # ---- Neutral atoms (Harvard / MIT / QuEra, Caltech) ----
    dict(key="HARV-448", org="Harvard / MIT / QuEra", platform="neutral atoms", kind=DEMONSTRATED,
         metric="physical_qubits", value=448, unit="atoms", date="2025-11-03",
         source="https://doi.org/10.1038/s41586-025-09848-5", source_quality=PAPER,
         note="Bluvstein et al., Nature (accepted 2025-11-03): arrays of up to 448 atoms implementing a universal "
              "fault-tolerant architecture; dozens of logical qubits and hundreds of logical teleportations."),
    dict(key="HARV-3000", org="Harvard / MIT / QuEra", platform="neutral atoms", kind=DEMONSTRATED,
         metric="continuous_hours", value=2.0, unit="hours (3,000+ qubits)", date="2025-09-29",
         source="https://content.news.harvard.edu/gazette/story/2025/09/clearing-significant-hurdle-to-quantum-computing/",
         source_quality=ORG, note="Chiu et al., Nature 2025: more than 3,000 qubits operated continuously for more than "
                                "two hours; more than 50 million atoms cycled through."),
    dict(key="CALT-6100", org="Caltech", platform="neutral atoms", kind=DEMONSTRATED,
         metric="physical_qubits", value=6100, unit="atoms", date="2025-09",
         source="https://mappingignorance.org/2025/10/01/a-3000-qubit-system-capable-of-continuous-operation/",
         source_quality=SECONDARY, note="6,100-atom tweezer array that ran for less than 13 seconds, as reported by a secondary source."),
]

DEMO_CUTOFF = "2026-11-17"