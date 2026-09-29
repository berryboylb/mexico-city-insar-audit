# Reference and Ramp Sensitivity in a Mexico City Sentinel-1 InSAR Time Series: A Processing Audit with Sparse GNSS Validation

*Draft manuscript, reference audit updated 2026-09-29. Project numerical results are traced to existing files using* `[S: path → table/key]` *relative to the project root. Literature and official documentation use author–year citations. Provider credits remain in Acknowledgements. Background sources do not verify this project's numerical results; see* `final_report/REFERENCE_AUDIT.md`.

---

## Abstract

We audit a 2024 Sentinel-1 descending time series over central–eastern Mexico City: 25 acquisitions from 2024-01-13 to 2024-12-26, 80 m grid, processed with MintPy 1.6.4 from HyP3 interferograms. The audit tests how processing choices change the dominant long-wavelength relative line-of-sight (LOS) velocity field.

The uncorrected field contains a fitted plane with gradients of −11.72 mm/yr/km (east–west) and −2.88 mm/yr/km (north–south). The plane explains 64.4% of spatial variance and spans 333 mm/yr peak-to-peak over the valid footprint.

Four processing choices change this field by very different amounts:

- **Adding redundancy.** Seven redundant interferograms (seven closure triangles) change the map by 3.89 mm/yr RMS and the east–west gradient by −0.012 mm/yr/km.
- **Topographic-residual correction** changes the map by about 1 mm/yr RMS.
- **ERA5 tropospheric correction** changes it by 1.25 mm/yr RMS and reduces the east–west gradient by 0.93%.
- **Reference patch.** Changing the reference patch shifts the velocity datum by about 204–208 mm/yr but leaves the gradients unchanged to floating-point precision.
- **Linear-ramp removal** changes the map by about 123 mm/yr RMS and sets the fitted gradient to zero by construction.

Ramp treatment is therefore the dominant processing sensitivity. However, its removal of the plane does not by itself show the plane is an artifact.

Only two GNSS stations with 2024 daily solutions lie inside the scene (ICMX and MMX1, 11 km apart). They provide one reference-invariant test. Over their common window (10 epochs, 2024-04-18 to 2024-10-03):

- GNSS gives an ICMX − MMX1 LOS rate difference of 256.3 mm/yr (95% CI 242.1–270.6).
- No-ramp InSAR gives 240.5 mm/yr (redundant) and 234.3 mm/yr (ERA5).
- Ramp-removed InSAR gives 98.1 and 99.5 mm/yr.

Under the study's documented comparison rule, the redundant no-ramp case falls inside U95, the ERA5 no-ramp case is borderline (1.04 × U95), and both ramp-removed cases differ by about 9.7 × U95. U95 is a study-defined envelope of selected terms, not a demonstrated 95% bound on all error; ICMX interference is unquantified. The rule was encoded in the analysis script, but no independent preregistration is claimed.

GNSS therefore favors no-ramp processing along this one mostly east–west baseline. That conclusion is subject to an official interference warning at ICMX, partial 2024 coverage at MMX1, and only six exact-date epoch pairs. It does not validate the full two-dimensional plane, its north–south component, or a physical interpretation of the field. The velocities are relative descending-LOS rates, not absolute vertical subsidence.

---

## 1. Research question

Earlier leveling, InSAR and GPS work documents substantial land subsidence in Mexico City (Chaussard et al., 2021). That regional history motivates this audit, but the present 2024 descending-LOS result must be evaluated on its own terms. Torres et al. (2012) describe the Sentinel-1 mission; neither paper validates the 2024 measurements analyzed here.

The primary question is: **does independent evidence favor the original long-wavelength InSAR gradient (no ramp removal) or the linear-ramp-removed result?**

Secondary questions:

1. How sensitive is the relative LOS velocity field to network redundancy, topographic-residual correction, tropospheric correction, reference choice, and spatial-ramp removal?
2. Which of these sensitivities change spatial contrasts, and which only change the velocity datum?

## 2. Data

### 2.1 Sentinel-1 interferograms

- **Products.** HyP3 GAMMA interferograms at 80 m (file-name code `INT80`) from Sentinel-1 descending relative orbit 41 [S: `mintpy/PROCESSING_LOG.md` → *Software and configuration*]. The MintPy geometry gives heading −167.738979° [S: `external_validation/GNSS_LOS_VALIDATION.md` → *Geometry and sign verification*]. The mission background is Torres et al. (2012); product-specific values come from the local records.
- **Processing system.** All 31 interferograms were processed by ASF DAAC HyP3 2026 using the hyp3_gamma plugin version 9.1.0 running GAMMA release 20240627. They were projected to WGS 84 / UTM zone 14N at 80 m, and phase was unwrapped by minimum cost flow. ASF's product guide describes the GAMMA workflow and minimum-cost-flow unwrapping (ASF DAAC, n.d.); the 31 local product READMEs record these product versions and credit text [S: `hyp3/*/*.README.md.txt` → header, *Using this data*]. Hogenson et al. (2020) is ASF's requested citation for the HyP3 software, not evidence for this run's configuration.
- **DEM.** HyP3 used the Copernicus DEM GLO-30 [S: `hyp3/*/*_dem.tif.xml` → `idCredit`; ASF DAAC, n.d.; CDSE, n.d.]. The required credit text is reproduced under Acknowledgements.
- **Dates.** 25 acquisitions from 2024-01-13 to 2024-12-26, with no acquisitions between 2024-05-12 and 2024-06-29 [S: `mintpy/PROCESSING_LOG.md` → *Acquisition dates*].
- **Grid.** 346 × 329 pixels, EPSG:32614. The subset is latitude 19.25–19.50°, longitude −99.20 to −98.95° [S: `mintpy_redundant/PROCESSING_LOG.md` → configuration].
- **Networks.**
  - Original: a 24-interferogram chain (25 nodes, no cycles) [S: `mintpy/PROCESSING_LOG.md` → *Status and scientific scope*].
  - Redundant: 31 interferograms (24 plus 7 added), cycle rank 7, seven local closure triangles. Temporal baselines are 12–60 days, perpendicular baselines −138.6 to +127.1 m, and spatial mean coherence 0.856–0.970 (median 0.940) [S: `mintpy_redundant/audit/REDUNDANT_NETWORK_AUDIT.md` → *Inputs and network structure*].

