# Mexico City redundant-network diagnostic audit

> **Historical stage report.** Final interpretation is in `final_report/MANUSCRIPT_DRAFT.md`. Both original mid-year chain bridge edges are sides of tested triangles here; “remaining bridges” means links outside the seven triangles. Stage verdicts about ramp sensitivity do not establish the gradient's physical cause.

## Executive conclusion

Validation passed: the loaded stack contains the expected 25 acquisitions and 31 unique interferograms, including all seven additions, on geometry identical to the original analysis. The additions create exactly seven local closure triangles. They provide meaningful—but spatially and temporally limited—unwrapping diagnostics. They do not validate the non-redundant connectors between those local cycles or the network as a whole.

The redundant inversion closely reproduces the original broad relative Sentinel-1 line-of-sight (LOS) velocity field: the common-mask RMS difference is 3.891 mm/yr, the median difference is +0.138 mm/yr, and the east–west gradient changes by only −0.012 mm/yr/km. Most differences are small, but deviations are concentrated at closure-failure pixels and can be locally large. The broad west-to-east gradient remains highly sensitive to spatial-ramp treatment and the displayed velocity offset remains highly sensitive to reference choice. Consequently, the result is preliminary relative LOS velocity, not a validated claim of physical subsidence or uplift.

## Inputs and network structure

- Acquisitions: 25
- Primary interferograms kept/dropped: 31/0
- Unique date pairs: 31; duplicates: 0
- Temporal baseline: 12–60 days
- Perpendicular baseline: −138.633 to +127.092 m
- Spatial mean coherence: minimum 0.85631, median 0.93997, mean 0.93340, maximum 0.97049
- Connectivity: one connected component
- Cycle rank: 31 − 25 + 1 = 7
- Closure triangles: 7

The triangles are:

| # | Dates |
|---:|---|
| 1 | 2024-01-13 / 2024-01-25 / 2024-02-06 |
| 2 | 2024-03-01 / 2024-03-13 / 2024-03-25 |
| 3 | 2024-04-30 / 2024-05-12 / 2024-06-29 |
| 4 | 2024-06-29 / 2024-08-04 / 2024-08-16 |
| 5 | 2024-08-28 / 2024-09-09 / 2024-09-21 |
| 6 | 2024-10-27 / 2024-11-08 / 2024-11-20 |
| 7 | 2024-12-02 / 2024-12-14 / 2024-12-26 |

Each added edge closes one local three-edge loop. The remaining links between these neighborhoods are bridges: they have no independent cycle check. Thus “seven triangles” does not mean all 31 interferograms received independent closure validation.

## Closure diagnostics before correction

MintPy's aggregate closure product has 81,299 valid pixels. Of these, 2,334 (2.871%) have at least one non-zero integer ambiguity. The failure-count distribution is: 78,965 pixels with zero failing triangles; 1,873 with one; 370 with two; 71 with three; 19 with four; and one with five. The maximum is five failed triangles at one pixel.

Strict three-edge-valid statistics are:

| Triangle | Failed / valid | Failure % | Mean coherence, fail | Mean coherence, pass |
|---|---:|---:|---:|---:|
| Jan 13–Jan 25–Feb 06 | 92 / 81,078 | 0.113 | 0.689 | 0.953 |
| Mar 01–Mar 13–Mar 25 | 20 / 81,123 | 0.025 | 0.550 | 0.956 |
| Apr 30–May 12–Jun 29 | 1,509 / 80,860 | 1.866 | 0.546 | 0.905 |
| Jun 29–Aug 04–Aug 16 | 768 / 80,457 | 0.955 | 0.334 | 0.886 |
| Aug 28–Sep 09–Sep 21 | 208 / 80,804 | 0.257 | 0.258 | 0.923 |
| Oct 27–Nov 08–Nov 20 | 31 / 80,602 | 0.038 | — | — |
| Dec 02–Dec 14–Dec 26 | 20 / 80,867 | 0.025 | — | — |

