#!/usr/bin/env python3
import csv, json, itertools
from pathlib import Path
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import ndimage

ROOT = Path('mintpy_redundant')
OUT = ROOT / 'audit'
OUT.mkdir(exist_ok=True)
stack_file = ROOT / 'inputs/ifgramStack.h5'

with h5py.File(stack_file, 'r') as f:
    pairs = [(a.decode(), b.decode()) for a,b in f['date'][:]]
    phase = f['unwrapPhase'][:]
    coherence = f['coherence'][:]
    attrs = dict(f.attrs)
ref_y, ref_x = int(attrs['REF_Y']), int(attrs['REF_X'])
ref_phase = phase[:, ref_y, ref_x].copy()
phase_ref = phase.copy()
for i in range(len(pairs)):
    nz = phase_ref[i] != 0
    phase_ref[i, nz] -= ref_phase[i]

pair_index = {p:i for i,p in enumerate(pairs)}
nodes = sorted(set(sum(([a,b] for a,b in pairs), [])))
triangles = [t for t in itertools.combinations(nodes, 3)
             if (t[0],t[1]) in pair_index and (t[0],t[2]) in pair_index and (t[1],t[2]) in pair_index]
water = h5py.File(ROOT/'waterMask.h5','r')['waterMask'][:].astype(bool)
avg_coh = h5py.File(ROOT/'avgSpatialCoh.h5','r')['coherence'][:]
mask_conn = h5py.File(ROOT/'maskConnComp.h5','r')['mask'][:].astype(bool)
base_mask = water & np.isfinite(avg_coh) & (avg_coh != 0)

