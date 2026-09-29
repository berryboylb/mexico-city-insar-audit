# Figure index: manuscript figures

Six existing figures were selected; none was regenerated or modified. Figure 7 is a new plot of existing outputs, made in the 2026-09-28 reporting pass. Supplementary Figure S1 is an existing figure, included after visual inspection against the recorded results. Case labels follow the manuscript (§3.2): A = redundant, no ramp; B = redundant, linear ramp removed; C = ERA5, no ramp; D = ERA5, linear ramp removed.

---

## Figure 1: Closure failures by triangle

**File:** `mintpy_redundant/audit/closure_failures_by_triangle.png`

**Caption.** Integer phase-closure ambiguity (cycles) for each of the seven closure triangles created by the seven added interferograms, with the percentage of strictly valid pixels that fail. Failures are concentrated in the two mid-year triangles: 2024-04-30/05-12/06-29 (1.87%) and 2024-06-29/08-04/08-16 (0.95%). They cluster in the north-east and south of the scene, reach ±2 cycles, and coincide with low coherence (source: `mintpy_redundant/audit/audit_results.json` → `closure.triangles`).

**Establishes:** where and when unwrapping is locally inconsistent within the seven tested loops.

**Cannot establish:**

- the reliability of edges outside these seven triangles; both original mid-year bridge edges are included in the two mid-year triangles, but a failing triangle does not identify the faulty edge;
- which edge of a failing triangle is wrong;
- that the broad velocity gradient is free of unwrapping error.

Sparse closure does not validate every interferogram.

## Figure 2: Four-case velocity comparison

**File:** `mintpy_redundant_era5/audit/fig_four_case_velocity_comparison.png`

**Caption.** Relative Sentinel-1 descending-LOS velocity (mm/yr) for cases A–D over 2024-01-13 to 2024-12-26, all on common colour limits. The reference is pixel Y/X 7/186 and the reference date is 2024-09-09.

- Rows compare no ERA5 (top) with ERA5 (bottom): the maps are nearly identical (C − A RMS 1.25 mm/yr).
- Columns compare no ramp (left) with linear ramp removed (right): ramp removal changes the map by about 123 mm/yr RMS and removes the fitted −11.7 mm/yr/km east–west gradient by construction (source: `mintpy_redundant_era5/audit/audit_results.json`).

**Establishes:** that ramp treatment dominates the other processing choices, and that ERA5 hardly changes the field.

**Cannot establish:**

- which of the two columns is correct;
- that ramp removal targeted an artifact;
- that ERA5 captured all atmospheric error.

The colour-scale midpoint is not zero, and colours are relative LOS, not uplift or subsidence.

## Figure 3: Reference sensitivity

**File:** `mintpy_redundant/audit/fig_reference_sensitivity.png`

**Caption.** Case A velocity re-referenced to three 9 × 9-pixel candidate patches: the existing northern patch, western high terrain and southwestern high terrain (crosses mark the patch centres). The candidates were chosen by geometry and elevation only. Moving the reference shifts the whole map by about 205–208 mm/yr, while the east–west (−11.719) and north–south (−2.881 mm/yr/km) gradients are unchanged (source: `mintpy_redundant/audit/reference_sensitivity.csv`).

**Establishes:** that reference choice is a datum shift; it alters absolute-looking local rates but no spatial difference.

**Cannot establish:**

- which, if any, candidate patch is stable ground;
- anything about whether spatial contrasts are real, since a reference change neither validates nor invalidates them.

## Figure 4: GNSS projected to LOS

**File:** `external_validation/fig_gnss_los_timeseries.png`

**Caption.** NGL IGS20 daily GNSS positions for 2024 projected into descending LOS (toward the satellite positive), using each station's incidence angle.

- **Top row:** the five stations on a shared y-scale. Open circles mark days matched to Sentinel-1 dates within ±1 day. MXTX, MXTO and TOL2 lie outside the scene and use edge incidence values.
- **Bottom panel:** the reference-invariant ICMX − MMX1 differential, with all shared clean days in grey and the 10 Sentinel-matched epochs in black (256.3 mm/yr, 95% range 242.1–270.6). The common window is 2024-04-18 to 2024-10-03.

