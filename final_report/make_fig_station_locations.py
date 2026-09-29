#!/usr/bin/env python3
"""Station-location figure: ICMX and MMX1 on the case-A (redundant, no-ramp) velocity map.

Reads existing outputs only; writes fig_station_locations.png/.pdf into final_report/.
No processing is rerun. Run with the project mounted read-only and final_report/ writable:

  docker run --rm --platform linux/amd64 --network none \
    -v "$PWD":/data:ro -v "$PWD/final_report":/data/final_report -w /data \
    ghcr.io/insarlab/mintpy:latest python final_report/make_fig_station_locations.py

Coordinate-to-pixel conversion is the one validated in
external_validation/run_gnss_los_validation.py (pyproj EPSG:4326 -> raster EPSG, then
floor((coord - X_FIRST|Y_FIRST)/STEP) on the corner-registered grid). The script asserts
that it reproduces the stored station pixels and the stored 9x9 patch medians.
"""
import json
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

ROOT = Path('/data')
OUT = ROOT / 'final_report'
RES = json.loads((ROOT / 'external_validation/gnss_los_results.json').read_text())

# Case A exactly as used in the GNSS validation (CASES['A_redundant_no_ramp'])
VEL_FILE = ROOT / 'mintpy_redundant/audit/velocity_B_topo.h5'
GEOM_FILE = ROOT / 'mintpy_redundant/inputs/geometryGeo.h5'
MASK_FILES = [ROOT / 'mintpy_redundant/maskTempCoh.h5', ROOT / 'mintpy_redundant_era5/maskTempCoh.h5']
PATCH = 9
STATIONS = {'ICMX': dict(marker='^', dx=-0.2, dy=-0.9, ha='left', va='top'),
            'MMX1': dict(marker='s', dx=0.35, dy=0.9, ha='left', va='bottom')}

INK, INK2, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
# Diverging blue <-> red with neutral grey midpoint (0 = reference pixel's velocity)
CMAP = LinearSegmentedColormap.from_list(
    'blue_grey_red', ['#0d366b', '#2a78d6', '#9ec5f4', '#f0efec', '#f4a6a3', '#e34948', '#8a1c1c'])

# ------------------------------------------------------------------ inputs
with h5py.File(VEL_FILE, 'r') as f:
    vel = f['velocity'][()] * 1000.0          # m/yr -> mm/yr
    va = {k: (v.decode() if isinstance(v, bytes) else str(v)) for k, v in f.attrs.items()}
with h5py.File(GEOM_FILE, 'r') as f:
    ga = dict(f.attrs)
mask = np.ones(vel.shape, bool)
for mf in MASK_FILES:
    with h5py.File(mf, 'r') as f:
        mask &= f['mask'][()].astype(bool)     # common mask, as in the GNSS validation

assert va.get('mintpy.deramp', 'None') in ('None', 'no'), va['mintpy.deramp']   # no-ramp case
start, end = va['START_DATE'], va['END_DATE']
ref_y, ref_x = int(va['REF_Y']), int(va['REF_X'])
epsg = int(ga['EPSG'])
X0, Y0, DX, DY = (float(ga[k]) for k in ['X_FIRST', 'Y_FIRST', 'X_STEP', 'Y_STEP'])
ny, nx = vel.shape

# ------------------------------------- validated coordinate-to-pixel conversion
tr = Transformer.from_crs(4326, epsg, always_xy=True)
stored = RES['geometry']['stations']
st = {}
for s in STATIONS:
    lat, lon = stored[s]['latitude'], stored[s]['longitude']
    xu, yu = tr.transform(lon, lat)
    px = int(np.floor((xu - X0) / DX)); py = int(np.floor((yu - Y0) / DY))
    assert (py, px) == (stored[s]['y'], stored[s]['x']), (s, py, px)
    assert abs(xu - stored[s]['utm_x']) < 1e-3 and abs(yu - stored[s]['utm_y']) < 1e-3, s
    h = PATCH // 2
    ys, xs = slice(py - h, py + h + 1), slice(px - h, px + h + 1)
    vm = mask[ys, xs] & np.isfinite(vel[ys, xs])
    med = float(np.median(vel[ys, xs][vm]))
    rec = RES['patches']['A_redundant_no_ramp'][s][str(PATCH)]['velocity_median_mm_yr']
    assert vm.sum() == PATCH * PATCH and abs(med - rec) < 1e-3, (s, med, rec)
    st[s] = dict(lat=lat, lon=lon, x=xu, y=yu, px=px, py=py, med=med)

win = RES['matching']['common_dates']
win0, win1 = f'{win[0][:4]}-{win[0][4:6]}-{win[0][6:]}', f'{win[-1][:4]}-{win[-1][4:6]}-{win[-1][6:]}'
fmt = lambda d: f'{d[:4]}-{d[4:6]}-{d[6:]}'

# ------------------------------------------------------------------ figure
km = 1e-3
extent = [X0 * km, (X0 + nx * DX) * km, (Y0 + ny * DY) * km, Y0 * km]   # pixel edges
shown = np.where(mask & np.isfinite(vel), vel, np.nan)
lim = float(np.ceil(np.nanpercentile(np.abs(shown), 99.5) / 10) * 10)

plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
                     'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK})
fig, ax = plt.subplots(figsize=(7.4, 7.6), facecolor=SURF)
ax.set_facecolor('#d9d8d4')      # masked / invalid pixels
im = ax.imshow(shown, extent=extent, origin='upper', cmap=CMAP, vmin=-lim, vmax=lim,
               interpolation='nearest')

