import csv
import tempfile
import unittest
from pathlib import Path

from build_dashboard import FILES, build, load


def rows(name):
    with open(name, newline="") as f:
        return list(csv.DictReader(f))


class TestDashboardBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.index = build(".", cls.tmp.name, built="2026-11-18")
        cls.html = cls.index.read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_placeholders_replaced_and_page_is_self_contained(self):
        self.assertNotIn("__DATA__", self.html)
        self.assertNotIn("__BUILT__", self.html)
        self.assertIn("Built 2026-11-18", self.html)
        self.assertEqual(self.html.count("</script>"), 1)          # the data cannot close the script early
        self.assertNotIn("<script src", self.html)
        self.assertNotIn('rel="stylesheet"', self.html)

    def test_all_rows_are_embedded(self):
        data = load(".")
        self.assertEqual(len(data["estimates"]), len(rows("published_estimates.csv")))
        self.assertEqual(len(data["hardware"]), len(rows("hardware_status.csv")))
        self.assertEqual(len(data["sensitivity"]), len(rows("sensitivity.csv")))
        for key in ("GE19", "G25", "WEB-98k", "MODEL"):
            self.assertIn(f'"key":"{key}"', self.html)

    def test_data_files_are_copied_for_download(self):
        for name in FILES:
            self.assertTrue((Path(self.tmp.name) / "data" / name).exists(), name)

    def test_page_states_that_it_predicts_no_date(self):
        self.assertIn("does not predict when RSA-2048 could be broken", self.html)
        self.assertIn("None of this predicts a date", self.html)
        self.assertIn('lang="en"', self.html)

    def test_every_hardware_row_keeps_its_kind_and_source(self):
        for r in load(".")["hardware"]:
            self.assertIn(r["kind"], {"demonstrated", "roadmap target"})
            self.assertTrue(r["source"].startswith("http"))
            self.assertTrue(r["source_quality"])


class TestSensitivityGrid(unittest.TestCase):
    def setUp(self):
        self.rows = load(".")["sensitivity"]

    def test_grid_is_complete(self):
        self.assertEqual(len(self.rows), 6 * 6 * 4)

    def test_baseline_matches_the_estimator(self):
        base = next(r for r in self.rows if r["p"] == 1e-3 and r["reaction_us"] == 10.0 and r["cycle_us"] == 1.0)
        self.assertTrue(base["feasible"])
        self.assertAlmostEqual(base["expected_volume_Mqd"], 5.69, delta=0.01)
        self.assertEqual((base["d1"], base["d2"]), (17, 29))

    def test_no_feasible_design_at_5e_minus_3(self):
        self.assertTrue(all(not r["feasible"] for r in self.rows if r["p"] == 5e-3))
        self.assertTrue(all(r["feasible"] for r in self.rows if r["p"] <= 3e-3))

    def test_volume_rises_with_error_rate_and_with_reaction_time(self):
        for rt in {r["reaction_us"] for r in self.rows}:
            for ct in {r["cycle_us"] for r in self.rows}:
                v = [r["expected_volume_Mqd"] for r in sorted(self.rows, key=lambda r: r["p"])
                     if r["reaction_us"] == rt and r["cycle_us"] == ct and r["feasible"]]
                self.assertEqual(v, sorted(v), f"over p at reaction {rt}, cycle {ct}")
        for p in (1e-4, 1e-3, 3e-3):
            for ct in {r["cycle_us"] for r in self.rows}:
                v = [r["expected_volume_Mqd"] for r in sorted(self.rows, key=lambda r: r["reaction_us"])
                     if r["p"] == p and r["cycle_us"] == ct]
                self.assertEqual(v, sorted(v), f"over reaction time at p {p}, cycle {ct}")


if __name__ == "__main__":
    unittest.main(verbosity=2)