"""Rerun one archived configuration without overwriting historical results."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil

import openmc
from model import make_model

LAB = Path(__file__).resolve().parents[1]


def main():
    cases = {c["id"]: c for c in json.loads((LAB / "results/manifest.json").read_text())}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=cases, default="point-i100-s1")
    parser.add_argument("--cross-sections", type=Path,
                        help="OpenMC HDF5 cross_sections.xml; alternatively use OPENMC_CROSS_SECTIONS")
    parser.add_argument("--openmc-exec", default="openmc")
    parser.add_argument("--export-only", action="store_true")
    args = parser.parse_args()
    case = cases[args.case]
    xs = args.cross_sections or os.environ.get("OPENMC_CROSS_SECTIONS")
    if xs:
        xs = Path(xs).expanduser().resolve()
        if not xs.is_file():
            parser.error(f"Cross-section index not found: {xs}")
    elif not args.export_only:
        parser.error("Supply --cross-sections or set OPENMC_CROSS_SECTIONS.")
    executable = shutil.which(args.openmc_exec)
    if not args.export_only and executable is None:
        parser.error("OpenMC executable not found; activate the OpenMC environment.")

    model = make_model(case, xs)
    output = LAB / "runs" / f"{args.case}-{datetime.now():%Y%m%d-%H%M%S-%f}"
    output.mkdir(parents=True)
    (output / "case.json").write_text(json.dumps(case, indent=2) + "\n")
    if args.export_only:
        model.export_to_xml(directory=output)
        print(f"Inputs exported to {output}")
        return
    statepoint = model.run(
        cwd=output, threads=case["threads"], geometry_debug=True,
        openmc_exec=executable, export_model_xml=False,
    )
    with openmc.StatePoint(statepoint, autolink=False) as sp:
        print(f"Combined k-effective: {sp.keff}")
        print(f"Active batches: {sp.n_realizations}")
    print(f"New results: {output}")


if __name__ == "__main__":
    main()