Source: `external_validation/gnss_los_results.json` → `gnss_differential`, `regional`.

**Establishes:**

- the independent GNSS LOS contrast between the two stations inside the scene;
- MMX1's partial 2024 coverage;
- that the regional stations move far more slowly than the ICMX–MMX1 contrast.

**Cannot establish:**

- anything about the InSAR field away from the two stations;
- that the ICMX data are free of interference (INEGI warning);
- vertical motion, since LOS mixes east and up.

## Figure 5: GNSS vs InSAR differential

**File:** `external_validation/fig_gnss_vs_insar_differential.png`

**Caption.**

- **Left:** ICMX − MMX1 differential LOS time series at the 10 common epochs, with the mean offset removed. GNSS is black; InSAR cases A–D use 9 × 9-pixel patch medians.
- **Right:** GNSS − InSAR rate difference for each case. The thick bar is the AR(1)-adjusted statistical 95% interval. Whiskers show U95, a study-defined envelope combining that half-width with selected sensitivity terms for GNSS cadence, outlier treatment, matching tolerance and patch size. U95 is not a demonstrated 95% bound on all error.
- **Results:** A falls within the envelope (+15.8 mm/yr, 0.81 × U95). C is borderline (+22.0, 1.04 × U95). B and D differ much more (+158.2 and +156.9, about 9.7 × U95).

Source: `external_validation/gnss_los_results.json` → `decision`.

**Establishes:** that along the ICMX–MMX1 baseline, the no-ramp result agrees much better with GNSS than the ramp-removed result under the stated comparison rule.

**Cannot establish:**

- validity of the full spatial plane or its north–south gradient;
- a physical cause for the gradient;
- agreement over the full year: this is a 168-day, 10-epoch comparison (6 exact-date pairs), not a full-year rate.

The ICMX interference warning is not included in U95. Its effect is unquantified; low scatter and annual histories cannot rule out a smooth station bias.

## Figure 6: Patch-size and period sensitivity

**File:** `external_validation/fig_patch_sensitivity.png`

**Caption.**

- **Left:** InSAR ICMX − MMX1 rate for each case at 5 × 5, 9 × 9 and 13 × 13-pixel patches (400–1,040 m). Filled circles are the common window, with 95% error bars; open squares are the full-year velocity. The grey band is GNSS with its 95% range.
- **Right:** robust within-patch velocity dispersion (MAD).

Patch size moves the InSAR differential by less than 4 mm/yr, and ramp choice moves it by about 140 mm/yr. The full-year values (open squares: A 227.7, B 94.2 mm/yr) are labelled as **not equivalent** to the common-window GNSS rate.

Source: `external_validation/gnss_los_comparison.csv`.

**Establishes:** that the GNSS comparison is not an artifact of patch size, and how large the common-window vs full-year difference is.

**Cannot establish:** anything about patches away from the two stations, or full-year agreement with GNSS.

## Figure 7: Station locations on the velocity map (new)

**Files:** `final_report/fig_station_locations.png` (300 dpi), `final_report/fig_station_locations.pdf`
**Script:** `final_report/make_fig_station_locations.py`. It reads existing outputs through a read-only mount and writes only to `final_report/`.

**Caption.** Case A relative Sentinel-1 descending-LOS velocity (redundant network, topographic correction, no ramp removal) in WGS 84 / UTM zone 14N (EPSG:32614), with a 2 km scale bar and grid-north arrow.

- **Map period.** The map is a linear fit to 25 acquisitions, 2024-01-13 to 2024-12-26.
- **Comparison period.** The GNSS comparison uses a shorter window, 2024-04-18 to 2024-10-03 (10 epochs).
- **Colour scale.** Relative LOS velocity in mm/yr; positive means motion toward the satellite. Zero is the velocity of the InSAR reference pixel Y/X 7/186 (white star, marked separately; reference date 2024-09-09). The diverging colour scale is centred on that reference, with limits ±210 mm/yr.
- **Stations.**
  - ICMX (triangle; 19.4056° N, −99.1709°; pixel Y/X 130/41) and MMX1 (square; 19.4317° N, −99.0684°; pixel Y/X 95/175) are at their median 2024 NGL IGS20 coordinates.
  - The outlined squares are the actual 9 × 9-pixel (720 m) extraction patches.
  - The black line is the 11.1 km station baseline (10.76 km E, 2.87 km N).
