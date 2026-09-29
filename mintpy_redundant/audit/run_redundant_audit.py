#!/usr/bin/env python3
import csv,json
from pathlib import Path
import h5py,numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path('mintpy_redundant'); O=R/'audit'; B=Path('mintpy')
CASES={
'A_raw':O/'velocity_A_raw.h5','B_topo_primary':O/'velocity_B_topo.h5',
'C_raw_linearRamp':O/'velocity_C_raw_linearRamp.h5','D_topo_linearRamp':O/'velocity_D_topo_linearRamp.h5',
'E_exclude_flagged_raw':O/'velocity_E_exclude_flagged_raw.h5','F_exclude_flagged_topo':O/'velocity_F_exclude_flagged_topo.h5'}
def rd(p,d):
 with h5py.File(p,'r') as f:return f[d][:],dict(f.attrs)
mask,_=rd(R/'maskTempCoh.h5','mask'); mask=mask.astype(bool)
height,ga=rd(R/'inputs/geometryGeo.h5','height'); dem,_=rd(R/'demErr.h5','dem')
old,_=rd(B/'velocity.h5','velocity'); oldmask,_=rd(B/'maskTempCoh.h5','mask'); oldmask=oldmask.astype(bool)
new,va=rd(R/'velocity.h5','velocity'); tc,_=rd(R/'temporalCoherence.h5','temporalCoherence'); oldtc,_=rd(B/'temporalCoherence.h5','temporalCoherence')
h,w=new.shape;x=float(ga['X_FIRST'])+np.arange(w)*float(ga['X_STEP']);y=float(ga['Y_FIRST'])+np.arange(h)*float(ga['Y_STEP']);xx,yy=np.meshgrid(x,y);extent=[x.min(),x.max(),y.min(),y.max()]
common=mask&oldmask&np.isfinite(height)&(height!=0)&np.isfinite(old)&np.isfinite(new)&(old!=0)&(new!=0)
def valid(a):return mask&np.isfinite(a)&(a!=0)&np.isfinite(height)&(height!=0)
def plane(a,m):
 X=np.c_[((xx[m]-xx[m].mean())/1000),((yy[m]-yy[m].mean())/1000),np.ones(m.sum())];c=np.linalg.lstsq(X,a[m],rcond=None)[0]; fit=np.full(a.shape,np.nan);fit[m]=X@c;return c,fit
def corr(a,b,m):return float(np.corrcoef(a[m],b[m])[0,1])
def summarize(a,m,base):
 v=a[m];c,fit=plane(a,m);d=a-base; dm=m&np.isfinite(base)&(base!=0)
 return {'valid_pixels':int(m.sum()),'min_mm_yr':float(v.min()*1000),'p05_mm_yr':float(np.percentile(v,5)*1000),'median_mm_yr':float(np.median(v)*1000),'p95_mm_yr':float(np.percentile(v,95)*1000),'max_mm_yr':float(v.max()*1000),'east_gradient_mm_yr_km':float(c[0]*1000),'north_gradient_mm_yr_km':float(c[1]*1000),'velocity_elevation_corr':corr(a,height,m),'baseline_diff_median_mm_yr':float(np.median(d[dm])*1000),'baseline_diff_p05_mm_yr':float(np.percentile(d[dm],5)*1000),'baseline_diff_p95_mm_yr':float(np.percentile(d[dm],95)*1000),'baseline_diff_rmse_mm_yr':float(np.sqrt(np.mean(d[dm]**2))*1000),'baseline_diff_maxabs_mm_yr':float(np.max(np.abs(d[dm]))*1000)}
