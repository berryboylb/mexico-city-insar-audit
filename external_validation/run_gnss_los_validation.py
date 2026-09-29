#!/usr/bin/env python3
"""GNSS-to-descending-LOS validation of the redundant/ERA5 MintPy cases.

Run from the project root through the MintPy container:
    ./mintpy-run python external_validation/run_gnss_los_validation.py

Reads only; writes exclusively inside external_validation/ (gnss_processed/,
gnss_los_results.json, gnss_los_comparison.csv, fig_*.png).
"""
import csv, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import h5py
import numpy as np
from scipy import stats
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('/data'); EV = ROOT/'external_validation'; RAW = EV/'gnss_raw'; PROC = EV/'gnss_processed'
PROC.mkdir(exist_ok=True)
STATIONS = ['ICMX', 'MMX1', 'MXTX', 'MXTO', 'TOL2']
PRIMARY = ['ICMX', 'MMX1']
URL = {s: f'https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/{s}.tenv3' for s in STATIONS}
STEPS_URL = 'https://geodesy.unr.edu/NGLStationPages/steps.txt'
RETRIEVED = {'tenv3': '2026-09-27 (file mtime 22:06 local); server Content-Length re-checked 2026-09-27T21:14Z, identical',
             'steps': '2026-09-27T21:14:33Z'}
TOL_DAYS = 1           # primary Sentinel<->GNSS matching tolerance
PATCHES = [5, 9, 13]   # square patch sizes (pixels, 80 m)
PRIMARY_PATCH = 9
NBOOT = 4000
YR = 365.25


def dt64(d):
    d = str(d)
    return np.datetime64(f'{d[:4]}-{d[4:6]}-{d[6:]}') if '-' not in d else np.datetime64(d)


def years(t, t0=None):
    t = np.asarray(t)
    return (t - (t[0] if t0 is None else t0)).astype('timedelta64[D]').astype(float)/YR


def ols(x, z):
    """Slope, standard error, 95% t half-width, residuals."""
    x = np.asarray(x, float); z = np.asarray(z, float); n = len(x)
    G = np.column_stack([np.ones(n), x]); b = np.linalg.lstsq(G, z, rcond=None)[0]; r = z - G@b
    se = np.sqrt(np.sum(r*r)/max(n-2, 1)/np.sum((x-x.mean())**2)) if n > 2 else np.nan
    hw = stats.t.ppf(.975, n-2)*se if n > 2 else np.nan
    return float(b[1]), float(se), float(hw), r


def ar1_halfwidth(x, z):
    """95% half-width with AR(1) effective sample size (Bretherton-style; epochs treated as ordered)."""
    s, se, _, r = ols(x, z); n = len(z)
    rho = float(np.corrcoef(r[:-1], r[1:])[0, 1]) if n > 3 else 0.0
    rho = max(rho, 0.0); neff = max(n*(1-rho)/(1+rho), 3.0)
    se_adj = se*np.sqrt((n-2)/max(neff-2, 1))
    return float(stats.t.ppf(.975, max(neff-2, 1))*se_adj), rho, neff


def block_boot(x, z, nboot=NBOOT, block=3, seed=0):
    rng = np.random.default_rng(seed); n = len(z)
    G = np.column_stack([np.ones(n), x]); b = np.linalg.lstsq(G, z, rcond=None)[0]; r = z - G@b
    starts = np.arange(max(1, n-block+1)); out = np.empty(nboot)
    for k in range(nboot):
        idx = []
        while len(idx) < n:
            q = int(rng.choice(starts)); idx.extend(range(q, min(q+block, n)))
        out[k] = np.linalg.lstsq(G, G@b + r[np.array(idx[:n])], rcond=None)[0][1]
    return out


# ---------------------------------------------------------------- parsing
def parse_tenv3(path):
    lines = path.read_text().splitlines(); header = lines[0].split(); rows = []
    for line in lines[1:]:
        p = line.split()
        if not p:
            continue
        rows.append(dict(site=p[0], date=datetime.strptime(p[1], '%y%b%d').strftime('%Y-%m-%d'), decimal_year=float(p[2]),
                         mjd=int(p[3]), reflon=float(p[6]),
                         east_m=float(p[7])+float(p[8]), north_m=float(p[9])+float(p[10]), up_m=float(p[11])+float(p[12]),
                         antenna_height_m=float(p[13]), sigma_e_m=float(p[14]), sigma_n_m=float(p[15]), sigma_u_m=float(p[16]),
                         corr_en=float(p[17]), corr_eu=float(p[18]), corr_nu=float(p[19]),
                         latitude_deg=float(p[20]), longitude_deg=float(p[21]), height_m=float(p[22])))
    return rows, header


def parse_steps(path):
    out = {s: [] for s in STATIONS}
    for line in path.read_text().splitlines():
        p = line.split()
        if len(p) >= 4 and p[0] in out:
            d = datetime.strptime(p[1], '%y%b%d').strftime('%Y-%m-%d')
            if p[2] == '1':
                out[p[0]].append(dict(date=d, type='equipment', description=' '.join(p[3:])))
            else:
                out[p[0]].append(dict(date=d, type='earthquake', threshold_distance_km=float(p[3]),
                                      distance_km=float(p[4]), magnitude=float(p[5]), event_id=p[6]))
    return out


COMP = [('east_m', .005, .010), ('north_m', .005, .010), ('up_m', .015, .020)]  # (component, min outlier thr, min jump thr)


