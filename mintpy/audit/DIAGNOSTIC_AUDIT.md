# Mexico City MintPy Diagnostic Sensitivity Audit

> **Historical stage report.** Read the publication interpretation in `final_report/MANUSCRIPT_DRAFT.md`. The two original mid-year chain bridge interferograms are included in tested closure triangles after network expansion. Statements here that they have no closure check apply only to the original chain.

## Executive finding

The strong west-to-east pattern is **not robust to spatial-ramp treatment** and therefore must not be assumed to represent ground deformation.

- The baseline topography-corrected result has an east-west plane gradient of **-11.7228 mm/yr/km** and north-south gradient of **-2.8404 mm/yr/km**. A fitted plane explains 64.25% of its spatial variance.
- Removing a linear spatial ramp from the time series reduces both fitted gradients to numerical zero by construction and changes the map by **122.65 mm/yr RMS** relative to baseline.
- Topographic correction alone changes the raw result by only **0.975 mm/yr RMS**, so it does not explain the large gradient.
- The two long bridge interferograms each contain broad east-west phase gradients: 0.3477 and 0.3657 rad/km. Planes explain 63.2% and 69.7% of their phase variance.
- Re-referencing changes the map offset and reported local rates but leaves the spatial gradients unchanged to floating-point precision.

All velocities below are **relative Sentinel-1 line-of-sight velocities**. Their signs are not labeled as subsidence or uplift.

## Preservation and common processing choices

All baseline HDF5 products remained in place. New velocity and time-series products, statistics, code, and publication figures were written to `mintpy/audit/`. No data were downloaded and no original HyP3 products were deleted or modified.

Every case used:

- all 25 dates from 2024-01-13 through 2024-12-26;
- `mintpy/maskTempCoh.h5` for ramp estimation and statistical masking;
- reference date 2024-09-09;
- the inherited reference pixel Y/X `(7, 186)`;
- a first-order temporal velocity model;
- residual-based uncertainty estimation;
- 80,837 inverted pixels, of which 80,836 have finite nonzero velocity.

The audit script explicitly checked that all six input time-series files contain identical date arrays before calculation.

## Cases

| ID | Input and correction | Valid | Min | P05 | Median | P95 | Max | E-W gradient | N-S gradient | Corr(velocity,elevation) | Difference from baseline RMS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | Raw `timeseries.h5` | 80,836 | -152.65 | -58.10 | 146.98 | 204.54 | 247.46 | -11.7477 | -2.8952 | 0.4264 | 0.975 |
| B | Topography-corrected `timeseries_demErr.h5` | 80,836 | -152.45 | -58.43 | 146.21 | 203.35 | 245.72 | -11.7228 | -2.8404 | 0.4245 | 0.000 |
| C | Raw, linear ramp removed | 80,836 | -199.25 | -69.14 | 9.51 | 115.14 | 192.73 | ~0 | ~0 | -0.0090 | 122.651 |
| D | Topography-corrected, linear ramp removed | 80,836 | -200.18 | -69.10 | 9.42 | 115.05 | 192.79 | ~0 | ~0 | -0.0098 | 122.654 |
| E1 | Raw, quadratic ramp removed — exploratory | 80,836 | -253.02 | -86.36 | -6.63 | 91.52 | 187.77 | ~0 | ~0 | 0.0873 | 137.916 |
| E2 | Topography-corrected, quadratic ramp removed — exploratory | 80,836 | -253.88 | -86.34 | -6.72 | 91.29 | 187.57 | ~0 | ~0 | 0.0871 | 137.939 |

Velocity statistics are mm/yr. Gradient units are mm/yr/km. Differences are computed against the existing `mintpy/velocity.h5` baseline. Full precision is in `case_statistics.csv` and `audit_results.json`.

The estimated DEM-error/elevation Pearson correlation is **0.5622**. This correlation is common to all cases because all cases are compared with the same `demErr.h5` and elevation grid. The raw-to-topography-corrected velocity change is small compared with the spatial-ramp sensitivity, despite the moderate DEM-error/elevation correlation.

### Materiality of corrections

- **Topographic correction:** small velocity effect for this run. Raw minus baseline has median +0.742 mm/yr, 5th/95th differences +0.088/+1.649 mm/yr, and maximum absolute difference 4.600 mm/yr.
- **Linear ramp correction:** dominant effect. Topography-corrected linear-ramp minus baseline has median -101.424 mm/yr, 5th/95th differences -210.306/+22.967 mm/yr, RMS 122.654 mm/yr, and maximum absolute difference 251.239 mm/yr.
- **Quadratic ramp correction:** exploratory and even more influential. Topography-corrected quadratic-ramp minus baseline has median -125.702 mm/yr and RMS 137.939 mm/yr. A quadratic surface can remove broad real spatial signals as well as artifacts; this result is not preferred merely because the plane-fit gradient becomes zero.