Failures are strongly associated with lower coherence. The two midyear triangles dominate; their integer ambiguity ranges from −2 to +2 cycles. Most of their failures lie inside the common connected-component mask (92.1% and 91.4%), so they cannot be dismissed solely as disconnected margins. The Apr–Jun failures are broadly distributed with northeastern and southern concentrations; the Jun–Aug failures also show coherent low-quality patches and boundary effects. Exact maps and per-edge implication counts are in `closure_failure_count.png`, `closure_failures_by_triangle.png`, `closure_triangle_statistics.csv`, and `closure_interferogram_flags.csv`.

Closure identifies an inconsistent three-edge sum, not the uniquely faulty edge. The diagnostic exclusion case therefore removes only the newly added long edge from each of the two triangles above the 0.5% threshold; it is a reproducible stress test, not an unwrapping correction or proof those edges are wrong.

## Velocity and correction sensitivity

All rates below are relative Sentinel-1 LOS velocity in mm/yr. The primary case uses the same reference date (2024-09-09), original reference pixel (Y/X 7/186), common temporal model, and temporal-coherence mask as the comparison cases.

| Case | Valid pixels | Min | P05 | Median | P95 | Max | E–W gradient (mm/yr/km) | velocity/elevation r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw, all 31 | 80,791 | −141.39 | −58.19 | 147.27 | 204.77 | 231.14 | −11.744 | 0.427 |
| Topography-corrected, all 31 | 80,791 | −142.03 | −58.54 | 146.58 | 203.56 | 229.00 | −11.719 | 0.425 |
| Raw + linear ramp removal | 80,791 | −191.15 | −69.33 | 9.23 | 115.20 | 179.28 | ~0 | −0.011 |
| Topography-corrected + linear ramp removal | 80,791 | −192.04 | −69.26 | 9.15 | 115.07 | 179.07 | ~0 | −0.011 |
| Exclude flagged added edges, topography-corrected | 80,787 | −151.79 | −58.28 | 146.40 | 203.36 | 241.46 | −11.696 | 0.424 |

Topographic correction changes the all-31 map by 0.971 mm/yr RMS (topographic minus raw median −0.744 mm/yr; 5th/95th percentiles −1.644/−0.091 mm/yr). Estimated DEM error correlates with elevation at r = 0.566. Its effect is materially smaller than the ramp sensitivity.

Linear ramp removal mathematically projects out a fitted plane, so the fitted east–west and north–south gradients become numerical zero. It shifts the median from +146.58 to +9.15 mm/yr and changes the map relative to the original baseline by about 122.97 mm/yr RMS. This is the dominant processing sensitivity and shows that the broad gradient cannot safely be assumed to be deformation.

Excluding the two closure-flagged added edges changes the all-31 topography-corrected map by 3.688 mm/yr RMS, with median −0.137 mm/yr and 5th/95th percentiles −1.722/+1.221 mm/yr. Extremes reach −103.62/+80.29 mm/yr in localized areas, while the east–west gradient changes only from −11.719 to −11.696 mm/yr/km. This reinforces that redundancy reveals localized reliability problems without resolving the origin of the broad gradient.

## Comparison with the original 24-pair chain

On 80,787 common valid pixels, redundant-minus-original topography-corrected velocity has:

- RMS 3.891 mm/yr
- median +0.138 mm/yr
- 5th/95th percentiles −1.605/+2.266 mm/yr
- minimum/maximum −73.49/+97.07 mm/yr
- 4.27% of pixels above 5 mm/yr absolute difference, 2.55% above 10 mm/yr, and 1.01% above 20 mm/yr
- detrended spatial correlation 0.9974 and detrended RMS difference 3.880 mm/yr

The original and redundant east–west gradients are −11.706 and −11.718 mm/yr/km; the change is −0.012 mm/yr/km. The north–south gradients are −2.856 and −2.883 mm/yr/km. Closure-failure pixels have 21.09 mm/yr redundant-versus-original RMS difference, compared with 1.74 mm/yr at closure-clean pixels. The maximum absolute difference is 97.07 mm/yr at Y/X 318/180 (UTM E 493,160 m, N 2,130,760 m).

