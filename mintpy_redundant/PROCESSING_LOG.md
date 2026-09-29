# Redundant-network processing log

## Scope and preservation

This run extends the original 24-interferogram Mexico City Sentinel-1 analysis with seven supplied HyP3 interferograms. All new processing and diagnostics were written under `mintpy_redundant/`. The baseline directories `mintpy/` and `mintpy/audit/`, and all HyP3 products, were treated as read-only. No data were downloaded, deleted, or recreated.

Software: MintPy 1.6.4 (`2026-07-25`), invoked through `./mintpy-run`.

Configuration file: `mintpy_config.txt`:

```ini
mintpy.compute.cluster = local
mintpy.load.processor = hyp3
mintpy.load.unwFile = ../hyp3/*/*_unw_phase.tif
mintpy.load.corFile = ../hyp3/*/*_corr.tif
mintpy.load.demFile = ../hyp3/*/*_dem.tif
mintpy.load.incAngleFile = ../hyp3/*/*_lv_theta.tif
mintpy.load.waterMaskFile = ../hyp3/*/*_water_mask.tif
mintpy.subset.lalo = 19.25:19.50, -99.20:-98.95
mintpy.reference.lalo = auto
mintpy.networkInversion.weightFunc = var
mintpy.troposphericDelay.method = no
mintpy.topographicResidual = yes
mintpy.topographicResidual.pixelwiseGeometry = yes
```

No ionospheric correction data were available, no deramp was configured for the primary result, and no tropospheric correction was introduced. The primary inversion used variance-based weighting.

## Input validation

`inputs/ifgramStack.h5` contains 25 unique acquisition dates and 31 unique date pairs. It has the required `date`, `bperp`, `coherence`, `unwrapPhase`, and `dropIfgram` datasets, with consistent dimensions. All seven supplied pairs are present exactly once:

1. 20240113_20240206
2. 20240301_20240325
3. 20240430_20240629
4. 20240629_20240816
5. 20240828_20240921
6. 20241027_20241120
7. 20241202_20241226

The redundant and baseline geometry datasets (`height`, `incidenceAngle`, `slantRangeDistance`, and `waterMask`) are array-identical, with shape 346 × 329, 80 m grid spacing, and EPSG:32614 coordinates. No accidental duplicate pair was found.

## Commands executed

The previously completed `load_data` stage was not rerun. The substantive commands were:

```bash
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep modify_network
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep reference_point
./mintpy-run reference_point.py mintpy_redundant/inputs/ifgramStack.h5 -y 7 -x 186 --force
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep quick_overview
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep correct_unwrap_error
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep invert_network
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep correct_LOD
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep correct_SET
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep correct_ionosphere
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep correct_troposphere
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep deramp
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep correct_topography
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep residual_RMS
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep reference_date
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy_redundant --dostep velocity
./mintpy-run remove_ramp.py mintpy_redundant/timeseries.h5 -m mintpy_redundant/maskTempCoh.h5 -s linear -o mintpy_redundant/audit/timeseries_raw_linearRamp.h5
./mintpy-run remove_ramp.py mintpy_redundant/timeseries_demErr.h5 -m mintpy_redundant/maskTempCoh.h5 -s linear -o mintpy_redundant/audit/timeseries_topo_linearRamp.h5
./mintpy-run timeseries2velocity.py mintpy_redundant/timeseries.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant/audit/velocity_A_raw.h5
./mintpy-run timeseries2velocity.py mintpy_redundant/timeseries_demErr.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant/audit/velocity_B_topo.h5
./mintpy-run timeseries2velocity.py mintpy_redundant/audit/timeseries_raw_linearRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant/audit/velocity_C_raw_linearRamp.h5
./mintpy-run timeseries2velocity.py mintpy_redundant/audit/timeseries_topo_linearRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant/audit/velocity_D_topo_linearRamp.h5
./mintpy-run timeseries2velocity.py mintpy_redundant/audit/timeseries_exclude_flagged_raw.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant/audit/velocity_E_exclude_flagged_raw.h5
./mintpy-run timeseries2velocity.py mintpy_redundant/audit/timeseries_exclude_flagged_demErr.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant/audit/velocity_F_exclude_flagged_topo.h5
./mintpy-run python mintpy_redundant/closure_diagnostics.py
./mintpy-run python mintpy_redundant/audit/run_redundant_audit.py
```

For the flagged-edge diagnostic, a copy of the stack was made at `audit/ifgramStack_exclude_flagged_added.h5`; the original stack was not changed. The copied stack excluded `20240430_20240629` and `20240629_20240816`, retained 29 connected edges, and was inverted to explicit files under `audit/`. These edges were selected because their triangles exceeded 0.5% strict-valid closure failures; closure alone cannot determine which edge within a triangle is wrong.

## Network and reference records

All 31 interferograms were retained in the primary network. Temporal baselines span 12–60 days and perpendicular baselines span −138.633 to +127.092 m. Spatial mean coherence ranges from 0.85631 to 0.97049 (median 0.93997; mean 0.93340). The graph is connected and has 25 nodes, 31 edges, cycle rank 7, and seven local triangles.

The automatic `reference_point` run initially selected Y/X 180/216. To enable a controlled comparison with the original analysis, the stack was then explicitly re-referenced to the valid original pixel Y/X 7/186. Its UTM position is E 493,640 m, N 2,155,640 m (EPSG:32614). The reference date is 2024-09-09. These choices were held fixed in all velocity cases; alternative reference patches were applied analytically to copies of the velocity array.

## Warnings and processing decisions

- `correct_unwrap_error` performed no correction because the configured/automatic method was `no`; closure results therefore diagnose the loaded unwrapped phases rather than a corrected product.
- Sentinel-1 LOD correction was not required. Solid Earth tide, ionospheric, tropospheric, and deramp stages made no primary correction under the configuration and available inputs.
- No residual-RMS date exceeded MintPy's three-times-median threshold (reported threshold 0.0064 m).
- Temporal coherence near 1 is not proof of perfect data quality. The original chain produces a degenerate value of 1 because it lacks redundant constraints; even the redundant result only tests seven local cycles.
- The two closure-sensitive added edges were excluded only in a separately named diagnostic case. They were not removed from the primary network.

## Principal resulting files

- Primary: `velocity.h5`, `timeseries.h5`, `timeseries_demErr.h5`, `demErr.h5`, `temporalCoherence.h5`, `maskTempCoh.h5`, `timeseriesResidual.h5`
- Network: `network.pdf`, `coherenceMatrix.pdf`, `coherenceHistory.pdf`, `pbaseHistory.pdf`
- Closure: `numTriNonzeroIntAmbiguity.h5`, `numTriNonzeroIntAmbiguity.png`, and the tables/maps under `audit/`
- Audit cases and figures: all `audit/velocity_*.h5`, `audit/case_statistics.csv`, `audit/reference_sensitivity.csv`, `audit/audit_results.json`, and `audit/fig_*.png`

Scientific interpretation and numerical comparisons are in `audit/REDUNDANT_NETWORK_AUDIT.md`.
