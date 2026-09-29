# Mexico City MintPy Processing Log

## Status and scientific scope

Processing was continued on 2026-09-24 from the completed `correct_SET` stage through velocity generation. These products are **preliminary InSAR results**, not scientifically validated deformation conclusions.

The network contains 25 acquisitions and 24 retained interferograms and is a chain-only graph. It has no phase-closure triangles and no redundant interferometric paths. Consequently, unwrapping errors cannot be independently validated by closure, and the temporal-coherence value of 1.0 on valid pixels is a network-geometry degeneracy rather than evidence of perfect data quality.

No original HyP3 ZIP or source product was deleted, modified, or overwritten. No new data were downloaded.

## Software and configuration

- MintPy: `1.6.4`, dated `2026-07-25`
- Required command wrapper: `./mintpy-run`
- Custom configuration: `/data/mintpy_config.txt` (host path: `mintpy_config.txt`)
- Work directory: `/data/mintpy` (host path: `mintpy/`)
- Processor: HyP3
- Orbit: Sentinel-1 descending, relative orbit 41
- Spatial reference: EPSG:32614 (UTM zone 14N)
- Grid: 346 rows x 329 columns at 80 m spacing

Exact custom configuration:

```text
# Mexico City Sentinel-1 HyP3 InSAR time-series

mintpy.compute.cluster = local
mintpy.load.processor = hyp3

# Interferograms
mintpy.load.unwFile = ../hyp3/*/*_unw_phase.tif
mintpy.load.corFile = ../hyp3/*/*_corr.tif

# Geometry
mintpy.load.demFile = ../hyp3/*/*_dem.tif
mintpy.load.incAngleFile = ../hyp3/*/*_lv_theta.tif
mintpy.load.waterMaskFile = ../hyp3/*/*_water_mask.tif

# Limit processing to the Mexico City study area
mintpy.subset.lalo = 19.25:19.50, -99.20:-98.95

# Start with automatic referencing; we will audit reference choices later
mintpy.reference.lalo = auto

# Processing
mintpy.networkInversion.weightFunc = var
mintpy.troposphericDelay.method = no
mintpy.topographicResidual = yes
mintpy.topographicResidual.pixelwiseGeometry = yes
```

Tropospheric correction was disabled. Ionospheric correction inputs were unavailable. No deramping correction was configured. Topographic residual correction was enabled with pixelwise geometry.

## Acquisition dates

All 25 dates used in velocity estimation:

```text
20240113  20240125  20240206  20240218  20240301
20240313  20240325  20240406  20240418  20240430
20240512  20240629  20240804  20240816  20240828
20240909  20240921  20241003  20241015  20241027
20241108  20241120  20241202  20241214  20241226
```

No dates were excluded from velocity fitting.

## Reference pixel and reference date

- Reference pixel (Y, X): `(7, 186)`
- Authoritative HDF5 reference coordinates (`REF_LON`, `REF_LAT`): UTM easting 493680 m, northing 2155600 m. Despite the attribute names, these are projected coordinates, not geographic degrees.
- Converted reference location (EPSG:4326): latitude 19.4949937 N, longitude -99.0602279 E
- A coordinate reconstructed directly as `X_FIRST + REF_X * X_STEP`, `Y_FIRST + REF_Y * Y_STEP` is offset by half a pixel (40 m) from the stored reference coordinates, consistent with an edge/center convention difference; the stored reference coordinates are reported above.
- Minimum-residual-RMS reference date: `20240909`, RMS `0.0009858359 m`
- No epoch exceeded the residual-RMS rejection threshold of 3 x median RMS (`0.0066 m`).

## Exact commands and outcomes

Version inspection:

```sh
./mintpy-run smallbaselineApp.py --version
```

An initial `correct_topography` invocation failed before scientific processing because the work directory was omitted:

```sh
./mintpy-run smallbaselineApp.py mintpy_config.txt --dostep correct_topography
```

MintPy looked for `/data/inputs/ifgramStack.h5`, while the existing stack is `/data/mintpy/inputs/ifgramStack.h5`. The failure created/updated template backups under the root-level `inputs/` and `pic/` directories but did not alter HyP3 source data. CLI help confirmed `--dir/--work-dir`; processing was then correctly targeted at the existing work directory.

