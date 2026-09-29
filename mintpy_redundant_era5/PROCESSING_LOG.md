# ERA5/PyAPS sensitivity processing log

## Scope and preservation

This is a separate atmospheric-correction sensitivity case. The existing `mintpy/` and `mintpy_redundant/` trees were read only. Baseline hashes, modification timestamps, and sizes were recorded before processing and verified unchanged afterward.

- MintPy: 1.6.4 (`2026-07-25`)
- PyAPS3: 0.3.7
- Invocation: every MintPy/PyAPS command used `./mintpy-run`
- New case: `mintpy_redundant_era5/`
- Weather directory: `mintpy_redundant_era5/weather/`

The CDS credential file was checked only for existence inside the container. Its contents were never read, printed, copied, or logged.

## Exact inputs derived from HDF5 metadata

- 25 acquisition dates: 20240113, 20240125, 20240206, 20240218, 20240301, 20240313, 20240325, 20240406, 20240418, 20240430, 20240512, 20240629, 20240804, 20240816, 20240828, 20240909, 20240921, 20241003, 20241015, 20241027, 20241108, 20241120, 20241202, 20241214, 20241226.
- `CENTER_LINE_UTC`: 45280.111419 seconds = 12:34:40.111 UTC.
- MintPy nearest ERA5 product time: 13:00 UTC.
- Stored grid: EPSG:32614; 346 × 329 pixels; 80 m spacing.
- Pixel-center geographic footprint: longitude −99.202418 to −98.952350°, latitude 19.250885 to 19.500420°.
- MintPy/PyAPS requested SNWE: 10, 30, −110, −90. This results from MintPy 1.6.4's required 2° minimum interpolation buffer followed by outward rounding to 10° boundaries.
- Reference: Y/X 7/186; reference date 20240909.

## Configuration

`mintpy_config_era5.txt` copies the original configuration and changes only:

```ini
mintpy.troposphericDelay.method = pyaps
mintpy.troposphericDelay.weatherModel = ERA5
mintpy.troposphericDelay.weatherDir = ./weather
```

The same redundant stack, subset, variance-weighted inversion, mask, reference point/date, topographic correction, and linear velocity model were retained. The atmospheric correction was applied to a copied `timeseries_demErr.h5`; atmospheric and topographic delay subtraction commute, and this avoids rerunning or modifying the completed redundant inversion.

## Commands and outcomes

Dependency and metadata inspection (passed):

```bash
./mintpy-run python -c "import os,cdsapi,pyaps3,mintpy; ..."
./mintpy-run info.py mintpy_redundant/timeseries_demErr.h5 --compact
./mintpy-run info.py mintpy_redundant/inputs/geometryGeo.h5 --compact
./mintpy-run info.py mintpy_redundant/inputs/ifgramStack.h5 --compact
./mintpy-run tropo_pyaps3.py --help
./mintpy-run python -c "from mintpy.tropo_pyaps3 import closest_weather_model_hour,get_snwe; ..."
```

Authentication test (passed):

```bash
./mintpy-run python -c "import cdsapi; ... retrieve('reanalysis-era5-pressure-levels', one actual date/hour, temperature at 1000 hPa, area [20,-100,19,-98]) ..."
```

The 198-byte response is isolated at `weather/auth_test/era5_auth_20240113_13.grib`. No credential value was accessed or emitted.

ERA5 calculation and correction (passed):

```bash
./mintpy-run tropo_pyaps3.py -f mintpy_redundant_era5/timeseries_demErr.h5 -g mintpy_redundant_era5/inputs/geometryGeo.h5 -m ERA5 -w mintpy_redundant_era5/weather --tropo-file mintpy_redundant_era5/ERA5.h5 -o mintpy_redundant_era5/timeseries_demErr_ERA5.h5 --debug
```

PyAPS requested geopotential, temperature, and specific humidity at all 37 ERA5 pressure levels for the 25 actual dates at 13:00 UTC. Exactly 25 GRIB files were downloaded, totaling about 35 MB. One CDS HTTP 502 occurred after date 18; the client retried successfully after its 120-second backoff. No date is missing.

Velocity and ramp cases (passed):

```bash
./mintpy-run timeseries2velocity.py mintpy_redundant_era5/timeseries_demErr_ERA5.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant_era5/velocity_ERA5.h5
./mintpy-run remove_ramp.py mintpy_redundant_era5/timeseries_demErr_ERA5.h5 -m mintpy_redundant_era5/maskTempCoh.h5 -s linear -o mintpy_redundant_era5/audit/timeseries_ERA5_linearRamp.h5
./mintpy-run timeseries2velocity.py mintpy_redundant_era5/audit/timeseries_ERA5_linearRamp.h5 --ref-date 20240909 --poly 1 --uq residue -o mintpy_redundant_era5/audit/velocity_ERA5_linearRamp.h5
./mintpy-run python mintpy_redundant_era5/audit/run_atmospheric_audit.py
```

The first audit-script run calculated the numerical products and four figures but failed while rendering the representative time-series date axis because compact `YYYYMMDD` values were parsed as years. The script was corrected to explicit `YYYY-MM-DD` parsing and rerun successfully. This was a plotting-only failure; ERA5 and velocity products were unaffected.

## Product validation and warnings

- `ERA5.h5`, corrected time series, and both velocities are valid HDF5 files with the expected 346 × 329 dimensions.
- ERA5 and input date arrays match exactly: 25/25, zero missing dates.
- ERA5 delay cube contains zero NaNs.
- Corrected output retained REF_Y/REF_X 7/186 and REF_DATE 20240909 through MintPy's `diff.py` reference handling.
- Absolute ERA5 slant delays range from −2.3055 to −1.9538 m. Absolute sign follows the MintPy/PyAPS slant-delay convention; the applied correction is the spatially and temporally double-referenced difference.
- The largest single-pixel neighbor delay difference is 0.01898 m on 20240816. Delay maps are spatially smooth overall, with terrain-related fine structure and no scene-wide seam.
- ERA5 velocity changes are larger near the array boundary: outer-ten-pixel RMS 3.062 mm/yr versus 0.846 mm/yr in the interior. The −15.192 mm/yr minimum occurs at corner Y/X 345/0 and is treated as an edge effect.

## Baseline integrity verification

Before and after processing, the following timestamps, sizes, and SHA-1 values were identical:

| File | mtime | bytes | SHA-1 |
|---|---:|---:|---|
| `mintpy/velocity.h5` | 1790272985 | 2365536 | 7184b9c4b291dcc68a44db42b5b3c0617e5b02bb |
| `mintpy/timeseries_demErr.h5` | 1790272968 | 13314144 | 04e6e7f7b9b2ff182a98f38694514b3ae0bf9e64 |
| `mintpy_redundant/velocity.h5` | 1790538573 | 2365536 | d657999322e1dec2b9f5b6b5bc9bd46db940812b |
| `mintpy_redundant/timeseries.h5` | 1790538567 | 13313720 | 5288b9a9acd9a0450007265b06c0ae78dcc4a20f |
| `mintpy_redundant/timeseries_demErr.h5` | 1790538568 | 13314144 | 5fd7c040f2f9502e1956ce73467d5a04f70ce2d2 |
| `mintpy_redundant/maskTempCoh.h5` | 1790538502 | 136648 | 38305f45920e10b546f8e432ab66ef271c935e8e |
| `mintpy_redundant/inputs/ifgramStack.h5` | 1790538308 | 30367336 | 39a26f4e8eed054206d4bb5c4a1963194c2dc83f |

Scientific results and limitations are in `audit/ATMOSPHERIC_SENSITIVITY_AUDIT.md`.