Ramp removal is a sensitivity test, not proof that the removed field is entirely orbital or atmospheric. Conversely, the scale of the change proves that the original broad gradient is not correction-invariant.

## Alternative candidate reference areas

Each candidate is a 9 x 9 pixel patch. These are candidate reference areas, not confirmed stable ground.

Selection rules:

1. `north_existing`: centered on the existing reference pixel.
2. `west_high_terrain`: highest mean-elevation patch with at least 50 baseline-valid pixels in the western third, excluding the southern third.
3. `southwest_high_terrain`: highest mean-elevation patch with at least 50 baseline-valid pixels in the western half of the southern third.

| Candidate | Center Y/X | Pixel bounds Y, X | UTM center easting, northing (m) | Valid pixels | Mean elevation (m) | Mean baseline patch rate (mm/yr) |
|---|---:|---:|---:|---:|---:|---:|
| Northern existing neighbourhood | 7, 186 | Y 3–11, X 182–190 | 493640, 2155640 | 80 | 2223.95 | -0.729 |
| Western high terrain | 152, 4 | Y 148–156, X 0–8 | 479080, 2144040 | 81 | 2318.67 | 203.999 |
| Southwestern high terrain | 341, 4 | Y 337–345, X 0–8 | 479080, 2128920 | 81 | 2649.15 | 205.785 |

### Reference-invariance demonstration

Let the original velocity field be `v(x,y)`. Referencing to patch `R` subtracts its spatially uniform mean rate `c_R`:

`v_R(x,y) = v(x,y) - c_R`.

Therefore:

`dv_R/dx = dv/dx` and `dv_R/dy = dv/dy`.

Likewise, any two-pixel difference is invariant:

`v_R(p) - v_R(q) = [v(p)-c_R] - [v(q)-c_R] = v(p)-v(q)`.

Numerically:

| Reference patch | Subtracted rate (mm/yr) | Map median after reference (mm/yr) | E-W gradient | N-S gradient | Rate at north patch | Rate at west patch | Rate at southwest patch |
|---|---:|---:|---:|---:|---:|---:|---:|
| North | -0.729 | 146.938 | -11.72281845 | -2.84037833 | 0.000 | 204.728 | 206.514 |
| West | 203.999 | -57.790 | -11.72281832 | -2.84037830 | -204.728 | 0.000 | 1.786 |
| Southwest | 205.785 | -59.576 | -11.72281831 | -2.84037830 | -206.514 | -1.786 | 0.000 |

Rates and medians are mm/yr; gradients are mm/yr/km. Gradient differences are below 0.0000002 mm/yr/km and arise from floating-point arithmetic. The >200 mm/yr offset change shows that reference choice radically changes absolute-looking local rates, but it does not remove the west-east spatial structure.

## Bridge interferogram inspection

| Pair | Valid pixels | Plane E-W gradient (rad/km) | Plane N-S gradient (rad/km) | Plane R² | Adjacent jump P95 / P99 / max (rad) |
|---|---:|---:|---:|---:|---:|
| 20240512_20240629 | 80,762 | 0.3477 | 0.1087 | 0.6319 | 0.481 / 1.872 / 9.227 |
| 20240629_20240804 | 80,579 | 0.3657 | 0.0152 | 0.6965 | 0.447 / 2.013 / 8.232 |

Both bridge interferograms show a visually similar broad east-west ramp. The second is especially plane-dominated. The southern edge is noisy and fragmented, and both maps terminate along the eastern coverage boundary. More than 99.997% of valid pixels belong to the largest connected valid region, so the many small holes do not split the principal footprint. However, maximum adjacent phase jumps exceed 2π in both interferograms, indicating localized discontinuities, unwrapping boundaries, or edge/no-data transitions that require pixel-level inspection.

These two long bridge edges are critical in a chain-only graph: any phase error they contain propagates into every later acquisition because no alternative path or closure triangle exists. Similar broad patterns in both pairs do not independently validate them.

## Figures

- `fig_raw_vs_topography_corrected_velocity.png`
- `fig_no_ramp_vs_linear_ramp_velocity.png`
- `fig_velocity_difference_maps.png`
- `fig_dem_error.png`
- `fig_elevation.png`
- `fig_alternative_reference_comparison.png`
- `fig_bridge_interferograms.png`
- MintPy wrapped-phase inspections: `bridge_20240512_20240629.png`, `bridge_20240629_20240804.png`

All publication comparison figures use identical color limits within each comparison and label EPSG:32614 axes explicitly as UTM easting and northing.

## Exact commands

Inspection and directory setup:

