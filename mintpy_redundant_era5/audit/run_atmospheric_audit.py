#!/usr/bin/env python3
import csv, json
from pathlib import Path
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('/data')
OUT = ROOT / 'mintpy_redundant_era5' / 'audit'
OUT.mkdir(parents=True, exist_ok=True)

def read(path, ds):
    with h5py.File(ROOT / path, 'r') as f:
        return np.squeeze(f[ds][()]), dict(f.attrs)

mask, _ = read('mintpy_redundant/maskTempCoh.h5', 'mask')
mask = mask.astype(bool)
closure, _ = read('mintpy_redundant/numTriNonzeroIntAmbiguity.h5', 'mask')
closure_fail = np.isfinite(closure) & (closure > 0)
geom, ga = read('mintpy_redundant/inputs/geometryGeo.h5', 'height')

case_paths = {
    'A_baseline_no_ramp': ('mintpy_redundant/audit/velocity_B_topo.h5', 'velocity'),
    'B_baseline_linear_ramp': ('mintpy_redundant/audit/velocity_D_topo_linearRamp.h5', 'velocity'),
    'C_ERA5_no_ramp': ('mintpy_redundant_era5/velocity_ERA5.h5', 'velocity'),
    'D_ERA5_linear_ramp': ('mintpy_redundant_era5/audit/velocity_ERA5_linearRamp.h5', 'velocity'),
}
cases = {k: read(*v)[0].astype(float) * 1000 for k, v in case_paths.items()}
common = mask.copy()
for a in cases.values(): common &= np.isfinite(a) & (a != 0)

y, x = np.indices(mask.shape)
east = (float(ga['X_FIRST']) + x * float(ga['X_STEP'])) / 1000
north = (float(ga['Y_FIRST']) + y * float(ga['Y_STEP'])) / 1000

def plane_stats(a):
    z = a[common]; xx = east[common]; yy = north[common]
    xc, yc = xx - xx.mean(), yy - yy.mean()
    G = np.column_stack([np.ones(z.size), xc, yc])
    b = np.linalg.lstsq(G, z, rcond=None)[0]
    fit = G @ b
    r2 = 1 - np.sum((z-fit)**2) / np.sum((z-z.mean())**2)
    plane_range = float(fit.max() - fit.min())
    return dict(east_gradient_mm_yr_km=float(b[1]), north_gradient_mm_yr_km=float(b[2]),
                gradient_magnitude_mm_yr_km=float(np.hypot(b[1], b[2])),
                fitted_plane_peak_to_peak_mm_yr=plane_range, fitted_plane_variance_explained=float(r2))

stats = {}
for name, a in cases.items():
    z = a[common]
    stats[name] = dict(valid_pixels=int(z.size), min_mm_yr=float(z.min()),
        p05_mm_yr=float(np.percentile(z,5)), median_mm_yr=float(np.median(z)),
        p95_mm_yr=float(np.percentile(z,95)), max_mm_yr=float(z.max()), **plane_stats(a))

def diffstats(a, b, subset=common):
    z = (a-b)[subset & np.isfinite(a) & np.isfinite(b)]
    return dict(n=int(z.size), min=float(z.min()), p05=float(np.percentile(z,5)),
                median=float(np.median(z)), mean=float(z.mean()), p95=float(np.percentile(z,95)),
                max=float(z.max()), rms=float(np.sqrt(np.mean(z*z))))