def qc(rows):
    r = [dict(x) for x in rows if x['date'].startswith('2024-')]
    t = np.array([np.datetime64(x['date']) for x in r]); x = years(t)
    counts = {}
    for q in r:
        counts[q['date']] = counts.get(q['date'], 0) + 1
    dup = sorted(d for d, n in counts.items() if n > 1)
    keep = np.array([q['date'] not in dup for q in r]); reasons = [['duplicate_date'] if q['date'] in dup else [] for q in r]
    # formal-sigma rule: any sigma > 5x station 2024 median
    for c in ['sigma_e_m', 'sigma_n_m', 'sigma_u_m']:
        s = np.array([q[c] for q in r]); thr = 5*np.median(s)
        for i in np.flatnonzero(s > thr):
            reasons[i].append(f'{c}_gt_5x_median_{thr:.6f}m'); keep[i] = False
    # robust detrended-residual rule, per component, single pass
    thresholds = {}
    for c, minthr, _ in COMP:
        z = np.array([q[c] for q in r]); _, _, _, res = ols(x[keep], z[keep])
        med = np.median(res); mad = 1.4826*np.median(np.abs(res-med)); thr = max(6*mad, minthr); thresholds[c] = thr
        idx = np.flatnonzero(keep); bad = np.abs(res-med) > thr
        for i in idx[bad]:
            reasons[i].append(f'{c}_detrended_residual_{(res[list(idx).index(i)]-med)*1000:+.2f}mm_gt_{thr*1000:.2f}mm')
        keep[idx[bad]] = False
    # jump candidates between consecutive raw days (<=2 d apart): reported, never corrected
    steps = []
    for c, _, hard in COMP:
        z = np.array([q[c] for q in r]); dz = np.diff(z); gd = np.diff(t).astype('timedelta64[D]').astype(int)
        short = dz[gd <= 2]; scale = 1.4826*np.median(np.abs(short-np.median(short)))
        thr = max(8*scale, hard)
        for j in np.flatnonzero((gd <= 2) & (np.abs(dz) > thr)):
            steps.append(dict(component=c, date_before=str(t[j]), date_after=str(t[j+1]), jump_mm=float(dz[j]*1000), threshold_mm=float(thr*1000)))
    # persistent-offset test at each jump candidate: mean of 10 d before vs 10 d after (clean data)
    for s in steps:
        c = s['component']; tb = np.datetime64(s['date_before']); ta = np.datetime64(s['date_after'])
        zc = np.array([q[c] for q in r]); tt = t
        pre = keep & (tt <= tb) & (tt > tb-np.timedelta64(10, 'D')); post = keep & (tt >= ta) & (tt < ta+np.timedelta64(10, 'D'))
        s['persistent_offset_mm_10d_means'] = float((np.mean(zc[post])-np.mean(zc[pre]))*1000) if pre.any() and post.any() else None
    gaps = []
    for a, b in zip(t[:-1], t[1:]):
        n = int((b-a)/np.timedelta64(1, 'D'))-1
        if n > 0:
            gaps.append(dict(after=str(a), before=str(b), missing_days=n))
    for q, k, why in zip(r, keep, reasons):
        q['included'] = bool(k); q['exclusion_reason'] = ';'.join(why)
    return r, dup, steps, gaps, thresholds


# ------------------------------------------------------------------- GNSS
raw_all, qcinfo, r2024 = {}, {}, {}
steps_db = parse_steps(RAW/'NGL_steps.txt')
FIELDS = ['site', 'date', 'decimal_year', 'mjd', 'east_m', 'north_m', 'up_m', 'antenna_height_m', 'sigma_e_m', 'sigma_n_m', 'sigma_u_m',
          'corr_en', 'corr_eu', 'corr_nu', 'latitude_deg', 'longitude_deg', 'height_m']
