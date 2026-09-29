# ERA5/PyAPS atmospheric-correction sensitivity audit

> **Historical stage report.** The final baseline comparison, U95 limits and ERA5 metadata provenance are in `final_report/MANUSCRIPT_DRAFT.md` and `final_report/PROVENANCE_NOTE_ERA5_METADATA.md`.

## Scientific conclusion

ERA5 does not materially reduce the broad west-to-east relative Sentinel-1 LOS velocity gradient, and it does not resolve the result's extreme sensitivity to linear-ramp removal. ERA5 changes the no-ramp velocity by only 1.252 mm/yr RMS on the common mask and reduces the fitted east-west gradient by 0.93%. Linear-ramp removal changes the same map by 123.151 mm/yr RMS before ERA5 and 122.350 mm/yr after ERA5. The ramp choice therefore remains roughly two orders of magnitude more influential in RMS terms.

This is an atmospheric sensitivity test, not evidence that the remaining signal is physical deformation. No feature is interpreted as subsidence or uplift.

## Controlled comparison

All four cases use 80,791 common valid pixels, the same 25 dates, mask, reference date 2024-09-09, reference pixel Y/X 7/186, topographic correction, linear velocity model, and redundant-network inversion:

| Case | P05 | Median | P95 | E–W gradient | N–S gradient | Plane magnitude | Plane peak-to-peak | Plane variance explained |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: baseline, no ramp | −58.541 | 146.584 | 203.565 | −11.7190 | −2.8814 | 12.0680 | 332.672 | 64.386% |
| B: baseline, linear ramp removed | −69.264 | 9.155 | 115.065 | ~0 | ~0 | ~0 | ~0 | ~0 |
| C: ERA5, no ramp | −58.110 | 146.748 | 201.507 | −11.6098 | −2.8830 | 11.9624 | 330.348 | 64.036% |
| D: ERA5, linear ramp removed | −68.602 | 9.925 | 114.867 | ~0 | ~0 | ~0 | ~0 | ~0 |

Velocity and gradients are mm/yr and mm/yr/km, respectively. Plane peak-to-peak is mm/yr over the common valid footprint.

ERA5 reduces the east-west gradient by 0.1092 mm/yr/km (0.93%), gradient magnitude by 0.88%, and plane peak-to-peak amplitude by 0.70%. Plane variance explained decreases by only 0.00350 in absolute fraction. These are minor changes, not removal of the long-wavelength plane.

## ERA5-induced change

For C minus A:

- RMS: 1.252 mm/yr
- median: +0.274 mm/yr
- mean: −0.065 mm/yr
- 5th/95th percentiles: −1.942/+1.069 mm/yr
- minimum/maximum: −15.192/+1.276 mm/yr
- spatial correlation: 0.999917

For D minus B, RMS is 1.205 mm/yr, median +0.627 mm/yr, and spatial correlation 0.999794.

The most negative ERA5 change occurs at array corner Y/X 345/0. The outer ten pixels have 3.062 mm/yr RMS change, versus 0.846 mm/yr in the interior. This localized extreme is therefore treated as an edge effect, not a robust atmospheric correction. The broader correction is spatially smooth, small, and incapable of explaining the pre-existing west-east plane.

## Ramp dominance

Baseline ramp removal changes velocity by 123.151 mm/yr RMS and shifts the median by about −101.98 mm/yr. After ERA5, ramp removal still changes velocity by 122.350 mm/yr RMS and shifts the median by about −101.41 mm/yr. ERA5 reduces the ramp-effect RMS by only 0.801 mm/yr (0.65%).

The near-zero gradients in cases B and D are an expected mathematical consequence of fitting and subtracting a linear spatial plane; they do not demonstrate which part of the plane was atmospheric, orbital, processing-related, or geophysical.

## Closure-sensitive regions

The ERA5-induced RMS change is 1.000 mm/yr across 2,216 common-mask closure-failure pixels and 1.259 mm/yr across 78,575 closure-clean pixels. Closure-sensitive areas do not change disproportionately under ERA5. This is consistent with closure failures being an interferometric phase-consistency issue rather than a signal explained by a date-dependent, spatially smooth ERA5 correction.

The seven triangles remain local. ERA5 does not add network redundancy or independently validate the untested bridge interferograms.

## Delay integrity inspection

- Expected/found dates: 25/25; no missing dates.
- NaN samples: 0.
- Absolute slant delay range: −2.3055 to −1.9538 m.
- Maximum within-date spatial range: 0.1792 m.
- Maximum adjacent-pixel difference: 0.01898 m, on 2024-08-16.
- Acquisition time: 12:34:40.111 UTC; ERA5 hour selected by MintPy: 13:00 UTC.
- Corrected series uses the same spatial and temporal reference as the input.

The delay maps are smoothly varying at long wavelengths and contain terrain-correlated fine structure. No missing strip, scene-wide discontinuity, sign reversal, or reference mismatch was found. Larger corrections at the southwestern boundary warrant caution; velocity differences at the outer edge should not be over-interpreted.

## Stability across prior sensitivity dimensions

- Network: adding seven redundant edges changed the original chain result by 3.891 mm/yr RMS but changed the east-west gradient by only −0.012 mm/yr/km.
- Atmosphere: ERA5 changes the redundant map by 1.252 mm/yr RMS and reduces the east-west gradient by only 0.93%.
- Topography: the prior audit found a 0.971 mm/yr RMS effect and little gradient change.
- Reference: alternative patches shift the velocity offset by approximately 205–208 mm/yr but leave the gradient invariant.
- Ramp: linear-plane subtraction changes the map by about 122–123 mm/yr RMS and explicitly removes the fitted gradient.

Thus the broad gradient is stable under redundant-network, ERA5, and topographic-correction choices, and is mathematically invariant to additive reference changes. It is not stable under ramp treatment. That combination does not establish physical deformation: the ramp ambiguity remains the dominant unresolved scientific issue.

## Limitations and recommendations

ERA5 has coarse native spatial resolution relative to the 80 m InSAR grid and cannot represent all local turbulent or urban atmospheric structure. A single nearest-hour pressure-level realization cannot prove the absence of atmospheric artifacts. The acquisition record spans less than one year, reference stability has no external validation, and most network bridges remain without closure redundancy.

Recommended next steps are:

1. Validate the long-wavelength field and reference patches with GNSS and/or leveling projected into Sentinel-1 LOS.
2. Add overlapping interferograms that close cycles across the existing bridge segments.
3. Test independent orbital/ramp controls and, if available, higher-resolution atmospheric products or GNSS-derived zenith delays.
4. Extend the time span to separate persistent, seasonal, and stochastic components.
5. Exclude or down-weight boundary pixels when interpreting local ERA5 differences.

## Deliverables

- `audit_results.json`: full machine-readable statistics and per-date delay checks.
- `case_statistics.csv`: four-case common-mask statistics.
- `fig_four_case_velocity_comparison.png`: A–D velocity maps with common limits.
- `fig_ERA5_velocity_change.png`: baseline, ERA5, and difference maps.
- `fig_ERA5_delay_maps.png`: representative delay maps.
- `fig_gradient_comparison.png`: fitted east-west and north-south gradients.
- `fig_representative_timeseries_ERA5.png`: baseline versus ERA5 patch time series.
- `../PROCESSING_LOG.md`: exact configuration, commands, warnings, inputs, and integrity checks.
