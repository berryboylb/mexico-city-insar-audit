#!/usr/bin/env python3
import csv
import json
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

ROOT = Path("mintpy")
OUT = ROOT / "audit"
OUT.mkdir(exist_ok=True)

CASES = {
    "A_raw": OUT / "velocity_A_raw.h5",
    "B_topo": OUT / "velocity_B_topo.h5",
    "C_raw_linearRamp": OUT / "velocity_C_raw_linearRamp.h5",
    "D_topo_linearRamp": OUT / "velocity_D_topo_linearRamp.h5",
    "E_raw_quadraticRamp_exploratory": OUT / "velocity_E_raw_quadraticRamp_exploratory.h5",
    "E_topo_quadraticRamp_exploratory": OUT / "velocity_E_topo_quadraticRamp_exploratory.h5",
}

TS_CASES = {
    "A_raw": ROOT / "timeseries.h5",
    "B_topo": ROOT / "timeseries_demErr.h5",
    "C_raw_linearRamp": OUT / "timeseries_raw_linearRamp.h5",
    "D_topo_linearRamp": OUT / "timeseries_topo_linearRamp.h5",
    "E_raw_quadraticRamp_exploratory": OUT / "timeseries_raw_quadraticRamp.h5",
    "E_topo_quadraticRamp_exploratory": OUT / "timeseries_topo_quadraticRamp.h5",
}

def read(path, dataset):
    with h5py.File(path, "r") as f:
        return f[dataset][:], dict(f.attrs)

mask, _ = read(ROOT / "maskTempCoh.h5", "mask")
mask = mask.astype(bool)
height, geom_attrs = read(ROOT / "inputs/geometryGeo.h5", "height")
dem_err, _ = read(ROOT / "demErr.h5", "dem")
baseline, vel_attrs = read(ROOT / "velocity.h5", "velocity")

dates_by_case = {}
for name, path in TS_CASES.items():
    with h5py.File(path, "r") as f:
        dates_by_case[name] = [x.decode() for x in f["date"][:]]
if len({tuple(x) for x in dates_by_case.values()}) != 1:
    raise RuntimeError("Audit time-series date lists differ")

h, w = height.shape
x = float(geom_attrs["X_FIRST"]) + np.arange(w) * float(geom_attrs["X_STEP"])
y = float(geom_attrs["Y_FIRST"]) + np.arange(h) * float(geom_attrs["Y_STEP"])
xx, yy = np.meshgrid(x, y)
extent = [x.min(), x.max(), y.min(), y.max()]

def valid_for(arr):
    return mask & np.isfinite(arr) & (arr != 0) & np.isfinite(height) & (height != 0)

def plane_stats(arr, valid):
    xk = (xx[valid] - np.mean(xx[valid])) / 1000.0
    yk = (yy[valid] - np.mean(yy[valid])) / 1000.0
    A = np.column_stack((xk, yk, np.ones(valid.sum())))
    coef, _, _, _ = np.linalg.lstsq(A, arr[valid], rcond=None)
    fit = A @ coef
    ssr = np.sum((arr[valid] - fit) ** 2)
    sst = np.sum((arr[valid] - np.mean(arr[valid])) ** 2)
    return float(coef[0]), float(coef[1]), float(1 - ssr / sst)

def corr(a, b, valid):
    v = valid & np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[v], b[v])[0, 1])

baseline_valid = valid_for(baseline)
dem_valid = mask & np.isfinite(dem_err) & np.isfinite(height) & (height != 0)
dem_elev_corr = corr(dem_err, height, dem_valid)