for s in STATIONS:
    rows, header = parse_tenv3(RAW/f'{s}.tenv3'); raw_all[s] = rows
    r, dup, jumps, gaps, thr = qc(rows); r2024[s] = r
    clean = [q for q in r if q['included']]; excl = [q for q in r if not q['included']]
    for name, data, extra in [('raw', r, ['included', 'exclusion_reason']), ('cleaned', clean, []), ('excluded', excl, ['exclusion_reason'])]:
        with open(PROC/f'{s}_2024_{name}.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS+extra, extrasaction='ignore'); w.writeheader(); w.writerows(data)
    st = steps_db[s]
    qcinfo[s] = dict(source_url=URL[s], retrieved=RETRIEVED['tenv3'],
                     sha256=hashlib.sha256((RAW/f'{s}.tenv3').read_bytes()).hexdigest(), bytes=(RAW/f'{s}.tenv3').stat().st_size,
                     format='NGL tenv3 ASCII, daily 24-h final solutions', reference_frame='IGS20 (NGL tenv3/IGS20 directory)',
                     units='metres (positions and formal sigmas); ENU relative to NGL reference position; east/north/up positive',
                     position_definition='_e0+__east, n0+_north, u0+__up (integer+fractional parts summed)',
                     antenna_heights_2024_m=sorted({q['antenna_height_m'] for q in r}), reflon_2024=sorted({q['reflon'] for q in r}),
                     full_start=rows[0]['date'], full_end=rows[-1]['date'], full_count=len(rows),
                     start_2024=r[0]['date'], end_2024=r[-1]['date'], count_2024=len(r), cleaned_count_2024=len(clean),
                     excluded=[{k: q[k] for k in ['date', 'exclusion_reason']} for q in excl],
                     duplicate_dates=dup, gaps=gaps, longest_gap_days=max([g['missing_days'] for g in gaps], default=0),
                     outlier_thresholds_mm={k: v*1000 for k, v in thr.items()}, jump_candidates=jumps,
                     ngl_steps_all=st, ngl_steps_2023_12_to_2025_01=[x for x in st if '2023-12-01' <= x['date'] <= '2025-01-31'],
                     median_sigma_mm={c: float(np.median([q[f'sigma_{c}_m'] for q in r])*1000) for c in 'enu'})

# ---------------------------------------------------------------- geometry
with h5py.File(ROOT/'mintpy_redundant/inputs/geometryGeo.h5', 'r') as f:
    inc = f['incidenceAngle'][()]; ga = dict(f.attrs)
heading = float(ga['HEADING']); az = -(heading-90); az -= np.round(az/360)*360   # MintPy 1.6.4 heading2azimuth_angle (right-looking)
tr = Transformer.from_crs(4326, int(ga['EPSG']), always_xy=True)
X0, Y0, DX, DY = (float(ga[k]) for k in ['X_FIRST', 'Y_FIRST', 'X_STEP', 'Y_STEP'])
geom = {}
for s in STATIONS:
    lat = float(np.median([q['latitude_deg'] for q in r2024[s]])); lon = float(np.median([q['longitude_deg'] for q in r2024[s]]))
    xu, yu = tr.transform(lon, lat)
    px = int(np.floor((xu-X0)/DX)); py = int(np.floor((yu-Y0)/DY))       # X_FIRST/Y_FIRST are the upper-left pixel corner
    inside = 0 <= py < inc.shape[0] and 0 <= px < inc.shape[1]
    cy = min(max(py, 0), inc.shape[0]-1); cx = min(max(px, 0), inc.shape[1]-1); i = float(inc[cy, cx])
    ce = -np.sin(np.radians(i))*np.sin(np.radians(az)); cn = np.sin(np.radians(i))*np.cos(np.radians(az)); cu = np.cos(np.radians(i))
    geom[s] = dict(latitude=lat, longitude=lon, utm_x=xu, utm_y=yu, y=py, x=px, inside_aoi=inside, incidence_deg=i,
                   angle_source='station pixel' if inside else 'nearest raster edge pixel (diagnostic only)',
                   azimuth_deg=float(az), los_e=float(ce), los_n=float(cn), los_u=float(cu),
                   pixel_centre_offset_m=[float(xu-(X0+(px+.5)*DX)), float(yu-(Y0+(py+.5)*DY))])
    for q in r2024[s]:
        q['los_m'] = ce*q['east_m'] + cn*q['north_m'] + cu*q['up_m']
# sanity: unit vector and descending right-looking direction (ground->satellite points ESE, i.e. east component > 0)
for s in PRIMARY:
    g = geom[s]; assert abs(g['los_e']**2+g['los_n']**2+g['los_u']**2-1) < 1e-9 and g['los_e'] > 0 and g['los_n'] < 0

# ---------------------------------------------------------------- matching
with h5py.File(ROOT/'mintpy_redundant/timeseries_demErr.h5', 'r') as f:
    sar_dates = [d.decode() for d in f['date'][()]]; ts_attrs = dict(f.attrs)
sar_t = np.array([dt64(d) for d in sar_dates])


def match(rows, tol):
    """Nearest GNSS day within +/-tol; ties resolved to the preceding day. No interpolation."""
    t = np.array([np.datetime64(q['date']) for q in rows]); out = {}
    if not len(t):
        return out
    for d, sd in zip(sar_dates, sar_t):
        off = (t-sd).astype('timedelta64[D]').astype(int); cand = np.flatnonzero(np.abs(off) <= tol)
        if len(cand):
            j = min(cand, key=lambda k: (abs(off[k]), off[k] > 0))
            out[d] = dict(rows[j], offset_days=int(off[j]))
    return out


def clean_rows(s):
    return [q for q in r2024[s] if q['included']]


def gnss_diff(tol=TOL_DAYS, use_raw=False, dates=None):
    src = (lambda s: r2024[s]) if use_raw else clean_rows
    m1, m2 = match(src('ICMX'), tol), match(src('MMX1'), tol)
    cd = [d for d in sar_dates if d in m1 and d in m2 and (dates is None or d in dates)]
    return cd, np.array([m1[d]['los_m']-m2[d]['los_m'] for d in cd]), m1, m2


common, g_d, mI, mM = gnss_diff()
ct = np.array([dt64(d) for d in common]); cx = years(ct)
exact = [d for d in common if mI[d]['offset_days'] == 0 and mM[d]['offset_days'] == 0]
sar_in_window = [d for d in sar_dates if common[0] <= d <= common[-1]]
mmx1_span = (r2024['MMX1'][0]['date'], r2024['MMX1'][-1]['date'])

# ------------------------------------------------------------------- InSAR
CASES = {
    'A_redundant_no_ramp':      ('mintpy_redundant/timeseries_demErr.h5', 'mintpy_redundant/audit/velocity_B_topo.h5', 'mintpy_redundant/temporalCoherence.h5'),
    'B_redundant_linear_ramp':  ('mintpy_redundant/audit/timeseries_topo_linearRamp.h5', 'mintpy_redundant/audit/velocity_D_topo_linearRamp.h5', 'mintpy_redundant/temporalCoherence.h5'),
    'C_ERA5_no_ramp':           ('mintpy_redundant_era5/timeseries_demErr_ERA5.h5', 'mintpy_redundant_era5/velocity_ERA5.h5', 'mintpy_redundant_era5/temporalCoherence.h5'),
    'D_ERA5_linear_ramp':       ('mintpy_redundant_era5/audit/timeseries_ERA5_linearRamp.h5', 'mintpy_redundant_era5/audit/velocity_ERA5_linearRamp.h5', 'mintpy_redundant_era5/temporalCoherence.h5'),
}
with h5py.File(ROOT/'mintpy_redundant/maskTempCoh.h5', 'r') as f:
    mask = f['mask'][()].astype(bool)
with h5py.File(ROOT/'mintpy_redundant_era5/maskTempCoh.h5', 'r') as f:
    mask &= f['mask'][()].astype(bool)          # common mask (identical in practice)
patch, ts_cube, vel_map, case_attrs = {}, {}, {}, {}
for cname, (tsf, vf, cohf) in CASES.items():
    with h5py.File(ROOT/tsf, 'r') as f:
        arr = f['timeseries'][()]; assert [d.decode() for d in f['date'][()]] == sar_dates
        a = dict(f.attrs); case_attrs[cname] = {k: str(a.get(k)) for k in ['REF_DATE', 'REF_Y', 'REF_X', 'UNIT', 'mintpy.deramp']}
    with h5py.File(ROOT/vf, 'r') as f:
        vel = f['velocity'][()]*1000; vstd = f['velocityStd'][()]*1000
    with h5py.File(ROOT/cohf, 'r') as f:
        coh = f['temporalCoherence'][()]
    ts_cube[cname] = arr; vel_map[cname] = vel; patch[cname] = {}
    for s in PRIMARY:
        py, px = geom[s]['y'], geom[s]['x']; patch[cname][s] = {}
        for n in PATCHES:
            h = n//2; ys = slice(py-h, py+h+1); xs = slice(px-h, px+h+1)
            vm = mask[ys, xs] & np.isfinite(vel[ys, xs]); v = vel[ys, xs][vm]
            series = np.median(arr[:, ys, xs][:, vm], axis=1)
            patch[cname][s][str(n)] = dict(patch_size_px=n, patch_size_m=n*80, valid_pixels=int(vm.sum()), total_pixels=n*n,
                                           temporal_coherence_median=float(np.median(coh[ys, xs][vm])), temporal_coherence_min=float(np.min(coh[ys, xs][vm])),
                                           velocity_median_mm_yr=float(np.median(v)), velocity_mad_mm_yr=float(1.4826*np.median(np.abs(v-np.median(v)))),
                                           velocity_iqr_mm_yr=float(np.subtract(*np.percentile(v, [75, 25]))),
                                           velocity_std_median_mm_yr=float(np.median(vstd[ys, xs][vm])), single_pixel_velocity_mm_yr=float(vel[py, px]),
                                           timeseries_m=series.tolist())

# linear plane removed by the ramp step, estimated from A-B (and C-D) velocity differences
YY, XX = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]
plane = {}
for nr, rr in [('A_minus_B', ('A_redundant_no_ramp', 'B_redundant_linear_ramp')), ('C_minus_D', ('C_ERA5_no_ramp', 'D_ERA5_linear_ramp'))]:
    dv = vel_map[rr[0]]-vel_map[rr[1]]; ok = mask & np.isfinite(dv)
    east_km = (XX[ok]*DX)/1000
    north_km = ((mask.shape[0]-1-YY[ok])*abs(DY))/1000
    G = np.column_stack([np.ones(ok.sum()), east_km, north_km]); b, *_ = np.linalg.lstsq(G, dv[ok], rcond=None)
    fit_rms = float(np.sqrt(np.mean((dv[ok]-G@b)**2)))
    de = (geom['ICMX']['x']-geom['MMX1']['x'])*DX/1000; dn = (geom['MMX1']['y']-geom['ICMX']['y'])*abs(DY)/1000
    plane[nr] = dict(gradient_east_mm_yr_per_km=float(b[1]), gradient_north_mm_yr_per_km=float(b[2]), plane_fit_rms_mm_yr=fit_rms,
                     ICMX_minus_MMX1_baseline_east_km=float(de), ICMX_minus_MMX1_baseline_north_km=float(dn),
                     plane_ICMX_minus_MMX1_mm_yr=float(b[1]*de+b[2]*dn))