- **Patch values.** The patch-median velocities, ICMX 181.5 and MMX1 −46.2 mm/yr, are full-year values. They are not the GNSS-window rates.
- **Grey areas.** No data, or outside the common temporal-coherence mask.

Source: `mintpy_redundant/audit/velocity_B_topo.h5`; `external_validation/gnss_los_results.json` → `geometry.stations`, `patches.A_redundant_no_ramp`, `matching.common_dates`.

**Verification.**
- The script reuses the validated conversion: pyproj EPSG:4326 → EPSG:32614, then floor((coord − X_FIRST|Y_FIRST)/STEP).
- It asserts that the stored station pixels, UTM coordinates and 9 × 9 patch medians are reproduced. All assertions passed.
- The exported PNG and the PDF (rasterised) were inspected visually on 2026-09-28. Labels are legible and nothing is clipped.

**Establishes:** where the two GNSS stations, their extraction patches and the reference pixel sit relative to the velocity field; and that the ICMX–MMX1 baseline is mostly east–west and crosses the main gradient.

**Cannot establish:**

- anything about GNSS agreement (see Figure 5);
- the velocity during the GNSS window, since the map is full-year;
- stability of the reference pixel;
- vertical motion.

The ±210 mm/yr colour limit is a display choice (99.5th percentile of |v|, rounded up to 10 mm/yr), not a physical threshold.

## Supplementary Figure S1: Fitted plane gradients by case

**File:** `mintpy_redundant_era5/audit/fig_gradient_comparison.png`

**Inspection result (2026-09-28): included.** Its bar heights match `mintpy_redundant_era5/audit/audit_results.json` → `cases.*`:

| Case | E–W (mm/yr/km) | N–S (mm/yr/km) |
|---|---:|---:|
| A | −11.719 | −2.881 |
| B | 7.6 × 10⁻⁷ | −7.3 × 10⁻⁷ |
| C | −11.610 | −2.883 |
| D | −6.3 × 10⁻⁸ | −6.6 × 10⁻⁷ |

The y-axis label, "Fitted gradient (mm/yr/km)", has the correct units.

**Caption.** East–west and north–south gradients of the least-squares plane fitted to each case's velocity map on the common mask (80,791 px). Cases A and C have essentially the same plane (ERA5 reduces the east–west gradient by 0.93%). Cases B and D show no visible bars because linear-ramp removal sets the fitted plane to about 10⁻⁶ mm/yr/km by construction.

**Label caveats to state with the figure:**

- The x-axis tick labels use the audit-stage names `A_baseline_no_ramp`, `B_baseline_linear_ramp`, `C_ERA5_no_ramp` and `D_ERA5_linear_ramp`. "baseline" there means the **redundant, topographically corrected, no-ERA5** case (manuscript cases A/B), not the original chain network.
- The figure has no title.
- The empty B and D slots are values of about zero, not missing data.

**Establishes:** that the plane is essentially unchanged by ERA5 and is removed entirely by the linear ramp.

**Cannot establish:** whether the plane is real deformation or error.

---

### Considered but not selected

- `mintpy_redundant/audit/network.png`: too small to show the closure triangles legibly.
- `mintpy/audit/fig_bridge_interferograms.png`: a strong supplementary candidate for claim C09.

### Credit line for all InSAR-derived figures

Figures 1–3, 5–7 and S1 should carry the HyP3 README image credit: "InSAR product processed by ASF DAAC HyP3 2026 using GAMMA software. Contains modified Copernicus Sentinel data 2024, processed by ESA." Figure 4 shows GNSS only (NGL-processed).