stats = {}
arrays = {}
for name, path in CASES.items():
    arr, _ = read(path, "velocity")
    arrays[name] = arr
    valid = valid_for(arr)
    vals = arr[valid]
    east, north, plane_r2 = plane_stats(arr, valid)
    dv = arr - baseline
    dvalid = valid & baseline_valid
    stats[name] = {
        "valid_pixels": int(valid.sum()),
        "min_m_per_yr": float(vals.min()),
        "p05_m_per_yr": float(np.percentile(vals, 5)),
        "median_m_per_yr": float(np.median(vals)),
        "p95_m_per_yr": float(np.percentile(vals, 95)),
        "max_m_per_yr": float(vals.max()),
        "east_gradient_mm_per_yr_per_km": east * 1000,
        "north_gradient_mm_per_yr_per_km": north * 1000,
        "plane_r2": plane_r2,
        "velocity_elevation_corr": corr(arr, height, valid),
        "dem_error_elevation_corr": dem_elev_corr,
        "baseline_diff_median_mm_per_yr": float(np.median(dv[dvalid]) * 1000),
        "baseline_diff_rmse_mm_per_yr": float(np.sqrt(np.mean(dv[dvalid] ** 2)) * 1000),
        "baseline_diff_p05_mm_per_yr": float(np.percentile(dv[dvalid], 5) * 1000),
        "baseline_diff_p95_mm_per_yr": float(np.percentile(dv[dvalid], 95) * 1000),
        "baseline_diff_max_abs_mm_per_yr": float(np.max(np.abs(dv[dvalid])) * 1000),
    }

# Candidate 9x9 reference patches. Existing patch is centered on the stored
# reference pixel. Terrain candidates maximize mean elevation while requiring
# at least 50 valid pixels within the named geographic search sector.
radius = 4
def patch(center_y, center_x):
    return (slice(max(0, center_y-radius), min(h, center_y+radius+1)),
            slice(max(0, center_x-radius), min(w, center_x+radius+1)))

def select_high_patch(region):
    best = None
    for cy in range(radius, h-radius):
        for cx in range(radius, w-radius):
            if not region[cy, cx]:
                continue
            sl = patch(cy, cx)
            vm = baseline_valid[sl]
            if vm.sum() < 50:
                continue
            score = float(np.mean(height[sl][vm]))
            if best is None or score > best[0]:
                best = (score, cy, cx)
    if best is None:
        raise RuntimeError("No valid candidate reference patch")
    return best[1], best[2]