# --------------------------------------------------------------- comparison
def insar_diff(cname, n, dates):
    a = np.array(patch[cname]['ICMX'][str(n)]['timeseries_m']); b = np.array(patch[cname]['MMX1'][str(n)]['timeseries_m'])
    idx = [sar_dates.index(d) for d in dates]; return a[idx]-b[idx]


g_rate, g_se, g_hw, g_res = ols(cx, g_d)
g_boot = block_boot(cx, g_d, seed=11); g_ci_boot = np.percentile(g_boot, [2.5, 97.5])
g_ts_rate = stats.theilslopes(g_d, cx)[0]
# cadence sensitivity: all common daily solutions inside the common acquisition window (NOT an InSAR-equivalent sampling)
cI = {q['date']: q for q in clean_rows('ICMX')}; cM = {q['date']: q for q in clean_rows('MMX1')}
dd = sorted(d for d in set(cI) & set(cM) if str(ct[0]) <= d <= str(ct[-1]))
dd_t = np.array([np.datetime64(d) for d in dd]); dd_z = np.array([cI[d]['los_m']-cM[d]['los_m'] for d in dd])
g_daily_rate, g_daily_se, g_daily_hw, _ = ols(years(dd_t, ct[0]), dd_z)
dd_all = sorted(set(cI) & set(cM)); dd_all_t = np.array([np.datetime64(d) for d in dd_all])
g_daily_all_rate = ols(years(dd_all_t), np.array([cI[d]['los_m']-cM[d]['los_m'] for d in dd_all]))[0]
# outlier-treatment sensitivity: unfiltered raw solutions, same matching rule
raw_common, raw_gd, *_ = gnss_diff(use_raw=True); g_raw_rate = ols(years(np.array([dt64(d) for d in raw_common])), raw_gd)[0]
# matching-tolerance sensitivity
tol_sens = {}
for tol in [0, 1, 2]:
    cd, z, *_ = gnss_diff(tol=tol); tol_sens[tol] = dict(n=len(cd), dates=cd, gnss_rate_mm_yr=ols(years(np.array([dt64(d) for d in cd])), z)[0]*1000)

