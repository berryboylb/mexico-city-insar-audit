# External-validation data availability

## Outcome

Independent GNSS validation is feasible at a small number of points, but the 2024 station geometry is not dense enough to validate the full west-to-east gradient by itself. The recommended next route is a combination: **A, GNSS-to-LOS validation as the primary independent test**, followed by **B, comparison with the official INEGI 2019 deformation raster as a historical spatial-pattern check only**. The INEGI raster reuses Sentinel-1 and is not independent confirmation.

No existing MintPy, redundant-network, or ERA5 result was modified. This investigation downloaded no raw RINEX or raster data; only official station-list metadata and small processed-text availability checks were queried.

## Authoritative-source findings

### INEGI subsidence and MOGEZOD

The closest official Mexico City deformation product found is INEGI's **“Distribución espacial y magnitud de la subsidencia en la Ciudad de México en 2019”**, edition 2020. It is a 30 m GeoTIFF in ITRF2008 epoch 2010.0, covering 98°48′–99°15′ W and 19°09′–19°39′ N, and reports millimetres per year. The catalog explicitly says it was calculated from 2019 Sentinel-1A/B SAR imagery ([INEGI product catalog](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463849650); [INEGI subsidence program](https://www.inegi.org.mx/temas/subsidencia/)). No newer official Mexico City raster close to 2024 was identified in the current catalog.

INEGI's methodology processes ascending and descending Sentinel-1 stacks separately and combines their geometries to estimate the vertical component. The published Mexico City product is therefore a **combined-orbit vertical/hundimiento product**, not a descending LOS raster directly comparable without accounting for geometry and the different 2019 epoch ([INEGI methodology, Volume 2](https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825199395.pdf); [Volume 3](https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463904441.pdf)). It is valuable for qualitative spatial-pattern and order-of-magnitude comparison, but it is neither contemporaneous nor independent of Sentinel-1.

