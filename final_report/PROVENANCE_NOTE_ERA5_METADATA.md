# Provenance note: ERA5 metadata discrepancy

*Prepared 2026-09-28 during the reporting pass. No HDF5 file was modified. All HDF5 attributes below were read through a read-only Docker bind mount (`-v "$PWD":/data:ro`).*

## 1. The discrepancy

The ERA5-corrected products carry a configuration attribute stating that no tropospheric correction was applied.

| File | Attribute | Stored value |
|---|---|---|
| `mintpy_redundant_era5/timeseries_demErr_ERA5.h5` (case C time series) | `mintpy.troposphericDelay.method` | `no` |
| `mintpy_redundant_era5/velocity_ERA5.h5` (case C velocity) | `mintpy.troposphericDelay.method` | `no` |
| `mintpy_redundant_era5/audit/timeseries_ERA5_linearRamp.h5` (case D time series) | `mintpy.troposphericDelay.method` | `no` |
| `mintpy_redundant_era5/audit/velocity_ERA5_linearRamp.h5` (case D velocity) | `mintpy.troposphericDelay.method` | `no` |

The primary file is `mintpy_redundant_era5/timeseries_demErr_ERA5.h5`, the direct output of the ERA5 correction. The other three are derived from it.

The same attribute and value appear on every other HDF5 file in `mintpy_redundant_era5/`, including `ERA5.h5` (the delay cube itself), `timeseries_demErr.h5`, `demErr.h5`, `maskTempCoh.h5` and `temporalCoherence.h5`. They also appear on the no-ERA5 files in `mintpy_redundant/`.

## 2. Why the attribute is a configuration record, not processing history

The attribute is a copy of a template (configuration) setting made when the stack was loaded. It is not written by the correction step.

- **The stack was loaded with ERA5 switched off.** `mintpy_config.txt` sets `mintpy.troposphericDelay.method = no`.
- **MintPy copies the template into metadata at load time.** In MintPy 1.6.4 `load_data.py` (lines 87–93 in the `ghcr.io/insarlab/mintpy:latest` image, tag v1.6.4, commit `297aa160`), every template key/value is copied into the metadata dictionary. That metadata then propagates to downstream files.
- **The correction step never updates the key.** In the same source tree, `mintpy.troposphericDelay.method` is referenced only in `smallbaselineApp.py`, which reads it to decide whether to run the step. `tropo_pyaps3.py` does not write it.
- **ERA5 was not run through `smallbaselineApp.py`.** It was applied by calling `tropo_pyaps3.py` directly on a copy of the already-loaded `timeseries_demErr.h5`. That file inherited `no` from the original load, and the ERA5 configuration file (`mintpy_config_era5.txt`, `method = pyaps`) was never loaded into the stack metadata.

The attribute therefore records the configuration at load time. It must not be read as a statement of which corrections were applied, and it has not been used that way in this report.

## 3. Existing processing evidence that the correction was applied

The following evidence was already recorded before this reporting pass. No new processing was run.

1. **Command record.** `mintpy_redundant_era5/PROCESSING_LOG.md` → *Commands and outcomes* records:

   ```
   ./mintpy-run tropo_pyaps3.py -f mintpy_redundant_era5/timeseries_demErr.h5 -g mintpy_redundant_era5/inputs/geometryGeo.h5 -m ERA5 -w mintpy_redundant_era5/weather --tropo-file mintpy_redundant_era5/ERA5.h5 -o mintpy_redundant_era5/timeseries_demErr_ERA5.h5 --debug
   ```

   The same log records that exactly 25 ERA5 GRIB files (13:00 UTC, 37 pressure levels) were downloaded, with no date missing.
2. **Delay-product integrity.** `mintpy_redundant_era5/audit/audit_results.json` → `delay_integrity` records the following for `ERA5.h5`: `date_count` 25, `dates_match_input` true, `missing_dates` [], `nan_count` 0, and absolute slant delays from −2.3055 to −1.9538 m.
3. **Historical content consistency check, not release evidence.** `external_validation/GNSS_LOS_VALIDATION.md` reports a 3.2 mm agreement with a double-referenced PyAPS delay, but the inline check code was not preserved. Its result cannot be independently reproduced from this package and is not used to support the release conclusion.
4. **A measurable, spatially smooth change.** `mintpy_redundant_era5/audit/audit_results.json` → `comparisons.ERA5_minus_baseline_no_ramp_mm_yr` records a C − A velocity RMS of 1.252 mm/yr over 80,791 pixels. The spatial correlation is 0.999917, and the east–west gradient falls by 0.93% (`plane_reduction`). A file that was only relabelled would give zero difference.
5. **Baseline preserved.** The ERA5 stage recorded identical SHA-1 values, sizes and mtimes for the baseline `mintpy_redundant/` files before and after processing (`mintpy_redundant_era5/PROCESSING_LOG.md` → *Baseline integrity verification*). The change therefore lives in the new ERA5 files, not in an overwritten baseline.

## 4. Limitation of the evidence

The 3.2 mm consistency check (item 3) was run as an inline `./mintpy-run python -c '...'` command. The log records the command's purpose but not its code, so the check cannot be re-executed exactly from the project files. The release relies on items 1, 2, 4 and 5 instead.

## 5. Recommendation for any data release

- Do not edit the protected HDF5 files.
- Ship this note (or an equivalent README entry) with any release of `mintpy_redundant_era5/`. It should state that `mintpy.troposphericDelay.method = no` reflects the load-time configuration and that `timeseries_demErr_ERA5.h5` and its derivatives are ERA5-corrected via `tropo_pyaps3.py` (PyAPS3 0.3.7, MintPy 1.6.4).
- If corrected attributes are wanted in a release, write them to **new copies** and record that change in the release's processing history.
