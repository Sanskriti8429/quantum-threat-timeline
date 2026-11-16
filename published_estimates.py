"""Published resource estimates for factoring RSA-2048, as quoted in the papers (stage 5e, part 2).

Every row records WHERE its numbers come from. `source_quality`:
  "primary text"       read in the paper itself (this project fetched and read it)
  "cited in another"   quoted by a different paper that cites it; not read directly
  "search excerpt"     seen in a search-result excerpt of the paper; verify in the paper before citing
Runtimes are EXPECTED runtimes in days unless the note says otherwise.
"""

ROWS = [
    dict(key="GE19", label="Gidney & Ekera 2019", arxiv="1905.09749v3",
         platform="surface code", connectivity="2D grid, nearest neighbor",
         p=1e-3, cycle_us=1.0, reaction_us=10.0,
         qubits=20e6, runtime_days=0.31,
         source_quality="primary text",
         note="Table 3, n = 2048: 20 M qubits, 5.1 h per run, retry risk 31%, 0.31 days expected, "
              "5.9 Mqd expected volume. Title rounds to 8 hours."),
    dict(key="G25", label="Gidney 2025", arxiv="2505.15917v1",
         platform="surface code + yoked cold storage + cultivation", connectivity="2D grid, nearest neighbor",
         p=1e-3, cycle_us=1.0, reaction_us=10.0,
         qubits=897_864, runtime_days=4.96,
         source_quality="primary text",
         note="Sec. 3.2: 897,864 physical qubits (reported as under one million), 12.07 h per shot, "
              "9.2 expected shots, 93.3% of shots free of logical error, 4.96 days (rounded up to a week in the prose). "
              "6.5e9 Toffolis, 1,409 logical qubits at peak."),
    dict(key="WEB-98k", label="Pinnacle (Webster et al. 2026), smallest point", arxiv="2602.11457",
         platform="QLDPC (generalized bicycle codes)", connectivity="non-local within code blocks",
         p=1e-3, cycle_us=1.0, reaction_us=10.0,
         qubits=98_000, runtime_days=30.0,
         source_quality="primary text",
         note="Abstract/intro (fewer than 100,000 qubits) and Fig. 1 caption (one month); the 98,000 figure is "
              "as quoted by Cain et al. 2026. One processing unit. A preprint (v1 12 Feb 2026, v2 5 May 2026)."),
    dict(key="WEB-139k", label="Pinnacle, one-week point", arxiv="2602.11457",
         platform="QLDPC (generalized bicycle codes)", connectivity="non-local within code blocks",
         p=1e-3, cycle_us=1.0, reaction_us=10.0,
         qubits=139_000, runtime_days=7.0,
         source_quality="search excerpt",
         note="Reported as about one week with 139 thousand qubits. Verify in the paper's results table (v2)."),
    dict(key="WEB-400k", label="Pinnacle, one-day point", arxiv="2602.11457",
         platform="QLDPC (generalized bicycle codes)", connectivity="non-local within code blocks",
         p=1e-3, cycle_us=1.0, reaction_us=10.0,
         qubits=400_000, runtime_days=1.0,
         source_quality="search excerpt",
         note="Reported as about one day with 400 thousand qubits. Verify in the paper (v2)."),
    dict(key="WEB-1M", label="Pinnacle, one-million-qubit point", arxiv="2602.11457",
         platform="QLDPC (generalized bicycle codes)", connectivity="non-local within code blocks",
         p=1e-3, cycle_us=1.0, reaction_us=10.0,
         qubits=1_000_000, runtime_days=8 / 24,
         source_quality="search excerpt",
         note="Reported as an expected eight hours with one million qubits (v2 text). "
              "Verify in the paper."),
    dict(key="WEB-1ms", label="Pinnacle at a 1 ms cycle (neutral-atom-like)", arxiv="2602.11457",
         platform="QLDPC (generalized bicycle codes)", connectivity="non-local within code blocks",
         p=1e-3, cycle_us=1000.0, reaction_us=10000.0,
         qubits=9_500_000, runtime_days=30.0,
         source_quality="search excerpt",
         note="One month with 9.5 M qubits at p = 1e-3 in v2; the first version said 13 M. Estimates changed "
              "between versions."),
    dict(key="ZHOU25", label="Zhou et al. 2025 (transversal, atom arrays)", arxiv="(ISCA 2025)",
         platform="surface code, transversal gates", connectivity="non-local (reconfigurable atoms)",
         p=None, cycle_us=1000.0, reaction_us=None,
         qubits=19e6, runtime_days=5.6,
         source_quality="cited in another",
         note="19 M qubits, d = 27; physical error rate not checked. Cited as about one week by Cain et al. "
              "and as 5.6 days by two other papers. Not read directly."),
    dict(key="ORA-se", label="Cain et al. 2026, space-efficient", arxiv="2603.28627",
         platform="high-rate lifted-product qLDPC, neutral atoms", connectivity="non-local, reconfigurable atoms",
         p=1e-3, cycle_us=1000.0, reaction_us=None,
         qubits=11_033, runtime_days=4.3e4,
         source_quality="primary text",
         note="Fig. 3b annotation as I read it from extracted text (verify in the figure). Sequential "
              "Toffolis; lp(3,7)24 memory; circuit from Gidney 2025."),
    dict(key="ORA-bal", label="Cain et al. 2026, balanced", arxiv="2603.28627",
         platform="high-rate lifted-product qLDPC, neutral atoms", connectivity="non-local, reconfigurable atoms",
         p=1e-3, cycle_us=1000.0, reaction_us=None,
         qubits=13_255, runtime_days=1.0e4,
         source_quality="primary text",
         note="Fig. 3b annotation as I read it (verify in the figure)."),
    dict(key="ORA-par", label="Cain et al. 2026, time-efficient (P = 1,160)", arxiv="2603.28627",
         platform="high-rate lifted-product qLDPC, neutral atoms", connectivity="non-local, reconfigurable atoms",
         p=1e-3, cycle_us=1000.0, reaction_us=None,
         qubits=102_000, runtime_days=97.0,
         source_quality="primary text",
         note="Text and conclusion: about 102,000 qubits, 97 days. The authors call it preliminary: it "
              "assumes P Toffolis run in parallel using high-rate surgery, and uses the 2019 circuit."),
]

SAME_AS_GE19 = dict(p=1e-3, cycle_us=1.0, reaction_us=10.0)


def same_hardware_assumptions(row):
    return all(row[k] == v for k, v in SAME_AS_GE19.items())


def qubit_days(row):
    """Qubits times expected runtime, in megaqubit-days. NOT comparable across different cycle times."""
    return row["qubits"] * row["runtime_days"] / 1e6