### 2.2 ERA5

- ERA5 hourly pressure-level fields (C3S, n.d.; Hersbach et al., 2020) came through PyAPS3 0.3.7. Jolivet et al. (2011, 2014) describe the atmospheric-delay method and its evaluation; the PyAPS3 documentation identifies the Python 3 implementation adapted for ERA5 (PyAPS developers, n.d.). The recorded processing used the 13:00 UTC product for a 12:34:40 UTC acquisition time [S: `mintpy_redundant_era5/PROCESSING_LOG.md`].
- 25 of 25 dates were retrieved, with no NaN samples [S: `mintpy_redundant_era5/PROCESSING_LOG.md` → *Exact inputs*, *Product validation*; `mintpy_redundant_era5/audit/audit_results.json` → `delay_integrity`].

### 2.3 GNSS

- **Product.** Nevada Geodetic Laboratory (NGL) final daily 24-hour solutions, `tenv3` format, IGS20 frame, for ICMX, MMX1, MXTX, MXTO and TOL2 (NGL, n.d.). Blewitt et al. (2018) is NGL's requested citation for its processed data products; the product format and frame are documented by NGL and in the preserved files.
- **Station providers.**
  - ICMX and TOL2 belong to INEGI's Red Geodésica Nacional Activa (RGNA).
  - MMX1 is listed in the NOAA NGS CORS network as the Mexico City WAAS station, with FAA listed as operator (NOAA NGS, n.d.).
  - The operators of MXTX and MXTO were not investigated and are not attributed here.

  [S: `external_validation/DATA_AVAILABILITY.md` → *GNSS inventory*; `external_validation/source_inventory.json` → `sources`; `external_validation/gnss_station_inventory.csv` → `notes`, `raw_rinex_status`; INEGI, n.d.-a]. No raw RINEX was used; all positions are NGL-processed.
- **Provenance.** Retrieved 2026-09-27; SHA-256 hashes and URLs in [S: `external_validation/gnss_raw/MANIFEST.json`].
- **Discontinuities.** The NGL steps database lists no equipment or earthquake step for any of the five stations between 2023-12-01 and 2025-01-31 [S: `external_validation/gnss_los_results.json` → `qc.<STA>.ngl_steps_2023_12_to_2025_01`].

Only ICMX and MMX1 lie inside the processed scene and have 2024 solutions [S: `external_validation/DATA_AVAILABILITY.md` → *GNSS inventory*].

| Station | Location relative to scene | 2024 daily solutions (raw / cleaned) | Notes |
|---|---|---:|---|
| ICMX | inside, western | 362 / 362 | INEGI states data are unavailable because interference produces low-quality observations (INEGI, n.d.-a) |
| MMX1 | inside, central–eastern | 137 / 133 | Data only 2024-04-16 to 2024-10-10 |
| MXTX | about 10 km NE, outside | 356 / 356 | frame/common-mode diagnostic only |
| MXTO | about 43 km W, outside | 356 / 356 | frame/common-mode diagnostic only |
| TOL2 | about 46 km W, outside | 366 / 366 | frame/common-mode diagnostic only |

Sources: `external_validation/GNSS_LOS_VALIDATION.md` → *Data and provenance*; `external_validation/DATA_AVAILABILITY.md` → station table.

### 2.4 Other official products (not used quantitatively)

INEGI publishes a 2019 Mexico City subsidence raster (approximately 30 m, derived from Sentinel-1 ascending and descending observations to estimate vertical movement; INEGI, 2021, n.d.-b). It is therefore not independent of Sentinel-1 data, and it is not contemporaneous. It was identified but not used [S: `external_validation/DATA_AVAILABILITY.md` → *INEGI subsidence and MOGEZOD*].

## 3. Methods

### 3.1 Time-series processing

All time-series processing used MintPy 1.6.4 (Yunjun et al., 2019) with HyP3 inputs (Hogenson et al., 2020; ASF DAAC, n.d.). This is a small-baseline network analysis in the broader SBAS tradition (Berardino et al., 2002); the actual weighted inversion and correction implementation is MintPy's, not Berardino et al.'s exact algorithm:

- variance-weighted network inversion;
- topographic-residual (DEM-error) correction with pixelwise geometry (Fattahi & Amelung, 2013);
- no primary tropospheric correction, no ionospheric correction (no inputs available), and no primary deramp.

The configuration is in [S: `mintpy_redundant/PROCESSING_LOG.md` → configuration block]. Velocities are first-order polynomial fits to all 25 dates, with the reference date 2024-09-09 and residual-based uncertainty [S: `mintpy/audit/DIAGNOSTIC_AUDIT.md` → *Preservation and common processing choices*].

**Reference.** All cases share reference pixel Y/X 7/186, near the northern edge. The authoritative MintPy HDF5 centre coordinate is UTM E 493,680 m, N 2,155,600 m (19.49499° N, −99.06023°) [S: `mintpy/PROCESSING_LOG.md` → *Reference pixel and reference date*]. See §5.4 for a half-pixel reporting discrepancy.