A, B, C, D = [cases[k] for k in case_paths]
comparisons = {
    'ERA5_minus_baseline_no_ramp_mm_yr': diffstats(C,A),
    'ERA5_minus_baseline_linear_ramp_mm_yr': diffstats(D,B),
    'ramp_effect_baseline_mm_yr': diffstats(B,A),
    'ramp_effect_ERA5_mm_yr': diffstats(D,C),
    'ERA5_change_closure_failure_mm_yr': diffstats(C,A,common & closure_fail),
    'ERA5_change_closure_clean_mm_yr': diffstats(C,A,common & ~closure_fail),
    'spatial_correlation_baseline_vs_ERA5_no_ramp': float(np.corrcoef(A[common],C[common])[0,1]),
    'spatial_correlation_baseline_vs_ERA5_linear_ramp': float(np.corrcoef(B[common],D[common])[0,1]),
}
delta = C - A
edge10 = np.zeros_like(common)
edge10[:10, :] = edge10[-10:, :] = True
edge10[:, :10] = edge10[:, -10:] = True
min_yx = np.unravel_index(np.nanargmin(np.where(common, delta, np.nan)), delta.shape)
comparisons['ERA5_edge_diagnostic'] = {
    'minimum_change_yx': [int(min_yx[0]), int(min_yx[1])],
    'minimum_change_mm_yr': float(delta[min_yx]),
    'distance_to_array_edge_pixels': int(min(min_yx[0], delta.shape[0]-1-min_yx[0], min_yx[1], delta.shape[1]-1-min_yx[1])),
    'outer_10_pixel_rms_mm_yr': float(np.sqrt(np.mean(delta[common & edge10]**2))),
    'interior_rms_mm_yr': float(np.sqrt(np.mean(delta[common & ~edge10]**2))),
}
comparisons['plane_reduction'] = {
    'east_gradient_percent': float(100 * (abs(stats['A_baseline_no_ramp']['east_gradient_mm_yr_km']) - abs(stats['C_ERA5_no_ramp']['east_gradient_mm_yr_km'])) / abs(stats['A_baseline_no_ramp']['east_gradient_mm_yr_km'])),
    'gradient_magnitude_percent': float(100 * (stats['A_baseline_no_ramp']['gradient_magnitude_mm_yr_km'] - stats['C_ERA5_no_ramp']['gradient_magnitude_mm_yr_km']) / stats['A_baseline_no_ramp']['gradient_magnitude_mm_yr_km']),
    'plane_peak_to_peak_percent': float(100 * (stats['A_baseline_no_ramp']['fitted_plane_peak_to_peak_mm_yr'] - stats['C_ERA5_no_ramp']['fitted_plane_peak_to_peak_mm_yr']) / stats['A_baseline_no_ramp']['fitted_plane_peak_to_peak_mm_yr']),
    'variance_explained_absolute_change': float(stats['C_ERA5_no_ramp']['fitted_plane_variance_explained'] - stats['A_baseline_no_ramp']['fitted_plane_variance_explained']),
}

delay, da = read('mintpy_redundant_era5/ERA5.h5', 'timeseries')
with h5py.File(ROOT/'mintpy_redundant_era5/ERA5.h5','r') as f:
    delay_dates = [v.decode() for v in f['date'][()]]
with h5py.File(ROOT/'mintpy_redundant_era5/timeseries_demErr.h5','r') as f:
    input_dates = [v.decode() for v in f['date'][()]]
delay_checks = {'date_count':len(delay_dates), 'dates_match_input':delay_dates == input_dates,
                'missing_dates':sorted(set(input_dates)-set(delay_dates)), 'nan_count':int(np.isnan(delay).sum())}
per_date=[]
for i,d in enumerate(delay_dates):
    q=delay[i][mask & np.isfinite(delay[i])]
    gx=np.abs(np.diff(delay[i],axis=1)); gy=np.abs(np.diff(delay[i],axis=0))
    per_date.append(dict(date=d,min_m=float(q.min()),median_m=float(np.median(q)),max_m=float(q.max()),
        spatial_range_m=float(q.max()-q.min()),p99_neighbor_jump_m=float(np.nanpercentile(np.r_[gx.ravel(),gy.ravel()],99)),
        max_neighbor_jump_m=float(np.nanmax(np.r_[gx.ravel(),gy.ravel()]))))
delay_checks['per_date']=per_date
delay_checks['overall_min_m']=float(np.nanmin(delay)); delay_checks['overall_max_m']=float(np.nanmax(delay))
delay_checks['max_spatial_range_m']=max(v['spatial_range_m'] for v in per_date)
delay_checks['max_neighbor_jump_m']=max(v['max_neighbor_jump_m'] for v in per_date)

# Case statistics CSV
fields=['case','valid_pixels','min_mm_yr','p05_mm_yr','median_mm_yr','p95_mm_yr','max_mm_yr',
        'east_gradient_mm_yr_km','north_gradient_mm_yr_km','gradient_magnitude_mm_yr_km',
        'fitted_plane_peak_to_peak_mm_yr','fitted_plane_variance_explained']
