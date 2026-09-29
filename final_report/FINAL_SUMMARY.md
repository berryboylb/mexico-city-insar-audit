# Final summary

Publication interpretation (2026-09-29): this summary is read with the corrected manuscript and evidence table. The aim is to use 2024 Sentinel-1 observations to study relative ground movement in part of Mexico City and assess how reliably they support an interpretation of land subsidence. The main result is better GNSS agreement without linear-ramp removal along ICMX–MMX1; it does not validate the entire map, identify the cause, or establish absolute vertical subsidence. U95 is a study-defined envelope of selected terms, and case C is borderline. ICMX interference remains unquantified.

## What we asked

Satellite radar (Sentinel-1, 2024, one descending track) shows a strong west-to-east gradient in how fast the ground in central–eastern Mexico City appears to move toward or away from the satellite. Such a gradient can be real ground motion, or it can come from orbit errors, the atmosphere, or processing mistakes.

A common processing step, linear-ramp removal, simply subtracts a best-fit tilted plane from the map. The question was: **should that step be applied here?** In other words, does independent evidence support the original gradient or the ramp-removed map?

## What we found

1. **Ramp choice dominates.** Removing the ramp changes the velocity map by about 123 mm/yr on average (RMS). The other processing choices change it far less:
   - adding seven extra interferograms: 3.9 mm/yr;
   - topographic correction: about 1 mm/yr;
   - weather-model (ERA5) correction: 1.3 mm/yr.
2. **Removing the ramp proves nothing by itself.** Subtracting a plane always removes the plane. That says nothing about whether the plane was an error or real motion.
3. **The reference point sets the zero level, not the pattern.** Moving it shifts every value by about 205–208 mm/yr but leaves every difference between two places unchanged. It cannot confirm or refute the gradient.
4. **The GNSS stations side with "no ramp" on the one line they can test.** Two GPS stations inside the scene, ICMX (west) and MMX1 (east, about 11 km apart), measured a difference of about 256 mm/yr in the satellite's viewing direction between April and October 2024. Over the same period:
   - without ramp removal, the radar gives about 240 mm/yr (redundant network) or 234 mm/yr (with ERA5); the first lies within the study-defined comparison envelope and the second is borderline;
   - with ramp removal, it gives about 98–100 mm/yr; this is roughly 157 mm/yr too small, about ten times the selected comparison envelope. That envelope does not quantify all station errors.
5. **The agreement is not perfect.** Even without ramp removal, the radar under-estimates the GNSS contrast by 16–22 mm/yr.

## What this contributes

- A traceable audit that ranks processing sensitivities for this dataset.
- A clear separation of choices that shift the zero level (reference) from those that change spatial patterns (ramp).
- A reference-independent GNSS test showing that linear-ramp removal substantially reduces the measured contrast along this one baseline, conditional on GNSS station quality.

## Limits

- **One line, two points.** GNSS tests the gradient only along the ICMX–MMX1 line, which runs mostly west–east. The north–south part of the gradient, and the rest of the map, are untested.
- **Station quality.** INEGI officially warns that ICMX has interference problems. Its effect is unquantified; low scatter and annual histories cannot rule out a smooth bias. ICMX's rate also sped up in 2024. MMX1 has data only from April to October 2024. There are only 10 matched dates, 6 of them exact.
- **Not vertical subsidence.** All radar rates are relative motion along the satellite's line of sight, measured against an arbitrary reference pixel. They mix east–west and vertical motion.
- **Atmosphere and unwrapping are not fully ruled out.** The small ERA5 effect does not prove there is no atmospheric error. The seven closure loops check only small parts of the interferogram network.
- **Short record.** Less than one year of data cannot separate steady motion from seasonal effects.

## Reporting gaps: status after the 2026-09-28 reporting pass

**Resolved:**

1. **Bibliography.** `MANUSCRIPT_DRAFT.md` now gives in-text citations and full, DOI-checked entries for:
   - MintPy (Yunjun et al., 2019);
   - HyP3 (Hogenson et al., 2020);
   - PyAPS (Jolivet et al., 2011, 2014);
   - ERA5 (Hersbach et al., 2020);
   - NGL (Blewitt et al., 2018);
   - DEM-error correction (Fattahi & Amelung, 2013).

   Acknowledgements add the HyP3 README product and version credit, the Copernicus DEM credit, and GNSS station-provider attribution (INEGI RGNA for ICMX and TOL2; NOAA NGS CORS for MMX1). §3.3 now describes our own closure diagnostic and states that no closure-based correction was run.
2. **Station location map.** `fig_station_locations.png`/`.pdf` (Figure 7) come with a reproducible script, `make_fig_station_locations.py`. The script checks the station pixels and patch medians against the recorded results.
3. **Misleading metadata.** Documented in `PROVENANCE_NOTE_ERA5_METADATA.md`:
   - File: `mintpy_redundant_era5/timeseries_demErr_ERA5.h5` and its derivatives.
   - Attribute: `mintpy.troposphericDelay.method`, value `no`.
   - The note sets out the existing evidence that ERA5 was applied. No HDF5 file was changed.
4. **ERA5 gradient figure.** Inspected, and it matches `audit_results.json`. It is included as Supplementary Figure S1, with label caveats.

**Still open:**

1. **Operators of MXTX and MXTO** have not been identified. These two stations are regional diagnostics only.
2. **Case-label harmonization.** Stage reports reuse the letters A–F with different meanings. The §3.2 mapping table must go into any supplement, and Figure S1's tick labels use the audit-stage word "baseline".
3. **Unresolved gradient discrepancy.** The chain's east–west gradient is reported as −11.7228 in one place and −11.7057 mm/yr/km in another. Different fitting masks are a plausible explanation, but this was not recomputed and does not affect the conclusion.
4. **ERA5 consistency check not re-executable.** The 3.2 mm check was run as an inline command whose code was not preserved and is not used as release evidence.

The manuscript now cites a publisher-verified Mexico City subsidence study (Chaussard et al., 2021) and the Sentinel-1 mission paper (Torres et al., 2012) as background. Neither paper validates this project's 2024 measurements.

## Optional future experiments (outside the current scope)

1. **An ascending 2024 Sentinel-1 stack**, processed independently with the same audit (network redundancy, no ramp vs ramp, ERA5). This is the most decisive next step: it would test the whole plane under a second viewing geometry and allow a rough east/vertical split.
2. Independent reprocessing of ICMX and MMX1 raw GNSS data, and leveling or additional GNSS inside the scene, especially north and south of the ICMX–MMX1 line.
3. More interferograms that create overlapping loops around the mid-year triangles and test the remaining links between local loops.
4. A longer time series, to separate steady, seasonal and atmospheric signals.
5. Higher-resolution atmospheric corrections, or GNSS-derived delays.