### 3.2 Sensitivity cases and label reconciliation

The stage reports reuse the letters A–F with **different meanings**. This manuscript uses the ERA5/GNSS labels throughout.

| Manuscript label | Description | Chain audit (`mintpy/audit`) | Redundant audit (`mintpy_redundant/audit`) | ERA5 audit and GNSS validation |
|---|---|---|---|---|
| Chain-NR | 24-edge chain, topographic correction, no ramp | B | original "baseline" in comparisons | — |
| Chain-LR | 24-edge chain, topographic correction, linear ramp removed | D | — | — |
| **A** | 31-edge redundant, topographic correction, no ramp (primary) | — | B_topo_primary | A |
| **B** | 31-edge redundant, topographic correction, linear ramp removed | — | D_topo_linearRamp | B |
| **C** | A plus ERA5 correction | — | — | C |
| **D** | C with linear ramp removed | — | — | D |
| Excl-2 | A with the two closure-flagged added edges excluded (diagnostic) | — | F_exclude_flagged_topo | — |
| Chain-QR | Chain, quadratic ramp removed (exploratory) | E2 | — | — |

**Ramp removal.** Linear and quadratic ramps were removed with MintPy `remove_ramp.py` using the temporal-coherence mask, applied to each epoch of the time series before the velocity fit [S: `mintpy/audit/DIAGNOSTIC_AUDIT.md` → *Exact commands*].

**ERA5.** The correction was applied with MintPy's `tropo_pyaps3.py` to a copy of the topographically corrected series. That script computes slant delay from ERA5 pressure-level data (C3S, n.d.; Hersbach et al., 2020) with PyAPS3 (Jolivet et al., 2011, 2014; PyAPS developers, n.d.) [S: `mintpy_redundant_era5/PROCESSING_LOG.md` → *Commands and outcomes*].

The ERA5-corrected HDF5 files carry the attribute `mintpy.troposphericDelay.method = no`. This is a load-time configuration record, not processing history (§5.4, item 7; `final_report/PROVENANCE_NOTE_ERA5_METADATA.md`).

### 3.3 Diagnostics

- **Plane fits.** Least-squares planes fitted to each velocity map on the common mask give east–west and north–south gradients, peak-to-peak amplitude and variance explained [S: `mintpy_redundant_era5/audit/case_statistics.csv`].
- **Closure (diagnostic only; no closure-based correction was applied).** Our own script, `mintpy_redundant/closure_diagnostics.py`, implements the closure check:
  - It referenced each unwrapped interferogram to pixel Y/X 7/186.
  - For each of the seven triangles (a, b, c) it formed C = φ_ab + φ_bc − φ_ac.
  - It took the integer ambiguity as round((C − wrap(C))/2π), with wrap(·) mapping to [−π, π). MintPy's phase-closure method uses integer ambiguities of interferogram triplets (Yunjun et al., 2019; MintPy developers, n.d.-c); the displayed equation and threshold describe this project's own script, not a result imported from that paper.
  - It counted a pixel as failing when the ambiguity ≠ 0 and all three edges were valid.

  The per-pixel count of failing triangles exactly reproduces MintPy's `numTriNonzeroIntAmbiguity.h5` from the `quick_overview` step on all jointly finite pixels [S: `mintpy_redundant/audit/closure_results.json` → `mintpy_aggregate_exact_match_on_joint_finite_pixels` = true].

  MintPy's phase-closure unwrapping-error *correction* was **not** run: `correct_unwrap_error` resolved to method `no` and changed nothing [S: `mintpy_redundant/PROCESSING_LOG.md` → *Warnings and processing decisions*]. Closure results therefore diagnose the loaded HyP3 unwrapped phases. Per-triangle results are in [S: `mintpy_redundant/audit/audit_results.json` → `closure.triangles`]. The Excl-2 case is a separate exclusion diagnostic, not a correction [S: `mintpy_redundant/PROCESSING_LOG.md` → *Warnings and processing decisions*].
- **Reference sensitivity.** Three 9 × 9 candidate patches (northern existing, western high terrain, southwestern high terrain) were chosen by geometry and elevation only, then applied analytically [S: `mintpy/audit/DIAGNOSTIC_AUDIT.md` → *Alternative candidate reference areas*].

### 3.4 GNSS-to-LOS comparison

Implementation: `external_validation/run_gnss_los_validation.py`.

**Quality control.** Duplicate dates were checked for (none found). A formal-sigma rule excluded days with σ above 5× the station median (none excluded). A robust detrended-residual rule excluded days beyond max(6 × MAD, 5 mm E/N or 15 mm U). Jump candidates were reported but never corrected, and gaps were never interpolated.

The outcome was four MMX1 exclusions (east-component spikes on 2024-08-16, 08-28, 08-30 and 09-09) and none elsewhere [S: `external_validation/GNSS_LOS_VALIDATION.md` → *Parsing and quality control*].

**Projection into LOS.** ENU displacements were projected with MintPy's own `enu2los` formula:

`LOS = −E sin i sin a + N sin i cos a + U cos i`

where a = −102.261021° and i is sampled at each station pixel: 32.319° at ICMX (Y/X 130/41) and 31.625° at MMX1 (Y/X 95/175). Positive LOS means motion toward the satellite (MintPy developers, n.d.-a). The projection coefficients follow MintPy's official source formula (MintPy developers, n.d.-b), and the numerical sign was checked against the locally used code [S: `external_validation/GNSS_LOS_VALIDATION.md` → *Geometry and sign verification*].

**Station geometry (Figure 7).** Station coordinates are median 2024 NGL positions. They were converted with pyproj to EPSG:32614, then to pixels with floor((coordinate − X_FIRST|Y_FIRST)/STEP) on the corner-registered grid [S: `external_validation/gnss_los_results.json` → `geometry.pixel_rule`].

