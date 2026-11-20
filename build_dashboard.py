"""Stage 6b: build the static dashboard (docs/index.html) from the three CSV data files."""
import csv
import datetime
import json
import shutil
from pathlib import Path

FILES = ("published_estimates.csv", "hardware_status.csv", "sensitivity.csv")


def _num(x):
    return None if x in ("", "None", None) else float(x)


def load(folder="."):
    folder = Path(folder)
    with open(folder / "published_estimates.csv", newline="") as f:
        estimates = [dict(key=r["key"], label=r["label"], arxiv=r["arxiv"], platform=r["platform"],
                          connectivity=r["connectivity"], p=_num(r["p"]), cycle_us=_num(r["cycle_us"]),
                          reaction_us=_num(r["reaction_us"]), qubits=float(r["qubits"]),
                          runtime_days=float(r["expected_runtime_days"]), megaqubit_days=float(r["megaqubit_days"]),
                          same_hw=r["same_hw_as_GE19"] == "True", source_quality=r["source_quality"], note=r["note"])
                     for r in csv.DictReader(f)]
    with open(folder / "hardware_status.csv", newline="") as f:
        hardware = [dict(key=r["key"], org=r["org"], platform=r["platform"], kind=r["kind"], metric=r["metric"],
                         value=float(r["value"]), unit=r["unit"], date=r["date"],
                         target_year=int(r["target_year"]) if r["target_year"] else None, source=r["source"],
                         source_quality=r["source_quality"], note=r["note"]) for r in csv.DictReader(f)]
    with open(folder / "sensitivity.csv", newline="") as f:
        sens = []
        for r in csv.DictReader(f):
            feasible = r["feasible"] == "1"
            row = dict(p=float(r["p"]), reaction_us=float(r["reaction_us"]), cycle_us=float(r["cycle_us"]), feasible=feasible)
            for k in ("d1", "d2", "c_mul", "c_exp", "c_sep"):
                row[k] = int(r[k]) if feasible else None
            for k in ("physical_qubits", "runtime_h", "retry_risk", "expected_runtime_h", "expected_volume_Mqd"):
                row[k] = float(r[k]) if feasible else None
            sens.append(row)
    return dict(estimates=estimates, hardware=hardware, sensitivity=sens)


def build(folder=".", out="docs", built=None):
    folder, out = Path(folder), Path(out)
    data = load(folder)
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = (folder / "dashboard_template.html").read_text(encoding="utf-8")
    html = html.replace("__DATA__", payload).replace("__BUILT__", built or datetime.date.today().isoformat())
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    for name in FILES:
        shutil.copyfile(folder / name, out / "data" / name)
    return out / "index.html"


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KB) and copied the data files to docs/data/")