rows_out = []
for cname in CASES:
    for n in PATCHES:
        s_d = insar_diff(cname, n, common)
        s_rate, s_se, s_hw, s_res = ols(cx, s_d)
        delta = g_d - s_d
        d_rate, d_se, d_hw, d_res = ols(cx, delta)
        d_hw_ar1, rho, neff = ar1_halfwidth(cx, delta)
        d_boot = np.percentile(block_boot(cx, delta, seed=100+n), [2.5, 97.5])
        loo = [ols(np.delete(cx, k), np.delete(delta, k))[0]*1000 for k in range(len(cx))]
        aligned = delta - delta.mean()
        g_detr = g_d - (np.polyval(np.polyfit(cx, g_d, 1), cx)); s_detr = s_d - np.polyval(np.polyfit(cx, s_d, 1), cx)
        s_ts = stats.theilslopes(s_d, cx)[0]
        full = patch[cname]['ICMX'][str(n)]['velocity_median_mm_yr'] - patch[cname]['MMX1'][str(n)]['velocity_median_mm_yr']
        # InSAR sampled only at exact-date pairs and at tolerance variants
        e_s = ols(years(np.array([dt64(d) for d in exact])), insar_diff(cname, n, exact))[0]*1000
        e_g = tol_sens[0]['gnss_rate_mm_yr']
        tol_diffs = []
        for tol in [0, 1, 2]:
            cd, z, *_ = gnss_diff(tol=tol); xx = years(np.array([dt64(d) for d in cd]))
            tol_diffs.append(ols(xx, z - insar_diff(cname, n, cd))[0]*1000)
        rows_out.append(dict(
            case=cname, patch_size_px=n, patch_size_m=n*80,
            valid_px_ICMX=patch[cname]['ICMX'][str(n)]['valid_pixels'], valid_px_MMX1=patch[cname]['MMX1'][str(n)]['valid_pixels'],
            tcoh_median_ICMX=patch[cname]['ICMX'][str(n)]['temporal_coherence_median'], tcoh_median_MMX1=patch[cname]['MMX1'][str(n)]['temporal_coherence_median'],
            common_epochs=len(common), common_start=common[0], common_end=common[-1], common_days=int((ct[-1]-ct[0])/np.timedelta64(1, 'D')),
            gnss_diff_mm_yr=g_rate*1000, gnss_diff_ci95_lo=(g_rate-g_hw)*1000, gnss_diff_ci95_hi=(g_rate+g_hw)*1000,
            insar_diff_common_mm_yr=s_rate*1000, insar_diff_ci95_lo=(s_rate-s_hw)*1000, insar_diff_ci95_hi=(s_rate+s_hw)*1000,
            gnss_minus_insar_mm_yr=d_rate*1000, gmi_ci95_ols_lo=(d_rate-d_hw)*1000, gmi_ci95_ols_hi=(d_rate+d_hw)*1000,
            gmi_ci95_ar1_lo=(d_rate-d_hw_ar1)*1000, gmi_ci95_ar1_hi=(d_rate+d_hw_ar1)*1000, gmi_residual_lag1_rho=rho, gmi_neff=neff,
            gmi_ci95_blockboot_lo=d_boot[0]*1000, gmi_ci95_blockboot_hi=d_boot[1]*1000,
            gmi_leave_one_out_min=min(loo), gmi_leave_one_out_max=max(loo),
            aligned_rmse_mm=float(np.sqrt(np.mean(aligned**2))*1000), correlation=float(np.corrcoef(g_d, s_d)[0, 1]),
            detrended_correlation=float(np.corrcoef(g_detr, s_detr)[0, 1]),
            gmi_theilsen_mm_yr=(g_ts_rate - s_ts)*1000, gmi_raw_gnss_mm_yr=None,  # filled below
            gmi_tol0_exact_mm_yr=tol_diffs[0], gmi_tol1_mm_yr=tol_diffs[1], gmi_tol2_mm_yr=tol_diffs[2],
            insar_diff_full_period_mm_yr=full, insar_common_minus_full_mm_yr=s_rate*1000-full,
            gnss_minus_insar_full_period_NONEQUIVALENT_mm_yr=g_rate*1000-full,
        ))
# raw-GNSS variant of the difference (raw matched dates may differ from cleaned)
for row in rows_out:
    rd = ols(years(np.array([dt64(d) for d in raw_common])), raw_gd - insar_diff(row['case'], row['patch_size_px'], raw_common))[0]*1000
    row['gmi_raw_gnss_mm_yr'] = rd

# ----------------------------------------------------- decision (pre-stated rule)
# Systematic allowance added in quadrature to the AR(1)-adjusted statistical half-width:
#   GNSS cadence (acquisition-sampled vs all-daily rate), GNSS outlier treatment (clean vs raw),
#   matching tolerance (max |change| over 0/1/2 d), patch size (half-range over 5/9/13 px).
# A case is REJECTED if |GNSS-InSAR| > U95, CONSISTENT otherwise. ICMX interference is treated separately
# as a stress test: the unmodelled ICMX bias that would be needed to reconcile each case.
sys_cad = abs(g_rate*1000 - g_daily_rate*1000); sys_out = abs(g_rate*1000 - g_raw_rate*1000)
decision = {}
for cname in CASES:
    rr = [r for r in rows_out if r['case'] == cname]; p = next(r for r in rr if r['patch_size_px'] == PRIMARY_PATCH)
    sys_tol = max(abs(p[k]-p['gnss_minus_insar_mm_yr']) for k in ['gmi_tol0_exact_mm_yr', 'gmi_tol2_mm_yr'])
    sys_patch = (max(r['insar_diff_common_mm_yr'] for r in rr) - min(r['insar_diff_common_mm_yr'] for r in rr))/2
    stat = (p['gmi_ci95_ar1_hi']-p['gmi_ci95_ar1_lo'])/2
    sys = float(np.sqrt(sys_cad**2+sys_out**2+sys_tol**2+sys_patch**2)); U = float(np.sqrt(stat**2+sys**2))
    diff = p['gnss_minus_insar_mm_yr']
    decision[cname] = dict(gnss_minus_insar_mm_yr=diff, stat_halfwidth_ar1=stat, sys_cadence=sys_cad, sys_outlier=sys_out,
                           sys_matching=sys_tol, sys_patch=sys_patch, sys_total=sys, U95=U, z=diff/(U/1.96),
                           verdict='consistent' if abs(diff) <= U else 'rejected',
                           icmx_bias_needed_mm_yr=diff, icmx_bias_needed_mm_over_window=diff*p['common_days']/YR)
for r in rows_out:
    r['U95_primary_rule_mm_yr'] = decision[r['case']]['U95']; r['verdict_primary_patch'] = decision[r['case']]['verdict']

# ------------------------------------------------------ ICMX / MMX1 reliability
def annual_los_rates(s):
    g = geom[s]; out = {}
    for yr in range(2008, 2027):
        rr = [q for q in raw_all[s] if q['date'].startswith(f'{yr}-')]
        if len(rr) < 60:
            continue
        t = np.array([np.datetime64(q['date']) for q in rr]); z = np.array([g['los_e']*q['east_m']+g['los_n']*q['north_m']+g['los_u']*q['up_m'] for q in rr])
        e = np.array([q['east_m'] for q in rr]); u = np.array([q['up_m'] for q in rr])
        out[yr] = dict(n=len(rr), los_theilsen_mm_yr=float(stats.theilslopes(z, years(t))[0]*1000),
                       up_theilsen_mm_yr=float(stats.theilslopes(u, years(t))[0]*1000), east_theilsen_mm_yr=float(stats.theilslopes(e, years(t))[0]*1000))
    return out


