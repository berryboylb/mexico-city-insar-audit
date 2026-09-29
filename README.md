# Mexico City 2024 Sentinel-1 InSAR processing audit

This release uses 2024 Sentinel-1 radar observations to study **relative ground movement** in part of Mexico City and assess how reliably the measurements support interpretation of land subsidence. It packages existing analyses; no satellite processing was run for this release.

## Finding

Along the roughly 11 km ICMX–MMX1 GNSS baseline, the **no-ramp** InSAR result agrees better with GNSS. Across the 168-day shared comparison window (2024-04-18 to 2024-10-03; 10 matched epochs, 6 on the same day), GNSS gives an ICMX − MMX1 line-of-sight (LOS) rate difference of 256.3 mm/year. The redundant-network no-ramp result gives 240.5 mm/year (15.8 lower); the ERA5 no-ramp result gives 234.3 (22.0 lower). Linear-ramp removal gives 98.1 or 99.5 mm/year, roughly 157–158 lower than GNSS. See the [manuscript](final_report/MANUSCRIPT_DRAFT.md) and [evidence table](final_report/EVIDENCE_TABLE.csv).

This is a **one-baseline comparison**. It does not validate the full two-dimensional map, determine a physical cause, or establish absolute vertical subsidence. The maps are relative descending-LOS velocities, mixing horizontal and vertical motion. ICMX has an official interference warning; its effect remains unquantified. Low daily scatter and annual histories cannot rule out a smooth bias.

U95 in the comparison is a study-defined envelope combining an AR(1)-adjusted statistical half-width with selected sensitivity terms. It is not a demonstrated 95% bound on every error. Case C is borderline at 1.04 × U95. No independent preregistration is claimed. Full-record map rates (25 acquisitions, 2024-01-13 to 2024-12-26) must not be substituted for the 168-day GNSS comparison rates.

## Reading order

1. [Manuscript](final_report/MANUSCRIPT_DRAFT.md) — methods, results, limitations, acknowledgements and verified references.
2. [Evidence table](final_report/EVIDENCE_TABLE.csv) — claim-to-result traceability.
3. [Figure index](final_report/FIGURE_INDEX.md) — captions and limits for every cited figure.
4. [ERA5 metadata provenance note](final_report/PROVENANCE_NOTE_ERA5_METADATA.md) — why the load-time `method = no` attribute persists in ERA5-corrected HDF5 products.
5. [Final summary](final_report/FINAL_SUMMARY.md) — short account and remaining reporting discrepancies.
6. [Release checks and storage cleanup](docs/REPRODUCIBILITY_AND_STORAGE.md) — what is independently checkable and how to reduce local disk use after verifying an archive.

Earlier diagnostic reports under `mintpy/audit/`, `mintpy_redundant/audit/`, `mintpy_redundant_era5/audit/`, and `external_validation/` document their respective stages. Their interpretation and figure verdicts are **historical** where they conflict with the manuscript. In particular, both original mid-year chain “bridge” interferograms belong to tested closure triangles in the expanded network. Those triangles do not identify a uniquely faulty edge or validate all other links.

## Contents and run order

| Stage | Records and code | Lightweight results |
|---|---|---|
| Original 24-edge chain | `mintpy/PROCESSING_LOG.md`, `mintpy/audit/run_diagnostic_audit.py`, `mintpy_config.txt`, `smallbaselineApp.cfg` | `mintpy/audit/` JSON, CSV and figures |
| 31-edge expanded network and seven closure triangles | `mintpy_redundant/PROCESSING_LOG.md`, `mintpy_redundant/closure_diagnostics.py`, `mintpy_redundant/audit/run_redundant_audit.py` | `mintpy_redundant/audit/` JSON, CSV and figures |
| ERA5 sensitivity | `mintpy_redundant_era5/PROCESSING_LOG.md`, `mintpy_redundant_era5/mintpy_config_era5.txt`, `mintpy_redundant_era5/audit/run_atmospheric_audit.py` | `mintpy_redundant_era5/audit/` JSON, CSV and figures |
| GNSS LOS comparison | `external_validation/run_gnss_los_validation.py`, `external_validation/GNSS_LOS_VALIDATION.md`, `external_validation/gnss_raw/MANIFEST.json` | `external_validation/gnss_los_results.json`, comparison CSV, processed GNSS CSV and figures |
| Reporting | `final_report/make_fig_station_locations.py` | Manuscript, evidence table, figure index and station-location figure |

The stage order was chain inversion and diagnostics → expanded network and closure diagnostics → ERA5 sensitivity → GNSS comparison → final reporting. Logs give the original commands and decisions. The `hyp3/` folders contain only the 31 product READMEs and DEM credit metadata; the radar products themselves are excluded.

## Reproducibility and exclusions

The scripts are retained as scientific records and require the **excluded** MintPy HDF5 stacks, source interferograms, and weather products for full execution. This repository is a lightweight publication package, not a self-contained pipeline rerun. The original project retains those files. No jobs, new downloads, ascending stack, or scientific pipeline execution were performed during packaging.

Recorded processing used MintPy 1.6.4, PyAPS3 0.3.7, HyP3 `hyp3_gamma` 9.1.0 and GAMMA 20240627. Python analyses import `numpy`, `scipy`, `h5py`, `matplotlib` and `pyproj`; exact versions for those Python libraries were not recorded and are not invented here. The Docker wrapper `mintpy-run` uses a mutable `latest` image tag and a local CDS credential path; it is included as a command record, not a reproducible immutable environment. Raw NGL `tenv3` station files and the NGL steps snapshot are included with hashes in the manifest. See [data availability](external_validation/DATA_AVAILABILITY.md).

Excluded inputs include radar ZIPs, HyP3 TIFFs, MintPy HDF5 products, ERA5 GRIB files, archives, caches, temporary files and credentials. `.gitignore` also blocks their accidental addition. The unpreserved inline 3.2 mm ERA5 check is **not** used as evidence; the logged command, delay integrity and measured C − A change are documented in the [provenance note](final_report/PROVENANCE_NOTE_ERA5_METADATA.md).

Packaging changed only release copies of documentation and normalized CRLF to LF in 23 CSV files and one HTTP-header record; numerical values, scripts, figures, and source-project files were not altered.

## Remaining discrepancies

- A chain east–west fitted gradient is reported as −11.7228 versus −11.7057 mm/year/km in two earlier analyses; differing masks are a plausible explanation, unverified without recomputation. Neither value changes the baseline comparison.
- Case letters A–F were reused across stages; the manuscript §3.2 maps them. Supplementary Figure S1 retains the audit-stage word “baseline” in tick labels.
- `median(pixelwise B − A)` is about **−101.984** mm/year, while `median(B) − median(A)` is about **−137.430** mm/year. They answer different questions.
- The ERA5 HDF5 `mintpy.troposphericDelay.method = no` attribute records the load-time configuration and is not an ERA5 processing verdict.
- Prior Mexico City subsidence work and the Sentinel-1 mission are now cited in the manuscript for context. Those papers are independent background sources, not validation of this 2024 result.

No license has been selected for this release.

Run `python3 scripts/verify_release.py` to check the released numerical tables and recompute the matched GNSS rate from the included cleaned daily positions. This does not rerun the satellite inversion or original GNSS processing.