Figure 7 plots both stations, their 9 × 9-pixel extraction patches, the connecting baseline and the separate InSAR reference pixel on the case-A velocity map. Its plotting script re-derives the station pixels and the 9 × 9 patch medians and asserts that they match the recorded values [S: `final_report/make_fig_station_locations.py`].

The baseline between the station coordinates is 11.1 km (10.76 km E, 2.87 km N). The plane calculation in §4.3 uses pixel-index offsets, 10.72 km E and 2.80 km N [S: `external_validation/gnss_los_results.json` → `ramp_plane.A_minus_B`].

**Matching.** Each GNSS day was matched to a Sentinel-1 date within ±1 day, without interpolation. The common ICMX/MMX1/Sentinel window is 10 epochs, 2024-04-18 to 2024-10-03 (168 days); six of these are exact same-day pairs [S: `external_validation/gnss_los_results.json` → `matching`].

**Observable.** The primary observable is reference-invariant: ICMX − MMX1 for both GNSS and InSAR. InSAR values are medians over 5 × 5, 9 × 9 (primary) and 13 × 13 pixel patches. Every patch pixel was valid, and median temporal coherence was ≥ 0.9995 [S: `external_validation/GNSS_LOS_VALIDATION.md` → *InSAR patch sampling*].

**Study-defined decision rule** (documented in the analysis script; no independent preregistration is claimed):

- U95 = √(AR(1)-adjusted statistical half-width² + systematic²).
- The systematic term combines four effects: GNSS cadence, outlier treatment, matching tolerance, and patch-size half-range.
- A case is *consistent* if |GNSS − InSAR| ≤ U95 [S: `external_validation/gnss_los_results.json` → `decision`].

U95 combines only the listed statistical and sensitivity terms. It has not been shown to cover 95% of all possible errors, and excludes the unquantified ICMX interference. A binary label close to the threshold, especially case C, should not be read as a sharp scientific separation.

## 4. Results

### 4.1 The long-wavelength field and processing sensitivities (full-year, 25 epochs)

Case A has a fitted plane with gradients of −11.719 mm/yr/km (east–west) and −2.881 mm/yr/km (north–south). The plane has a magnitude of 12.07 mm/yr/km, spans 332.7 mm/yr peak-to-peak and explains 64.39% of variance [S: `mintpy_redundant_era5/audit/case_statistics.csv` → `A_baseline_no_ramp`]. The fitted gradients of all four cases are compared in Figure S1: A and C are nearly identical, and B and D are about 10⁻⁶ mm/yr/km because their planes were removed. The median relative LOS velocity is +146.58 mm/yr, and the 5th/95th percentiles are −58.54 / +203.56 mm/yr (same source).

| Sensitivity | Map change (RMS, mm/yr) | Effect on E–W gradient | Source |
|---|---:|---|---|
| Topographic correction (chain) | 0.975 | small | `mintpy/audit/DIAGNOSTIC_AUDIT.md` → Cases, row A |
| Topographic correction (redundant) | 0.971 | −11.744 → −11.719 | `REDUNDANT_NETWORK_AUDIT.md` → *Velocity and correction sensitivity* |
| Chain → redundant network (80,787 px) | 3.891 | −0.012 mm/yr/km | `mintpy_redundant/audit/audit_results.json` → `baseline_comparison` |
| Exclude two closure-flagged edges | 3.688 | −11.719 → −11.696 | `REDUNDANT_NETWORK_AUDIT.md` |
| ERA5 (C − A) | 1.252 | −0.93% (−11.719 → −11.610) | `mintpy_redundant_era5/audit/audit_results.json` → `comparisons` |
| Reference patch (north ↔ W/SW) | datum shift 204.7–207.5 | unchanged (< 2×10⁻⁷ mm/yr/km) | `mintpy/audit/DIAGNOSTIC_AUDIT.md` → *Reference-invariance demonstration*; `mintpy_redundant/audit/reference_sensitivity.csv` |
| Linear ramp (B − A) | 123.151 | set to ~0 by construction | `mintpy_redundant_era5/audit/audit_results.json` → `ramp_effect_baseline_mm_yr` |
| Linear ramp after ERA5 (D − C) | 122.350 | ~0 | same → `ramp_effect_ERA5_mm_yr` |
| Quadratic ramp (chain, exploratory) | 137.939 | ~0 | `mintpy/audit/DIAGNOSTIC_AUDIT.md` → Cases, row E2 |

**Ramp removal.** The case medians change from +146.584 (A) to +9.155 (B) mm/yr, so median(B) − median(A) is approximately −137.430 mm/yr. The median of the pixelwise B − A map is approximately −101.984 mm/yr; these are different statistics [S: `mintpy_redundant_era5/audit/case_statistics.csv` → A/B; `mintpy_redundant_era5/audit/audit_results.json` → `comparisons.ramp_effect_baseline_mm_yr.median`].

**Reference choice.** It changes absolute-looking local rates by more than 200 mm/yr, but by construction it leaves every spatial difference, and so every gradient, unchanged. Reference choice is a datum choice. It neither validates nor invalidates spatial contrasts.

**Original mid-year bridge interferograms.** The two original chain edges spanning 2024-05-12–06-29 and 2024-06-29–08-04 each contain a broad east–west phase gradient: 0.3477 and 0.3657 rad/km, with plane R² of 0.632 and 0.697 [S: `mintpy/audit/audit_results.json` → `bridge_interferograms`]. Both become sides of tested closure triangles in the expanded network: 04-30/05-12/06-29 and 06-29/08-04/08-16. The added long edges close those loops. These tests expose local inconsistencies but cannot identify which edge is faulty or prove that the broad gradient is deformation.