[MOGEZOD](https://www.inegi.org.mx/programas/mogezod/) is a five-year-cycle program combining GNSS and SAR for deformation of Mexico's geodetic frame, with historical coverage since 2011. No downloadable MOGEZOD 2024 Mexico City subsidence raster or per-station processed time series was identified. Product-specific independence cannot be assumed because the program uses both GNSS and SAR.

### GNSS inventory

The exhaustive candidate inventory in `gnss_station_inventory.csv` comes from the official NGL final-solution holdings within the AOI and a deliberately generous nearby box (19.15–19.60° N, 99.75–98.85° W). It includes historical stations so that apparent map markers are not mistaken for 2024 observations.

Five nearby stations have processed daily ENU positions during 2024:

| Station | Location | 2024 daily solutions | Role |
|---|---|---:|---|
| ICMX | 19.4056, −99.1709; inside western AOI | 362 | Primary independent point, but quality warning |
| MMX1 | 19.4317, −99.0684; inside central/eastern AOI | 137 | Primary independent point, incomplete 2024 |
| MXTX | 19.5396, −98.8763; ~10 km northeast | 356 | Eastern regional context |
| MXTO | 19.2798, −99.6078; ~43 km west | 356 | Western regional context, outside scene |
| TOL2 | 19.2932, −99.6435; ~46 km west | 366 | Long-lived regional reference, outside scene |

NGL provides daily IGS20 and North-America-frame east, north, and up components in `tenv3` ASCII ([NGL access documentation](https://geodesy.unr.edu/PlugNPlayPortal.php)). Direct station downloads are recorded in the CSV. These are processed GNSS products independent of the Sentinel-1 observations.

INEGI's [RGNA RINEX service](https://www.inegi.org.mx/app/geo2/rgna/) provides RINEX 2.11/3.04: hourly files at a 15 s recording interval and daily RINEX 2.11 files at 30 s. It currently warns that ICMX data are unavailable until further notice because interference generates low-quality observations. That warning must be carried into any use of the otherwise nearly complete NGL ICMX processed series.

NOAA's official CORS list identifies MMX1 (Mexico City WAAS) as operating from GPS day 2008:116, nominally 1 s for recent data and decimated to 30 s after 30 days; it also lists TOL2 at 15 s ([NOAA CORS list](https://geodesy.noaa.gov/CORS/sort_sites.shtml); [NOAA data products](https://geodesy.noaa.gov/CORS/data.shtml)). NOAA raw RINEX is available for MMX1. NGL supplies its processed ENU series.

The [USGS GNSS-source directory](https://earthquake.usgs.gov/monitoring/gps/sources.php) recognizes Mexican GNSS providers, but no USGS-operated continuous station or downloadable 2024 Mexico City displacement product was found for this AOI. General USGS Mexico City subsidence pages are contextual, not validation datasets.

### Spatial coverage limitation

Only ICMX and MMX1 lie inside the processed AOI and have any 2024 processed ENU data. Their longitude separation is about 0.103° (roughly 11 km), while the scene spans about 0.25° longitude. MMX1 has only 137 daily solutions in 2024. The other three contemporaneous stations lie outside the raster.

This supports pointwise tests and one sparse west-to-east contrast, but **does not provide enough well-distributed interior stations to fit or independently validate the full two-dimensional plane**. A two-point difference is especially vulnerable to monument-specific motion, gaps, reference-frame choices, and ICMX's interference warning.

## Exact GNSS-to-descending-LOS projection

The stored geometry is descending, right-looking Sentinel-1:

- `ORBIT_DIRECTION = DESCENDING`
- platform heading = −167.738979° clockwise from north
- incidence-angle raster = 30.506622–32.678330° from vertical
- MintPy LOS sign = **motion toward the satellite is positive**

MintPy 1.6.4 converts platform heading to ground-to-satellite azimuth using

`azimuth = −(heading − 90°) = −102.261021°`.

For GNSS displacement `(E,N,U)` with east, north, and up positive, MintPy's exact projection is

`LOS_toward = −E sin(i) sin(a) + N sin(i) cos(a) + U cos(i)`

where `i` is the local incidence angle and `a = −102.261021°`. Using the actual pixelwise incidence raster, the coefficients range over the scene as:

- east: +0.496059 to +0.527606
- north: −0.114661 to −0.107805
- up: +0.841715 to +0.861570

At the center pixel (`i = 31.602330°`):

`LOS_toward = 0.512068 E − 0.111284 N + 0.851706 U`.

Thus eastward and upward motion produce positive MintPy LOS displacement for this descending geometry; northward motion produces a small negative contribution. The coefficients must be sampled from `incidenceAngle` at each station rather than using only the center value.

Before comparing rates, the GNSS LOS series must be put into the same relative convention as InSAR: use the same 2024 dates/model where possible, subtract the 2024-09-09 temporal reference, and subtract the GNSS-projected LOS rate of the selected reference site or reference patch. Comparing absolute NGL IGS20 velocities directly with a spatially referenced InSAR map would mix reference conventions.

## Recommended validation route

### Primary: A — GNSS-to-LOS

1. Download only the small NGL `tenv3` series for ICMX, MMX1, MXTX, MXTO, and TOL2.
2. Inspect gaps, offsets, uncertainties, equipment changes, and ICMX quality before fitting anything.
3. Estimate 2024 ENU trends with the exact InSAR date span and project them using the local coefficients above.
4. Compare ICMX and MMX1 against common-mask InSAR values using a small local raster patch, not one pixel.
5. Use TOL2/MXTO/MXTX only to assess regional frame behavior; do not pretend they sample the AOI plane.

This is the only identified route that is observationally independent of Sentinel-1.

### Secondary: B — INEGI 2019 raster

Use the official raster only to test whether persistent spatial patterns and relative ordering resemble the 2019 combined-orbit vertical product. Do not compare signs or magnitudes as though it were a 2024 descending LOS map, and do not count agreement as independent satellite validation.

### Future: C — ascending-track comparison

An independently processed ascending 2024 Sentinel-1 stack would be the strongest way to diagnose whether the west-east signal changes sign as expected for horizontal contamination and to solve approximate east/up components with the descending stack. No ready official 2024 ascending Mexico City product was found, so this requires a new processing project and is not started here.

## Decision before validation analysis

Proceed with GNSS-to-LOS only after accepting these limitations: two usable stations inside the scene, incomplete MMX1 coverage, an explicit ICMX data-quality warning, and insufficient spatial density to validate the entire west-east plane. The validation can test local rates and a sparse cross-scene contrast; it cannot by itself establish that the full broad gradient is physical.