reliability = {}
for s in STATIONS:
    c = clean_rows(s); t = np.array([np.datetime64(q['date']) for q in c]); x = years(t)
    scat = {}
    for comp in ['east_m', 'north_m', 'up_m', 'los_m']:
        _, _, _, res = ols(x, np.array([q[comp] for q in c]))
        dres = np.diff(res)
        scat[comp.replace('_m', '')] = dict(detrended_robust_std_mm=float(1.4826*np.median(np.abs(res-np.median(res)))*1000),
                                           day_to_day_robust_std_mm=float(1.4826*np.median(np.abs(dres-np.median(dres)))/np.sqrt(2)*1000))
    reliability[s] = dict(scatter_2024=scat, annual_rates=annual_los_rates(s) if s in PRIMARY else None)

# ------------------------------------------------------------ regional
regional = {}
for s in STATIONS:
    c = clean_rows(s); t = np.array([np.datetime64(q['date']) for q in c]); x = years(t)
    regional[s] = dict(n=len(c), start=c[0]['date'], end=c[-1]['date'], inside_aoi=geom[s]['inside_aoi'], angle_source=geom[s]['angle_source'])
    for comp in ['east_m', 'north_m', 'up_m', 'los_m']:
        rt, se, hw, _ = ols(x, np.array([q[comp] for q in c])); regional[s][comp.replace('_m', '_mm_yr')] = rt*1000; regional[s][comp.replace('_m', '_ci95_mm_yr')] = hw*1000
# common-mode: detrended daily LOS residuals on days shared by all stations within the MMX1 window
days = sorted(set.intersection(*[{q['date'] for q in clean_rows(s)} for s in STATIONS]))
resid = {}
for s in STATIONS:
    d = {q['date']: q['los_m'] for q in clean_rows(s)}; t = np.array([np.datetime64(k) for k in days]); z = np.array([d[k] for k in days])
    resid[s] = ols(years(t), z)[3]*1000
cm = np.median(np.vstack([resid[s] for s in ['MXTX', 'MXTO', 'TOL2']]), axis=0)
corr = {a: {b: float(np.corrcoef(resid[a], resid[b])[0, 1]) for b in STATIONS} for a in STATIONS}
# frame test: a uniform regional translation cancels in ICMX-MMX1; quantify the regional LOS rate spread and the
# common-mode residual that would enter only if the two stations' projection coefficients differ.
dcoef = {k: geom['ICMX'][k]-geom['MMX1'][k] for k in ['los_e', 'los_n', 'los_u']}
regional_summary = dict(shared_days=len(days), shared_start=days[0], shared_end=days[-1], residual_correlation=corr,
                        regional_common_mode_std_mm=float(np.std(cm)),
                        common_mode_removed_icmx_minus_mmx1_resid_std_mm=float(np.std((resid['ICMX']-cm)-(resid['MMX1']-cm))),
                        icmx_minus_mmx1_resid_std_mm=float(np.std(resid['ICMX']-resid['MMX1'])),
                        projection_coefficient_difference_ICMX_minus_MMX1=dcoef,
                        los_rate_range_regional_mm_yr=[min(regional[s]['los_mm_yr'] for s in ['MXTX', 'MXTO', 'TOL2']), max(regional[s]['los_mm_yr'] for s in ['MXTX', 'MXTO', 'TOL2'])])

# ---------------------------------------------------------------- outputs
def js(o):
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


out = dict(
    generated_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),
    question='Does independent GNSS favour the original long-wavelength InSAR gradient (no ramp) or the linear-ramp-removed result?',
    sources=dict(tenv3=URL, steps=STEPS_URL, steps_sha256=hashlib.sha256((RAW/'NGL_steps.txt').read_bytes()).hexdigest(), retrieved=RETRIEVED),
    icmx_quality_warning='INEGI RGNA currently states ICMX data are unavailable until further notice because interference generates low-quality observations (https://www.inegi.org.mx/app/geo2/rgna/). Treated as an unquantified systematic risk; see reliability and stress test.',
    qc=qcinfo,
    geometry=dict(source='mintpy_redundant/inputs/geometryGeo.h5', heading_deg=heading, azimuth_deg=float(az), orbit=ga['ORBIT_DIRECTION'],
                  mintpy_version='1.6.4', sign='positive = motion toward satellite (MintPy enu2los; ifgram_inversion phase2range = -wavelength/4pi)',
                  formula='LOS = -E sin(i) sin(a) + N sin(i) cos(a) + U cos(i)', pixel_rule='floor((coord - X_FIRST|Y_FIRST)/STEP); corner-registered grid', stations=geom),
    insar_reference=dict(REF_DATE=ts_attrs['REF_DATE'], REF_Y=ts_attrs['REF_Y'], REF_X=ts_attrs['REF_X'], per_case=case_attrs),
    matching=dict(tolerance_days=TOL_DAYS, rule='nearest cleaned daily 24-h NGL solution within +/-1 day of the Sentinel-1 date; ties to preceding day; no interpolation',
                  sentinel_dates=sar_dates, MMX1_2024_span=mmx1_span, sentinel_dates_in_common_window=sar_in_window, common_dates=common,
                  details=[dict(sentinel=d, ICMX=mI[d]['date'], ICMX_offset=mI[d]['offset_days'], MMX1=mM[d]['date'], MMX1_offset=mM[d]['offset_days']) for d in common],
                  exact_date_pairs=exact, tolerance_sensitivity=tol_sens),
    gnss_differential=dict(rate_mm_yr=g_rate*1000, ols_ci95=[(g_rate-g_hw)*1000, (g_rate+g_hw)*1000], block_boot_ci95=(g_ci_boot*1000).tolist(),
                           theil_sen_mm_yr=g_ts_rate*1000, raw_unfiltered_rate_mm_yr=g_raw_rate*1000, raw_common_dates=raw_common,
                           daily_common_window_rate_mm_yr=g_daily_rate*1000, daily_common_window_n=len(dd),
                           daily_all_shared_2024_rate_mm_yr=g_daily_all_rate*1000, daily_all_shared_2024_span=[dd_all[0], dd_all[-1]], daily_all_shared_2024_n=len(dd_all),
                           series_mm=(g_d*1000).tolist()),
    ramp_plane=plane, patches=patch, comparisons=rows_out, decision=decision, reliability=reliability,
    regional=dict(per_station=regional, summary=regional_summary, note='Outside-AOI stations use nearest-edge incidence and are frame/common-mode diagnostics only; they do not sample the InSAR plane.'),
)
with open(EV/'gnss_los_results.json', 'w') as f:
    json.dump(out, f, indent=1, default=js)