The redundant residual RMS distribution improves modestly: median/mean decrease from 1.489/1.566 mm to 1.429/1.530 mm. Temporal coherence has median 0.99978 (5th percentile 0.98453) in the redundant inversion. The chain-only baseline reports exactly 1.0 everywhere, a consequence of absent redundancy rather than evidence of perfect observations.

The previous extreme range largely persists: the primary redundant result spans −142.03 to +229.00 mm/yr, versus approximately −152.45 to +245.72 mm/yr in the original masked result. The maps remain highly correlated and representative percentile time series nearly overlap, but localized anomalies in closure-failure zones are less stable.

## Reference-area sensitivity

Candidate areas are 9×9-pixel patches selected to be small, multi-pixel, largely valid regions. They are candidates only; no external evidence establishes stability.

| Candidate | Center Y/X | UTM E/N (m) | Valid pixels | Mean elevation (m) | Patch rate subtracted (mm/yr) | Re-referenced map median (mm/yr) |
|---|---|---:|---:|---:|---:|---:|
| Existing northern neighborhood | 7/186 | 493640 / 2155640 | 80 | 2223.95 | −0.616 | 147.20 |
| Western high terrain | 152/4 | 479080 / 2144040 | 81 | 2318.67 | 204.114 | −57.53 |
| Southwestern high terrain | 341/4 | 479080 / 2128920 | 81 | 2649.15 | 206.910 | −60.33 |

For a velocity map v(x,y), reference to a patch with mean c gives v′(x,y)=v(x,y)−c. Therefore ∂v′/∂x=∂v/∂x and ∂v′/∂y=∂v/∂y. Numerically, all three cases retain E–W gradient −11.718965 mm/yr/km and N–S gradient −2.881426 mm/yr/km to rounding, while map medians shift by roughly 205–208 mm/yr between northern and western/southwestern candidates. Reference choice changes the additive zero and local reported rates; it does not remove the spatial gradient.

## Scientific assessment and limitations

The seven additions materially improve diagnostic power relative to a pure chain: they expose non-zero integer closure ambiguities, localize instability, make temporal coherence non-degenerate, and slightly reduce residual RMS. They do not independently validate every interferogram or establish that the broad gradient is geophysical. Each loop is isolated and local, the links between loops remain untested bridges, and closure cannot uniquely identify the responsible edge.

The earlier interpretation therefore does not change: the broad west-to-east relative LOS velocity gradient is robust to adding these seven edges but is highly sensitive to spatial-ramp handling, while absolute displayed rates are highly sensitive to the reference region. Local patterns are generally consistent between the 24- and 31-edge inversions, except in closure-failure areas where differences can be large. No sign is interpreted here as physical subsidence or uplift.

Recommended next work:

1. Add more interferograms that create overlapping, independent cycles—especially across the midyear and bridge segments—rather than only isolated triangles.
2. Evaluate physically appropriate atmospheric corrections and independent orbital/ramp controls; compare correction alternatives without overwriting this baseline.
3. Validate reference stability and spatial patterns against GNSS and/or leveling data, preferably projected into Sentinel-1 LOS.
4. Extend the temporal record to distinguish persistent motion from seasonal, atmospheric, or short-baseline artifacts.
5. Inspect/reprocess the source unwrapping for the two dominant midyear triangles and boundary regions before interpreting localized extremes.

## Deliverables

Machine-readable results are in `audit_results.json`; case and reference tables are in `case_statistics.csv` and `reference_sensitivity.csv`. Principal figures are:

- `fig_baseline_vs_redundant_velocity.png`
- `fig_ramp_topography_sensitivity.png`
- `fig_reference_sensitivity.png`
- `fig_dem_error_elevation.png`
- `fig_temporal_coherence_comparison.png`
- `fig_residual_rms_comparison.png`
- `fig_representative_point_timeseries.png`
- `closure_failure_count.png`
- `closure_failures_by_triangle.png`
- `network.png`

The exact primary configuration, command record, decisions, and warnings are in `../PROCESSING_LOG.md`.