west_region = np.zeros_like(mask)
west_region[:2*h//3, :w//3] = True
southwest_region = np.zeros_like(mask)
southwest_region[2*h//3:, :w//2] = True
patch_centers = {
    "north_existing": (int(vel_attrs["REF_Y"]), int(vel_attrs["REF_X"])),
    "west_high_terrain": select_high_patch(west_region),
    "southwest_high_terrain": select_high_patch(southwest_region),
}

patches = {}
for pname, (cy, cx) in patch_centers.items():
    sl = patch(cy, cx)
    vm = baseline_valid[sl]
    patches[pname] = {
        "center_y": cy, "center_x": cx,
        "y_min": sl[0].start, "y_max_inclusive": sl[0].stop - 1,
        "x_min": sl[1].start, "x_max_inclusive": sl[1].stop - 1,
        "center_easting_m": float(xx[cy, cx]),
        "center_northing_m": float(yy[cy, cx]),
        "valid_pixels": int(vm.sum()),
        "mean_elevation_m": float(np.mean(height[sl][vm])),
        "median_elevation_m": float(np.median(height[sl][vm])),
    }

# Re-reference the baseline by subtracting each patch mean. The operation is
# a spatially uniform constant, so plane slopes and all pairwise differences
# are invariant to floating-point precision.
reference_tests = {}
for ref_name, ref_info in patches.items():
    sl = (slice(ref_info["y_min"], ref_info["y_max_inclusive"]+1),
          slice(ref_info["x_min"], ref_info["x_max_inclusive"]+1))
    vm = baseline_valid[sl]
    offset = float(np.mean(baseline[sl][vm]))
    reref = baseline - offset
    east, north, _ = plane_stats(reref, baseline_valid)
    local_rates = {}
    for local_name, local_info in patches.items():
        lsl = (slice(local_info["y_min"], local_info["y_max_inclusive"]+1),
               slice(local_info["x_min"], local_info["x_max_inclusive"]+1))
        lvm = baseline_valid[lsl]
        local_rates[local_name] = float(np.mean(reref[lsl][lvm]))
    reference_tests[ref_name] = {
        "subtracted_patch_mean_m_per_yr": offset,
        "rereferenced_median_m_per_yr": float(np.median(reref[baseline_valid])),
        "east_gradient_mm_per_yr_per_km": east * 1000,
        "north_gradient_mm_per_yr_per_km": north * 1000,
        "local_patch_rates_m_per_yr": local_rates,
    }

# Bridge-interferogram diagnostics.
bridge_pairs = ["20240512_20240629", "20240629_20240804"]
bridge = {}
bridge_arrays = {}
with h5py.File(ROOT / "inputs/ifgramStack.h5", "r") as f:
    pairs = [f"{a.decode()}_{b.decode()}" for a, b in f["date"][:]]
    unw = f["unwrapPhase"]
    wavelength = float(f.attrs["WAVELENGTH"])
    for pair in bridge_pairs:
        idx = pairs.index(pair)
        phase = unw[idx, :, :]
        valid = mask & np.isfinite(phase) & (phase != 0)
        east, north, r2 = plane_stats(phase, valid)
        dx = np.abs(np.diff(phase, axis=1)); dxv = valid[:, 1:] & valid[:, :-1]
        dy = np.abs(np.diff(phase, axis=0)); dyv = valid[1:, :] & valid[:-1, :]
        jumps = np.concatenate((dx[dxv], dy[dyv]))
        labels, ncomp = ndimage.label(valid)
        sizes = np.bincount(labels.ravel())[1:]
        bridge[pair] = {
            "valid_pixels": int(valid.sum()),
            "valid_fraction_pct": float(valid.mean() * 100),
            "connected_valid_regions": int(ncomp),
            "largest_region_fraction_of_valid": float(sizes.max()/valid.sum()) if sizes.size else 0,
            "east_phase_gradient_rad_per_km": east,
            "north_phase_gradient_rad_per_km": north,
            "plane_r2": r2,
            "adjacent_jump_p95_rad": float(np.percentile(jumps, 95)),
            "adjacent_jump_p99_rad": float(np.percentile(jumps, 99)),
            "adjacent_jump_max_rad": float(jumps.max()),
        }
        bridge_arrays[pair] = phase * (-wavelength / (4*np.pi)) * 100.0

results = {
    "dates": dates_by_case["A_raw"],
    "common_mask_pixels": int(mask.sum()),
    "dem_error_elevation_corr": dem_elev_corr,
    "cases": stats,
    "reference_patches": patches,
    "reference_tests": reference_tests,
    "bridge_interferograms": bridge,
}
(OUT / "audit_results.json").write_text(json.dumps(results, indent=2) + "\n")

with open(OUT / "case_statistics.csv", "w", newline="") as f:
    fields = ["case"] + list(next(iter(stats.values())).keys())
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for name, values in stats.items(): writer.writerow({"case": name, **values})

with open(OUT / "reference_sensitivity.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["reference", "subtracted_patch_mean_m_per_yr", "rereferenced_median_m_per_yr",
                     "east_gradient_mm_per_yr_per_km", "north_gradient_mm_per_yr_per_km",
                     "rate_at_north_patch_m_per_yr", "rate_at_west_patch_m_per_yr", "rate_at_southwest_patch_m_per_yr"])
    for name, v in reference_tests.items():
        lr = v["local_patch_rates_m_per_yr"]
        writer.writerow([name, v["subtracted_patch_mean_m_per_yr"], v["rereferenced_median_m_per_yr"],
                         v["east_gradient_mm_per_yr_per_km"], v["north_gradient_mm_per_yr_per_km"],
                         lr["north_existing"], lr["west_high_terrain"], lr["southwest_high_terrain"]])

def add_map(ax, data, title, cmap, vmin=None, vmax=None, cbar_label=""):
    d = np.where(mask, data, np.nan)
    im = ax.imshow(d, extent=extent, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(title)
    ax.set_xlabel("UTM easting (m), EPSG:32614")
    ax.set_ylabel("UTM northing (m), EPSG:32614")
    ax.ticklabel_format(style="plain", axis="both", useOffset=False)
    cb = plt.colorbar(im, ax=ax, shrink=0.84)
    cb.set_label(cbar_label)
    return im

common_vals = np.concatenate([arrays["A_raw"][baseline_valid], arrays["B_topo"][baseline_valid]])
vlo, vhi = np.percentile(common_vals, [1, 99]) * 1000
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
add_map(axs[0], arrays["A_raw"]*1000, "A. Raw velocity", "RdBu_r", vlo, vhi, "Relative LOS velocity (mm/yr)")
add_map(axs[1], arrays["B_topo"]*1000, "B. Topography-corrected velocity", "RdBu_r", vlo, vhi, "Relative LOS velocity (mm/yr)")
fig.savefig(OUT / "fig_raw_vs_topography_corrected_velocity.png", dpi=220); plt.close(fig)

sel = ["A_raw", "C_raw_linearRamp", "B_topo", "D_topo_linearRamp"]
allv = np.concatenate([arrays[n][baseline_valid] for n in sel]) * 1000
vlo2, vhi2 = np.percentile(allv, [1, 99])
titles = ["Raw: no ramp", "Raw: linear ramp removed", "Topo-corrected: no ramp", "Topo-corrected: linear ramp removed"]
fig, axs = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
for ax, n, title in zip(axs.flat, sel, titles): add_map(ax, arrays[n]*1000, title, "RdBu_r", vlo2, vhi2, "Relative LOS velocity (mm/yr)")
fig.savefig(OUT / "fig_no_ramp_vs_linear_ramp_velocity.png", dpi=220); plt.close(fig)

diff_names = ["A_raw", "C_raw_linearRamp", "D_topo_linearRamp", "E_topo_quadraticRamp_exploratory"]
diffs = [(arrays[n]-baseline)*1000 for n in diff_names]
dlim = np.percentile(np.abs(np.concatenate([d[baseline_valid] for d in diffs])), 99)
fig, axs = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
for ax, n, d in zip(axs.flat, diff_names, diffs): add_map(ax, d, f"{n} minus baseline", "RdBu_r", -dlim, dlim, "Velocity difference (mm/yr)")
fig.savefig(OUT / "fig_velocity_difference_maps.png", dpi=220); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
dl = np.percentile(np.abs(dem_err[dem_valid]), 99)
add_map(ax, dem_err, "Estimated DEM error", "RdBu_r", -dl, dl, "DEM error (m)")
fig.savefig(OUT / "fig_dem_error.png", dpi=220); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
hv = height[mask & np.isfinite(height) & (height != 0)]
add_map(ax, height, "Elevation", "terrain", np.percentile(hv, 1), np.percentile(hv, 99), "Elevation (m)")
fig.savefig(OUT / "fig_elevation.png", dpi=220); plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(16, 5.2), constrained_layout=True)
rv = []
for name, p in patches.items():
    sl = (slice(p["y_min"], p["y_max_inclusive"]+1), slice(p["x_min"], p["x_max_inclusive"]+1))
    vm = baseline_valid[sl]; rv.append((name, baseline - np.mean(baseline[sl][vm])))
rvals = np.concatenate([a[baseline_valid] for _, a in rv])*1000
rlo, rhi = np.percentile(rvals, [1, 99])
for ax, (name, a) in zip(axs, rv):
    add_map(ax, a*1000, f"Referenced to {name}", "RdBu_r", rlo, rhi, "Relative LOS velocity (mm/yr)")
    for pn, p in patches.items(): ax.plot(p["center_easting_m"], p["center_northing_m"], "ks" if pn==name else "k+", ms=5)
fig.savefig(OUT / "fig_alternative_reference_comparison.png", dpi=220); plt.close(fig)

bvals = np.concatenate([a[mask & np.isfinite(a) & (a != 0)] for a in bridge_arrays.values()])
blim = np.percentile(np.abs(bvals), 99)
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
for ax, pair in zip(axs, bridge_pairs): add_map(ax, bridge_arrays[pair], pair, "RdBu_r", -blim, blim, "Relative LOS displacement (cm)")
fig.suptitle("Bridge interferograms (unwrapped phase converted with -lambda/4pi)")
fig.savefig(OUT / "fig_bridge_interferograms.png", dpi=220); plt.close(fig)

print(json.dumps(results, indent=2))
