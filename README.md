# OpenMC Learning Lab

Small, reproducible experiments in neutron transport with OpenMC.
Each lab starts with a physical question, changes one factor at a time, and ends
with code, recorded results, interpretation, and explicit limits.

## Labs

| Lab | Question | Status |
|---|---|---|
| [01 - Reflective Pin Cell: Materials, Geometry, and Source Convergence](experiments/01-reflective-pin-cell/README.md) | How do material definitions and geometry lead to an eigenvalue calculation, and what evidence supports source convergence? | Completed |

## Start here

- Read the [Lab 01 report](experiments/01-reflective-pin-cell/README.md).
- Use the [experiment report template](templates/LAB_TEMPLATE.md) for additional experiments.

## Run transport calculations

An OpenMC 0.16.0 executable, its matching Python package, and a compatible HDF5
cross-section library are required. `environment.yml` describes the intended
software requirements; package availability depends on the platform.

```bash
export OPENMC_CROSS_SECTIONS=/path/to/cross_sections.xml
python experiments/01-reflective-pin-cell/scripts/run.py --case point-i100-s1
```

New runs go to an ignored, timestamped `runs/` directory. They never overwrite
the historical results. See the lab report for data requirements and additional
commands. Nuclear-data libraries are not bundled.

## Public archive scope

The archive includes model inputs, simulation settings, numerical results, and
analysis scripts. OpenMC's version and the number of simulation threads are retained
as calculation settings. See [PUBLICATION.md](PUBLICATION.md).