### 4.2 Network redundancy and closure

- **Closure failures.** Across the seven triangles, 2,334 of 81,299 valid pixels (2.871%) have at least one non-zero integer closure ambiguity [S: `mintpy_redundant/audit/audit_results.json` → `closure.mintpy_nonzero_pct`].
- **Mid-year concentration.** Failures cluster in the two mid-year triangles: 1.866% for 2024-04-30/05-12/06-29 and 0.955% for 06-29/08-04/08-16, with ambiguities of ±2 cycles. Mean coherence at failing pixels is much lower than at passing pixels (0.546 vs 0.905 and 0.334 vs 0.886) [same → `closure.triangles`].
- **Chain vs redundant differences.** They concentrate at closure-failure pixels: RMS 21.09 mm/yr there, against 1.74 mm/yr at closure-clean pixels [same → `baseline_comparison`].
- **Temporal coherence.** Median 0.99978 in the redundant inversion. The chain inversion's value is exactly 1.0 everywhere by construction [same → `temporal_coherence`].

### 4.3 GNSS comparison (common window only: 10 epochs, 2024-04-18 → 2024-10-03)

**GNSS differential.** ICMX − MMX1 LOS = **256.3 mm/yr**. Its 95% range is 242.1–270.6 by OLS and 246.5–264.5 by block bootstrap; Theil–Sen gives 255.0 [S: `external_validation/gnss_los_results.json` → `gnss_differential`].

Main comparison (9 × 9 patches) [S: `external_validation/gnss_los_comparison.csv`, rows `patch_size_px = 9`; `external_validation/gnss_los_results.json` → `decision`]:

| Case | InSAR ICMX − MMX1 (mm/yr) | GNSS − InSAR (mm/yr) | U95 | \|Δ\|/U95 | Aligned RMSE (mm) | Verdict |
|---|---:|---:|---:|---:|---:|---|
| A | 240.5 | +15.8 | 19.5 | 0.81 | 3.5 | consistent |
| B | 98.1 | +158.2 | 16.3 | 9.72 | 25.7 | rejected |
| C | 234.3 | +22.0 | 21.2 | 1.04 | 4.6 | rejected, marginally |
| D | 99.5 | +156.9 | 16.1 | 9.76 | 25.5 | rejected |

**Robustness** [S: `external_validation/gnss_los_comparison.csv`]:

- For A, the GNSS − InSAR difference varies from +14.6 to +17.9 mm/yr across patch sizes.
- Using exact-date epochs only gives +10.0; using raw unfiltered GNSS gives +21.5; leave-one-epoch-out gives +12.8 to +18.6.
- In every variant, the ramp-removed cases stay at 155–166 mm/yr.

**Correlation does not discriminate.** Raw correlation is ≥ 0.997 in all four cases, because a plane changes amplitude, not temporal shape.

**Full-year values are not equivalent.** The full-year InSAR ICMX − MMX1 differentials are 227.7 (A), 94.2 (B), 227.3 (C) and 94.9 (D) mm/yr [S: `external_validation/gnss_los_comparison.csv` → `insar_diff_full_period_mm_yr`]. These cover 2024-01-13 to 2024-12-26 and are **not** comparable with the 168-day GNSS rate. The common-window minus full-year InSAR difference is +12.8 mm/yr for A and +3.9 mm/yr for B.

**Plane contribution along the baseline.** Over the full year, the fitted A − B plane contributes 133.7 mm/yr to the ICMX − MMX1 difference. The baseline used here is 10.72 km east and 2.80 km north, from station pixel indices [S: `external_validation/gnss_los_results.json` → `ramp_plane.A_minus_B`]. The station coordinates themselves are 10.76 km east and 2.87 km north apart (Figure 7).

**GNSS cadence effect.** Using all 122 shared daily GNSS solutions in the window gives 244.9 mm/yr instead of 256.3. This 11.5 mm/yr effect is the largest single systematic term [S: `external_validation/gnss_los_results.json` → `gnss_differential.daily_common_window_rate_mm_yr`; `decision.*.sys_cadence`].

**Station-quality checks** [S: `external_validation/GNSS_LOS_VALIDATION.md` → *ICMX quality warning*]:

- ICMX passes all numerical QC, with detrended LOS scatter of 4.2 mm.
- Its annual LOS rate was −15 to −36 mm/yr in 2017–2023, then −41.0 (2024) and −43.4 (2025); its vertical rate roughly doubled from 2023 to 2024.
- Reconciling the ramp-removed cases would require about 73 mm of unmodeled differential station displacement over 168 days. The available daily scatter and annual histories do not quantify or rule out a smooth interference-related bias at ICMX.

**Regional stations.** MXTX, MXTO and TOL2 have 2024 LOS rates between −16.3 and −45.0 mm/yr. Detrended-residual correlations are 0.17–0.46. A uniform frame error would leak less than 0.1 mm/yr into the station difference [S: `external_validation/gnss_los_results.json` → `regional`]. These stations lie outside the scene and do not sample the InSAR plane.

## 5. Discussion

### 5.1 Ramp removal is a sensitivity, not a diagnosis

Linear-ramp removal forces the fitted plane to zero by construction. That it "eliminates" the gradient is therefore arithmetic, and says nothing about whether the gradient was orbital, atmospheric, propagated unwrapping error, or real deformation.

The earlier stage reports describe the gradient as "not robust to ramp treatment" [S: `mintpy/audit/DIAGNOSTIC_AUDIT.md` → *Executive finding*]. That statement is correct as a description of sensitivity. It should not be read as evidence that the gradient is an artifact.