with open(OUT/'case_statistics.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for k,v in stats.items(): w.writerow({'case':k,**v})

result={'common_valid_pixels':int(common.sum()),'cases':stats,'comparisons':comparisons,
        'delay_integrity':delay_checks,'reference':{'y':7,'x':186,'date':'20240909'},
        'acquisition_center_utc_seconds':45280.111419,'ERA5_hour_utc':13,
        'ERA5_SNWE':[10,30,-110,-90]}
with open(OUT/'audit_results.json','w') as f: json.dump(result,f,indent=2)

extent=[east.min(),east.max(),north.min(),north.max()]
def im(ax,a,title,vmin,vmax,cmap='RdBu_r'):
    q=np.where(common,a,np.nan); h=ax.imshow(q,extent=extent,origin='upper',cmap=cmap,vmin=vmin,vmax=vmax,aspect='equal')
    ax.set_title(title); ax.set_xlabel('UTM easting (km)'); ax.set_ylabel('UTM northing (km)'); return h

# Four comparable maps
lo=min(np.percentile(A[common],2),np.percentile(C[common],2)); hi=max(np.percentile(A[common],98),np.percentile(C[common],98))
fig,axs=plt.subplots(2,2,figsize=(13,11),constrained_layout=True)
for ax,(k,a) in zip(axs.ravel(),cases.items()):
    h=im(ax,a,k.replace('_',' '),lo,hi)
fig.colorbar(h,ax=axs,label='Relative LOS velocity (mm/yr)',shrink=.8)
fig.savefig(OUT/'fig_four_case_velocity_comparison.png',dpi=220); plt.close(fig)

# ERA5 changes and delay-derived velocity correction
delta_r=D-B
lim=np.percentile(np.abs(delta[common]),98)
fig,axs=plt.subplots(1,3,figsize=(17,5),constrained_layout=True)
h=im(axs[0],A,'Baseline, no ramp',lo,hi); fig.colorbar(h,ax=axs[0],label='mm/yr')
h=im(axs[1],C,'ERA5 corrected, no ramp',lo,hi); fig.colorbar(h,ax=axs[1],label='mm/yr')
h=im(axs[2],delta,'ERA5 minus baseline',-lim,lim); fig.colorbar(h,ax=axs[2],label='Velocity change (mm/yr)')
fig.savefig(OUT/'fig_ERA5_velocity_change.png',dpi=220); plt.close(fig)

# Plane/gradient summary
fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
names=list(stats); xx=np.arange(4); ew=[stats[k]['east_gradient_mm_yr_km'] for k in names]; ns=[stats[k]['north_gradient_mm_yr_km'] for k in names]
ax.bar(xx-.18,ew,.36,label='east-west'); ax.bar(xx+.18,ns,.36,label='north-south'); ax.axhline(0,color='k',lw=.8)
ax.set_xticks(xx,names,rotation=18,ha='right'); ax.set_ylabel('Fitted gradient (mm/yr/km)'); ax.legend()
fig.savefig(OUT/'fig_gradient_comparison.png',dpi=220); plt.close(fig)

# Delay snapshots and spatial range over time
inds=[0,len(delay_dates)//2,len(delay_dates)-1]
fig,axs=plt.subplots(1,3,figsize=(16,5),constrained_layout=True)
vals=np.concatenate([delay[i][mask] for i in inds]); dl,dh=np.percentile(vals,[2,98])
for ax,i in zip(axs,inds):
    q=np.where(mask,delay[i],np.nan); h=ax.imshow(q,extent=extent,origin='upper',cmap='viridis',vmin=dl,vmax=dh,aspect='equal'); ax.set_title(f'ERA5 LOS delay {delay_dates[i]}'); ax.set_xlabel('UTM easting (km)'); ax.set_ylabel('UTM northing (km)')
fig.colorbar(h,ax=axs,label='Absolute slant delay (m)',shrink=.8)
fig.savefig(OUT/'fig_ERA5_delay_maps.png',dpi=220); plt.close(fig)

# Representative patch time series, consistently referenced as stored
base_ts,_=read('mintpy_redundant_era5/timeseries_demErr.h5','timeseries'); era_ts,_=read('mintpy_redundant_era5/timeseries_demErr_ERA5.h5','timeseries')
pts={'north reference':(7,186),'west high terrain':(152,4),'southwest high terrain':(341,4)}
dates=np.array([f'{d[:4]}-{d[4:6]}-{d[6:8]}' for d in delay_dates], dtype='datetime64[D]')
fig,axs=plt.subplots(3,1,figsize=(11,10),sharex=True,constrained_layout=True)
for ax,(name,(cy,cx)) in zip(axs,pts.items()):
    ys=slice(max(0,cy-4),min(mask.shape[0],cy+5)); xs=slice(max(0,cx-4),min(mask.shape[1],cx+5))
    ax.plot(dates,np.nanmedian(np.where(mask[ys,xs],base_ts[:,ys,xs],np.nan),axis=(1,2))*1000,'o-',label='baseline')
    ax.plot(dates,np.nanmedian(np.where(mask[ys,xs],era_ts[:,ys,xs],np.nan),axis=(1,2))*1000,'o-',label='ERA5 corrected')
    ax.set_title(name); ax.set_ylabel('Relative LOS displacement (mm)'); ax.grid(alpha=.3); ax.legend()
fig.savefig(OUT/'fig_representative_timeseries_ERA5.png',dpi=220); plt.close(fig)

print(json.dumps({'common_valid_pixels':int(common.sum()),'cases':stats,'comparisons':comparisons,'delay_summary':{k:v for k,v in delay_checks.items() if k!='per_date'}},indent=2))