# 9x9-pixel extraction patches (pixel-edge outlines) and station markers
for s, sty in STATIONS.items():
    p = st[s]; h = PATCH // 2
    x_left = (X0 + (p['px'] - h) * DX) * km
    y_top = (Y0 + (p['py'] - h) * DY) * km
    ax.add_patch(Rectangle((x_left, y_top + PATCH * DY * km), PATCH * DX * km, -PATCH * DY * km,
                           fill=False, ec=INK, lw=1.4, zorder=4))
    ax.plot(p['x'] * km, p['y'] * km, sty['marker'], ms=5.5, mfc=INK, mec='white', mew=1.0, zorder=6)
    ax.annotate(f"{s}\n{p['lat']:.4f}° N, {p['lon']:.4f}°\npixel Y/X {p['py']}/{p['px']}",
                (p['x'] * km, p['y'] * km), xytext=(p['x'] * km + sty['dx'], p['y'] * km + sty['dy']),
                ha=sty['ha'], va=sty['va'], fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85), zorder=7)

# Baseline between the station coordinates
a, b = st['ICMX'], st['MMX1']
ax.plot([a['x'] * km, b['x'] * km], [a['y'] * km, b['y'] * km], '-', color=INK, lw=1.6, zorder=5)
de, dn = (b['x'] - a['x']) * km, (b['y'] - a['y']) * km
mx, my = (a['x'] + b['x']) / 2 * km, (a['y'] + b['y']) / 2 * km
ax.annotate(f'ICMX–MMX1 baseline {np.hypot(de, dn):.1f} km\n({de:.2f} km E, {dn:.2f} km N)',
            (mx, my), xytext=(-6, 14), textcoords='offset points', ha='center', va='bottom', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85), zorder=7)

# InSAR reference pixel (single pixel), marked separately
rx0, ry0 = (X0 + ref_x * DX) * km, (Y0 + ref_y * DY) * km
rcx, rcy = rx0 + DX * km / 2, ry0 + DY * km / 2
ax.add_patch(Rectangle((rx0, ry0 + DY * km), DX * km, -DY * km, fill=False, ec=INK, lw=1.0, zorder=4))
ax.plot(rcx, rcy, '*', ms=15, mfc='white', mec=INK, mew=1.2, zorder=6)
ax.annotate(f'InSAR reference pixel Y/X {ref_y}/{ref_x}\n(velocity ≡ 0; ref. date {fmt(va["REF_DATE"])})',
            (rcx, rcy), xytext=(rcx - 0.6, rcy - 1.2), ha='right', va='top', fontsize=8,
            arrowprops=dict(arrowstyle='-', color=INK, lw=0.8, shrinkB=6),
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85), zorder=7)

# Scale bar (2 km) and grid-north arrow, lower left
x_sb, y_sb = extent[0] + 1.2, extent[2] + 1.2
ax.add_patch(Rectangle((x_sb - 0.3, y_sb - 0.45), 2.6, 1.25, fc='white', ec='none', alpha=0.85, zorder=6))
ax.plot([x_sb, x_sb + 2], [y_sb, y_sb], '-', color=INK, lw=3, solid_capstyle='butt', zorder=7)
ax.text(x_sb + 1, y_sb + 0.2, '2 km', ha='center', va='bottom', fontsize=8, zorder=7)
ax.annotate('', xy=(extent[1] - 1.2, extent[2] + 2.6), xytext=(extent[1] - 1.2, extent[2] + 1.0),
            arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.4), zorder=7)
ax.text(extent[1] - 1.2, extent[2] + 2.7, 'N (grid)', ha='center', va='bottom', fontsize=8, zorder=7)

ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
ax.set_aspect('equal')
ax.set_xlabel(f'UTM easting (km), WGS 84 / UTM zone 14N (EPSG:{epsg})')
ax.set_ylabel(f'UTM northing (km), EPSG:{epsg}')
ax.ticklabel_format(useOffset=False, style='plain')

cb = fig.colorbar(im, ax=ax, orientation='horizontal', fraction=0.045, pad=0.09, extend='both')
cb.set_label('Relative LOS velocity (mm/yr), Sentinel-1 descending; '
             'positive = toward satellite, relative to reference pixel')
cb.outline.set_visible(False)

ax.set_title('Case A (redundant network, topographic correction, no ramp removal)\n'
             f'Velocity map: linear fit to 25 acquisitions, {fmt(start)} to {fmt(end)} (full year)\n'
             f'Shorter GNSS comparison window: {win0} to {win1} ({len(win)} epochs)',
             fontsize=9, loc='left')
fig.text(0.01, 0.005,
         f'Outlined squares: {PATCH}×{PATCH}-pixel ({PATCH*80} m) extraction patches; patch-median velocity '
         f'ICMX {st["ICMX"]["med"]:.1f}, MMX1 {st["MMX1"]["med"]:.1f} mm/yr\n'
         '(full-year values, not the GNSS-window rates). Grey: no data or outside the common temporal-coherence mask.\n'
         'Station coordinates: median 2024 NGL IGS20 positions. Sources: '
         'mintpy_redundant/audit/velocity_B_topo.h5; external_validation/gnss_los_results.json.',
         fontsize=6.8, color=INK2, va='bottom')
fig.tight_layout(rect=(0, 0.06, 1, 1))
for ext in ('png', 'pdf'):
    fig.savefig(OUT / f'fig_station_locations.{ext}', dpi=300, facecolor=SURF)
print(json.dumps({s: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()} for s, d in st.items()},
                 indent=1), 'colour limit ±', lim, 'mm/yr')