with open(EV/'gnss_los_comparison.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0])); w.writeheader(); w.writerows(rows_out)

# ---------------------------------------------------------------- figures
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
CASE_COL = dict(zip(CASES, ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']))
CASE_LAB = {'A_redundant_no_ramp': 'A  redundant, no ramp', 'B_redundant_linear_ramp': 'B  redundant, linear ramp',
            'C_ERA5_no_ramp': 'C  ERA5, no ramp', 'D_ERA5_linear_ramp': 'D  ERA5, linear ramp'}
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.facecolor': 'white', 'axes.titleweight': 'bold', 'axes.titlesize': 9.5})
import matplotlib.dates as mdates
MF = mdates.DateFormatter('%b')


def sar_ticks(ax, dates=sar_dates):
    for d in dates:
        ax.axvline(dt64(d), color=GRID, lw=.8, zorder=0)


# 1. ENU small multiples
fig, axs = plt.subplots(3, 5, figsize=(15, 7.5), sharex=True, constrained_layout=True)
for j, s in enumerate(STATIONS):
    r = r2024[s]; t = np.array([np.datetime64(q['date']) for q in r]); inc_ = np.array([q['included'] for q in r])
    for i, (c, lab) in enumerate([('east_m', 'East'), ('north_m', 'North'), ('up_m', 'Up')]):
        ax = axs[i, j]; z = (np.array([q[c] for q in r]) - np.median([q[c] for q in r]))*1000
        sar_ticks(ax)
        ax.plot(t[inc_], z[inc_], '.', ms=2.5, color='#2a78d6', label='retained')
        if (~inc_).any():
            ax.plot(t[~inc_], z[~inc_], 'x', ms=6, mew=1.5, color='#e34948', label='excluded (QC)')
        if j == 0: ax.set_ylabel(f'{lab} (mm, 2024 median removed)')
        if i == 0: ax.set_title(f"{s}  ({'inside AOI' if geom[s]['inside_aoi'] else 'outside AOI'};  {qcinfo[s]['cleaned_count_2024']}/{qcinfo[s]['count_2024']} days)")
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,4,7,10])); ax.xaxis.set_major_formatter(MF); ax.set_xlim(np.datetime64('2024-01-01'), np.datetime64('2024-12-31'))
axs[0, 1].legend(loc='lower left', fontsize=8, frameon=False)
fig.suptitle('NGL IGS20 daily ENU, 2024 — raw solutions with QC exclusions (thin vertical lines = Sentinel-1 dates)', fontsize=11, color=INK)
fig.savefig(EV/'fig_gnss_enu_timeseries.png', dpi=200); plt.close(fig)

# 2. LOS small multiples + differential
fig = plt.figure(figsize=(15, 8), constrained_layout=True); gs = fig.add_gridspec(2, 5, height_ratios=[1, 1.1])
ax0 = None
for j, s in enumerate(STATIONS):
    ax = fig.add_subplot(gs[0, j], sharey=ax0); ax0 = ax0 or ax
    c = clean_rows(s); t = np.array([np.datetime64(q['date']) for q in c]); z = np.array([q['los_m'] for q in c])*1000
    z -= np.median(z); sar_ticks(ax); ax.plot(t, z, '.', ms=2, color='#2a78d6')
    m = match(c, TOL_DAYS); mt = [dt64(d) for d in m]; mz = [(m[d]['los_m']*1000) - np.median([q['los_m'] for q in c])*1000 for d in m]
    ax.plot(mt, mz, 'o', ms=4, mfc='white', mec=INK, mew=1, label='matched to S1 (±1 d)')
    ax.set_title(f"{s}: {regional[s]['los_mm_yr']:+.0f} mm/yr" + ('' if geom[s]['inside_aoi'] else ' (outside AOI)'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,4,7,10])); ax.xaxis.set_major_formatter(MF); ax.set_xlim(np.datetime64('2024-01-01'), np.datetime64('2024-12-31'))
    if j == 0: ax.set_ylabel('LOS toward satellite (mm, median removed)'); ax.legend(fontsize=8, frameon=False, loc='lower left')
ax = fig.add_subplot(gs[1, :]); sar_ticks(ax)
ax.plot(dd_all_t, np.array([cI[d]['los_m']-cM[d]['los_m'] for d in dd_all])*1000 - g_d[0]*1000, '.', ms=3, color='#9c9b96', label='all shared clean days')
ax.plot(ct, (g_d-g_d[0])*1000, 'o-', color=INK, lw=2, ms=6, label=f'S1-matched epochs: {g_rate*1000:.1f} mm/yr (95% {g_rate*1000-g_hw*1000:.1f}–{g_rate*1000+g_hw*1000:.1f})')
ax.set_title('ICMX − MMX1 GNSS LOS differential (reference-invariant); first matched epoch = 0'); ax.set_ylabel('mm'); ax.legend(frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.suptitle('GNSS projected into Sentinel-1 descending LOS with per-station incidence (cleaned series; shared y-scale in top row)', fontsize=11, color=INK)
fig.savefig(EV/'fig_gnss_los_timeseries.png', dpi=200); plt.close(fig)

# 3. GNSS vs InSAR differential
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True, gridspec_kw=dict(width_ratios=[1.3, 1]))
a1.plot(ct, (g_d-g_d.mean())*1000, 'o-', color=INK, lw=2.4, ms=7, label=f'GNSS  {g_rate*1000:.0f} mm/yr', zorder=5)
for cname in CASES:
    z = insar_diff(cname, PRIMARY_PATCH, common); r = next(q for q in rows_out if q['case'] == cname and q['patch_size_px'] == PRIMARY_PATCH)
    a1.plot(ct, (z-z.mean())*1000, 'o-', color=CASE_COL[cname], lw=2, ms=5, label=f"{CASE_LAB[cname]}  {r['insar_diff_common_mm_yr']:.0f} mm/yr")
