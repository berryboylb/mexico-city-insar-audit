# Reference audit

Checked 2026-09-29 against the manuscript's claims, publisher or author records, official dataset and software documentation, and the local product records. These sources explain methods and provenance; none verifies this project's 2024 numerical results. Those results are traced in the manuscript with `[S: ...]` pointers to preserved analysis files.

| Manuscript citation | Claim it supports and scope | Verified DOI or official URL |
|---|---|---|
| Torres et al. (2012) | Sentinel-1 mission background; not the orbit, dates, or HyP3 settings of this run | https://doi.org/10.1016/j.rse.2011.05.028 |
| Chaussard et al. (2021) | Prior Mexico City subsidence research; not evidence for a 2024 rate or cause | https://doi.org/10.1029/2020JB020648 |
| Berardino et al. (2002) | Small-baseline network method heritage; not a description of MintPy's exact inversion | https://doi.org/10.1109/TGRS.2002.803792 |
| Yunjun et al. (2019) | MintPy time-series inversion and phase-closure concepts; project configuration and diagnostic thresholds come from local records | https://doi.org/10.1016/j.cageo.2019.104331 |
| Fattahi & Amelung (2013) | DEM-error correction method; local logs establish whether it ran | https://doi.org/10.1109/TGRS.2012.2227761 |
| Jolivet et al. (2011) | Reanalysis-based atmospheric phase-delay correction method; not a PyAPS3 version source | https://doi.org/10.1029/2011GL048757 |
| Jolivet et al. (2014) | Evaluation and limits of global atmospheric-model corrections; does not bound this scene's residual atmosphere | https://doi.org/10.1002/2013JB010588 |
| Hersbach et al. (2020) | ERA5 reanalysis description; exact local hour and downloads come from the processing log | https://doi.org/10.1002/qj.3803 |
| Blewitt et al. (2018) | NGL's requested citation for its processed GNSS products; station data, frame, and time span are established separately | https://doi.org/10.1029/2018EO104623 |
| Hogenson et al. (2020) | ASF's requested HyP3 software citation. The concept DOI does not identify the exact plugin build | https://doi.org/10.5281/zenodo.4646138 |
| ASF DAAC (n.d.) | HyP3 InSAR product workflow, GAMMA and minimum-cost-flow unwrapping; local READMEs establish versions and required product credit | https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/ |
| C3S (n.d.) | ERA5 hourly pressure-level dataset and data-provider credit; not the local application time | https://doi.org/10.24381/cds.bd0915c6 |
| CDSE (n.d.) | Copernicus DEM GLO-30 dataset and credit guidance; local DEM metadata establishes the input used | https://doi.org/10.5270/ESA-c5d3d65 |
| INEGI (2021) | 2019 Mexico City study, Sentinel-1 ascending and descending inputs, combined vertical estimate, and approximately 30 m raster | https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825199395.pdf |
| INEGI (n.d.-a) | RGNA station source and current ICMX interference warning; the warning's effect on the NGL series is unquantified | https://www.inegi.org.mx/app/geo2/rgna/ |
| INEGI (n.d.-b) | Catalog entry for the 2019 Mexico City raster; the methods and resolution are supported by INEGI (2021) | https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463849650 |
| MintPy developers (n.d.-a) | Positive-toward-satellite LOS sign convention | https://github.com/insarlab/MintPy/blob/main/docs/FAQs.md |
| MintPy developers (n.d.-b) | ENU-to-LOS projection formula; local geometry gives the coefficients used here | https://github.com/insarlab/MintPy/blob/main/src/mintpy/asc_desc2horz_vert.py |
| MintPy developers (n.d.-c) | Software implementation of phase-closure ambiguity handling; this study's closure calculation is local and no closure-based correction was run | https://github.com/insarlab/MintPy/blob/main/src/mintpy/unwrap_error_phase_closure.py |
| NGL (n.d.) | Final daily `tenv3` product, IGS20 frame and steps database; processed-data credit also requires Blewitt et al. (2018) | https://geodesy.unr.edu/PlugNPlayPortal.php |
| NOAA NGS (n.d.) | MMX1 identification in the CORS network and FAA operator attribution; NGL supplied the processed series used here | https://geodesy.noaa.gov/CORS/sort_sites.shtml |
| PyAPS developers (n.d.) | PyAPS3 Python 3 / ERA5 implementation; method papers are Jolivet et al. (2011, 2014) | https://github.com/insarlab/PyAPS |

## Credits and local evidence

- The HyP3 product wording, image credit, software versions, and GAMMA release are transcribed from all 31 preserved `hyp3/*/*.README.md.txt` files. The DEM credit is in `hyp3/*/*_dem.tif.xml`. These credits appear in manuscript Acknowledgements; a software paper alone does not satisfy them.
- ERA5 is credited to C3S in the Acknowledgements. The weather-file metadata provenance issue is documented in `final_report/PROVENANCE_NOTE_ERA5_METADATA.md`; the undocumented 3.2 mm check is not used as evidence.
- NGL receives the processed-position credit, while INEGI RGNA and NOAA NGS CORS identify original station sources where verified. The operators of MXTX and MXTO remain unidentified.
- The INEGI catalog page is dynamically rendered, so its web text is difficult to inspect directly; the official 2021 methods report independently supports the manuscript's methodological description. The 2019 product was not used quantitatively and cannot validate this 2024 Sentinel-1 map.
- The superseded GNSS draft archive cited in older text is absent from the release. The manuscript now cites the preserved validation log and final comparison CSV and omits the uncheckable former draft value.

The original phase-closure, GNSS comparison, U95 envelope, and ramp-sensitivity values are study results, not literature-derived claims. They retain their local `[S: ...]` citations in the manuscript. No source establishes ICMX's interference magnitude, a 95% bound on every error, a physical cause, or absolute vertical subsidence for this map.