### 5.2 What the GNSS test adds

The ICMX − MMX1 difference is the only independent, reference-invariant constraint available along this baseline. Linear-ramp removal takes away about 142 mm/yr of the common-window InSAR differential: 240.5 − 98.1 [S: `external_validation/gnss_los_comparison.csv`]. B and D disagree with GNSS far more than the selected terms in U95, while ICMX interference remains unquantified.

The no-ramp cases are close but not exact. Both under-estimate the GNSS contrast by 16–22 mm/yr (6–9%). The best-supported statement is that **GNSS favors no-ramp processing along the tested ICMX–MMX1 baseline**, subject to the ICMX interference warning, MMX1's partial year, and the small number of epochs.

### 5.3 What the GNSS test cannot establish

**Only one direction is tested.** The baseline is mostly east–west (10.72 km E, 2.80 km N). The plane's north–south gradient, curvature, and behaviour in the rest of the scene are untested. Agreement at two points does not validate the complete spatial plane.

**Data are sparse and short.** There are two stations and 10 epochs (6 exact) over 168 days.

**Atmospheric error is not excluded.** ERA5 changes the field by about 1 mm/yr RMS, and slightly worsens the GNSS residual at this baseline (+22.0 vs +15.8 mm/yr). A small response to one coarse, hourly reanalysis correction cannot rule out unresolved local or turbulent atmospheric structure (C3S, n.d.; Jolivet et al., 2014); this study used one nearest-hour realization [S: `mintpy_redundant_era5/audit/ATMOSPHERIC_SENSITIVITY_AUDIT.md` → *Limitations*].

**Unwrapping is only partly checked.** Closure tests seven isolated local triangles, including triangles containing both original mid-year bridge interferograms. Links outside those triangles have no cycle check. Closure failure identifies an inconsistent triangle, not a uniquely faulty edge, and sparse redundancy does not validate every interferogram [S: `mintpy_redundant/audit/REDUNDANT_NETWORK_AUDIT.md` → *Inputs and network structure*].

**Rates are relative LOS, not vertical.** All InSAR rates are relative descending-LOS velocities referenced to Y/X 7/186. They are not absolute and not vertical subsidence. The LOS projection mixes east and up (east coefficient ≈ +0.52, up coefficient ≈ +0.85; MintPy developers, n.d.-a, n.d.-b), so signs cannot be read directly as subsidence or uplift.

### 5.4 Reconciled and unresolved discrepancies between stage reports

| # | Discrepancy | Resolution |
|---|---|---|
| 1 | Case letters A–F mean different cases in different reports | **Resolved** by the mapping table in §3.2 |
| 2 | Reference "centre" given as E 493,640 / N 2,155,640 in the audits but as 493,680 / 2,155,600 in the HDF5 attributes | **Resolved.** `run_redundant_audit.py` computes `X_FIRST + i·step`, which is the pixel's upper-left corner. The HDF5 value is the pixel centre, which is authoritative [S: `mintpy/PROCESSING_LOG.md` → *Reference pixel*] |
| 3 | Linear-ramp RMS reported as 122.654, 122.974 and 123.151 mm/yr | **Resolved.** Different comparison maps: chain-LR vs chain; redundant-LR vs *chain*; redundant-LR vs redundant (same-network, used here) |
| 4 | Chain E–W gradient −11.7228 [`mintpy/audit`, 80,836 px] vs −11.7057 [`mintpy_redundant/audit` → `baseline_comparison.original_east_gradient`, 80,787 common px] | **Unresolved without recomputation.** Probably the different pixel masks used for the plane fit. The 0.017 mm/yr/km difference is immaterial to every conclusion |
| 5 | Northern reference patch mean −0.729 (chain) vs −0.616 mm/yr (redundant); W/SW offsets "205–208" vs 204.0/205.8 | **Resolved.** Different networks, and patch-mean vs relative-to-north-patch quantities |
| 6 | Residual-RMS threshold 0.0066 m (chain log) vs 0.0064 m (redundant log) | **Resolved.** Separate inversions; no conflict |
| 7 | `mintpy_redundant_era5/timeseries_demErr_ERA5.h5` (and derivatives) has attribute `mintpy.troposphericDelay.method` = `no` | **Documented; metadata-only.** The attribute is a load-time configuration value, not processing history. The logged direct `tropo_pyaps3.py` command, 25/25-date delay integrity and 1.252 mm/yr RMS C − A change support that ERA5 was applied. The previously reported 3.2 mm check cannot be independently repeated because its code was not preserved, so it is not used as evidence here. See `final_report/PROVENANCE_NOTE_ERA5_METADATA.md` |
| 8 | An earlier GNSS draft was superseded; the final GNSS − InSAR value for A is +15.8 mm/yr | **Documented.** The GNSS validation log records the station-pixel indexing and per-case coherence corrections, but the superseded draft archive is not included in this release. Its former numerical value is not used as evidence here [S: `external_validation/GNSS_LOS_VALIDATION.md` → *Superseded draft*; `external_validation/gnss_los_comparison.csv` → A, 9 × 9 patch] |

## 6. Limitations

1. **One year of data.** A linear model over less than a year cannot separate persistent, seasonal and atmospheric components.
2. **Unwrapping is only partly validated.** Closure covers seven isolated triangles, including the two original mid-year bridge edges; other links remain unchecked.
3. **No ionospheric correction.** Only a single ERA5 realization was used for the troposphere.
4. **The reference patch is unvalidated.** It sits near the northern edge and has no independent stability evidence.
5. **GNSS covers two stations and one baseline.** ICMX carries an official interference warning. MMX1 covers only April–October 2024. The comparison has 10 epochs (6 exact). Formal intervals exclude unquantified systematics such as monument motion and ICMX interference.
6. **Only descending geometry is available.** East and up cannot be separated; LOS rates are relative, not vertical.
7. **The exploratory quadratic ramp may remove real signal.** It is reported only as a sensitivity.

