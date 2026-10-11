# Model Verification and Numerical Reproduction

## Input consistency

For all eight cases, the model exported materials, geometry, and settings XML
with parsed content matching the archived inputs. Comparison excluded XML
formatting, element order, and the cross-section library path.

`check_model.py` reproduced the number-density, composition, region-membership,
and analytic-volume values in the experiment report.

## Representative transport rerun

A separate `point-i100-s1` run completed with geometry debugging enabled:

| Quantity | Absolute difference from archived result |
|---|---:|
| Combined k | 1.38e-14 |
| Reported standard error | 6.68e-15 |
| Maximum difference in generation k | 1.78e-15 |

This same-seed rerun checks numerical reproduction. It is not an additional
independent replicate in the five-seed analysis.

## Result consistency

The eight included statepoints retain the original numerical datasets.
Their SHA-256 digests are recorded in the manifest. `analyze.py` regenerates
the result tables, generation traces, replicate statistics, and figures.

These checks establish consistency between the model, recorded results, and
analysis. They do not validate the reactor physics against an experimental
benchmark or guarantee bitwise reproduction across builds or machines.