arr={k:rd(p,'velocity')[0] for k,p in CASES.items()}; stats={k:summarize(a,valid(a),old) for k,a in arr.items()}
demm=mask&np.isfinite(dem)&np.isfinite(height)&(height!=0); demcorr=corr(dem,height,demm)
diff=new-old; dc=diff[common]
co,fo=plane(old,common);cn,fn=plane(new,common); oldlocal=old-fo;newlocal=new-fn
local={'old_new_detrended_corr':corr(oldlocal,newlocal,common),'old_new_detrended_rmse_mm_yr':float(np.sqrt(np.mean((newlocal[common]-oldlocal[common])**2))*1000)}
# Compare ramp-corrected products directly.
oldr,_=rd(B/'audit/velocity_D_topo_linearRamp.h5','velocity'); newr=arr['D_topo_linearRamp']; rm=common&np.isfinite(oldr)&np.isfinite(newr)&(oldr!=0)&(newr!=0)
local['old_new_linear_ramp_corr']=corr(oldr,newr,rm);local['old_new_linear_ramp_rmse_mm_yr']=float(np.sqrt(np.mean((newr[rm]-oldr[rm])**2))*1000)
# Fixed 9x9 candidate patches from the prior audit.
centers={'north_existing':(7,186),'west_high_terrain':(152,4),'southwest_high_terrain':(341,4)};refs={}
for rn,(cy,cx) in centers.items():
 sl=(slice(max(0,cy-4),min(h,cy+5)),slice(max(0,cx-4),min(w,cx+5))); pm=valid(new)[sl];off=float(np.mean(new[sl][pm])); rr=new-off;c,_=plane(rr,valid(new));loc={}
 for ln,(ly,lx) in centers.items():
  ls=(slice(max(0,ly-4),min(h,ly+5)),slice(max(0,lx-4),min(w,lx+5)));lm=valid(new)[ls];loc[ln]=float(np.mean(rr[ls][lm])*1000)
 refs[rn]={'center_yx':[cy,cx],'center_utm_m':[float(xx[cy,cx]),float(yy[cy,cx])],'valid_pixels':int(pm.sum()),'mean_elevation_m':float(np.mean(height[sl][pm])),'subtracted_rate_mm_yr':off*1000,'rereferenced_median_mm_yr':float(np.median(rr[valid(new)])*1000),'east_gradient_mm_yr_km':float(c[0]*1000),'north_gradient_mm_yr_km':float(c[1]*1000),'local_patch_rates_mm_yr':loc}
def read_rms(p):
 out={}
 for line in Path(p).read_text().splitlines():
  if line and not line.startswith('#'):a,b=line.split();out[a]=float(b)
 return out