results=[]
ambiguities=[]
for a,b,c in triangles:
    ids=[pair_index[(a,b)],pair_index[(b,c)],pair_index[(a,c)]]
    closure = phase_ref[ids[0]] + phase_ref[ids[1]] - phase_ref[ids[2]]
    wrapped = -np.pi + np.mod(closure + np.pi, 2*np.pi)
    ambiguity = np.round((closure - wrapped)/(2*np.pi)).astype(np.int16)
    valid3 = base_mask & np.all(phase[ids] != 0, axis=0)
    fail = valid3 & (ambiguity != 0)
    mintpy_fail = base_mask & (ambiguity != 0)
    tri_coh = np.nanmean(coherence[ids],axis=0)
    labels,ncomp = ndimage.label(fail)
    sizes=np.bincount(labels.ravel())[1:]
    qcounts={}
    h,w=fail.shape
    quadrants={'NW':(slice(0,h//2),slice(0,w//2)),'NE':(slice(0,h//2),slice(w//2,w)),
               'SW':(slice(h//2,h),slice(0,w//2)),'SE':(slice(h//2,h),slice(w//2,w))}
    for q,sl in quadrants.items(): qcounts[q]=int(fail[sl].sum())
    results.append({
      'triangle':f'{a}_{b}_{c}', 'edge_ab':f'{a}_{b}', 'edge_bc':f'{b}_{c}', 'edge_ac':f'{a}_{c}',
      'valid_three_edge_pixels':int(valid3.sum()), 'nonzero_ambiguity_pixels':int(fail.sum()),
      'nonzero_ambiguity_pct':float(100*fail.sum()/valid3.sum()),
      'mintpy_compatible_nonzero_pixels':int(mintpy_fail.sum()),
      'failure_mean_coherence':float(np.mean(tri_coh[fail])) if fail.any() else None,
      'pass_mean_coherence':float(np.mean(tri_coh[valid3 & ~fail])) if np.any(valid3 & ~fail) else None,
      'failure_in_common_connected_mask_pct':float(100*np.sum(fail & mask_conn)/fail.sum()) if fail.any() else None,
      'failure_components':int(ncomp), 'largest_failure_component_pixels':int(sizes.max()) if sizes.size else 0,
      'ambiguity_min':int(ambiguity[fail].min()) if fail.any() else 0,
      'ambiguity_max':int(ambiguity[fail].max()) if fail.any() else 0,
      **{f'fail_{q}':v for q,v in qcounts.items()}
    })
    ambiguities.append(ambiguity)

ambiguities=np.asarray(ambiguities)
aggregate=np.sum(ambiguities != 0,axis=0).astype(float)
aggregate[~base_mask]=np.nan
aggregate[aggregate==len(triangles)]=np.nan
mintpy_agg=h5py.File(ROOT/'numTriNonzeroIntAmbiguity.h5','r')['mask'][:]
cmp=np.isfinite(aggregate)&np.isfinite(mintpy_agg)
match=bool(np.array_equal(aggregate[cmp],mintpy_agg[cmp]))

edge_scores={p:0 for p in pairs}
edge_fail_pixels={p:0 for p in pairs}
for row in results:
    for key in ['edge_ab','edge_bc','edge_ac']:
        p=tuple(row[key].split('_'))
        edge_scores[p]+=1
        edge_fail_pixels[p]+=row['nonzero_ambiguity_pixels']

with open(OUT/'closure_triangle_statistics.csv','w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=list(results[0].keys())); wr.writeheader(); wr.writerows(results)
with open(OUT/'closure_interferogram_flags.csv','w',newline='') as f:
    wr=csv.writer(f); wr.writerow(['interferogram','triangles_participated','summed_triangle_failure_pixels','added_pair'])
    added={'20240113_20240206','20240301_20240325','20240430_20240629','20240629_20240816','20240828_20240921','20241027_20241120','20241202_20241226'}
    for p in pairs: wr.writerow(['_'.join(p),edge_scores[p],edge_fail_pixels[p],('_'.join(p) in added)])

summary={'reference_yx':[ref_y,ref_x], 'triangle_count':len(triangles),
 'mintpy_aggregate_exact_match_on_joint_finite_pixels':match,
 'mintpy_valid_pixels':int(np.isfinite(mintpy_agg).sum()),
 'mintpy_nonzero_pixels':int(np.sum(np.isfinite(mintpy_agg)&(mintpy_agg>0))),
 'mintpy_nonzero_pct':float(100*np.sum(np.isfinite(mintpy_agg)&(mintpy_agg>0))/np.isfinite(mintpy_agg).sum()),
 'mintpy_max_failed_triangles_per_pixel':int(np.nanmax(mintpy_agg)), 'triangles':results}
(OUT/'closure_results.json').write_text(json.dumps(summary,indent=2)+'\n')

x0=float(attrs['X_FIRST']); xs=float(attrs['X_STEP']); y0=float(attrs['Y_FIRST']); ys=float(attrs['Y_STEP'])
h,w=mintpy_agg.shape
extent=[x0,x0+w*xs,y0+h*ys,y0]
fig,axs=plt.subplots(2,4,figsize=(16,8),constrained_layout=True)
for ax,row,amb in zip(axs.flat,results,ambiguities):
    shown=np.where(base_mask & (amb!=0),amb,np.nan)
    im=ax.imshow(shown,extent=extent,origin='upper',cmap='RdBu_r',vmin=-2,vmax=2,interpolation='nearest')
    ax.set_title(row['triangle'].replace('_','–')+'\n'+f"{row['nonzero_ambiguity_pct']:.2f}% failed")
    ax.set_xlabel('UTM easting (m), EPSG:32614'); ax.set_ylabel('UTM northing (m), EPSG:32614')
    ax.ticklabel_format(style='plain',axis='both',useOffset=False)
axs.flat[-1].axis('off')
fig.colorbar(im,ax=axs[:,:],shrink=.75,label='Integer closure ambiguity (cycles)')
fig.savefig(OUT/'closure_failures_by_triangle.png',dpi=220); plt.close(fig)

fig,ax=plt.subplots(figsize=(7,6),constrained_layout=True)
im=ax.imshow(mintpy_agg,extent=extent,origin='upper',cmap='magma',vmin=0,vmax=max(1,np.nanmax(mintpy_agg)),interpolation='nearest')
ax.set_title('Triangles with non-zero integer closure ambiguity')
ax.set_xlabel('UTM easting (m), EPSG:32614'); ax.set_ylabel('UTM northing (m), EPSG:32614')
ax.ticklabel_format(style='plain',axis='both',useOffset=False)
fig.colorbar(im,ax=ax,label='Number of failed triangles')
fig.savefig(OUT/'closure_failure_count.png',dpi=220); plt.close(fig)
print(json.dumps(summary,indent=2))