```sh
mkdir -p mintpy/audit
./mintpy-run remove_ramp.py --help
./mintpy-run timeseries2velocity.py --help
./mintpy-run info.py mintpy/inputs/ifgramStack.h5
./mintpy-run info.py mintpy/inputs/geometryGeo.h5
```

Ramp sensitivity products:

```sh
./mintpy-run remove_ramp.py mintpy/timeseries.h5 -m mintpy/maskTempCoh.h5 -s linear -o mintpy/audit/timeseries_raw_linearRamp.h5 --save-ramp-coeff
./mintpy-run remove_ramp.py mintpy/timeseries_demErr.h5 -m mintpy/maskTempCoh.h5 -s linear -o mintpy/audit/timeseries_topo_linearRamp.h5 --save-ramp-coeff
./mintpy-run remove_ramp.py mintpy/timeseries.h5 -m mintpy/maskTempCoh.h5 -s quadratic -o mintpy/audit/timeseries_raw_quadraticRamp.h5 --save-ramp-coeff
./mintpy-run remove_ramp.py mintpy/timeseries_demErr.h5 -m mintpy/maskTempCoh.h5 -s quadratic -o mintpy/audit/timeseries_topo_quadraticRamp.h5 --save-ramp-coeff
```

MintPy writes ramp-coefficient text beside the input file rather than beside the requested output. Thus `--save-ramp-coeff` created `mintpy/rampCoeff_timeseries.txt` and `mintpy/rampCoeff_timeseries_demErr.txt`; the later quadratic calls replaced the coefficients from the earlier linear calls. These were new diagnostic sidecars, not pre-existing baseline products. All HDF5 outputs remained isolated in `mintpy/audit/`.

Velocity estimates:

```sh
./mintpy-run timeseries2velocity.py mintpy/timeseries.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy/audit/velocity_A_raw.h5
./mintpy-run timeseries2velocity.py mintpy/timeseries_demErr.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy/audit/velocity_B_topo.h5
./mintpy-run timeseries2velocity.py mintpy/audit/timeseries_raw_linearRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy/audit/velocity_C_raw_linearRamp.h5
./mintpy-run timeseries2velocity.py mintpy/audit/timeseries_topo_linearRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy/audit/velocity_D_topo_linearRamp.h5
./mintpy-run timeseries2velocity.py mintpy/audit/timeseries_raw_quadraticRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy/audit/velocity_E_raw_quadraticRamp_exploratory.h5
./mintpy-run timeseries2velocity.py mintpy/audit/timeseries_topo_quadraticRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy/audit/velocity_E_topo_quadraticRamp_exploratory.h5
```

Bridge inspection:

```sh
./mintpy-run view.py mintpy/inputs/ifgramStack.h5 unwrapPhase-20240512_20240629 -m mintpy/maskConnComp.h5 --wrap --wrap-range -3.14159265 3.14159265 -c cmy --title 'Unwrapped phase 20240512_20240629 (wrapped for inspection)' --coord yx --dpi 200 --nodisplay -o mintpy/audit/bridge_20240512_20240629.png
./mintpy-run view.py mintpy/inputs/ifgramStack.h5 unwrapPhase-20240629_20240804 -m mintpy/maskConnComp.h5 --wrap --wrap-range -3.14159265 3.14159265 -c cmy --title 'Unwrapped phase 20240629_20240804 (wrapped for inspection)' --coord yx --dpi 200 --nodisplay -o mintpy/audit/bridge_20240629_20240804.png
```

Numerical analysis and publication figures:

```sh
./mintpy-run python mintpy/audit/run_diagnostic_audit.py
```

The script is retained as `run_diagnostic_audit.py`; machine-readable results are in `audit_results.json`, `case_statistics.csv`, and `reference_sensitivity.csv`.

## Limitations and recommended interpretation

1. The network has 25 nodes and only 24 chain edges. There are no phase-closure triangles, so unwrapping errors cannot be independently validated.
2. Linear ramp removal forces the best-fit plane to zero. Its dramatic effect establishes sensitivity, but does not identify whether the plane is orbital, atmospheric, propagated unwrapping error, a real broad LOS field, or a mixture.
3. Quadratic ramp results are explicitly exploratory and risk removing genuine long-wavelength signal.
4. Tropospheric correction was disabled, ionospheric correction data were unavailable, and the baseline processing had no deramp correction.
5. The observation interval is less than one full year, limiting separation of linear, seasonal, and atmospheric components.
6. Candidate high-terrain patches are selected geometrically and by elevation only; high terrain is not synonymous with stability.
7. Independent GNSS/leveling comparison, redundant interferograms, atmospheric modeling, orbital-ramp checks, and longer time coverage are required before physical interpretation.

The scientifically defensible conclusion is limited: the relative LOS field contains a large long-wavelength component that is strongly dependent on ramp correction and reference choice. It is not yet a validated deformation field.
