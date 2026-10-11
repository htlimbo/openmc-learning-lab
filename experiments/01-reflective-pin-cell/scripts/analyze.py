"""Regenerate all result tables and figures from the archived statepoints.

Only NumPy, h5py and Matplotlib are needed; no transport executable or
cross-section library is needed to analyze the recorded experiment.
"""

import csv
import hashlib
import json
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

LAB = Path(__file__).resolve().parents[1]
RESULTS = LAB / "results"


def read_case(case):
    path = LAB / case["statepoint"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != case["statepoint_sha256"]:
        raise ValueError(f"Archived statepoint checksum mismatch: {case['id']}")
    with h5py.File(path) as f:
        n = int(f["n_realizations"][()])
        for key, dataset in [("seed", "seed"), ("particles", "n_particles"),
                             ("batches", "n_batches"), ("inactive", "n_inactive"),
                             ("generations_per_batch", "generations_per_batch")]:
            if case[key] != int(f[dataset][()]):
                raise ValueError(f"Manifest mismatch: {case['id']}, {key}")
        k, error = f["k_combined"][()]
        # Statepoint global_tallies columns: current value, sum, sum of squares.
        global_tallies = f["global_tallies"][()]
        means = global_tallies[:, 1] / n
        errors = np.sqrt(np.maximum(0, (global_tallies[:, 2] / n - means**2) / (n - 1)))
        history = f["k_generation"][()]
        entropy = f["entropy"][()] if "entropy" in f else np.full(len(history), np.nan)
        source = f["source_bank"][()]
    row = {
        "case": case["id"], "initial_source": case["initial_source"],
        "seed": case["seed"], "particles_per_generation": case["particles"],
        "total_batches": case["batches"], "inactive_batches": case["inactive"],
        "active_batches": n, "generations_per_batch": case["generations_per_batch"],
        "k_combined": float(k), "k_combined_std_error": float(error),
    }
    for i, name in enumerate(["collision", "absorption", "tracklength", "leakage"]):
        row[name + "_mean"] = float(means[i])
        row[name + "_std_error"] = float(errors[i])
    cut = case["inactive"] * case["generations_per_batch"]
    row["mean_active_entropy_bits"] = float(entropy[cut:].mean()) if case["entropy_enabled"] else ""
    return row, history, entropy, source


def save(fig, name):
    fig.tight_layout()
    fig.savefig(RESULTS / "figures" / name, dpi=180)
    plt.close(fig)


def main():
    manifest = json.loads((RESULTS / "manifest.json").read_text())
    for folder in ["figures", "tables", "traces"]:
        (RESULTS / folder).mkdir(exist_ok=True)
    records = {case["id"]: read_case(case) for case in manifest}
    rows = [records[c["id"]][0] for c in manifest]
    with (RESULTS / "tables/run_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for case in manifest:
        _, k, entropy, _ = records[case["id"]]
        np.savetxt(
            RESULTS / "traces" / (case["id"] + ".csv"),
            np.column_stack((np.arange(1, len(k) + 1), k, entropy)),
            delimiter=",", header="generation,k_tracklength,entropy_bits", comments="",
        )

    # The two 30-inactive runs isolate a change of initial spatial source.
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex="col", sharey="row")
    for col, (ident, label) in enumerate([
        ("uniform-i30-s1", "Uniform initial source"),
        ("point-i30-s1", "Off-center point initial source"),
    ]):
        _, k, entropy, _ = records[ident]
        generations = np.arange(1, len(k) + 1)
        axes[0, col].plot(generations, k, ".-", ms=2, lw=0.8)
        axes[1, col].plot(generations, entropy, ".-", ms=2, lw=0.8)
        axes[0, col].set_title(label)
        axes[1, col].set_xlabel("Generation")
        for row in [0, 1]:
            axes[row, col].axvline(30.5, color="tab:red", ls="--", lw=1)
            axes[row, col].grid(alpha=0.25)
    axes[0, 0].set_ylabel("Generation k (track-length)")
    axes[1, 0].set_ylabel("Shannon entropy (bits)")
    save(fig, "source_convergence.png")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for i, (ident, label) in enumerate([
        ("uniform-i30-s1", "Uniform start"), ("point-i30-s1", "Point start"),
    ]):
        source = records[ident][3]
        axes[i].scatter(source["r"]["x"], source["r"]["y"], s=2, alpha=0.2)
        axes[i].add_patch(Circle((0, 0), 0.39218, fill=False, color="black"))
        axes[i].set(xlim=(-0.42, 0.42), ylim=(-0.42, 0.42),
                    xlabel="x (cm)", ylabel="y (cm)", title=label)
        axes[i].set_aspect("equal")
        axes[2].hist(source["r"]["z"], bins=np.linspace(-0.5, 0.5, 11),
                     weights=source["wgt"], density=True, histtype="step", label=label)
    axes[2].set(xlabel="z (cm)", ylabel="Probability density (1/cm)", title="Final source bank")
    axes[2].legend()
    save(fig, "source_distribution.png")

    selected = [r for r in rows if r["case"].startswith("point-i100-")]
    values = np.array([r["k_combined"] for r in selected])
    errors = np.array([r["k_combined_std_error"] for r in selected])
    mean = float(values.mean())
    std = float(values.std(ddof=1))
    rms = float(np.sqrt(np.mean(errors**2)))
    pair_delta = float(values[1] - values[0])
    pair_se = float(np.hypot(errors[0], errors[1]))
    statistics = {
        "cases": [r["case"] for r in selected], "n_independent_runs": len(values),
        "arithmetic_mean_k": mean, "sample_std_between_runs": std,
        "rms_reported_single_run_std_error": rms,
        "between_run_std_over_rms_reported_error": std / rms,
        "empirical_std_error_of_mean": std / np.sqrt(len(values)),
        "seed_11_minus_seed_1": pair_delta,
        "estimated_std_error_of_difference": pair_se,
        "absolute_difference_in_combined_std_errors": abs(pair_delta) / pair_se,
        "interpretation": "Descriptive small-sample comparison, not proof of source convergence or variance calibration.",
    }
    (RESULTS / "tables/replicate_statistics.json").write_text(json.dumps(statistics, indent=2) + "\n")
    fig, ax = plt.subplots(figsize=(7, 4))
    positions = np.arange(len(values))
    ax.errorbar(positions, values, yerr=errors, fmt="o", capsize=5,
                label="Run estimate +/- 1 reported standard error")
    ax.axhline(mean, color="tab:orange", ls="--", label="Arithmetic mean of five runs")
    ax.set(xticks=positions, xticklabels=[str(r["seed"]) for r in selected],
           xlabel="Random seed", ylabel="Combined k-effective", title="Independent-seed comparison")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    save(fig, "seed_comparison.png")

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.add_patch(Rectangle((-0.63, -0.63), 1.26, 1.26, color="lightblue", label="Water"))
    ax.add_patch(Circle((0, 0), 0.45720, color="gray", label="Zr cladding"))
    ax.add_patch(Circle((0, 0), 0.39218, color="goldenrod", label="Fuel"))
    ax.set(xlim=(-0.7, 0.7), ylim=(-0.7, 0.7), xlabel="x (cm)", ylabel="y (cm)",
           title="Input geometry: reflective outer boundaries")
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=8)
    save(fig, "geometry.png")
    print(json.dumps(statistics, indent=2))
    print(f"Verified and analyzed {len(rows)} archived statepoints.")


if __name__ == "__main__":
    main()