a1.set_title(f'ICMX − MMX1 LOS, {len(common)} common epochs, {PRIMARY_PATCH}×{PRIMARY_PATCH} px patches (mean offset removed)')
a1.set_ylabel('Differential LOS (mm)'); a1.legend(frameon=False, fontsize=8.5); a1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
names = list(CASES); yy = np.arange(len(names))[::-1]
for y, cname in zip(yy, names):
    dcs = decision[cname]; r = next(q for q in rows_out if q['case'] == cname and q['patch_size_px'] == PRIMARY_PATCH)
    a2.errorbar(dcs['gnss_minus_insar_mm_yr'], y, xerr=dcs['U95'], fmt='o', ms=8, color=CASE_COL[cname], capsize=5, lw=2)
    a2.errorbar(dcs['gnss_minus_insar_mm_yr'], y, xerr=dcs['stat_halfwidth_ar1'], fmt='none', color=INK, capsize=0, lw=4, alpha=.35)
    a2.text(dcs['gnss_minus_insar_mm_yr'], y+.22, f"{dcs['gnss_minus_insar_mm_yr']:+.1f} mm/yr;  |Δ|/U95 = {abs(dcs['gnss_minus_insar_mm_yr'])/dcs['U95']:.2f}  ({dcs['verdict']})", ha='center', fontsize=8.5, color=INK)
a2.axvline(0, color=INK2, lw=1); a2.set_yticks(yy, [CASE_LAB[c] for c in names]); a2.set_ylim(-.6, len(names)-.3)
a2.set_xlabel('GNSS − InSAR differential rate (mm/yr)'); a2.set_title('Discrepancy: thick = statistical 95%, whiskers = stat+systematic U95')
fig.savefig(EV/'fig_gnss_vs_insar_differential.png', dpi=200); plt.close(fig)

# 4. patch sensitivity
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
a1.axhspan((g_rate-g_hw)*1000, (g_rate+g_hw)*1000, color='#0b0b0b', alpha=.08, lw=0)
a1.axhline(g_rate*1000, color=INK, lw=2); a1.text(13.3, g_rate*1000, 'GNSS\n(95%)', va='center', fontsize=8.5, color=INK)
for k, cname in enumerate(CASES):
    rr = [q for q in rows_out if q['case'] == cname]; xo = (k-1.5)*.18
    a1.errorbar([q['patch_size_px']+xo for q in rr], [q['insar_diff_common_mm_yr'] for q in rr],
                yerr=[[q['insar_diff_common_mm_yr']-q['insar_diff_ci95_lo'] for q in rr], [q['insar_diff_ci95_hi']-q['insar_diff_common_mm_yr'] for q in rr]],
                fmt='o-', color=CASE_COL[cname], ms=6, lw=2, capsize=3, label=CASE_LAB[cname])
    a1.plot([q['patch_size_px']+xo for q in rr], [q['insar_diff_full_period_mm_yr'] for q in rr], 's', mfc='white', mec=CASE_COL[cname], ms=6)
a1.set_xticks(PATCHES, [f'{n}×{n}\n({n*80} m)' for n in PATCHES]); a1.set_xlim(3.8, 14.4)
a1.set_ylabel('ICMX − MMX1 LOS velocity (mm/yr)'); a1.set_title('InSAR differential vs patch size (● common window, □ full-year, NON-equivalent)')
a1.legend(frameon=False, fontsize=8, loc='center left')
for k, cname in enumerate(CASES):
    for n in PATCHES:
        v = [patch[cname][s][str(n)]['velocity_mad_mm_yr'] for s in PRIMARY]
        a2.bar(PATCHES.index(n)*5+k, v[0], color=CASE_COL[cname], width=.42, label=CASE_LAB[cname] if n == 5 else None)
        a2.bar(PATCHES.index(n)*5+k+.44, v[1], color=CASE_COL[cname], width=.42, alpha=.45)
a2.set_xticks([1.7, 6.7, 11.7], [f'{n}×{n} px' for n in PATCHES]); a2.set_ylabel('Within-patch robust MAD of velocity (mm/yr)')
a2.set_title('Patch dispersion (solid = ICMX, faded = MMX1)'); a2.legend(frameon=False, fontsize=8)
fig.savefig(EV/'fig_patch_sensitivity.png', dpi=200); plt.close(fig)

print(json.dumps(dict(common=common, exact=exact, mmx1_span=mmx1_span, gnss=out['gnss_differential'] | {'series_mm': None},
                      decision=decision, plane=plane, tol=tol_sens,
                      excluded={s: qcinfo[s]['excluded'] for s in STATIONS}, steps2024={s: qcinfo[s]['ngl_steps_2023_12_to_2025_01'] for s in STATIONS},
                      jumps={s: qcinfo[s]['jump_candidates'] for s in STATIONS}, geom={s: {k: geom[s][k] for k in ['y', 'x', 'incidence_deg', 'los_e', 'los_n', 'los_u', 'pixel_centre_offset_m']} for s in STATIONS},
                      rel={s: reliability[s] for s in PRIMARY}, regional=regional, rsum=regional_summary,
                      table=[{k: r[k] for k in ['case', 'patch_size_px', 'insar_diff_common_mm_yr', 'gnss_minus_insar_mm_yr', 'gmi_ci95_ar1_lo', 'gmi_ci95_ar1_hi', 'gmi_ci95_blockboot_lo', 'gmi_ci95_blockboot_hi', 'aligned_rmse_mm', 'correlation', 'detrended_correlation', 'gmi_raw_gnss_mm_yr', 'gmi_theilsen_mm_yr', 'gmi_leave_one_out_min', 'gmi_leave_one_out_max', 'gmi_tol0_exact_mm_yr', 'gmi_tol2_mm_yr', 'insar_diff_full_period_mm_yr', 'valid_px_ICMX', 'valid_px_MMX1', 'tcoh_median_ICMX', 'tcoh_median_MMX1']} for r in rows_out]),
                 indent=1, default=js))