rms_new=read_rms(R/'rms_timeseriesResidual_ramp.txt');rms_old=read_rms(B/'rms_timeseriesResidual_ramp.txt')
tcm=mask&np.isfinite(tc)&(tc>0);otcm=oldmask&np.isfinite(oldtc)&(oldtc>0)
tcstats={'redundant_valid':int(tcm.sum()),'redundant_min':float(tc[tcm].min()),'redundant_p05':float(np.percentile(tc[tcm],5)),'redundant_median':float(np.median(tc[tcm])),'redundant_mean':float(np.mean(tc[tcm])),'redundant_p95':float(np.percentile(tc[tcm],95)),'redundant_max':float(tc[tcm].max()),'original_median':float(np.median(oldtc[otcm])),'original_fraction_exactly_one':float(np.mean(oldtc[otcm]==1))}
comparison={'common_pixels':int(common.sum()),'difference_min_mm_yr':float(dc.min()*1000),'difference_p05_mm_yr':float(np.percentile(dc,5)*1000),'difference_median_mm_yr':float(np.median(dc)*1000),'difference_p95_mm_yr':float(np.percentile(dc,95)*1000),'difference_max_mm_yr':float(dc.max()*1000),'difference_rmse_mm_yr':float(np.sqrt(np.mean(dc**2))*1000),'original_east_gradient_mm_yr_km':float(co[0]*1000),'redundant_east_gradient_mm_yr_km':float(cn[0]*1000),'east_gradient_change_mm_yr_km':float((cn[0]-co[0])*1000),'original_north_gradient_mm_yr_km':float(co[1]*1000),'redundant_north_gradient_mm_yr_km':float(cn[1]*1000),**local}
closure=json.loads((O/'closure_results.json').read_text())
closure_count,_=rd(R/'numTriNonzeroIntAmbiguity.h5','mask'); cm=common&np.isfinite(closure_count)&(closure_count>0); clean=common&np.isfinite(closure_count)&(closure_count==0)
iy,ix=np.unravel_index(np.nanargmax(np.where(common,np.abs(diff),np.nan)),diff.shape)
comparison.update({'fraction_abs_difference_gt5mm':float(np.mean(np.abs(dc)*1000>5)),'fraction_abs_difference_gt10mm':float(np.mean(np.abs(dc)*1000>10)),'fraction_abs_difference_gt20mm':float(np.mean(np.abs(dc)*1000>20)),'difference_rmse_closure_failure_pixels_mm_yr':float(np.sqrt(np.mean(diff[cm]**2))*1000),'difference_rmse_closure_clean_pixels_mm_yr':float(np.sqrt(np.mean(diff[clean]**2))*1000),'max_abs_difference_yx':[int(iy),int(ix)],'max_abs_difference_utm_m':[float(xx[iy,ix]),float(yy[iy,ix])],'max_abs_difference_mm_yr':float(abs(diff[iy,ix])*1000)})
res={'cases':stats,'baseline_comparison':comparison,'dem_error_elevation_corr':demcorr,'reference_sensitivity':refs,'temporal_coherence':tcstats,'residual_rms_m':{'original':rms_old,'redundant':rms_new},'closure':closure}
(O/'audit_results.json').write_text(json.dumps(res,indent=2)+'\n')
with open(O/'case_statistics.csv','w',newline='') as f:
 fs=['case']+list(next(iter(stats.values())).keys());wr=csv.DictWriter(f,fieldnames=fs);wr.writeheader();[wr.writerow({'case':k,**v}) for k,v in stats.items()]
