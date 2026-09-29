# Release checks and local storage

## What this repository can verify

From a full clone, run:

```bash
python3 scripts/verify_release.py
```

This standard-library check recalculates the 256.3202 mm/year matched ICMX − MMX1 GNSS slope from the included cleaned daily ENU CSVs and stored LOS coefficients. It checks the four comparison differences and U95 arithmetic, the 25-node/31-edge network structure, closure count arithmetic, JSON/CSV agreement, Python syntax, local documentation links and indexed figure presence. It also screens for unexpectedly included large raw products and common credential patterns.

These are consistency checks of released records. They do **not** repeat the original GNSS cleaning, station geometry derivation, pixel extraction, radar inversion, closure calculation or ERA5 correction. They cannot establish that the full mapped gradient is physical subsidence. The original analysis logs and scripts remain available for inspection, but full reruns require the excluded HDF5, interferogram and weather data. MintPy's mutable container `latest` tag also prevents an exact environment recreation without the original image digest.

## Local disk cleanup

The GitHub repository is a small publication copy. Ignoring large files in Git does **not** remove them from the working folder on your Mac. The earlier inventory showed **29 root HyP3 ZIPs and 31 extracted `hyp3/` product directories**. Two folders have no matching ZIP in that inventory, so do not assume the ZIPs alone form a complete archive.

From your local project, first inspect what uses space:

```bash
du -sh . hyp3 mintpy mintpy_redundant mintpy_redundant_era5 external_validation/gnss_raw 2>/dev/null
find . -maxdepth 1 -name 'S1AA_*.zip' -type f | wc -l
find hyp3 -mindepth 1 -maxdepth 1 -type d | wc -l
git status --short
git clean -ndX
```

`git clean -ndX` only previews ignored files; it does not delete anything. It may show large ignored directories as a single line. The published Git history and GitHub ZIP do not contain the full scientific inputs.

Have local Codex create a **separate archive inventory** listing each ZIP, each extracted product directory, all HDF5 and ERA5 files, sizes and SHA-256 hashes, then compare product identifiers to identify the two missing ZIPs. Copy the full local scientific inputs and intermediate results to an external drive or other durable storage with sufficient space. Compare file counts and hashes at the destination before removing any local copy. Retain the 31 products, original raw GNSS, processing configurations, HDF5 outputs and weather data in the archive if future reruns matter.

Once an independently verified archive exists, local Codex can propose an explicit deletion list and the expected space savings. Review that list before deletion. A safe first candidate may be a second copy of a product that exists both as a verified ZIP and verified extracted directory, while keeping the archive's complete set. Do not treat the reported 29 ZIPs as interchangeable with all 31 extracted products.

## Scope of the completed research

This is a completed **processing sensitivity audit with one external GNSS baseline**, covering 2024 descending Sentinel-1 data. The no-ramp result is better supported on that baseline. A comprehensive citywide subsidence interpretation would require independent spatial constraints and additional viewing geometry or leveling. Those are possible future studies; they are not hidden claims of this release. The limits appear in the [manuscript](../final_report/MANUSCRIPT_DRAFT.md) and [summary](../final_report/FINAL_SUMMARY.md).
