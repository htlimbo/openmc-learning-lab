"""Check material composition, region membership, and analytic cell volumes."""

import json
from math import pi
from pathlib import Path

import openmc.data
from model import FUEL_RADIUS, CLAD_RADIUS, PITCH, HEIGHT, make_model

LAB = Path(__file__).resolve().parents[1]


def main():
    case = json.loads((LAB / "results/manifest.json").read_text())[0]
    model = make_model(case)
    water, fuel, _ = model.materials
    original = water.get_nuclide_atom_densities()
    half = water.clone()
    half.set_density("g/cm3", 0.5)
    changed = half.get_nuclide_atom_densities()
    checks = {"water_number_densities_atom_per_barn_cm": {
        n: {"original": original[n], "half_density": changed[n],
            "ratio": changed[n] / original[n]} for n in ["H1", "O16"]
    }}
    n = fuel.get_nuclide_atom_densities()
    uranium = ["U234", "U235", "U238"]
    checks["fuel_composition"] = {
        "O_to_U_atom_ratio": n["O16"] / sum(n[u] for u in uranium),
        "U235_atom_fraction_within_uranium": n["U235"] / sum(n[u] for u in uranium),
        "U235_mass_fraction_within_uranium":
            n["U235"] * openmc.data.atomic_mass("U235") /
            sum(n[u] * openmc.data.atomic_mass(u) for u in uranium),
    }
    volumes = {
        "fuel": pi * FUEL_RADIUS**2 * HEIGHT,
        "cladding": pi * (CLAD_RADIUS**2 - FUEL_RADIUS**2) * HEIGHT,
        "water": (PITCH**2 - pi * CLAD_RADIUS**2) * HEIGHT,
    }
    checks["volumes_cm3"] = volumes | {
        "sum": sum(volumes.values()), "outer_box": PITCH**2 * HEIGHT,
    }
    cells = list(model.geometry.get_all_cells().values())
    points = [(0, 0, 0), (0.42, 0, 0), (0.5, 0, 0), (0.62, 0.62, 0), (0.7, 0, 0)]
    checks["region_membership"] = [
        {"point_cm": p, "cells": [c.name for c in cells if p in c.region]}
        for p in points
    ]
    output = LAB / "results/tables/model_checks.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