with open(O/'reference_sensitivity.csv','w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['reference','center_y','center_x','easting_m','northing_m','valid_pixels','mean_elevation_m','subtracted_rate_mm_yr','map_median_mm_yr','east_gradient_mm_yr_km','north_gradient_mm_yr_km','north_local_mm_yr','west_local_mm_yr','southwest_local_mm_yr']);
 for k,v in refs.items():wr.writerow([k,*v['center_yx'],*v['center_utm_m'],v['valid_pixels'],v['mean_elevation_m'],v['subtracted_rate_mm_yr'],v['rereferenced_median_mm_yr'],v['east_gradient_mm_yr_km'],v['north_gradient_mm_yr_km'],*v['local_patch_rates_mm_yr'].values()])
def amap(ax,a,title,vmin,vmax,label,cmap='RdBu_r',m=mask):
 im=ax.imshow(np.where(m,a,np.nan),extent=extent,origin='upper',cmap=cmap,vmin=vmin,vmax=vmax,interpolation='nearest');ax.set_title(title);ax.set_xlabel('UTM easting (m), EPSG:32614');ax.set_ylabel('UTM northing (m), EPSG:32614');ax.ticklabel_format(style='plain',axis='both',useOffset=False);plt.colorbar(im,ax=ax,shrink=.82,label=label)
vals=np.r_[old[common],new[common]]*1000;lo,hi=np.percentile(vals,[1,99]);fig,ax=plt.subplots(1,3,figsize=(17,5),constrained_layout=True);amap(ax[0],old*1000,'Original 24-pair velocity',lo,hi,'Relative LOS velocity (mm/yr)',m=common);amap(ax[1],new*1000,'Redundant 31-pair velocity',lo,hi,'Relative LOS velocity (mm/yr)',m=common);dl=np.percentile(np.abs(dc*1000),99);amap(ax[2],diff*1000,'Redundant minus original',-dl,dl,'Difference (mm/yr)',m=common);fig.savefig(O/'fig_baseline_vs_redundant_velocity.png',dpi=220);plt.close(fig)
sel=['A_raw','B_topo_primary','C_raw_linearRamp','D_topo_linearRamp'];vv=np.concatenate([arr[k][valid(arr[k])] for k in sel])*1000;lo,hi=np.percentile(vv,[1,99]);fig,ax=plt.subplots(2,2,figsize=(12,10),constrained_layout=True)
for a,k in zip(ax.flat,sel):amap(a,arr[k]*1000,k,lo,hi,'Relative LOS velocity (mm/yr)')
fig.savefig(O/'fig_ramp_topography_sensitivity.png',dpi=220);plt.close(fig)
fig,ax=plt.subplots(1,3,figsize=(17,5),constrained_layout=True);rvals=[]
for rn,v in refs.items():rvals.append((rn,new-v['subtracted_rate_mm_yr']/1000))
rv=np.concatenate([a[valid(new)] for _,a in rvals])*1000;lo,hi=np.percentile(rv,[1,99])
for a,(rn,z) in zip(ax,rvals):amap(a,z*1000,'Reference: '+rn,lo,hi,'Relative LOS velocity (mm/yr)');[a.plot(xx[cy,cx],yy[cy,cx],'k+',ms=6) for cy,cx in centers.values()]
fig.savefig(O/'fig_reference_sensitivity.png',dpi=220);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5),constrained_layout=True);amap(ax[0],tc,'Redundant temporal coherence',0.7,1,'Temporal coherence','viridis');ax[1].hist(tc[tcm],bins=50,alpha=.7,label='31-pair');ax[1].hist(oldtc[otcm],bins=50,alpha=.5,label='24-pair');ax[1].set_xlabel('Temporal coherence');ax[1].set_ylabel('Pixels');ax[1].legend();fig.savefig(O/'fig_temporal_coherence_comparison.png',dpi=220);plt.close(fig)
dates=sorted(rms_new);fig,ax=plt.subplots(figsize=(11,4.5),constrained_layout=True);ax.plot(dates,[rms_old[d]*1000 for d in dates],'-o',ms=3,label='24-pair');ax.plot(dates,[rms_new[d]*1000 for d in dates],'-o',ms=3,label='31-pair');ax.set_ylabel('Residual RMS (mm)');ax.tick_params(axis='x',rotation=60);ax.legend();fig.savefig(O/'fig_residual_rms_comparison.png',dpi=220);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5),constrained_layout=True);dv=dem[demm];amap(ax[0],dem,'Redundant estimated DEM error',*np.percentile(dv,[1,99]),'DEM error (m)',m=demm);hv=height[demm];amap(ax[1],height,'Elevation',*np.percentile(hv,[1,99]),'Elevation (m)','terrain',demm);fig.savefig(O/'fig_dem_error_elevation.png',dpi=220);plt.close(fig)
# Representative point time series at prior p05/p50/p95 coordinates.
pts={'p05':(66,222),'p50':(21,97),'p95':(108,14)}; ots,_=rd(B/'timeseries_demErr.h5','timeseries');nts,_=rd(R/'timeseries_demErr.h5','timeseries');dates=np.array([np.datetime64(d[:4]+'-'+d[4:6]+'-'+d[6:]) for d in sorted(rms_new)])
fig,ax=plt.subplots(3,1,figsize=(10,10),sharex=True,constrained_layout=True)
for a,(pn,(py,px)) in zip(ax,pts.items()):a.plot(dates,(ots[:,py,px]-ots[0,py,px])*100,'-o',ms=3,label='24-pair');a.plot(dates,(nts[:,py,px]-nts[0,py,px])*100,'-o',ms=3,label='31-pair');a.set_ylabel('Relative LOS displacement (cm)');a.set_title(f'{pn}: Y/X={py},{px}, UTM={xx[py,px]:.0f},{yy[py,px]:.0f} m');a.legend()
fig.savefig(O/'fig_representative_point_timeseries.png',dpi=220);plt.close(fig)
print(json.dumps(res,indent=2))