```sh
./mintpy-run smallbaselineApp.py --help
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy --dostep correct_topography
./mintpy-run info.py mintpy/timeseries_demErr.h5
./mintpy-run info.py mintpy/demErr.h5
./mintpy-run info.py mintpy/timeseriesResidual.h5
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy --dostep residual_RMS
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy --dostep reference_date
./mintpy-run info.py mintpy/timeseries_demErr.h5
./mintpy-run smallbaselineApp.py mintpy_config.txt --dir mintpy --dostep velocity
./mintpy-run info.py mintpy/velocity.h5
```

Figure generation:

```sh
./mintpy-run view.py mintpy/velocity.h5 velocity -m mintpy/maskTempCoh.h5 -u cm --vlim -15 25 -c RdBu_r --title 'Preliminary LOS velocity (topography-corrected)' --dpi 200 --nodisplay -o mintpy/velocity_final.png
./mintpy-run view.py mintpy/temporalCoherence.h5 -m no --vlim 0 1 -c viridis --title 'Temporal coherence' --dpi 200 --nodisplay -o mintpy/temporal_coherence.png
```

This attempted network command failed because MintPy 1.6.4 `plot_network.py` does not accept `--figext` or `-o`:

```sh
./mintpy-run plot_network.py mintpy/inputs/ifgramStack.h5 -t mintpy/smallbaselineApp.cfg --show-kept --nodisplay --figext .png -o mintpy/interferogram_network.png
```

The previously generated MintPy `network.pdf` was verified as a one-page PDF and converted non-destructively:

An initial direct PDF-to-PNG conversion preserved transparency, causing black labels to disappear against a dark viewer background. The final PNG was therefore flattened through an opaque JPEG intermediate:

```sh
sips -s format png mintpy/network.pdf --out mintpy/interferogram_network.png
sips -s format jpeg mintpy/network.pdf --out /private/tmp/mintpy_network.jpg
sips -s format png /private/tmp/mintpy_network.jpg --out mintpy/interferogram_network.png
```

Representative points were selected from valid masked pixels nearest the 5th, 50th, and 95th percentiles of the velocity distribution. They are descriptive samples, not validated monitoring sites:

| Label | Y, X | Latitude, longitude | Map velocity |
|---|---:|---:|---:|
| p05 | 66, 222 | 19.4527065, -99.0331549 | -0.0584258 m/yr |
| p50 | 21, 97 | 19.4851980, -99.1284529 | +0.1462088 m/yr |
| p95 | 108, 14 | 19.4222433, -99.1916524 | +0.2033461 m/yr |

```sh
./mintpy-run tsview.py mintpy/timeseries_demErr.h5 --yx 66 222 --no-show-img --zero-first --nodisplay --dpi 200 -o mintpy/timeseries_point_p05.png
./mintpy-run tsview.py mintpy/timeseries_demErr.h5 --yx 21 97 --no-show-img --zero-first --nodisplay --dpi 200 -o mintpy/timeseries_point_p50.png
./mintpy-run tsview.py mintpy/timeseries_demErr.h5 --yx 108 14 --no-show-img --zero-first --nodisplay --dpi 200 -o mintpy/timeseries_point_p95.png
```

`tsview.py` warned that its time-series extension is fixed to PDF and ignored the requested PNG extension. The PDFs and TXT data were retained, then converted:

The direct conversions below were attempted first, then replaced by final opaque PNGs via JPEG intermediates after visual inspection exposed a transparency/background issue:

```sh
sips -s format png mintpy/timeseries_point_p05_ts.pdf --out mintpy/timeseries_point_p05.png
sips -s format png mintpy/timeseries_point_p50_ts.pdf --out mintpy/timeseries_point_p50.png
sips -s format png mintpy/timeseries_point_p95_ts.pdf --out mintpy/timeseries_point_p95.png
sips -s format jpeg mintpy/timeseries_point_p05_ts.pdf --out /private/tmp/mintpy_p05.jpg
sips -s format png /private/tmp/mintpy_p05.jpg --out mintpy/timeseries_point_p05.png
sips -s format jpeg mintpy/timeseries_point_p50_ts.pdf --out /private/tmp/mintpy_p50.jpg
sips -s format png /private/tmp/mintpy_p50.jpg --out mintpy/timeseries_point_p50.png
sips -s format jpeg mintpy/timeseries_point_p95_ts.pdf --out /private/tmp/mintpy_p95.jpg
sips -s format png /private/tmp/mintpy_p95.jpg --out mintpy/timeseries_point_p95.png
```