## 7. Conclusion

Processing choices affect this Mexico City Sentinel-1 time series very unequally:

- Adding redundancy, topographic correction and ERA5 each change the relative LOS field by about 1–4 mm/yr RMS and leave the broad gradient essentially unchanged.
- Reference choice shifts only the datum.
- Linear-ramp removal changes the field by about 123 mm/yr RMS.

The only independent test available, the ICMX − MMX1 GNSS difference, favors retaining the no-ramp gradient along that baseline and rejects linear-ramp removal there. That agreement is local, is qualified by station-quality and uncertainty limits, and does not validate the full spatial plane or its physical cause.

**Future work.** A separately processed 2024 ascending Sentinel-1 stack is the next decisive experiment. It would test whether the plane behaves as expected under a second look geometry and allow approximate east–up decomposition.

## 8. Reproducibility

**Software and environment.**

- MintPy 1.6.4 (2026-07-25) and PyAPS3 0.3.7, run via the `./mintpy-run` Docker wrapper (`ghcr.io/insarlab/mintpy:latest`).
- Configurations: `mintpy_config.txt` and `mintpy_redundant_era5/mintpy_config_era5.txt`.

**Command records.**

- `mintpy/PROCESSING_LOG.md` and `mintpy/audit/DIAGNOSTIC_AUDIT.md` → *Exact commands*
- `mintpy_redundant/PROCESSING_LOG.md`
- `mintpy_redundant_era5/PROCESSING_LOG.md`
- `external_validation/GNSS_LOS_VALIDATION.md` → *Commands*

**Analysis scripts.**

- `mintpy/audit/run_diagnostic_audit.py`
- `mintpy_redundant/closure_diagnostics.py`
- `mintpy_redundant/audit/run_redundant_audit.py`
- `mintpy_redundant_era5/audit/run_atmospheric_audit.py`
- `external_validation/run_gnss_los_validation.py`
- `final_report/make_fig_station_locations.py` (Figure 7; plotting only, reads existing outputs through a read-only mount)

**Machine-readable results.** `audit_results.json` and `case_statistics.csv` in each audit directory, `external_validation/gnss_los_results.json` and `external_validation/gnss_los_comparison.csv`.

**Integrity checks.**

- The ERA5 stage recorded SHA-1 values and mtimes for key baseline HDF5 files before and after processing [S: `mintpy_redundant_era5/PROCESSING_LOG.md` → *Baseline integrity verification*].
- The GNSS stage verified 1,131 protected files unchanged by SHA-256 [S: `external_validation/GNSS_LOS_VALIDATION.md` → *Commands*].
- No processing was rerun for this manuscript. Figure 7 is a new plot of existing outputs. Its script asserts that station pixels and 9 × 9 patch medians reproduce `external_validation/gnss_los_results.json`.

**Data availability.**

- This GitHub package includes HyP3 product READMEs and DEM metadata under `hyp3/`, but excludes radar ZIPs, TIFFs, HDF5 stacks and ERA5 GRIB files. The original local project retains those products.
- Raw GNSS files are in `external_validation/gnss_raw/`, with URLs and hashes in `MANIFEST.json`.
- Full pipeline reruns require the excluded products and the software environment described above. This release preserves scripts and results but does not claim a self-contained rerun.

## Acknowledgements

**Sentinel-1 / HyP3 product credit.** ASF's credit guidance (ASF DAAC, n.d.) and all 31 HyP3 product READMEs require the following product-specific acknowledgement [S: `hyp3/*/*.README.md.txt` → *Using this data*]:

> ASF DAAC HyP3 2026 using the hyp3_gamma plugin version 9.1.0 running GAMMA release 20240627. Contains modified Copernicus Sentinel data 2024, processed by ESA.

Any figure showing these data or products derived from them (Figures 1–3, 5–7 and S1) should carry the README's image credit: "InSAR product processed by ASF DAAC HyP3 2026 using GAMMA software. Contains modified Copernicus Sentinel data 2024, processed by ESA."

**DEM.** Credit as given in the HyP3 DEM metadata [S: `hyp3/*/*_dem.tif.xml` → `idCredit`] and the Copernicus DEM citation guidance (CDSE, n.d.): "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."

**GNSS.**
- Processed daily position time series are from the Nevada Geodetic Laboratory (Blewitt et al., 2018; NGL, n.d.).
- Original station data for ICMX and TOL2 are attributed to INEGI's Red Geodésica Nacional Activa (RGNA; INEGI, n.d.-a); no raw RINEX was processed here.
- MMX1 (Mexico City WAAS) is listed in the NOAA NGS CORS network with FAA as operator (NOAA NGS, n.d.); this study uses NGL-processed positions.
- The station operators for MXTX and MXTO have not been identified, and those stations were used only as a regional diagnostic.

[S: `external_validation/DATA_AVAILABILITY.md` → *GNSS inventory*; `external_validation/gnss_station_inventory.csv`].

**Weather model.** ERA5 pressure-level data came from the Copernicus Climate Change Service Climate Data Store (C3S, n.d.; Hersbach et al., 2020), accessed in the recorded PyAPS3 workflow [S: `mintpy_redundant_era5/PROCESSING_LOG.md` → *Commands and outcomes*].

## References

### Research literature and software citation

- Berardino, P., Fornaro, G., Lanari, R., & Sansosti, E. (2002). A new algorithm for surface deformation monitoring based on small baseline differential SAR interferograms. *IEEE Transactions on Geoscience and Remote Sensing, 40*(11), 2375–2383. https://doi.org/10.1109/TGRS.2002.803792
- Blewitt, G., Hammond, W. C., & Kreemer, C. (2018). Harnessing the GPS data explosion for interdisciplinary science. *Eos, 99*. https://doi.org/10.1029/2018EO104623
- Chaussard, E., Havazli, E., Fattahi, H., Cabral-Cano, E., & Solano-Rojas, D. (2021). Over a century of sinking in Mexico City: No hope for significant elevation and storage capacity recovery. *Journal of Geophysical Research: Solid Earth, 126*, e2020JB020648. https://doi.org/10.1029/2020JB020648
- Fattahi, H., & Amelung, F. (2013). DEM error correction in InSAR time series. *IEEE Transactions on Geoscience and Remote Sensing, 51*(7), 4249–4259. https://doi.org/10.1109/TGRS.2012.2227761
- Hersbach, H., Bell, B., Berrisford, P., Hirahara, S., Horányi, A., Muñoz-Sabater, J., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society, 146*(730), 1999–2049. https://doi.org/10.1002/qj.3803
- Hogenson, K., Kristenson, H., Kennedy, J., Johnston, A., Rine, J., Logan, T., Zhu, J., Williams, F., Herrmann, J., Smale, J., & Meyer, F. (2020). *Hybrid Pluggable Processing Pipeline (HyP3): A cloud-native infrastructure for generic processing of SAR data* [Computer software]. https://doi.org/10.5281/zenodo.4646138
- Jolivet, R., Grandin, R., Lasserre, C., Doin, M.-P., & Peltzer, G. (2011). Systematic InSAR tropospheric phase delay corrections from global meteorological reanalysis data. *Geophysical Research Letters, 38*(17), L17311. https://doi.org/10.1029/2011GL048757
- Jolivet, R., Agram, P. S., Lin, N. Y., Simons, M., Doin, M.-P., Peltzer, G., & Li, Z. (2014). Improving InSAR geodesy using global atmospheric models. *Journal of Geophysical Research: Solid Earth, 119*(3), 2324–2341. https://doi.org/10.1002/2013JB010588
- Torres, R., Snoeij, P., Geudtner, D., Bibby, D., Davidson, M., Attema, E., et al. (2012). GMES Sentinel-1 mission. *Remote Sensing of Environment, 120*, 9–24. https://doi.org/10.1016/j.rse.2011.05.028
- Yunjun, Z., Fattahi, H., & Amelung, F. (2019). Small baseline InSAR time series analysis: Unwrapping error correction and noise reduction. *Computers & Geosciences, 133*, 104331. https://doi.org/10.1016/j.cageo.2019.104331

### Official datasets and documentation

- Alaska Satellite Facility Distributed Active Archive Center (ASF DAAC). (n.d.). *Sentinel-1 InSAR product guide*. https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/
- Copernicus Climate Change Service (C3S). (n.d.). *ERA5 hourly data on pressure levels from 1940 to present* [Dataset]. Climate Data Store. https://doi.org/10.24381/cds.bd0915c6
- Copernicus Data Space Ecosystem (CDSE). (n.d.). *Copernicus DEM—Global and European Digital Elevation Model* [Dataset documentation and citation guidance]. https://doi.org/10.5270/ESA-c5d3d65
- Instituto Nacional de Estadística y Geografía (INEGI). (n.d.-a). *Archivos RINEX de la Red Geodésica Nacional Activa*. https://www.inegi.org.mx/app/geo2/rgna/
- Instituto Nacional de Estadística y Geografía (INEGI). (n.d.-b). *Distribución espacial y magnitud de la subsidencia en la Ciudad de México en 2019* [Product catalog]. https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463849650
- Instituto Nacional de Estadística y Geografía (INEGI). (2021). *Detección de zonas de subsidencia en México con técnicas satelitales* (Vol. 2). https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825199395.pdf
- MintPy developers. (n.d.-a). *Frequently asked questions: Line-of-sight sign convention*. https://github.com/insarlab/MintPy/blob/main/docs/FAQs.md
- MintPy developers. (n.d.-b). *`asc_desc2horz_vert.py`: ENU-to-LOS projection source*. https://github.com/insarlab/MintPy/blob/main/src/mintpy/asc_desc2horz_vert.py
- MintPy developers. (n.d.-c). *`unwrap_error_phase_closure.py`: Phase-closure implementation*. https://github.com/insarlab/MintPy/blob/main/src/mintpy/unwrap_error_phase_closure.py
- Nevada Geodetic Laboratory (NGL). (n.d.). *Plug and Play GPS data products: Final daily IGS20 solutions and steps database*. https://geodesy.unr.edu/PlugNPlayPortal.php
- NOAA National Geodetic Survey (NOAA NGS). (n.d.). *All NGS CORS sites*. https://geodesy.noaa.gov/CORS/sort_sites.shtml
- PyAPS developers. (n.d.). *PyAPS: Python-based atmospheric phase screen* [Software documentation]. https://github.com/insarlab/PyAPS

The HyP3 software citation follows ASF's requested form in the product README. Its concept DOI may resolve to a later Zenodo version; it does not identify the exact 9.1.0 plugin build. Product-specific software versions and mandatory data credits are recorded in the local READMEs and Acknowledgements. NGL's own portal requests Blewitt et al. (2018) when citing its processed products; the portal and preserved `tenv3` files establish the IGS20 format and station data. The providers of MXTX and MXTO original observations remain unattributed; those stations serve only as regional diagnostics. Sources considered but not used for claims are omitted from this reference list. See `final_report/REFERENCE_AUDIT.md` for the claim-to-source check.