## Numerical summary

- Velocity model: linear polynomial of order 1, using all 25 dates; uncertainty estimated from fitting residuals.
- Pixels inverted for velocity: 80,837 / 113,834 (71.0%).
- Temporally coherent mask: 80,837 / 113,834 pixels (71.0131%).
- Masked finite nonzero velocity pixels: 80,836.
- Full masked LOS velocity range: -0.15245359 to +0.24571674 m/yr (-15.2454 to +24.5717 cm/yr).
- Masked velocity percentiles (1, 5, 50, 95, 99%): -0.0747348, -0.0584270, +0.1462089, +0.2033464, +0.2071437 m/yr.
- Temporal coherence range on valid pixels: exactly 1.0; this is not an independent quality metric for this chain-only network.
- Topographic residual inversion: 80,836 pixels total, processed in four x-direction patches. Valid fractions were 4.5%, 79.4%, 97.9%, and 99.8%; the sparse first patch is an important edge/coverage warning.

## Result files

Primary numerical products:

- `timeseries_demErr.h5` — topographic-residual-corrected, reference-date-adjusted time series
- `demErr.h5` — estimated DEM error
- `timeseriesResidual.h5` — residual time series from topographic correction
- `timeseriesResidual_ramp.h5` — quadratic-ramp-removed residuals used only for residual RMS assessment
- `rms_timeseriesResidual_ramp.txt` and `.pdf` — epoch residual RMS
- `reference_date.txt` — selected reference date
- `velocity.h5` — velocity, velocity standard deviation, intercept, intercept standard deviation, and residue

Requested PNG figures:

- `velocity_final.png`
- `temporal_coherence.png`
- `interferogram_network.png`
- `timeseries_point_p05.png`
- `timeseries_point_p50.png`
- `timeseries_point_p95.png`

The associated point data are in `timeseries_point_p05_ts.txt`, `timeseries_point_p50_ts.txt`, and `timeseries_point_p95_ts.txt`.

## Warnings and interpretation limits

1. The 25-acquisition/24-interferogram chain has no closure triangles. Unwrapping errors were **not independently validated**, and one bad edge can propagate offsets into all later acquisitions.
2. Temporal coherence of 1.0 is structurally expected for an exactly determined chain and must not be interpreted as perfect coherence.
3. The broad, strongly offset velocity distribution and approximately one-year observation span warrant skepticism. The results may contain propagated unwrapping errors, reference-area instability, residual atmosphere, orbital ramps, or model/topography leakage.
4. Tropospheric correction was disabled, ionospheric data were unavailable, and no deramping correction was configured.
5. The reference pixel is near the northern edge (Y=7) and should be independently checked for stability.
6. `tsview.py` reported that no lookup table was found. Because these files use projected geo coordinates, it displayed UTM northing/easting under its `lat/lon` label; geographic coordinates in this log were independently transformed from EPSG:32614.
7. The first topographic-correction patch had only 4.5% invertible pixels, reflecting sparse valid coverage at one edge.

## Recommended research next steps

1. Add redundant interferograms spanning additional temporal baselines so closure-phase tests and network-based unwrapping-error correction become possible.
2. Audit individual unwrapped interferograms and connected components, especially across the 2024-05-12 to 2024-06-29 and 2024-06-29 to 2024-08-04 intervals.
3. Validate or replace the northern-edge reference pixel using stable bedrock and independent GNSS/leveling constraints.
4. Compare against independent GNSS in LOS geometry and published Mexico City subsidence patterns before physical interpretation.
5. Evaluate atmospheric correction and physically justified ramp treatment, then rerun sensitivity tests with alternate reference areas and masks.
6. Extend the time span beyond one year and test nonlinear/seasonal behavior; do not treat the present linear rates as robust long-term trends.
